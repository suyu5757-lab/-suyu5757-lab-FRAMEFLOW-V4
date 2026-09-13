"""The authoritative visual Prompt compiler for FrameFlow.

Semantic visual prompt decisions come from the versioned
``gpt-image-2-style-library`` catalog.  Only a short allow-list of production
invariants is added by FrameFlow: asset canvas ratio/output type and the
requested character four-zone reference-sheet layout.  Workflow state,
provider routing, QA diagnostics and IDs stay outside the copyable prompt.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Literal

from .asset_geometry import DEFAULT_BASE_ASSET_ASPECT_RATIOS, normalize_aspect_ratio
from .style_library_catalog import (
    PROMPT_BLOCKS,
    SELECTION_ORDER,
    STYLE_LIBRARY_SOURCE,
    STYLE_LIBRARY_SOURCE_PATH,
    STYLE_LIBRARY_SKILL_PATH,
    STYLE_LIBRARY_TEMPLATES,
    STYLE_LIBRARY_VERSION,
    TEMPLATES_BY_ID,
    style_library_snapshot,
)


PROMPT_CONTRACT_VERSION = "3.0-style-library"
PROMPT_WORKFLOW_ID = "style-library-visual-v1"
BASE_ASSET_PROMPT_COMPILER_VERSION = PROMPT_WORKFLOW_ID
BASE_ASSET_CLASSES = frozenset({"character", "scene", "prop", "product"})
VISUAL_ASSET_CLASSES = frozenset({"character", "scene", "prop", "product", "style", "fusion", "shot"})
PromptCompositionMode = Literal["style_library"]

_CLASS_ALIASES = {
    "environment": "scene",
    "environment_prop": "scene",
    "environment_state": "scene",
    "background": "scene",
    "landscape": "scene",
    "item": "prop",
    "vfx": "prop",
    "weapon_effect": "prop",
    "mechanical_effect": "prop",
    "dialogue": "audio",
    "voice": "audio",
    "mix": "audio",
}

# Only these values are inherited from the old production system.  They are
# hard constraints, not semantic prompt-writing rules.
FOUNDATIONAL_RULES = {
    "asset_canvas_ratio",
    "image_output_format",
    "character_four_zone_sheet",
    "fusion_and_shot_project_ratio",
}

LEGACY_PROMPT_MARKERS = (
    "suyu-skill-v2",
    "base-asset-v1",
    "legacy_supplement",
    "同时满足以下补充制作要求",
    "Prompt Contract",
    "FRAMEFLOW",
    "Image Execution Prompt",
    "资产 ID",
    "Prompt QA",
    "generationStatus",
    "imageGenerationEligible",
    "providerAspectRatio",
    "provider_aspect_ratio",
    "1536x1024",
    "1024x1024",
    "1024x1536",
    "openai",
    "OpenAI",
    "opencode",
    "OpenCode",
    "promptPack",
    "promptQuality",
    "user-confirmation-required",
    "generationNotes",
    "suggestedSize",
    "identityAnchor",
    "visibleEvent",
    "characterDetails",
    "sceneDetails",
    "propDetails",
    "fusionDetails",
    "shotPlan",
    "mustPreserve",
    "mustAvoid",
    "negativePrompt",
    "visualStyle",
    "cameraExecution",
    "lightingCausality",
    "atmosphereBehavior",
)

_JSON_FIELD_PATTERN = re.compile(r"[\{\}\[\]]")
_PIXEL_SIZE_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d{3,5}\s*[x×]\s*\d{3,5}(?![A-Za-z0-9])", re.I)
_INTERNAL_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:ASSET|ARTIFACT|PROMPT|RUN|C|P|S|SH|FUSION)[_-]?\d{1,5}[A-Z]?(?![A-Za-z0-9])", re.I)
_COMMAND_MARKERS = ("请返回", "请上传", "请保存", "进入下一阶段", "调用", "Provider", "供应商", "工作台")
_STYLE_LABELS = {
    "3D": "3D",
    "Architecture": "建筑空间",
    "Brand": "品牌视觉",
    "Character": "角色设计",
    "Characters": "人物表现",
    "Charts": "图表信息可视化",
    "Classical": "古典气质",
    "Documents": "出版物版式",
    "History": "历史题材",
    "Illustration": "插画",
    "Infographic": "信息图",
    "Other Use Cases": "特殊研发视觉",
    "Photography": "摄影",
    "Poster": "海报排版",
    "Product": "产品视觉",
    "Products": "商品视觉",
    "Realistic": "写实",
    "Scenes": "场景叙事",
    "UI": "界面视觉",
}
_KEY_LABELS = {
    "subjectTask": "主体任务",
    "compositionLayout": "构图布局",
    "visualStyleMaterials": "视觉风格与材质",
    "textLabels": "文字标签",
    "aspectRatioOutput": "画面规格",
    "constraintsNegative": "限制",
    "actionContinuity": "动作与连续性",
    "role": "参考用途",
    "scope": "控制范围",
    "purpose": "用途",
    "camera": "机位",
    "framing": "景别",
    "focus": "焦点",
    "depthOfField": "景深",
    "screenDirection": "屏幕方向",
    "firstFrame": "首帧",
    "lastFrame": "尾帧",
}


def canonical_asset_class(asset_class: str | None) -> str:
    value = str(asset_class or "unknown").strip().lower()
    return _CLASS_ALIASES.get(value, value)


def is_base_asset_class(asset_class: str | None) -> bool:
    return canonical_asset_class(asset_class) in BASE_ASSET_CLASSES


def prompt_composition_mode_for_asset(asset_class: str | None, requested: str | None = None) -> str:
    """Keep the old call shape while making the new compiler the only mode."""

    del asset_class, requested
    return "style_library"


def _has(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(_has(item) for item in value)
    if isinstance(value, dict):
        return any(_has(item) for item in value.values())
    return True


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    if isinstance(value, list):
        return "；".join(item for item in (_text(child) for child in value) if item)
    if isinstance(value, dict):
        return "；".join(item for item in (_text(child) for child in value.values()) if item)
    return str(value).strip()


def _render(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "、".join(item for item in (_render(child) for child in value) if item)
    if isinstance(value, dict):
        parts = []
        for key, child in value.items():
            child_text = _render(child)
            if child_text:
                parts.append(f"{_KEY_LABELS.get(str(key), str(key))}为{child_text}")
        return "；".join(parts)
    return str(value).strip()


def render_prompt_value(value: Any) -> str:
    """Render structured values for internal handoffs without JSON syntax."""

    return _render(value)


def _first(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if _has(value):
            return value
    return None


def _list(value: Any) -> list[str]:
    raw = value if isinstance(value, list) else [value] if _has(value) else []
    result: list[str] = []
    for item in raw:
        rendered = _text(item)
        if rendered and rendered not in result:
            result.append(rendered)
    return result


def _clean_visual_text(value: Any) -> str:
    rendered = _text(value)
    if not rendered:
        return ""
    if any(marker in rendered for marker in LEGACY_PROMPT_MARKERS):
        return ""
    # IDs may remain in internal reference metadata, but never in the text
    # copied into an image generator.
    rendered = _INTERNAL_ID_PATTERN.sub("", rendered)
    rendered = re.sub(r"\s+", " ", rendered).strip(" ;；，,\n")
    return rendered


def _clean_visual_list(value: Any) -> list[str]:
    return list(dict.fromkeys(item for item in (_clean_visual_text(child) for child in (value if isinstance(value, list) else [value])) if item))


def _contains_legacy(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key) in LEGACY_PROMPT_MARKERS or _contains_legacy(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_legacy(child) for child in value)
    return any(marker in str(value or "") for marker in LEGACY_PROMPT_MARKERS)


def _path_value(source: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = source
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if _has(current):
            return current
    return None


_PROMPT_PACK_KEYS = set(PROMPT_BLOCKS) | {"templateSelection", "referenceRoles", "actionContinuity"}
_LEGACY_PROMPT_PACK_KEYS = {
    "promptIntent", "referenceStrategy", "generationReferenceAssets", "identityAnchor", "identityLock",
    "visibleEvent", "spatialGeography", "materialEvidence", "lightingCausality", "cameraExecution",
    "atmosphereBehavior", "characterDetails", "sceneDetails", "propDetails", "itemDetails", "fusionDetails",
    "shotPlan", "visualStyle", "continuityChecklist", "negativePrompt", "generationNotes", "suggestedSize",
    "detailAnchorRegistry", "mustPreserve", "mustAvoid",
}


def _prompt_pack_source(prompt_pack: Any) -> dict[str, Any]:
    source = prompt_pack if isinstance(prompt_pack, dict) else {}
    nested = source.get("promptPack") if isinstance(source.get("promptPack"), dict) else source
    return nested if isinstance(nested, dict) else {}


def _legacy_prompt_fields(source: dict[str, Any]) -> list[str]:
    return sorted(
        str(key)
        for key in source
        if str(key) in LEGACY_PROMPT_MARKERS or str(key) in _LEGACY_PROMPT_PACK_KEYS
    )


def _prompt_pack_requires_regeneration(prompt_pack: Any) -> bool:
    source = _prompt_pack_source(prompt_pack)
    return bool(_legacy_prompt_fields(source) and not any(_has(source.get(key)) for key in PROMPT_BLOCKS))


def _context_shots(context: dict[str, Any]) -> list[dict[str, Any]]:
    values = context.get("shots") or context.get("shot_context") or []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _context_references(context: dict[str, Any]) -> list[Any]:
    values = context.get("references") or []
    return values if isinstance(values, list) else []


def _selection_text(source: dict[str, Any], context: dict[str, Any], asset_class: str) -> str:
    values = [
        _first(source, "subjectTask", "subject_task", "task", "goal", "intent"),
        _first(source, "visualStyleMaterials", "visual_style_materials", "styleDescription", "appearance"),
        _first(source, "textLabels", "text_labels", "text", "labels"),
        _first(source, "compositionLayout", "composition_layout", "layout", "composition"),
        context.get("project_brief"),
        context.get("projectBrief"),
        asset_class,
    ]
    values.extend(_text(shot.get("purpose") or shot.get("action") or shot.get("scene")) for shot in _context_shots(context))
    return " ".join(item for item in (_clean_visual_text(value) for value in values) if item).lower()


def _default_template_id(asset_class: str, text: str) -> str:
    if asset_class == "character":
        return "3d-collectible-toy" if any(word in text for word in ("3d", "公仔", "潮玩", "盲盒", "玩具")) else "character-design-sheet"
    if asset_class == "scene":
        return "scene-storytelling" if any(word in text for word in ("故事", "叙事", "分镜", "人物", "情绪", "直播")) else "architecture-space"
    if asset_class == "prop":
        return "concept-product-breakdown"
    if asset_class == "product":
        return "product-commerce-visual"
    if asset_class == "fusion":
        return "scene-storytelling"
    if asset_class == "shot":
        return "scene-storytelling"
    if asset_class == "style":
        return "illustration-art-style"
    return "scene-storytelling"


def _template_class_score(asset_class: str, template: dict[str, Any]) -> int:
    category = str(template.get("category") or "")
    if asset_class == "character" and category == "Characters & People":
        return 60
    if asset_class == "scene" and category in {"Architecture & Spaces", "Scenes & Storytelling"}:
        return 56
    if asset_class in {"prop", "product"} and category in {"Other Use Cases", "Products & E-commerce"}:
        return 56
    if asset_class in {"fusion", "shot"} and category == "Scenes & Storytelling":
        return 70
    if asset_class == "style" and category in {"Illustration & Art", "Photography & Realism", "Posters & Typography"}:
        return 45
    return 0


def _keyword_score(text: str, words: list[str]) -> int:
    return sum(1 for word in words if word.lower() in text)


def select_style_template(
    asset_class: str | None,
    source: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    template_override: str | None = None,
) -> dict[str, Any]:
    """Select a catalog template using the skill's ordered matching strategy."""

    cls = canonical_asset_class(asset_class)
    source = source if isinstance(source, dict) else {}
    context = context if isinstance(context, dict) else {}
    text = _selection_text(source, context, cls)
    override = str(template_override or _first(source, "templateOverride", "template_override") or "").strip()
    if override:
        template = TEMPLATES_BY_ID.get(override)
        if template is None:
            raise ValueError(f"style library 模板不存在：{override}")
        mode = "override"
        selected_id = override
    else:
        scores: list[tuple[int, int, str]] = []
        default_id = _default_template_id(cls, text)
        for index, template in enumerate(STYLE_LIBRARY_TEMPLATES):
            score = _template_class_score(cls, template)
            score += _keyword_score(text, [str(item) for item in template.get("keywords") or []]) * 12
            score += _keyword_score(text, [str(item) for item in template.get("styles") or []]) * 4
            score += _keyword_score(text, [str(item) for item in template.get("scenes") or []]) * 4
            if str(template.get("id")) == default_id:
                score += 25
            scores.append((score, -index, str(template["id"])))
        selected_id = max(scores)[2]
        template = TEMPLATES_BY_ID[selected_id]
        mode = "automatic"
    return {
        "templateId": selected_id,
        "category": template["category"],
        "visualStyleTags": list(template.get("styles") or []),
        "sceneTags": list(template.get("scenes") or []),
        "tags": list(template.get("tags") or []),
        "exampleCaseIds": list(template.get("examples") or []),
        "selectionMode": mode,
        "selectionOrder": list(SELECTION_ORDER),
        "libraryVersion": STYLE_LIBRARY_VERSION,
        "guidance": str(template.get("guidance") or ""),
        "pitfalls": str(template.get("pitfalls") or ""),
    }


