from __future__ import annotations

import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import server
from frameflow.prompt_design import canonicalize_prompt_output
from frameflow.story_rules import CONTINUITY_FIELDS


SOURCE_SCRIPT = "角色触碰机械手。接口灯亮起。"


def continuity_contract() -> dict[str, str]:
    return {field: f"{field} 已明确并与相邻镜头衔接" for field in CONTINUITY_FIELDS}


def seedance_plan(duration: float) -> dict[str, object]:
    return {
        "model": "seedance2.5",
        "generationMode": "reference_to_video",
        "targetDuration": duration,
        "aspectRatio": "16:9",
        "clipUnit": "one_shot_one_reviewable_clip",
        "promptTimeline": [{"time": f"0-{duration}", "action": "单一可见动作"}],
        "startState": "动作开始前的稳定状态",
        "playableChange": "主体完成一个可观察变化",
        "endState": "变化完成后的稳定状态",
        "continuityStrategy": "保持屏幕方向、视线和空间几何不变",
        "referenceAssignments": [],
        "audioStrategy": "环境声连续，动作声在变化点出现",
        "mustPreserve": [],
        "mustAvoid": [],
        "riskFlags": [],
        "fallbackRoute": "拆分为单一事件镜头并减少参考输入",
    }


def storyboard_candidate() -> dict[str, object]:
    requirements = [
        {
            "shotId": "SH001",
            "assetId": "C001",
            "assetClass": "character",
            "role": "锁定角色身份",
            "priority": "B",
            "required": True,
            "requiredReadiness": "production",
        },
        {
            "shotId": "SH001",
            "assetId": "S001",
            "assetClass": "scene",
            "role": "锁定空间布局",
            "priority": "B",
            "required": True,
            "requiredReadiness": "production",
        },
    ]
    scene = {
        "id": "S001",
        "name": "机库接口区",
        "description": "一处有明确前景、中景和接口灯光来源的机库空间。",
        "interiorExterior": "内景",
        "timeOfDay": "夜",
        "location": "机库接口区",
        "characterIds": ["C001"],
        "propIds": [],
        "narrativeFunction": "建立人与机械之间的接触关系",
        "emotion": "克制的悬念",
        "visualAnchors": ["接口灯", "金属地面"],
        "spatialGeography": "角色在前景左侧，机械手位于中景右侧，出口在后景。",
        "materialEvidence": "金属表面反射接口灯，接触位置有清晰阴影。",
        "lightingCausality": "接口灯从右后方照亮机械手和角色手部。",
        "soundscape": "低频设备声持续，接触时叠加短促机械声。",
        "productionDifficulty": "medium",
        "relevantShots": ["SH001", "SH002"],
        "sceneGoal": "让角色从试探接触进入确认机械响应",
        "characterDesire": "确认机械手是否会回应",
        "primaryObstacle": "机械接口没有立即给出反馈",
        "observableAction": "角色伸手触碰接口并抬头观察灯光",
        "stateChange": "空间从静默待机变为被接口灯激活",
        "turn": "接口灯突然亮起并改变角色判断",
        "entryState": "角色站在待机的机械手前",
        "exitState": "角色确认接口已经响应并准备继续行动",
    }

    def shot(shot_id: str, beat_id: str, visible_event: str, consequence: str, duration: float, asset_requirements: list[dict[str, object]]) -> dict[str, object]:
        return {
            "id": shot_id,
            "scene": "S001",
            "duration": duration,
            "purpose": "展示一个明确的状态变化",
            "size": "中近景",
            "camera": "固定机位后轻微跟随",
            "action": visible_event,
            "visibleEvent": visible_event,
            "eventConsequence": consequence,
            "sourceBeatIds": [beat_id],
            "subjectFocus": "角色手部、接口灯和即时反应",
            "performance": "动作克制，反应通过短暂停顿和视线变化呈现",
            "blocking": "角色位于前景左侧，动作朝向中景右侧接口",
            "coverageRole": "展示行动及其反应",
            "environmentPressure": "狭窄机库和持续设备声压缩可用行动空间",
            "microAction": "手指在接触后短暂收紧",
            "visualMotif": "冷色接口灯在金属表面形成反射",
            "cameraExecution": {"instruction": "保持中近景，动作点轻微跟随，不切换轴线"},
            "spatialGeography": "角色左前景，接口右中景，出口后景，屏幕方向保持向右",
            "materialEvidence": "手套与金属接口接触处出现阴影和反光变化",
            "lightingCausality": "接口灯亮起后，蓝色光线先落在机械手再反射到角色手部",
            "continuity": continuity_contract(),
            "seedancePlan": seedance_plan(duration),
            "assetRequirements": asset_requirements,
            "referenceRoles": [],
            "risks": [],
            "dialogue": "",
            "narration": "",
            "sound": "低频设备声和接触机械声",
            "environment": "待机机库接口区",
            "generationMethod": "reference_to_video",
            "difficulty": "medium",
        }

    second_requirements = [
        {**item, "shotId": "SH002"}
        for item in requirements
    ]
    return {
        "proposedScript": SOURCE_SCRIPT,
        "structure": [{"id": "STRUCT_001", "function": "setup_to_turn", "summary": "接触导致接口响应"}],
        "beats": [
            {"id": "B001", "text": "角色触碰机械手。", "function": "setup"},
            {"id": "B002", "text": "接口灯亮起。", "function": "turn"},
        ],
        "feasibility": {"verdict": "可执行", "difficulty": "medium"},
        "productionElements": {"characters": ["C001"], "scenes": ["S001"]},
        "scenes": [scene],
        "shots": [
            shot("SH001", "B001", "角色伸手触碰机械手接口", "接触位置出现清晰阴影，机械手保持待机", 4, requirements),
            shot("SH002", "B002", "接口灯亮起并照亮角色手部", "角色确认机械已经响应，空间状态从待机变为激活", 4, second_requirements),
        ],
        "risks": [],
        "assetHandoff": {
            "characters": [{"id": "C001", "name": "主角", "productionRole": "base_asset", "relevantShots": ["SH001", "SH002"], "generationReferenceAssets": []}],
            "scenes": [{"id": "S001", "name": "机库接口区", "productionRole": "base_asset", "relevantShots": ["SH001", "SH002"], "generationReferenceAssets": []}],
            "props": [],
            "soundRequirements": [],
            "shotAssetMatrix": [
                {"shotId": "SH001", "characterIds": ["C001"], "sceneIds": ["S001"]},
                {"shotId": "SH002", "characterIds": ["C001"], "sceneIds": ["S001"]},
            ],
        },
    }


