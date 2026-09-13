"""Versioned screenplay and storyboard review rules for FrameFlow.

The module deliberately contains production rules only.  It does not render a
Prompt, create an asset, or change workflow routing.  Keeping the rules here
lets a storyboard candidate, a manual story document, and the story-run API
share the same definitions without making the asset Prompt pipeline depend on
story-generation implementation details.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


DIRECTOR_RULE_PROFILE = "frameflow-director-v2"
DIRECTOR_RULE_PROFILE_VERSION = "2.0.0"
DIRECTOR_RULE_MODULES = {
    "scriptModules": [
        "writer-structure",
        "character-conflict",
        "scene-dramaturgy",
        "dialogue-and-silence",
        "source-coverage",
    ],
    "storyboardModules": [
        "beat-to-shot",
        "visual-dramaturgy",
        "blocking-and-coverage",
        "continuity-geometry",
        "shot-unit-contract",
        "seedance-execution",
    ],
    "handoffModules": [
        "storyboard-asset-requirements",
        "asset-provenance",
        "downstream-compatibility",
    ],
}

DIRECTOR_RULE_SOURCES = [
    {"id": "video-script-storyboard", "scope": "制作合同、来源覆盖、镜头单元与资产交接"},
    {"id": "muse-video-skill:Writer", "scope": "剧本结构、人物行动冲突、对白与沉默"},
    {"id": "smixs/visual-skills:Dramaturgy", "scope": "欲望阻碍、空间几何、视觉节奏与环境压力"},
    {"id": "wuwangzhang1216/DirectorSKILL", "scope": "导演分析、beat、blocking、coverage 与 QC"},
    {"id": "OSideMedia/higgsfield-ai-prompt-skill:shotlist-seedance", "scope": "Seedance 时长、参考角色、时间节拍与回退路线"},
    {"id": "video-asset-regulator", "scope": "分镜完成后的资产提取、依赖与下游边界"},
]

SCENE_DIRECTOR_FIELDS = (
    "sceneGoal",
    "characterDesire",
    "primaryObstacle",
    "observableAction",
    "stateChange",
    "turn",
    "entryState",
    "exitState",
)

SHOT_DIRECTOR_FIELDS = (
    "subjectFocus",
    "blocking",
    "coverageRole",
    "performance",
    "spatialGeography",
    "materialEvidence",
    "lightingCausality",
    "environmentPressure",
    "microAction",
)

CONTINUITY_FIELDS = (
    "screenDirection",
    "eyeline",
    "motionVector",
    "cutIn",
    "cutOut",
    "matchAction",
    "editBridge",
    "preRoll",
    "postRoll",
    "firstFrame",
    "lastFrame",
)

SEEDANCE_REQUIRED_FIELDS = (
    "model",
    "generationMode",
    "targetDuration",
    "aspectRatio",
    "clipUnit",
    "startState",
    "playableChange",
    "endState",
    "continuityStrategy",
    "audioStrategy",
    "fallbackRoute",
)

_PLACEHOLDERS = {
    "待确认",
    "待补充",
    "待定",
    "未知",
    "unknown",
    "tbd",
    "todo",
    "n/a",
    "不适用",
    "未填写",
}


def director_rule_profile() -> dict[str, Any]:
    """Return a serializable, immutable-by-convention rule profile payload."""
    return {
        "id": DIRECTOR_RULE_PROFILE,
        "version": DIRECTOR_RULE_PROFILE_VERSION,
        **{key: list(values) for key, values in DIRECTOR_RULE_MODULES.items()},
        "sources": [dict(item) for item in DIRECTOR_RULE_SOURCES],
    }


def is_director_rule_profile(value: Any) -> bool:
    """Whether a document/run is explicitly opted into the new profile.

    Old projects intentionally stay on their saved rule behaviour.  This
    predicate therefore never treats a missing field as an implicit upgrade.
    """
    if isinstance(value, dict):
        value = value.get("id") or value.get("rule_profile") or value.get("ruleProfile")
    return str(value or "").strip().lower() == DIRECTOR_RULE_PROFILE


def story_rule_profile_from_spec(spec: Any) -> dict[str, Any]:
    """Read a persisted profile while preserving legacy projects as legacy."""
    current = spec if isinstance(spec, dict) else {}
    profile = current.get("rule_profile") or current.get("ruleProfile")
    if not is_director_rule_profile(profile):
        return {"id": "legacy", "version": None, "enabled": False, "modules": {}, "sources": []}
    modules = current.get("rule_modules") or current.get("ruleModules")
    modules = modules if isinstance(modules, dict) else DIRECTOR_RULE_MODULES
    sources = current.get("rule_sources") or current.get("ruleSources")
    sources = sources if isinstance(sources, list) and sources else DIRECTOR_RULE_SOURCES
    return {
        "id": DIRECTOR_RULE_PROFILE,
        "version": str(current.get("rule_profile_version") or current.get("ruleProfileVersion") or DIRECTOR_RULE_PROFILE_VERSION),
        "enabled": True,
        "modules": {key: list(value) for key, value in modules.items() if isinstance(value, list)},
        "sources": [dict(item) for item in sources if isinstance(item, dict)],
    }


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "label", "description", "value", "plan", "instruction", "content"):
            if value.get(key) not in (None, "", []):
                return _text(value[key])
        return ""
    if isinstance(value, list):
        return " ".join(_text(item) for item in value if _text(item))
    return str(value or "").strip()


def _meaningful(value: Any) -> bool:
    text = _text(value)
    if not text:
        return False
    normalized = re.sub(r"[\s，,。；;：:、._-]+", "", text).lower()
    return bool(normalized) and normalized not in _PLACEHOLDERS


def _record_id(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("id") or value.get("assetId") or value.get("asset_id") or "").strip()


def _profile_from_input(input_package: dict[str, Any] | None) -> dict[str, Any]:
    package = input_package if isinstance(input_package, dict) else {}
    profile = package.get("rule_profile") or package.get("ruleProfile")
    if not profile:
        spec = package.get("story_spec") if isinstance(package.get("story_spec"), dict) else {}
        profile = spec.get("rule_profile") or spec.get("ruleProfile")
    if not is_director_rule_profile(profile):
        return {"id": "legacy", "version": None, "enabled": False, "modules": {}, "sources": []}
    modules = package.get("rule_modules") or package.get("ruleModules")
    modules = modules if isinstance(modules, dict) else DIRECTOR_RULE_MODULES
    sources = package.get("rule_sources") or package.get("ruleSources")
    sources = sources if isinstance(sources, list) and sources else DIRECTOR_RULE_SOURCES
    return {
        "id": DIRECTOR_RULE_PROFILE,
        "version": str(package.get("rule_profile_version") or package.get("ruleProfileVersion") or DIRECTOR_RULE_PROFILE_VERSION),
        "enabled": True,
        "modules": {key: list(value) for key, value in modules.items() if isinstance(value, list)},
        "sources": [dict(item) for item in sources if isinstance(item, dict)],
    }


def director_auto_review(
    result: dict[str, Any] | None,
    input_package: dict[str, Any] | None = None,
    repair_attempts: int = 0,
) -> dict[str, Any]:
    """Review a normalized candidate against the new director production contract.

    The function is intentionally deterministic.  It catches missing or
    non-handoffable facts before the candidate reaches the asset regulator;
    model judgement remains in the candidate-generation pass, not in the
    review gate.  Legacy projects get a transparent no-op report so no stored
    project is silently migrated to the new strict rules.
    """
    candidate = result if isinstance(result, dict) else {}
    package = input_package if isinstance(input_package, dict) else {}
    profile = _profile_from_input(package)
    now = datetime.now(timezone.utc).isoformat()
    if not profile["enabled"]:
        return {
            "status": "not_applicable",
            "acceptanceAllowed": True,
            "scriptAcceptanceAllowed": str(package.get("workflow_mode") or "") != "storyboard_from_source",
            "gates": [],
            "issues": [],
            "repairAttempts": repair_attempts,
            "ruleProfile": profile["id"],
            "ruleProfileVersion": profile["version"],
            "ruleModules": profile["modules"],
            "ruleSources": profile["sources"],
            "sourceScriptVersionId": package.get("source_script_version_id"),
            "sourceScriptHash": package.get("source_script_hash"),
            "handoffCompatibility": {
                "status": "not_applicable",
                "targets": ["video-asset-regulator", "asset-intent-preparation", "asset-prompt-run"],
                "missingFields": [],
                "sourceShotIds": [],
            },
            "checkedAt": now,
        }

    gate_order = (
        ("source_integrity", "来源完整性"),
        ("script_dramaturgy", "剧本戏剧结构"),
        ("source_coverage", "原文节拍覆盖"),
        ("scene_ledger", "场景导演台账"),
        ("shot_unit", "镜头单元"),
        ("visual_dramaturgy", "视觉戏剧与调度"),
        ("continuity_editability", "连续性与剪辑性"),
        ("seedance_execution", "Seedance 可执行性"),
        ("asset_handoff", "资产交接"),
        ("downstream_compatibility", "下游兼容性"),
    )
    issues: list[dict[str, Any]] = []

    def add(
        gate: str,
        code: str,
        severity: str,
        message: str,
        path: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        item: dict[str, Any] = {
            "code": code,
            "severity": severity,
            "stage": "script" if gate in {"source_integrity", "script_dramaturgy", "source_coverage"} else "storyboard" if gate != "downstream_compatibility" else "handoff",
            "gate": gate,
            "message": message,
        }
        if path:
            item["path"] = path
        if suggestion:
            item["suggestion"] = suggestion
        issues.append(item)

    workflow_mode = str(package.get("workflow_mode") or candidate.get("workflowMode") or "")
    source_script = str(package.get("current_script") or "")
    proposed_script = str(candidate.get("proposedScript") or "")
    if workflow_mode == "storyboard_from_source":
        if not source_script:
            add("source_integrity", "source_script_missing", "blocking", "直转分镜缺少锁定的来源剧本。", "sourceScript")
        elif proposed_script != source_script:
            add("source_integrity", "source_script_mutation", "blocking", "直转分镜候选修改了锁定来源剧本。", "proposedScript", "将 proposedScript 恢复为来源剧本原文。")
        if candidate.get("sourceScriptMutationDetected"):
            add("source_integrity", "source_script_mutation", "blocking", "模型曾返回过改写来源剧本的内容，已被兼容层恢复为原文并保留该审查记录。", "proposedScript")
    if not package.get("source_script_version_id"):
        add("source_integrity", "source_script_version_missing", "blocking", "候选缺少来源剧本版本 ID。", "sourceScriptVersionId")
    expected_hash = str(package.get("source_script_hash") or "")
    actual_hash = str(candidate.get("sourceScriptHash") or "")
    if expected_hash and actual_hash and expected_hash != actual_hash:
        add("source_integrity", "source_script_hash_mismatch", "blocking", "候选引用的来源剧本哈希与本次运行不一致。", "sourceScriptHash")
    if candidate.get("sourceScriptHashMismatchDetected"):
        add("source_integrity", "source_script_hash_mismatch", "blocking", "兼容层检测到模型返回的来源剧本哈希与本次运行不一致，已阻止候选进入确认。", "sourceScriptHash")
    expected_version = str(package.get("source_script_version_id") or "")
    actual_version = str(candidate.get("sourceScriptVersionId") or "")
    if expected_version and actual_version and expected_version != actual_version:
        add("source_integrity", "source_script_version_mismatch", "blocking", "候选引用的来源剧本版本与本次运行不一致。", "sourceScriptVersionId")
    if candidate.get("sourceScriptVersionMismatchDetected"):
        add("source_integrity", "source_script_version_mismatch", "blocking", "兼容层检测到模型返回的来源剧本版本与本次运行不一致，已阻止候选进入确认。", "sourceScriptVersionId")

    if not _meaningful(proposed_script):
        add("script_dramaturgy", "proposed_script_missing", "blocking", "候选缺少可审阅的拍摄剧本。", "proposedScript")
    if not isinstance(candidate.get("structure"), list) or not candidate.get("structure"):
        add("script_dramaturgy", "script_structure_missing", "blocking", "候选缺少故事结构与场景推进。", "structure", "输出结构化故事阶段或场景推进。")
    if not isinstance(candidate.get("beats"), list) or not candidate.get("beats"):
        add("script_dramaturgy", "script_beats_missing", "blocking", "候选缺少可追溯的故事 Beat。", "beats", "为每个关键叙事变化输出 beat。")
    if not isinstance(candidate.get("productionElements"), dict):
        add("script_dramaturgy", "production_elements_missing", "blocking", "候选缺少可交接的基础制作元素。", "productionElements")

    declared_additions: list[Any] = []
    for key in ("assumptions", "creativeAdditions", "creative_additions", "needsConfirmation", "needs_confirmation"):
        values = candidate.get(key)
        if isinstance(values, list):
            declared_additions.extend(value for value in values if value not in (None, "", []))
    if declared_additions:
        add(
            "script_dramaturgy",
            "creative_addition_needs_confirmation",
            "warning",
            "候选声明了新增情节、人物、道具或设定；需要用户确认后才能进入正式版本和下游生产。",
            "assumptions/creativeAdditions/needsConfirmation",
            "在候选审阅中确认或修订新增内容；未确认内容不会自动进入下游。",
        )

    coverage = candidate.get("sourceBeatCoverage") if isinstance(candidate.get("sourceBeatCoverage"), dict) else {}
    coverage_status = str(coverage.get("status") or "")
    if coverage_status not in {"complete", "not_applicable"}:
        add("source_coverage", "source_beat_coverage_incomplete", "blocking", "原始剧本节拍尚未被候选分镜完整覆盖。", "sourceBeatCoverage", "为每个镜头补充 sourceBeatIds，并补回缺失事件。")
    for item in _as_list(coverage.get("unknownMappings")):
        if isinstance(item, dict):
            add("source_coverage", "source_beat_unknown", "blocking", f"镜头 {item.get('shotId') or '未知'} 引用了不存在的原文节拍 {item.get('sourceBeatId') or '未知'}。", "sourceBeatCoverage")

    scenes = [item for item in _as_list(candidate.get("scenes")) if isinstance(item, dict)]
    shots = [item for item in _as_list(candidate.get("shots")) if isinstance(item, dict)]
    if not scenes:
        add("scene_ledger", "scene_ledger_missing", "blocking", "候选缺少完整场景台账。", "scenes")
    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("id") or f"scene[{index}]")
        for field in SCENE_DIRECTOR_FIELDS:
            if not _meaningful(scene.get(field)):
                add("scene_ledger", "scene_director_field_missing", "blocking", f"场景 {scene_id} 缺少 {field}。", f"scenes[{index}].{field}")
        if not isinstance(scene.get("relevantShots"), list) or not scene.get("relevantShots"):
            add("scene_ledger", "scene_shot_mapping_missing", "blocking", f"场景 {scene_id} 未声明关联镜头。", f"scenes[{index}].relevantShots")

    if not shots:
        add("shot_unit", "storyboard_shots_missing", "blocking", "候选缺少可执行镜头。", "shots")
    known_scene_ids = {str(scene.get("id") or "") for scene in scenes if scene.get("id")}
    handoff = candidate.get("assetHandoff") if isinstance(candidate.get("assetHandoff"), dict) else {}
    known_asset_ids = {str(value).strip() for value in _as_list(package.get("existing_asset_ids")) if str(value).strip()}
    for category in ("characters", "scenes", "props", "products", "styles", "soundRequirements"):
        for item in _as_list(handoff.get(category)):
            item_id = _record_id(item)
            if item_id:
                known_asset_ids.add(item_id)

    source_ledger = _as_list(package.get("source_beat_ledger"))
    require_beat_mapping = bool(source_ledger)
    all_requirement_errors: list[str] = []
    all_shot_ids: list[str] = []
    for index, shot in enumerate(shots):
        shot_id = str(shot.get("id") or f"shot[{index}]")
        all_shot_ids.append(shot_id)
        if known_scene_ids and str(shot.get("scene") or "") not in known_scene_ids:
            add("shot_unit", "scene_reference_missing", "blocking", f"镜头 {shot_id} 引用了未登记场景 {shot.get('scene') or '未知'}。", f"shots[{index}].scene")
        for field in ("purpose", "action", "visibleEvent", "eventConsequence"):
            if not _meaningful(shot.get(field)):
                add("shot_unit", "shot_unit_field_missing", "blocking", f"镜头 {shot_id} 缺少 {field}。", f"shots[{index}].{field}")
        if require_beat_mapping and not [value for value in _as_list(shot.get("sourceBeatIds")) if str(value).strip()]:
            add("shot_unit", "shot_source_beat_missing", "blocking", f"镜头 {shot_id} 未绑定任何原文 Beat。", f"shots[{index}].sourceBeatIds")
        event_text = " ".join(_text(shot.get(field)) for field in ("visibleEvent", "action", "eventConsequence"))
        if len(re.findall(r"(?:同时|然后|随后|接着|并且|；|;)", event_text)) >= 2:
            add("shot_unit", "shot_unit_multi_event_suspected", "warning", f"镜头 {shot_id} 可能包含多个主事件，请确认是否应拆镜。", f"shots[{index}]")
        for field in SHOT_DIRECTOR_FIELDS:
            if not _meaningful(shot.get(field)):
                add("visual_dramaturgy", "shot_director_field_missing", "blocking", f"镜头 {shot_id} 缺少 {field}。", f"shots[{index}].{field}")
        camera_execution = shot.get("cameraExecution")
        if not _meaningful(camera_execution):
            add("visual_dramaturgy", "camera_execution_missing", "blocking", f"镜头 {shot_id} 缺少可执行的摄影机说明。", f"shots[{index}].cameraExecution")
        if not _meaningful(shot.get("visualMotif")):
            add("visual_dramaturgy", "visual_motif_missing", "warning", f"镜头 {shot_id} 未记录视觉或声音母题；如果该镜头不是母题段落可忽略。", f"shots[{index}].visualMotif")

        continuity = shot.get("continuity") if isinstance(shot.get("continuity"), dict) else {}
        for field in CONTINUITY_FIELDS:
            if not _meaningful(continuity.get(field) or shot.get(field)):
                add("continuity_editability", "continuity_field_missing", "blocking", f"镜头 {shot_id} 缺少连续性字段 {field}。", f"shots[{index}].continuity.{field}")

        plan = shot.get("seedancePlan") if isinstance(shot.get("seedancePlan"), dict) else {}
        for field in SEEDANCE_REQUIRED_FIELDS:
            if field == "targetDuration":
                try:
                    meaningful_duration = float(plan.get(field) or 0) > 0
                except (TypeError, ValueError):
                    meaningful_duration = False
                if not meaningful_duration:
                    add("seedance_execution", "seedance_plan_field_missing", "blocking", f"镜头 {shot_id} 缺少可用的 Seedance {field}。", f"shots[{index}].seedancePlan.{field}")
            elif not _meaningful(plan.get(field)):
                add("seedance_execution", "seedance_plan_field_missing", "blocking", f"镜头 {shot_id} 缺少 Seedance {field}。", f"shots[{index}].seedancePlan.{field}")
        model = _text(plan.get("model") or shot.get("generator")).lower()
        try:
            shot_duration = float(shot.get("duration") or 0)
        except (TypeError, ValueError):
            shot_duration = 0
        try:
            plan_duration = float(plan.get("targetDuration") or 0)
        except (TypeError, ValueError):
            plan_duration = 0
        effective_duration = max(shot_duration, plan_duration)
        if "2.0" in model and effective_duration > 15:
            add("seedance_execution", "generator_duration_limit", "blocking", f"镜头 {shot_id} 超过 Seedance 2.0 的 15 秒边界。", f"shots[{index}].duration")
        if "2.5" in model and effective_duration > 30:
            add("seedance_execution", "generator_duration_limit", "blocking", f"镜头 {shot_id} 超过 Seedance 2.5 的 30 秒上限。", f"shots[{index}].duration")
        assignments = _as_list(plan.get("referenceAssignments"))
        for assignment_index, assignment in enumerate(assignments):
            if not isinstance(assignment, dict):
                add("seedance_execution", "reference_role_missing", "blocking", f"镜头 {shot_id} 的参考分配必须是带角色的对象。", f"shots[{index}].seedancePlan.referenceAssignments[{assignment_index}]")
                continue
            asset_id = str(assignment.get("assetId") or assignment.get("asset_id") or assignment.get("referenceId") or "").strip()
            role = _text(assignment.get("role"))
            controls = _text(assignment.get("controls") or assignment.get("controlRange"))
            exclusions = _text(assignment.get("doesNotControl") or assignment.get("mustNotControl") or assignment.get("exclusions"))
            if not asset_id or not role or not controls or not exclusions:
                add("seedance_execution", "reference_role_missing", "blocking", f"镜头 {shot_id} 的参考分配需要资产 ID、角色、控制范围和不控制范围。", f"shots[{index}].seedancePlan.referenceAssignments[{assignment_index}]")

        requirements = [item for item in _as_list(shot.get("assetRequirements")) if isinstance(item, dict)]
        if not requirements:
            all_requirement_errors.append(shot_id)
            add("asset_handoff", "asset_requirements_missing", "blocking", f"镜头 {shot_id} 缺少资产需求，无法交给资产监管。", f"shots[{index}].assetRequirements")
        for requirement_index, requirement in enumerate(requirements):
            req_asset_id = str(requirement.get("assetId") or requirement.get("asset_id") or "").strip()
            req_class = _text(requirement.get("assetClass") or requirement.get("asset_class"))
            req_shot_id = str(requirement.get("shotId") or requirement.get("shot_id") or "").strip()
            path = f"shots[{index}].assetRequirements[{requirement_index}]"
            if not req_asset_id or not req_class or not req_shot_id:
                add("asset_handoff", "asset_requirement_incomplete", "blocking", f"镜头 {shot_id} 的资产需求缺少 shotId、assetId 或 assetClass。", path)
            elif req_shot_id != shot_id:
                add("asset_handoff", "asset_requirement_shot_mismatch", "blocking", f"镜头 {shot_id} 的资产需求指向了 {req_shot_id}。", path)
            elif req_asset_id not in known_asset_ids:
                add("asset_handoff", "asset_dependency_missing", "blocking", f"镜头 {shot_id} 引用了未在交接包声明的资产 {req_asset_id}。", path)

    for category in ("characters", "scenes", "props", "products", "styles", "soundRequirements"):
        for item_index, asset_item in enumerate(_as_list(handoff.get(category))):
            if not isinstance(asset_item, dict):
                continue
            references = asset_item.get("generationReferenceAssets") or asset_item.get("generation_reference_assets") or asset_item.get("references") or []
            if not isinstance(references, list):
                references = [references]
            for reference_index, reference in enumerate(references):
                if not isinstance(reference, dict):
                    add("asset_handoff", "reference_role_missing", "blocking", "资产参考项必须是带控制边界的对象。", f"assetHandoff.{category}[{item_index}].generationReferenceAssets[{reference_index}]")
                    continue
                reference_id = str(reference.get("assetId") or reference.get("asset_id") or reference.get("referenceId") or reference.get("reference_id") or "").strip()
                asset_item_id = _record_id(asset_item)
                role = _text(reference.get("role") or reference.get("referenceRole"))
                controls = _text(reference.get("controls") or reference.get("controlRange") or reference.get("scope"))
                exclusions = _text(reference.get("doesNotControl") or reference.get("mustNotControl") or reference.get("exclusions"))
                reason = _text(reference.get("reason") or reference.get("purpose"))
                relevant_shots = reference.get("relevantShots") if "relevantShots" in reference else reference.get("relevant_shots")
                required = reference.get("required")
                if not reference_id or not role or not controls or not exclusions or not reason or not isinstance(relevant_shots, list) or not isinstance(required, bool):
                    add("asset_handoff", "reference_role_missing", "blocking", "每个资产参考项必须声明资产 ID、角色、控制范围、不控制范围、是否必需、用途和关联镜头。", f"assetHandoff.{category}[{item_index}].generationReferenceAssets[{reference_index}]")
                elif reference_id == asset_item_id:
                    add("asset_handoff", "reference_self_reference", "blocking", f"资产 {asset_item_id} 不得引用自身。", f"assetHandoff.{category}[{item_index}].generationReferenceAssets[{reference_index}]")
                elif reference_id not in known_asset_ids:
                    add("asset_handoff", "reference_id_unknown", "blocking", f"资产 {asset_item_id} 引用了未声明的参考资产 {reference_id}。", f"assetHandoff.{category}[{item_index}].generationReferenceAssets[{reference_index}]")

    if len(all_shot_ids) != len(set(all_shot_ids)):
        add("shot_unit", "shot_id_duplicate", "blocking", "候选镜头 ID 不唯一。", "shots")
    if not isinstance(handoff, dict) or not handoff:
        add("asset_handoff", "asset_handoff_missing", "blocking", "候选缺少资产交接包。", "assetHandoff")
    for category in ("characters", "scenes", "props", "soundRequirements"):
        if category not in handoff:
            add("asset_handoff", "asset_handoff_field_missing", "blocking", f"资产交接包缺少 {category} 分类。", f"assetHandoff.{category}")
    if not isinstance(handoff.get("shotAssetMatrix"), list):
        add("asset_handoff", "shot_asset_matrix_missing", "blocking", "资产交接包必须提供 shotAssetMatrix，以便资产监管按镜头解析依赖。", "assetHandoff.shotAssetMatrix")

    compatibility_missing: list[str] = []
    if all_requirement_errors:
        compatibility_missing.extend(f"{shot_id}.assetRequirements" for shot_id in all_requirement_errors)
    if not known_asset_ids:
        compatibility_missing.append("assetHandoff asset IDs")
    compatibility_blockers = [item for item in issues if item["gate"] == "asset_handoff" and item["severity"] == "blocking"]
    if compatibility_blockers:
        add("downstream_compatibility", "downstream_handoff_incomplete", "blocking", "当前候选无法完整投递到资产监管、资产意图和现有资产 Prompt 入口。", "assetHandoff", "补齐逐镜头资产需求与稳定资产声明。")
    compatibility_blocked = bool(compatibility_missing or compatibility_blockers)

    gates = []
    for gate_id, label in gate_order:
        gate_issues = [item for item in issues if item["gate"] == gate_id]
        if any(item["severity"] == "blocking" for item in gate_issues):
            status = "blocked"
        elif gate_issues:
            status = "warning"
        else:
            status = "passed"
        gates.append({"id": gate_id, "label": label, "status": status, "issueCodes": [item["code"] for item in gate_issues]})

    blocking_issues = [item for item in issues if item["severity"] == "blocking"]
    warning_issues = [item for item in issues if item["severity"] == "warning"]
    script_gates = {"source_integrity", "script_dramaturgy"}
    needs_user_review = bool(declared_additions) and not blocking_issues
    script_acceptance_allowed = workflow_mode != "storyboard_from_source" and not any(item["gate"] in script_gates for item in blocking_issues) and not needs_user_review
    status = "blocked" if blocking_issues else "needs_user_review" if needs_user_review else "passed_with_warnings" if warning_issues else "passed"
    return {
        "status": status,
        "acceptanceAllowed": not blocking_issues and not needs_user_review,
        "scriptAcceptanceAllowed": script_acceptance_allowed,
        "gates": gates,
        "issues": issues,
        "repairAttempts": repair_attempts,
        "ruleProfile": profile["id"],
        "ruleProfileVersion": profile["version"],
        "ruleModules": profile["modules"],
        "ruleSources": profile["sources"],
        "sourceScriptVersionId": package.get("source_script_version_id"),
        "sourceScriptHash": package.get("source_script_hash"),
        "handoffCompatibility": {
            "status": "blocked" if compatibility_blocked else "passed",
            "targets": ["video-asset-regulator", "asset-intent-preparation", "asset-prompt-run"],
            "missingFields": list(dict.fromkeys(compatibility_missing)),
            "sourceShotIds": [shot_id for shot_id in all_shot_ids if shot_id],
        },
        "checkedAt": now,
    }