def _geometry(asset_class: str, context: dict[str, Any], raw: dict[str, Any]) -> dict[str, str]:
    del raw
    project_ratio = context.get("output_aspect_ratio") or context.get("project_output_aspect_ratio") or context.get("projectOutputAspectRatio") or context.get("project_ratio") or "9:16"
    if asset_class in {"fusion", "shot"}:
        ratio = normalize_aspect_ratio(project_ratio, "9:16")
        source = "project_output"
    else:
        # Base assets keep their identity/reference canvas. A provider or
        # user-supplied pixel/ratio value cannot silently change it.
        ratio = normalize_aspect_ratio(DEFAULT_BASE_ASSET_ASPECT_RATIOS.get(asset_class, "16:9"), "16:9")
        source = "class_default"
    if asset_class == "character":
        output = "png"
    elif asset_class in {"scene", "prop", "product", "style", "fusion"}:
        output = "png"
    elif asset_class == "shot":
        output = "png"
    else:
        output = "png"
    return {"aspectRatio": ratio, "outputFormat": output, "source": source}


def _fixed_layout(asset_class: str, geometry: dict[str, str]) -> str:
    ratio = geometry["aspectRatio"]
    if asset_class == "character":
        return (
            "横向四区角色参考板，左侧约42%为角色面部与上半身特写，右侧约58%分为三个等宽全身视图区，"
            "从左到右依次为正面全身、严格90°侧面全身、严格180°背面全身；四个区域必须是同一角色，"
            "四个视图等高、同尺度、脚底对齐，完整显示头部、双手、双脚和服装下摆；"
            "使用统一、低干扰的浅灰展示背景和柔和均匀的棚拍光线。"
        )
    if asset_class == "scene":
        return "横向空环境参考板，清楚呈现前景、中景、背景、空间封口、主要地标和可用动作区域，不放入角色或独立道具。"
    if asset_class == "prop":
        return "正方形独立物件参考图，完整呈现主体轮廓、结构、功能细节、材质状态和尺度参照，不进行人物或场景融合。"
    if asset_class == "product":
        return "正方形产品展示图，产品主体占据视觉中心，完整呈现产品轮廓、材质、包装或关键功能，不让无关道具削弱识别。"
    if asset_class == "style":
        return "横向风格参考板，保持统一的视觉语言、构图节奏、色彩和材质表现。"
    if asset_class == "fusion":
        return f"按项目画面比例{ratio}构成一张统一融合图，角色、道具与场景处于同一透视和光线系统中。"
    if asset_class == "shot":
        return f"按项目画面比例{ratio}构成镜头视觉参考图，主体动作和摄影机关系清楚可见。"
    return f"使用{ratio}画面构成完整视觉资产。"