def prompt_pack(asset_class: str, subject: str) -> dict[str, object]:
    return canonicalize_prompt_output(
        asset_class,
        {"subjectTask": subject, "visualStyleMaterials": "写实、统一、清晰呈现主体结构与材质。"},
        "",
        context={"output_aspect_ratio": "16:9"},
    )["promptPack"]


class StoryHandoffChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(__file__).parent / f"test-story-handoff-{uuid.uuid4().hex}.db"
        self.runtime_root = Path(tempfile.gettempdir()) / f"frameflow-runtime-{self.db_path.stem}"
        self.db_patch = mock.patch.object(server, "DB_PATH", self.db_path)
        self.db_patch.start()
        self.secret_patch = mock.patch.object(server, "get_secret", return_value=None)
        self.secret_patch.start()
        self.client_context = TestClient(server.app)
        self.client = self.client_context.__enter__()

        created = self.client.post("/api/v2/projects", json={
            "name": "规则衔接验收",
            "ratio": "16:9",
            "duration": 8,
            "generator": "seedance2.5",
            "brief": "验证新剧本分镜规则到资产 Prompt 的衔接。",
        })
        self.assertEqual(created.status_code, 201, created.text)
        self.project_id = created.json()["document"]["id"]

        story = self.client.get(f"/api/v2/projects/{self.project_id}/story")
        self.assertEqual(story.status_code, 200, story.text)
        document = story.json()["story"]
        document["script"] = SOURCE_SCRIPT
        saved = self.client.put(f"/api/v2/projects/{self.project_id}/story", json={
            "expected_revision": story.json()["revision"],
            "spec": document["spec"],
            "script": document["script"],
            "scenes": [],
            "shots": [],
        })
        self.assertEqual(saved.status_code, 200, saved.text)

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.secret_patch.stop()
        self.db_patch.stop()
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(str(self.db_path) + suffix)
            if candidate.is_file():
                candidate.unlink()
        if self.runtime_root.is_dir():
            shutil.rmtree(self.runtime_root)

    def test_source_lineage_mismatch_is_retained_as_a_review_blocker(self) -> None:
        created = self.client.post(f"/api/v2/projects/{self.project_id}/story/runs", json={
            "workflow_mode": "storyboard_from_source",
            "duration": 8,
            "generator_profile": "seedance2.5",
        })
        self.assertEqual(created.status_code, 200, created.text)
        run_id = created.json()["id"]
        candidate = storyboard_candidate()
        candidate["sourceScriptVersionId"] = "SCRIPT_FROM_ANOTHER_RUN"
        candidate["sourceScriptHash"] = "hash-from-another-run"
        agent = mock.AsyncMock(side_effect=[candidate, candidate])
        with mock.patch.object(server, "_run_storyboard_agent", new=agent):
            started = self.client.post(f"/api/v2/story-runs/{run_id}/start")
        self.assertEqual(started.status_code, 200, started.text)
        output = started.json()["run"]["storyboard_output"]
        self.assertEqual(agent.await_count, 2)
        self.assertFalse(output["acceptanceAllowed"])
        codes = {item["code"] for item in output["autoReview"]["issues"]}
        self.assertIn("source_script_version_mismatch", codes)
        self.assertIn("source_script_hash_mismatch", codes)

    def test_storyboard_requirements_survive_regulator_and_prompt_handoff(self) -> None:
        created = self.client.post(f"/api/v2/projects/{self.project_id}/story/runs", json={
            "workflow_mode": "storyboard_from_source",
            "duration": 8,
            "generator_profile": "seedance2.5",
        })
        self.assertEqual(created.status_code, 200, created.text)
        run_id = created.json()["id"]

        with mock.patch.object(server, "_run_storyboard_agent", new=mock.AsyncMock(return_value=storyboard_candidate())):
            started = self.client.post(f"/api/v2/story-runs/{run_id}/start")
        self.assertEqual(started.status_code, 200, started.text)
        started_run = started.json()["run"]
        self.assertEqual(started_run["status"], "storyboard_review_required")
        review = started_run["storyboard_output"]["autoReview"]
        self.assertEqual(review["status"], "passed")
        self.assertTrue(review["acceptanceAllowed"])

        # The regulator intentionally returns only one of the two accepted
        # per-shot requirements. The accepted storyboard must remain the
        # source of truth for the missing requirement.
        regulator = {
            "assetExtraction": [
                {"id": "C001", "name": "主角", "assetClass": "character", "priority": "B"},
                {"id": "S001", "name": "机库接口区", "assetClass": "scene", "priority": "B"},
            ],
            "assetRequirements": [{"shotId": "SH001", "assetId": "C001", "assetClass": "character", "required": True}],
            "nextActions": [],
        }
        with mock.patch.object(server, "_run_regulator_agent", new=mock.AsyncMock(return_value=regulator)):
            accepted = self.client.post(f"/api/v2/story-runs/{run_id}/accept-storyboard", json={"scope": "all"})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()["run"]["status"], "regulator_review_required")

        finalized = self.client.post(f"/api/v2/story-runs/{run_id}/accept-regulator")
        self.assertEqual(finalized.status_code, 200, finalized.text)
        self.assertEqual(finalized.json()["run"]["status"], "succeeded")
        receipt = finalized.json()["handoffReceipt"]
        self.assertEqual(receipt["shotAssetEdges"], 4)
        self.assertEqual(set(receipt["provenance"]["sourceShotIds"]), {"SH001", "SH002"})
        self.assertTrue(receipt["provenance"]["sourceStoryboardVersionId"])

        project = self.client.get(f"/api/v2/projects/{self.project_id}").json()["document"]
        for shot in project["shots"]:
            self.assertEqual({item["assetId"] for item in shot["assetRequirements"]}, {"C001", "S001"})

        intents = self.client.get(f"/api/v2/projects/{self.project_id}/asset-intents")
        self.assertEqual(intents.status_code, 200, intents.text)
        prepared = self.client.post(f"/api/v2/projects/{self.project_id}/asset-intents/prepare", json={"expected_revision": intents.json()["revision"]})
        self.assertEqual(prepared.status_code, 200, prepared.text)
        self.assertEqual(prepared.json()["preparedAssetCount"], 0)
        self.assertEqual(prepared.json()["progress"]["total"], 2)

        current = prepared.json()
        for asset_id in ("C001", "S001"):
            response = self.client.post(
                f"/api/v2/projects/{self.project_id}/asset-intents/{asset_id}/interpret",
                json={"expected_revision": current["revision"], "mode": "script_only"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            current = response.json()
        self.assertTrue(current["progress"]["allHandled"])
        self.assertEqual(set(current["currentProvenance"]["sourceShotIds"]), {"SH001", "SH002"})

        prompt_output = {
            "assets": [
                {"id": "C001", "name": "主角", "assetClass": "character", "priority": "B", "required": True, "targetSkill": "video-character-design-director", "relevantShots": ["SH001", "SH002"], "prompt": "角色 Prompt", "promptPack": prompt_pack("character", "锁定主角身份"), "mustPreserve": [], "mustAvoid": []},
                {"id": "S001", "name": "机库接口区", "assetClass": "scene", "priority": "B", "required": True, "targetSkill": "video-scene-design-director", "relevantShots": ["SH001", "SH002"], "prompt": "场景 Prompt", "promptPack": prompt_pack("scene", "锁定机库空间"), "mustPreserve": [], "mustAvoid": []},
            ],
            "fusionPlans": [],
            "missingAssetRegister": [],
            "dependencyTable": [],
            "routingPlan": [],
            "nextActions": [],
            "warnings": [],
        }
        captured: dict[str, dict] = {}

        async def fake_regulator(request, project_id, input_package):
            captured["regulator"] = input_package
            return regulator

        async def fake_prompt(request, project_id, input_package):
            captured["prompt"] = input_package
            return prompt_output

        with mock.patch.object(server, "_run_regulator_agent", new=mock.AsyncMock(side_effect=fake_regulator)), mock.patch.object(server, "_run_asset_prompt_agent", new=mock.AsyncMock(side_effect=fake_prompt)):
            generated = self.client.post(
                f"/api/v2/projects/{self.project_id}/asset-prompt-runs",
                json={"expected_revision": current["revision"], "asset_intent_version": current["assetIntentVersion"]},
            )
        self.assertEqual(generated.status_code, 200, generated.text)

        handoff_provenance = captured["prompt"]["handoff_provenance"]
        self.assertEqual(set(handoff_provenance["sourceShotIds"]), {"SH001", "SH002"})
        self.assertTrue(handoff_provenance["sourceStoryboardVersionId"])
        for intent in captured["prompt"]["confirmed_asset_intents"]:
            self.assertEqual(set(intent["provenance"]["sourceShotIds"]), {"SH001", "SH002"})

        generated_run = generated.json()["run"]
        self.assertEqual(generated_run["handoffProvenance"], handoff_provenance)
        refreshed_intents = self.client.get(f"/api/v2/projects/{self.project_id}/asset-intents")
        self.assertEqual(refreshed_intents.status_code, 200, refreshed_intents.text)
        self.assertFalse(refreshed_intents.json()["manifestStale"], refreshed_intents.text)
        final_project = self.client.get(f"/api/v2/projects/{self.project_id}").json()["document"]
        for shot in final_project["shots"]:
            requirement_ids = {item["assetId"] for item in shot["assetRequirements"]}
            self.assertTrue({"C001", "S001"}.issubset(requirement_ids))
        self.assertTrue(any(item.get("assetClass") == "fusion" for item in final_project["assets"]))


if __name__ == "__main__":
    unittest.main()
