from __future__ import annotations

import unittest

from frameflow.agent import normalize_agent_patch
from frameflow.prompt_design import (
    AUDIO_PROMPT_SCHEMA_VERSION,
    PROMPT_CONTRACT_VERSION,
    STYLE_LIBRARY_SOURCE,
    STYLE_LIBRARY_VERSION,
    assess_prompt_pack,
    build_audio_prompt_package,
    build_natural_language_prompt,
    canonicalize_prompt_output,
    prompt_contract,
    prompt_contract_instructions,
    select_style_template,
    validate_clean_prompt,
)


class PromptDesignTests(unittest.TestCase):
    def test_contract_makes_style_library_the_visual_authority(self) -> None:
        contract = prompt_contract()
        self.assertEqual(contract["version"], PROMPT_CONTRACT_VERSION)
        self.assertEqual(contract["workflow"], "style-library-visual-v1")
        self.assertEqual(contract["rule_source"]["skill"], STYLE_LIBRARY_SOURCE)
        self.assertEqual(contract["rule_source"]["version"], STYLE_LIBRARY_VERSION)
        self.assertEqual(
            contract["prompt_blocks"],
            [
                "subjectTask",
                "compositionLayout",
                "visualStyleMaterials",
                "textLabels",
                "aspectRatioOutput",
                "constraintsNegative",
            ],
        )
        self.assertEqual(
            set(contract["prompt_pack_shape"]),
            {
                "subjectTask",
                "compositionLayout",
                "visualStyleMaterials",
                "textLabels",
                "aspectRatioOutput",
                "constraintsNegative",
                "referenceRoles",
                "actionContinuity",
            },
        )
        self.assertEqual(len(contract["templates"]), 22)
        self.assertTrue(all(item["guidance"] and item["pitfalls"] for item in contract["templates"]))
        instructions = prompt_contract_instructions()
        self.assertIn("gpt-image-2-style-library", instructions)
        self.assertIn("模板 pitfalls", instructions)
        self.assertIn("旧 Prompt 规则、旧字段、旧 fallback 均已退役", instructions)

    def test_template_selection_follows_asset_direction_and_allows_a_valid_override(self) -> None:
        expected = {
            "character": "character-design-sheet",
            "scene": "architecture-space",
            "prop": "concept-product-breakdown",
            "product": "product-commerce-visual",
            "fusion": "scene-storytelling",
            "shot": "scene-storytelling",
            "style": "illustration-art-style",
        }
        for asset_class, template_id in expected.items():
            selection = select_style_template(asset_class, {"subjectTask": asset_class})
            self.assertEqual(selection["templateId"], template_id)
            self.assertEqual(selection["libraryVersion"], STYLE_LIBRARY_VERSION)
            self.assertEqual(selection["selectionOrder"][-1], "template_pitfalls")
        overridden = select_style_template("character", template_override="realistic-photography")
        self.assertEqual(overridden["templateId"], "realistic-photography")
        self.assertEqual(overridden["selectionMode"], "override")
        with self.assertRaises(ValueError):
            select_style_template("character", template_override="not-a-style-library-template")

    def test_character_prompt_is_one_clean_four_zone_reference_board(self) -> None:
        result = canonicalize_prompt_output(
            "character",
            {
                "subjectTask": "一名冷白科幻驾驶员的可复用角色身份参考资产",
                "visualStyleMaterials": "写实动漫融合，冷白装甲、石墨黑结构、青蓝发光接口，清楚表现皮肤、发丝、织物和磨砂装甲差异。",
                "referenceRoles": [
                    {
                        "referenceId": "C001",
                        "role": "identity reference",
                        "purpose": "锁定脸部和服装身份",
                        "scope": "角色身份、服装结构和配色",
                    }
                ],
                "textLabels": "",
            },
            "",
        )
        prompt = result["copyablePrompt"]
        self.assertIn("左侧约42%为角色面部与上半身特写", prompt)
        self.assertIn("右侧约58%分为三个等宽全身视图区", prompt)
        self.assertIn("正面全身", prompt)
        self.assertIn("严格90°侧面全身", prompt)
        self.assertIn("严格180°背面全身", prompt)
        self.assertIn("写实动漫融合", prompt)
        self.assertIn("画面比例为16:9", prompt)
        self.assertIn("输出为PNG图像资产", prompt)
        self.assertIn("模板避坑：", prompt)
        for internal in ("C001", "character-design-sheet", "3d-collectible-toy", "Prompt Contract", "Provider", "OpenCode", "JSON"):
            self.assertNotIn(internal, prompt)
        self.assertEqual(result["promptQuality"]["status"], "ready")
        self.assertEqual(validate_clean_prompt(prompt, asset_class="character", base_asset=True), [])
        self.assertEqual(
            set(result["promptPack"]),
            {"templateSelection", "subjectTask", "compositionLayout", "visualStyleMaterials", "textLabels", "aspectRatioOutput", "constraintsNegative", "referenceRoles"},
        )

    def test_scene_prop_product_keep_fixed_canvas_and_independent_boundaries(self) -> None:
        cases = {
            "scene": {
                "subjectTask": "雨夜山腰祠堂的空环境",
                "visualStyleMaterials": "写实摄影，湿石材、旧木、冷蓝雨光与檐下暖光。",
            },
            "prop": {
                "subjectTask": "六翼折叠机械道具",
                "visualStyleMaterials": "磨砂钛灰外壳、黑色橡胶接缝、轻微使用划痕。",
            },
            "product": {
                "subjectTask": "透明护肤瓶产品主体",
                "visualStyleMaterials": "商业产品摄影，透明玻璃、金属泵头、柔和高光。",
            },
        }
        expected_ratios = {"scene": "16:9", "prop": "1:1", "product": "1:1"}
        for asset_class, pack in cases.items():
            result = canonicalize_prompt_output(asset_class, pack, "")
            prompt = result["prompt"]
            self.assertEqual(result["aspectRatioOutput"]["aspectRatio"], expected_ratios[asset_class])
            self.assertEqual(result["aspectRatioOutput"]["outputFormat"], "png")
            self.assertIn(f"画面比例为{expected_ratios[asset_class]}", prompt)
            self.assertIn("输出为PNG图像资产", prompt)
            self.assertNotIn("角色握住", prompt)
            self.assertNotIn("人物手持", prompt)
            self.assertNotIn("Prompt Contract", prompt)
            self.assertEqual(result["promptQuality"]["status"], "ready")
        self.assertIn("不放入角色或独立道具", canonicalize_prompt_output("scene", cases["scene"], "")["prompt"])
        self.assertIn("不进行人物或场景融合", canonicalize_prompt_output("prop", cases["prop"], "")["prompt"])

    def test_fusion_and_shot_inherit_project_ratio_and_require_visible_continuity(self) -> None:
        pack = {
            "subjectTask": "角色握住机械道具站在雨夜祠堂前",
            "visualStyleMaterials": "统一写实摄影，湿石材、旧木和装甲材质对同一环境光作出响应。",
            "actionContinuity": "角色从左向右迈步，摄影机低机位跟随，保持雨水反射和屏幕方向连续。",
            "referenceRoles": [{"referenceId": "C001", "purpose": "锁定角色身份", "scope": "角色"}],
        }
        for asset_class in ("fusion", "shot"):
            result = canonicalize_prompt_output(asset_class, pack, "", context={"output_aspect_ratio": "16:9"})
            self.assertEqual(result["aspectRatioOutput"]["aspectRatio"], "16:9")
            self.assertEqual(result["aspectRatioOutput"]["outputFormat"], "png")
            self.assertIn("按项目画面比例16:9", result["prompt"])
            self.assertIn("角色从左向右迈步", result["prompt"])
            self.assertEqual(result["promptPack"]["templateSelection"]["templateId"], "scene-storytelling")
            self.assertEqual(result["promptQuality"]["status"], "ready")
            self.assertNotIn("C001", result["prompt"])

    def test_empty_optional_blocks_are_trimmed_from_copyable_prompt(self) -> None:
        result = canonicalize_prompt_output(
            "product",
            {"subjectTask": "透明玻璃瓶", "visualStyleMaterials": "干净的商业产品摄影", "textLabels": ""},
            "",
        )
        self.assertNotIn("文字标签：", result["prompt"])
        self.assertNotIn("已上传参考图", result["prompt"])
        self.assertNotIn("{}", result["prompt"])
        self.assertNotIn("[]", result["prompt"])

    def test_old_pack_and_old_prompt_are_never_used_as_a_fallback(self) -> None:
        old_pack = {
            "promptIntent": "旧版场景意图",
            "identityAnchor": "旧版身份锚点",
            "sceneDetails": {"geography": "旧版空间"},
            "generationNotes": "legacy_supplement",
        }
        result = canonicalize_prompt_output("scene", old_pack, "旧版 Prompt 全文")
        self.assertEqual(result["prompt"], "")
        self.assertEqual(result["copyablePrompt"], "")
        self.assertTrue(result["needsRegeneration"])
        self.assertIn("promptIntent", result["legacyFieldsDropped"])
        self.assertEqual(result["promptQuality"]["status"], "needs-regeneration")
        self.assertEqual(build_natural_language_prompt("scene", old_pack, "旧版 Prompt 全文"), "")
        issues = validate_clean_prompt("FRAMEFLOW Prompt Contract v2.0；legacy_supplement；OpenCode")
        self.assertTrue(any("内部标记" in issue for issue in issues))

    def test_clean_manual_text_can_seed_only_the_new_subject_block(self) -> None:
        result = canonicalize_prompt_output("scene", {}, "A quiet room")
        self.assertIn("A quiet room", result["prompt"])
        self.assertIn("横向空环境参考板", result["prompt"])
        self.assertEqual(result["promptPack"]["subjectTask"], "A quiet room")
        self.assertFalse(result["needsRegeneration"])

    def test_clean_manual_edit_preserves_the_backend_prompt_without_dropping_invariants(self) -> None:
        generated = canonicalize_prompt_output(
            "character",
            {
                "subjectTask": "一名冷白科幻驾驶员",
                "visualStyleMaterials": "写实动漫融合，冷白装甲与青蓝发光接口",
            },
            "",
        )
        edited = generated["prompt"] + "\n\n强调装甲接缝、发丝边缘和磨砂材质的真实差异。"
        saved = canonicalize_prompt_output(
            "character",
            generated["promptPack"],
            edited,
            preserve_clean_prompt=True,
            strict_clean=True,
        )
        self.assertEqual(saved["copyablePrompt"], edited)
        self.assertIn("左侧约42%", saved["copyablePrompt"])
        self.assertIn("画面比例为16:9", saved["copyablePrompt"])
        self.assertEqual(saved["promptQuality"]["status"], "ready")

    def test_audio_contract_remains_separate_from_visual_rules(self) -> None:
        pack = {
            "audioDetails": {
                "sourceText": "看招。",
                "textStatus": "candidate",
                "voiceIdentity": "成年女性中文普通话，低沉、冷峻",
                "language": "中文",
                "dialect": "普通话",
            }
        }
        package = build_audio_prompt_package(pack, context={"shots": [{"id": "S03", "dialogue": "看招。"}]})
        self.assertEqual(package["schemaVersion"], AUDIO_PROMPT_SCHEMA_VERSION)
        self.assertEqual(package["copyText"], "")
        self.assertEqual(package["candidateText"], "看招。")
        self.assertIn("候选朗读文本待用户确认", build_natural_language_prompt("audio", pack))
        self.assertNotIn("空间关系与地理", build_natural_language_prompt("audio", pack))

    def test_audio_quality_reports_missing_confirmed_text(self) -> None:
        quality = assess_prompt_pack("audio", {"audioDetails": {"sourceText": "待确认", "textStatus": "candidate"}}, "待确认")
        self.assertEqual(quality["status"], "needs-confirmation")
        self.assertIn("朗读文本", quality["missing"])

    def test_legacy_agent_image_prompt_is_not_converted_into_a_visual_fallback(self) -> None:
        normalized = normalize_agent_patch(
            {"imagePrompt": "旧版 Prompt Contract；legacy_supplement"},
            base_project_revision=1,
            base_graph_revision=1,
        )
        self.assertEqual(normalized["patch"]["candidates"], [])
        self.assertIn("imagePrompt", normalized["patch"]["unsupported_operations"])


if __name__ == "__main__":
    unittest.main()