def _default_subject(asset_class: str) -> str:
    return {
        "character": "建立可跨镜头复用的角色视觉身份参考资产",
        "scene": "建立可跨镜头复用的环境与空间参考资产",
        "prop": "建立可复用的独立物件视觉参考资产",
        "product": "建立可复用的产品主体与材质参考资产",
        "style": "建立统一的视觉风格参考资产",
        "fusion": "将已确认的角色、道具和场景组织为同一镜头中的统一画面",
        "shot": "为当前镜头建立可执行的视觉参考画面",
    }.get(asset_class, "建立一张清晰、可直接用于图像生成的视觉资产参考图")


def _style_text(selection: dict[str, Any], supplied: Any) -> str:
    value = _clean_visual_text(supplied).rstrip("。；，, ")
    labels = [_STYLE_LABELS.get(str(item), str(item)) for item in selection.get("visualStyleTags") or []]
    base = "、".join(dict.fromkeys(labels)) or "克制、清晰的视觉表达"
    guidance = _clean_visual_text(selection.get("guidance")).rstrip("。；，, ")
    library_rule = f"采用{base}视觉语言"
    if guidance:
        library_rule += f"；{guidance}"
    if value and value not in library_rule:
        library_rule += f"；用户指定的具体表现为{value}"
    return library_rule + "。"


