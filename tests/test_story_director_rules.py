from __future__ import annotations

import hashlib
import unittest

from frameflow.story import story_checks, story_spec
from frameflow.contracts import contract_bundle, contract_snapshot
from frameflow.story_rules import (
    CONTINUITY_FIELDS,
    DIRECTOR_RULE_PROFILE,
    DIRECTOR_RULE_PROFILE_VERSION,
    director_auto_review,
    director_rule_profile,
)


def complete_candidate() -> tuple[dict, dict]:
    source = "一名角色抬头，门外警报灯亮起。"
    scene = {
        "id": "S001",
        "sceneGoal": "建立出口受阻的对峙空间",
        "characterDesire": "找到安全出口",
        "primaryObstacle": "门外警报和封锁",
        "observableAction": "角色抬头并退向出口",
        "stateChange": "角色从静止转为警觉",
        "turn": "警报灯突然亮起",
        "entryState": "角色低头站在门内",
        "exitState": "角色面向出口准备移动",
        "relevantShots": ["SH001"],
    }
    continuity = {field: "明确" for field in CONTINUITY_FIELDS}
    seedance = {
        "model": "seedance2.5",
        "generationMode": "reference_to_video",
        "targetDuration": 5,
        "aspectRatio": "16:9",
        "clipUnit": "one_shot_one_reviewable_clip",
        "promptTimeline": [{"time": "0-5", "action": "抬头并后退"}],
        "startState": "角色低头",
        "playableChange": "角色抬头并后退",
        "endState": "角色面向出口",
        "continuityStrategy": "保持右向视线和红色警报光方向",
        "audioStrategy": "警报声持续",
        "mustPreserve": [],
        "mustAvoid": [],
        "riskFlags": [],
        "fallbackRoute": "拆分为两个单事件镜头",
    }
    shot = {
        "id": "SH001",
        "scene": "S001",
        "duration": 5,
        "purpose": "展示角色的警觉反应",
        "action": "角色抬头并退向出口",
        "visibleEvent": "角色抬头并退向出口",
        "eventConsequence": "警报灯在角色脸上形成红色移动反射",
        "sourceBeatIds": ["B001"],
        "subjectFocus": "角色的眼睛和后退动作",
        "performance": "眉头收紧，呼吸变急",
        "blocking": "角色从画面左侧退向后景出口",
        "coverageRole": "展示反应",
        "environmentPressure": "警报灯和封锁门压迫角色移动",
        "microAction": "手指短暂收紧",
        "visualMotif": "红色警报光扫过湿地面",
        "cameraExecution": {"instruction": "中景固定后轻微跟随"},
        "spatialGeography": "角色在前景左侧，出口在后景右侧",
        "materialEvidence": "湿地面反射红色警报光",
        "lightingCausality": "右后方警报灯造成脸部和地面的红色反射",
        "continuity": continuity,
        "seedancePlan": seedance,
        "assetRequirements": [{
            "shotId": "SH001",
            "assetId": "C001",
            "assetClass": "character",
            "role": "角色身份",
            "priority": "A",
            "required": True,
            "requiredReadiness": "production",
        }],
    }
    candidate = {
        "proposedScript": source,
        "structure": [{"id": "BEAT_001", "function": "setup"}],
        "beats": [{"id": "B001", "text": source}],
        "productionElements": {},
        "sourceScriptHash": hashlib.sha256(source.encode()).hexdigest(),
        "sourceBeatCoverage": {"status": "complete", "items": [], "unknownMappings": []},
        "scenes": [scene],
        "shots": [shot],
        "assetHandoff": {
            "characters": [{"id": "C001", "name": "角色"}],
            "scenes": [],
            "props": [],
            "soundRequirements": [],
            "shotAssetMatrix": [{"shotId": "SH001", "characterIds": ["C001"]}],
        },
    }
    package = {
        "rule_profile": DIRECTOR_RULE_PROFILE,
        "rule_profile_version": DIRECTOR_RULE_PROFILE_VERSION,
        "workflow_mode": "optimize_script_and_storyboard",
        "current_script": source,
        "source_script_version_id": "SCRIPT_V1",
        "source_script_hash": hashlib.sha256(source.encode()).hexdigest(),
        "source_beat_ledger": [{"id": "B001", "text": source}],
        "existing_asset_ids": [],
    }
    return candidate, package