def _references(source: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    raw = _first(source, "referenceRoles", "reference_roles") or _context_references(context)
    values = raw if isinstance(raw, list) else [raw] if _has(raw) else []
    result: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        if isinstance(value, dict):
            role = _clean_visual_text(value.get("role") or value.get("referenceRole") or "视觉参考") or "视觉参考"
            scope = _clean_visual_text(value.get("scope") or value.get("controls") or value.get("purpose") or "其声明的视觉范围") or "其声明的视觉范围"
            purpose = _clean_visual_text(value.get("purpose") or value.get("notes") or scope) or scope
            reference_id = str(value.get("referenceId") or value.get("reference_id") or value.get("id") or value.get("artifact_id") or "").strip()
        else:
            role = "视觉参考"
            scope = "其声明的视觉范围"
            purpose = _clean_visual_text(value) or scope
            reference_id = ""
        result.append({"referenceId": reference_id, "role": role, "scope": scope, "purpose": purpose, "ordinal": index + 1})
    return result


def _reference_text(references: list[dict[str, Any]]) -> str:
    if not references:
        return ""
    parts = [f"已上传参考图{item['ordinal']}用于{item['purpose']}，只控制{item['scope']}" for item in references if item.get("purpose") or item.get("scope")]
    return "；".join(parts) + "。" if parts else ""


def _shot_action(source: dict[str, Any], context: dict[str, Any], asset_class: str) -> str:
    if asset_class not in {"fusion", "shot"}:
        return ""
    supplied = _clean_visual_text(_first(source, "actionContinuity", "action_continuity", "action", "continuity"))
    if supplied:
        return supplied
    parts: list[str] = []
    for shot in _context_shots(context)[:2]:
        action = _clean_visual_text(shot.get("action") or shot.get("purpose"))
        camera = _clean_visual_text(shot.get("camera") or shot.get("size") or shot.get("framing"))
        continuity = _clean_visual_text(shot.get("continuity") or shot.get("firstFrame") or shot.get("lastFrame"))
        if action:
            parts.append(f"主动作是{action}")
        if camera:
            parts.append(f"摄影机保持{camera}")
        if continuity:
            parts.append(f"连续性保持{continuity}")
    return "；".join(dict.fromkeys(parts))


def _constraints(asset_class: str, source: dict[str, Any], references: list[dict[str, Any]]) -> list[str]:
    values = _clean_visual_list(_first(source, "constraintsNegative", "constraints_negative", "constraints", "negative", "negativeDetails"))
    defaults = {
        "character": ["四个视图保持同一角色的脸部身份、发型、体型、服装结构、材质和配色，不添加第二个角色。"],
        "scene": ["保持空环境，不出现角色、独立道具、融合对象、接触阴影或无关文字。"],
        "prop": ["保持独立物件边界，不出现人物手部、场景融合、无关道具、Logo 或水印。"],
        "product": ["保持产品主体完整清晰，只使用用户明确提供的包装文字，不添加无关人物或装饰。"],
        "style": ["保持视觉语言统一，不混入互相冲突的媒介或风格。"],
        "fusion": ["避免拼贴感和贴图感；保持同一透视、接触关系、投射阴影、环境光遮蔽和材质响应。"],
        "shot": ["保持动作、屏幕方向、主体身份和光线连续，不加入无法被摄影机看见的抽象说明。"],
    }.get(asset_class, [])
    for item in defaults:
        if not any(item == current or item in current or current in item for current in values):
            values.append(item)
    if not references and asset_class in {"character", "fusion"}:
        # Do not force a reference paragraph; this line is a visual constraint
        # only when identity continuity has no uploaded visual authority.
        values = [item for item in values if "已上传参考图" not in item]
    return list(dict.fromkeys(values))


def normalize_visual_prompt_pack(
    asset_class: str | None,
    prompt_pack: Any = None,
    *,
    identity_anchor: Any = None,
    must_preserve: Any = None,
    must_avoid: Any = None,
    context: dict[str, Any] | None = None,
    template_override: str | None = None,
) -> dict[str, Any]:
    """Normalize only the new visual fields; old fields are never translated."""

    cls = canonical_asset_class(asset_class)
    source = deepcopy(prompt_pack) if isinstance(prompt_pack, dict) else {}
    context = deepcopy(context) if isinstance(context, dict) else {}
    source = _prompt_pack_source(source)
    provider_template = source.get("templateSelection") if isinstance(source.get("templateSelection"), dict) else {}
    selected_template_override = template_override or str(provider_template.get("templateId") or provider_template.get("template_id") or "").strip() or None
    selection = select_style_template(cls, source, context, selected_template_override)
    geometry = _geometry(cls, context, source)
    references = _references(source, context)
    subject = _clean_visual_text(_first(source, "subjectTask", "subject_task", "task", "goal", "intent"))
    # The retired independent identity-anchor field is never promoted to a
    # visual Prompt block. New identity facts must arrive in subjectTask or
    # visualStyleMaterials from the style-library Prompt response.
    composition = _clean_visual_text(_first(source, "compositionLayout", "composition_layout", "layout", "composition"))
    fixed_layout = _fixed_layout(cls, geometry)
    if cls == "character":
        # The four-zone layout is a production invariant.  A conflicting old
        # top/bottom layout is ignored rather than merged.
        composition = fixed_layout if not composition else f"{fixed_layout}补充布局要求：{composition}"
    else:
        composition = f"{fixed_layout}{('补充布局要求：' + composition) if composition else ''}"
    visual = _style_text(selection, _first(source, "visualStyleMaterials", "visual_style_materials", "styleDescription", "appearance"))
    text_labels = _clean_visual_text(_first(source, "textLabels", "text_labels", "text", "labels"))
    action = _shot_action(source, context, cls)
    constraints = _constraints(cls, source, references)
    template_pitfalls = _clean_visual_text(selection.get("pitfalls"))
    if template_pitfalls:
        constraints.append(f"模板避坑：{template_pitfalls}")
    # Explicit caller-level constraints are user content and are folded into
    # the visual constraint block, never retained under old field names.
    for value in list(must_preserve or []) if isinstance(must_preserve, list) else [must_preserve] if _has(must_preserve) else []:
        rendered = _clean_visual_text(value)
        if rendered and rendered not in constraints:
            constraints.append(rendered)
    for value in list(must_avoid or []) if isinstance(must_avoid, list) else [must_avoid] if _has(must_avoid) else []:
        rendered = _clean_visual_text(value)
        if rendered and rendered not in constraints:
            constraints.append(rendered)
    pack = {
        "templateSelection": selection,
        "subjectTask": subject or _default_subject(cls),
        "compositionLayout": composition,
        "visualStyleMaterials": visual,
        "textLabels": text_labels,
        "aspectRatioOutput": geometry,
        "constraintsNegative": list(dict.fromkeys(constraints)),
        "referenceRoles": references,
    }
    if action:
        pack["actionContinuity"] = action
    return pack


def _paragraph(value: Any) -> str:
    rendered = _clean_visual_text(value)
    if not rendered:
        return ""
    return rendered.rstrip("。；，,") + "。"


def _copyable_prompt(pack: dict[str, Any]) -> str:
    """Render only image-useful prose; metadata never crosses this boundary."""

    blocks = [
        _paragraph(pack.get("subjectTask")),
        _paragraph(pack.get("compositionLayout")),
        _paragraph(pack.get("visualStyleMaterials")),
        _paragraph(pack.get("textLabels")),
        _paragraph(f"画面比例为{pack.get('aspectRatioOutput', {}).get('aspectRatio')}，输出为PNG图像资产。" if isinstance(pack.get("aspectRatioOutput"), dict) and pack.get("aspectRatioOutput", {}).get("outputFormat") == "png" else ""),
    ]
    reference_text = _reference_text(pack.get("referenceRoles") if isinstance(pack.get("referenceRoles"), list) else [])
    if reference_text:
        blocks.append(_paragraph(reference_text))
    if _has(pack.get("actionContinuity")):
        blocks.append(_paragraph(pack.get("actionContinuity")))
    constraints = [_paragraph(item) for item in pack.get("constraintsNegative") or []]
    blocks.extend(item for item in constraints if item)
    # De-duplicate exact paragraphs while preserving the skill-defined order.
    result: list[str] = []
    seen: set[str] = set()
    for item in blocks:
        normalized = re.sub(r"\s+", "", item)
        if not item or normalized in seen:
            continue
        seen.add(normalized)
        result.append(item)
    return "\n\n".join(result).strip()


def build_natural_language_prompt(
    asset_class: str | None,
    raw_pack: Any,
    fallback_prompt: str = "",
    context: dict[str, Any] | None = None,
    composition_mode: str | None = None,
) -> str:
    del composition_mode
    cls = canonical_asset_class(asset_class)
    if cls == "audio":
        from .audio_prompt import build_audio_prompt_text

        return build_audio_prompt_text(raw_pack, fallback_prompt, context=context)
    source = deepcopy(raw_pack) if isinstance(raw_pack, dict) else {}
    source_fields = source.get("promptPack") if isinstance(source.get("promptPack"), dict) else source
    has_new_fields = isinstance(source_fields, dict) and any(_has(source_fields.get(key)) for key in PROMPT_BLOCKS)
    if _prompt_pack_requires_regeneration(source):
        return ""
    if isinstance(source_fields, dict) and not has_new_fields and fallback_prompt and not _contains_legacy(fallback_prompt):
        source_fields["subjectTask"] = fallback_prompt
    pack = normalize_visual_prompt_pack(cls, source, context=context)
    if not has_new_fields and _contains_legacy(fallback_prompt):
        return ""
    return _copyable_prompt(pack)


def validate_clean_prompt(prompt: str, previous_prompt: str = "", *, base_asset: bool = False, asset_class: str | None = None) -> list[str]:
    text = str(prompt or "").strip()
    issues: list[str] = []
    for marker in LEGACY_PROMPT_MARKERS:
        if marker in text:
            issues.append(f"可复制 Prompt 包含已退役或内部标记：{marker}")
    if _JSON_FIELD_PATTERN.search(text):
        issues.append("可复制 Prompt 不得包含 JSON 或结构化字段语法")
    if _PIXEL_SIZE_PATTERN.search(text):
        issues.append("可复制 Prompt 不得包含 Provider 像素尺寸")
    if any(marker in text for marker in _COMMAND_MARKERS):
        issues.append("可复制 Prompt 不得包含工作流或 Provider 操作指令")
    if len(text) > 6000:
        issues.append("可复制 Prompt 超过 6000 个字符，请删除重复内容")
    cls = canonical_asset_class(asset_class) if asset_class else ""
    if base_asset and not cls:
        cls = "base"
    if cls == "character" or (base_asset and cls == "base" and "角色" in text):
        required = ("左侧约42%", "角色面部与上半身特写", "右侧约58%", "正面全身", "严格90°侧面全身", "严格180°背面全身")
        for token in required:
            if token not in text:
                issues.append(f"角色四区布局缺少：{token}")
    previous = re.sub(r"\s+", "", str(previous_prompt or "").strip())
    current = re.sub(r"\s+", "", text)
    if len(previous) >= 160 and current.startswith(previous):
        issues.append("可复制 Prompt 仍以旧 Prompt 全文开头")
    return list(dict.fromkeys(issues))


def _foundational_prompt_issues(asset_class: str, prompt: str, prompt_pack: dict[str, Any]) -> list[str]:
    """Validate the non-negotiable production tokens for a manual edit."""

    issues = validate_clean_prompt(
        prompt,
        asset_class=asset_class,
        base_asset=asset_class in BASE_ASSET_CLASSES,
    )
    geometry = prompt_pack.get("aspectRatioOutput") if isinstance(prompt_pack.get("aspectRatioOutput"), dict) else {}
    ratio = str(geometry.get("aspectRatio") or "").strip()
    if ratio and ratio not in prompt:
        issues.append(f"可复制 Prompt 必须保留画面比例 {ratio}")
    if str(geometry.get("outputFormat") or "png").lower() == "png" and "PNG" not in prompt.upper():
        issues.append("可复制 Prompt 必须保留 PNG 输出格式")
    return list(dict.fromkeys(issues))


def prompt_pack_has_generation_fields(asset_class: str | None, prompt_pack: Any) -> bool:
    cls = canonical_asset_class(asset_class)
    if not isinstance(prompt_pack, dict):
        return False
    source = _prompt_pack_source(prompt_pack)
    if source is not prompt_pack:
        return False
    if any(str(key) not in _PROMPT_PACK_KEYS for key in prompt_pack):
        return False
    if _contains_legacy(prompt_pack):
        return False
    if "textLabels" not in prompt_pack:
        return False
    required = ("subjectTask", "compositionLayout", "visualStyleMaterials", "aspectRatioOutput", "constraintsNegative")
    if not all(_has(prompt_pack.get(key)) for key in required):
        return False
    if not isinstance(prompt_pack.get("templateSelection"), dict) or not prompt_pack["templateSelection"].get("templateId"):
        return False
    if cls in {"fusion", "shot"} and not _has(prompt_pack.get("actionContinuity")):
        return False
    return True


def assess_prompt_pack(asset_class: str, prompt_pack: Any, prompt: str = "", *, needs_regeneration: bool | None = None) -> dict[str, Any]:
    cls = canonical_asset_class(asset_class)
    if cls == "audio":
        from .audio_prompt import AUDIO_PROMPT_SCHEMA_VERSION, build_audio_prompt_package

        package = build_audio_prompt_package(prompt_pack, prompt)
        ready = bool(package.get("copyText"))
        return {
            "schema_version": AUDIO_PROMPT_SCHEMA_VERSION,
            "status": "ready" if ready else "needs-confirmation",
            "coverage": {"passed": 1 if ready else 0, "total": 1, "percent": 100 if ready else 0},
            "missing": [] if ready else ["朗读文本"],
            "boundaryIssues": [],
        }
    pack = prompt_pack if isinstance(prompt_pack, dict) else {}
    if needs_regeneration is None:
        needs_regeneration = _prompt_pack_requires_regeneration(pack)
    checks = [
        ("模板来自 style library", isinstance(pack.get("templateSelection"), dict) and bool(pack.get("templateSelection", {}).get("templateId"))),
        ("主体任务", _has(pack.get("subjectTask"))),
        ("构图布局", _has(pack.get("compositionLayout"))),
        ("视觉风格与材质", _has(pack.get("visualStyleMaterials"))),
        ("画面比例与输出", _has(pack.get("aspectRatioOutput"))),
        ("限制与负向要求", _has(pack.get("constraintsNegative"))),
        ("可复制 Prompt", bool(str(prompt or "").strip())),
    ]
    if cls in {"fusion", "shot"}:
        checks.append(("动作与连续性", _has(pack.get("actionContinuity"))))
    issues = validate_clean_prompt(prompt, asset_class=cls)
    passed = sum(1 for _, ok in checks if ok) - len(issues)
    passed = max(0, passed)
    total = len(checks)
    return {
        "schema_version": PROMPT_CONTRACT_VERSION,
        "status": "needs-regeneration" if needs_regeneration else "ready" if passed == total and not issues else "needs-detail",
        "coverage": {"passed": passed, "total": total, "percent": round(passed / total * 100) if total else 0},
        "missing": [label for label, ok in checks if not ok],
        "boundaryIssues": issues,
        "ruleSource": f"{STYLE_LIBRARY_SOURCE}@{STYLE_LIBRARY_VERSION}",
        "foundationalRules": sorted(FOUNDATIONAL_RULES),
    }


def prompt_contract(asset_class: str | None = None) -> dict[str, Any]:
    selected = canonical_asset_class(asset_class or "all")
    if selected == "audio":
        from .audio_prompt import audio_prompt_contract

        return audio_prompt_contract()
    return {
        "version": PROMPT_CONTRACT_VERSION,
        "workflow": PROMPT_WORKFLOW_ID,
        "asset_class": selected,
        "rule_source": {"skill": STYLE_LIBRARY_SOURCE, "version": STYLE_LIBRARY_VERSION, "skillPath": STYLE_LIBRARY_SKILL_PATH, "catalogPath": STYLE_LIBRARY_SOURCE_PATH},
        "selection_order": list(SELECTION_ORDER),
        "prompt_blocks": list(PROMPT_BLOCKS),
        "copy_boundary": {
            "user_visible": ["subjectTask", "compositionLayout", "visualStyleMaterials", "textLabels", "aspectRatioOutput", "constraintsNegative", "referenceRoles", "actionContinuity"],
            "hidden": ["templateSelection", "ruleSource", "retainedFoundationalRules", "legacyFieldsDropped", "needsRegeneration", "qaDiagnostics", "workflowState", "providerState"],
        },
        "retained_foundational_rules": sorted(FOUNDATIONAL_RULES),
        "prompt_pack_shape": {key: "visual generation content" for key in PROMPT_BLOCKS} | {"referenceRoles": "reference roles", "actionContinuity": "fusion/shot only"},
        "class_geometry": {
            "character": {"aspectRatio": "16:9", "outputFormat": "png", "layout": "character_four_zone_sheet"},
            "scene": {"aspectRatio": "16:9", "outputFormat": "png", "layout": "empty_environment_board"},
            "prop": {"aspectRatio": "1:1", "outputFormat": "png", "layout": "isolated_object_board"},
            "product": {"aspectRatio": "1:1", "outputFormat": "png", "layout": "isolated_product_board"},
            "style": {"aspectRatio": "16:9", "outputFormat": "png", "layout": "style_reference_board"},
            "fusion": {"aspectRatio": "project_output", "outputFormat": "png", "layout": "fusion_frame"},
            "shot": {"aspectRatio": "project_output", "outputFormat": "png", "layout": "shot_keyframe"},
        },
        "templates": [
            {
                "id": item["id"],
                "category": item["category"],
                "styles": item.get("styles", []),
                "scenes": item.get("scenes", []),
                "tags": item.get("tags", []),
                "examples": item.get("examples", []),
                "guidance": item.get("guidance", ""),
                "pitfalls": item.get("pitfalls", ""),
            }
            for item in STYLE_LIBRARY_TEMPLATES
        ],
    }


def prompt_contract_instructions(*, fusion: bool = False) -> str:
    scope = "融合/镜头视觉任务" if fusion else "视觉资产任务"
    return (
        f"你负责 FrameFlow 的{scope}。视觉 Prompt 的唯一规则来源是 gpt-image-2-style-library v{STYLE_LIBRARY_VERSION}；"
        "严格按输出目标、模板类别、visual style、scene tag、近似案例和模板 pitfalls 选择模板。"
        "只返回结构化视觉内容，不生成图片。最终 Prompt 必须按主体任务、构图布局、视觉风格与材质、文字标签、画面比例与输出格式、限制与负向要求组织。"
        "模板选择信息、案例编号、QA、Provider、工作流、资产 ID 和内部字段不得进入可复制 Prompt。"
        "FrameFlow 只额外保留资产画面比例、图像输出格式、项目比例继承和角色横向四区参考板等生产硬约束；旧 Prompt 规则、旧字段、旧 fallback 均已退役。"
        + ("融合或镜头任务必须补充可见动作、空间关系和连续性。" if fusion else "")
        + "中文请求使用中文，所有描述必须具体、可被图像生成模型看见。"
    )


def base_asset_geometry_prompt(asset_class: str | None, context: dict[str, Any] | None = None) -> str:
    cls = canonical_asset_class(asset_class)
    if cls not in VISUAL_ASSET_CLASSES:
        return ""
    context = context if isinstance(context, dict) else {}
    geometry = _geometry(cls, context, {})
    return _fixed_layout(cls, geometry)


def canonicalize_prompt_output(
    asset_class: str | None,
    raw_pack: Any,
    prompt: str,
    *,
    identity_anchor: Any = None,
    must_preserve: Any = None,
    must_avoid: Any = None,
    context: dict[str, Any] | None = None,
    composition_mode: str | None = None,
    previous_prompt: str = "",
    strict_clean: bool = False,
    template_override: str | None = None,
    preserve_clean_prompt: bool = False,
) -> dict[str, Any]:
    del composition_mode
    cls = canonical_asset_class(asset_class)
    if cls == "audio":
        from .audio_prompt import canonicalize_audio_output

        return canonicalize_audio_output(raw_pack, prompt, context=context)
    source_for_compile = deepcopy(raw_pack) if isinstance(raw_pack, dict) else {}
    source_fields = source_for_compile.get("promptPack") if isinstance(source_for_compile.get("promptPack"), dict) else source_for_compile
    needs_regeneration = _prompt_pack_requires_regeneration(source_for_compile)
    if isinstance(source_fields, dict) and not needs_regeneration and not any(_has(source_fields.get(key)) for key in PROMPT_BLOCKS) and str(prompt or "").strip() and not _contains_legacy(prompt):
        # A clean hand-written draft can seed the new subject block. An old
        # pack is still marked for regeneration below and can never become a
        # silent fallback merely because its prompt text looks harmless.
        source_fields["subjectTask"] = str(prompt).strip()
    pack = normalize_visual_prompt_pack(
        cls,
        source_for_compile,
        identity_anchor=identity_anchor,
        must_preserve=must_preserve,
        must_avoid=must_avoid,
        context=context,
        template_override=template_override,
    )
    compiled = "" if needs_regeneration else _copyable_prompt(pack)
    if preserve_clean_prompt and not needs_regeneration and str(prompt or "").strip() and prompt_pack_has_generation_fields(cls, source_fields):
        submitted_prompt = str(prompt).strip()
        manual_issues = _foundational_prompt_issues(cls, submitted_prompt, pack)
        if not manual_issues:
            compiled = submitted_prompt
        elif strict_clean:
            raise ValueError("；".join(manual_issues))
    issues = validate_clean_prompt(compiled, previous_prompt, asset_class=cls, base_asset=cls in BASE_ASSET_CLASSES)
    if strict_clean and (needs_regeneration or issues):
        raise ValueError("；".join(issues or ["旧 Prompt 结构已退役，请使用新的 style library 字段重新生成。"]))
    quality = assess_prompt_pack(cls, pack, compiled, needs_regeneration=needs_regeneration)
    preserve = _clean_visual_list(must_preserve or _first(raw_pack if isinstance(raw_pack, dict) else {}, "mustPreserve", "must_preserve"))
    avoid = _clean_visual_list(must_avoid or _first(raw_pack if isinstance(raw_pack, dict) else {}, "mustAvoid", "must_avoid"))
    return {
        "prompt": compiled,
        "copyablePrompt": compiled,
        "promptPack": pack,
        "promptQuality": quality,
        "promptContractVersion": PROMPT_CONTRACT_VERSION,
        "promptWorkflow": PROMPT_WORKFLOW_ID,
        "promptCompositionMode": "style_library",
        "promptCompilerVersion": PROMPT_WORKFLOW_ID,
        "ruleSource": f"{STYLE_LIBRARY_SOURCE}@{STYLE_LIBRARY_VERSION}",
        "mustPreserve": preserve,
        "mustAvoid": avoid,
        "aspectRatioOutput": deepcopy(pack.get("aspectRatioOutput") or {}),
        "legacyFieldsDropped": _legacy_prompt_fields(_prompt_pack_source(raw_pack)),
        "needsRegeneration": needs_regeneration,
    }


def style_library_prompt_snapshot() -> dict[str, Any]:
    return style_library_snapshot()


__all__ = [
    "BASE_ASSET_CLASSES",
    "BASE_ASSET_PROMPT_COMPILER_VERSION",
    "FOUNDATIONAL_RULES",
    "PROMPT_CONTRACT_VERSION",
    "PROMPT_WORKFLOW_ID",
    "PromptCompositionMode",
    "assess_prompt_pack",
    "base_asset_geometry_prompt",
    "build_natural_language_prompt",
    "canonical_asset_class",
    "canonicalize_prompt_output",
    "is_base_asset_class",
    "normalize_visual_prompt_pack",
    "prompt_composition_mode_for_asset",
    "prompt_contract",
    "prompt_contract_instructions",
    "prompt_pack_has_generation_fields",
    "render_prompt_value",
    "select_style_template",
    "style_library_prompt_snapshot",
    "validate_clean_prompt",
]