class StoryDirectorRuleTests(unittest.TestCase):
    def test_profile_contains_the_selected_skill_modules(self) -> None:
        profile = director_rule_profile()
        self.assertEqual(profile["id"], DIRECTOR_RULE_PROFILE)
        self.assertEqual(profile["version"], DIRECTOR_RULE_PROFILE_VERSION)
        self.assertIn("writer-structure", profile["scriptModules"])
        self.assertIn("visual-dramaturgy", profile["storyboardModules"])
        self.assertIn("downstream-compatibility", profile["handoffModules"])
        self.assertTrue(any(item["id"] == "muse-video-skill:Writer" for item in profile["sources"]))

    def test_live_contract_publishes_the_director_profile(self) -> None:
        bundle = contract_bundle()
        story_contract = bundle["story_contract"]
        self.assertEqual(story_contract["version"], "2.0")
        self.assertIn("director_scene_fields", story_contract)
        self.assertIn("auto_review_gates", story_contract)
        self.assertTrue(story_contract["rule_profiles"][0]["sources"])
        snapshot = contract_snapshot(bundle)
        self.assertEqual(snapshot["story_rule_profile"], DIRECTOR_RULE_PROFILE)
        self.assertEqual(snapshot["story_rule_profile_version"], DIRECTOR_RULE_PROFILE_VERSION)

    def test_complete_candidate_passes_without_calling_a_provider(self) -> None:
        candidate, package = complete_candidate()
        report = director_auto_review(candidate, package)
        self.assertEqual(report["status"], "passed", report)
        self.assertTrue(report["acceptanceAllowed"])
        self.assertEqual(report["handoffCompatibility"]["status"], "passed")

    def test_missing_director_fields_block_the_candidate(self) -> None:
        candidate, package = complete_candidate()
        candidate["shots"][0]["microAction"] = "待确认"
        report = director_auto_review(candidate, package)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["acceptanceAllowed"])
        self.assertTrue(any(item["code"] == "shot_director_field_missing" for item in report["issues"]))

    def test_handoff_reference_and_seedance_duration_gates_are_strict(self) -> None:
        candidate, package = complete_candidate()
        candidate["assetHandoff"]["characters"][0]["generationReferenceAssets"] = [{
            "assetId": "S001",
            "role": "空间尺度",
            "controls": "角色与场景的相对尺度",
            "doesNotControl": "不改变角色身份",
            "required": True,
            # reason and relevantShots are intentionally missing.
        }]
        candidate["shots"][0]["seedancePlan"]["model"] = "seedance2.0"
        candidate["shots"][0]["seedancePlan"]["targetDuration"] = 16
        report = director_auto_review(candidate, package)
        self.assertEqual(report["status"], "blocked")
        codes = {item["code"] for item in report["issues"]}
        self.assertIn("reference_role_missing", codes)
        self.assertIn("generator_duration_limit", codes)

    def test_declared_creative_addition_requires_user_review(self) -> None:
        candidate, package = complete_candidate()
        candidate["creativeAdditions"] = [{"type": "prop", "id": "P001", "reason": "让接触动作可见"}]
        report = director_auto_review(candidate, package)
        self.assertEqual(report["status"], "needs_user_review")
        self.assertFalse(report["acceptanceAllowed"])
        self.assertFalse(report["scriptAcceptanceAllowed"])
        self.assertTrue(any(item["code"] == "creative_addition_needs_confirmation" for item in report["issues"]))

    def test_direct_source_mutation_is_blocked(self) -> None:
        candidate, package = complete_candidate()
        package["workflow_mode"] = "storyboard_from_source"
        candidate["proposedScript"] = "被模型改写的剧本"
        report = director_auto_review(candidate, package)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["acceptanceAllowed"])
        self.assertFalse(report["scriptAcceptanceAllowed"])
        self.assertTrue(any(item["code"] == "source_script_mutation" for item in report["issues"]))

    def test_legacy_profile_is_not_silently_upgraded(self) -> None:
        report = director_auto_review({}, {"rule_profile": "legacy", "workflow_mode": "optimize_script_and_storyboard"})
        self.assertEqual(report["status"], "not_applicable")
        self.assertTrue(report["acceptanceAllowed"])

    def test_story_spec_exposes_profile_and_v2_story_checks_are_strict(self) -> None:
        document = {
            "storySpec": {"rule_profile": DIRECTOR_RULE_PROFILE, "rule_profile_version": DIRECTOR_RULE_PROFILE_VERSION},
            "script": "测试剧本",
            "scenes": [{"id": "S001"}],
            "shots": [{"id": "SH001", "scene": "S001", "duration": 3, "purpose": "目的", "size": "中景", "camera": "固定", "action": "动作"}],
            "assets": [],
        }
        spec = story_spec(document)
        self.assertEqual(spec["rule_profile"], DIRECTOR_RULE_PROFILE)
        checks = story_checks(document)
        self.assertFalse(checks["ok"])
        self.assertGreater(checks["errors"], 0)
        codes = {item["code"] for item in checks["issues"]}
        self.assertIn("scene_director_contract_incomplete", codes)
        self.assertIn("shot_director_contract_incomplete", codes)


if __name__ == "__main__":
    unittest.main()
