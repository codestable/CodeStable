"""冻结 routing experiments 的历史完整性；不代表当前 shipped skill 契约。"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _routing_fixture_states(experiment: str) -> dict[str, dict[str, object]]:
    fixtures = ROOT / "experiments" / experiment / "fixtures/routing"
    result: dict[str, dict[str, object]] = {}
    for path in sorted(fixtures.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        result[payload["id"]] = payload
    return result


def test_frozen_goal_routing_fixtures_keep_recorded_state_schema() -> None:
    feat = _routing_fixture_states("cs-feat-routing-001")
    epic = _routing_fixture_states("cs-epic-routing-001")
    deprecated = {"reviewStatus", "hasGoalPackage", "codeStatus", "qaStatus", "acceptanceStatus"}

    for payload in [*feat.values(), *epic.values()]:
        state = payload["task"].get("state", {})
        assert deprecated.isdisjoint(state), payload["id"]
        assert "终态优先" not in json.dumps(state, ensure_ascii=False), payload["id"]

    assert feat["rt-f10"]["expect"]["result_type"] == "DispatchGoalDriver"
    assert feat["rt-f11"]["expect"]["result_type"] == "Awaiting"
    assert feat["rt-f12"]["expect"]["result_type"] == "GoalHandoff"
    assert feat["rt-f13"]["expect"]["result_type"] == "NeedsHuman"
    assert feat["rt-f14"]["expect"]["result_type"] == "HumanCheckpoint"
    assert feat["rt-f15"]["expect"]["target"] == "FastForward"
    assert feat["rt-f16"]["expect"]["target"] == "Implementation"
    assert feat["rt-f16"]["expect"]["must_not_target"] == "GoalPackage"
    assert feat["rt-f17"]["expect"]["target"] == "GoalPackage"
    assert feat["rt-f18"]["expect"]["target"] == "FastForward"

    assert epic["rt-p09"]["expect"]["result_type"] == "DispatchGoalDriver"
    assert epic["rt-p11"]["expect"]["result_type"] == "Awaiting"
    assert epic["rt-p12"]["expect"]["result_type"] == "Completed"
    assert epic["rt-p13"]["expect"]["result_type"] == "GoalHandoff"
    assert epic["rt-p14"]["expect"]["result_type"] == "NeedsHuman"


def test_frozen_cs_router_fixtures_keep_recorded_outcomes() -> None:
    fixtures = _routing_fixture_states("cs-routing-001")
    assert set(fixtures) == {f"rt-c{i:02d}" for i in range(1, 18)}

    assert fixtures["rt-c01"]["expect"]["result_type"] == "RoutedTo"
    assert fixtures["rt-c01"]["expect"]["target"] == "cs-issue"
    assert fixtures["rt-c02"]["expect"]["result_type"] == "Completed"
    assert fixtures["rt-c03"]["expect"]["result_type"] == "Completed"
    assert fixtures["rt-c04"]["expect"]["result_type"] == "NeedsHuman"

    for fixture_id, forbidden in (
        ("rt-c05", "cs-goal"),
        ("rt-c06", "cs-refactor"),
        ("rt-c08", "cs-keep"),
    ):
        assert fixtures[fixture_id]["expect"]["must_not_target"] == forbidden

    assert fixtures["rt-c10"]["expect"]["target"] == "cs-onboard"
    assert fixtures["rt-c10"]["task"]["state"]["original_target"] == "cs-issue"
    assert fixtures["rt-c11"]["expect"]["target"] == "cs-issue"
    assert fixtures["rt-c12"]["expect"]["target"] == "cs-refactor"
    assert fixtures["rt-c13"]["expect"]["result_type"] == "HumanCheckpoint"
    assert fixtures["rt-c14"]["expect"]["result_type"] == "NeedsHuman"
    assert fixtures["rt-c15"]["expect"]["result_type"] == "HumanCheckpoint"
    assert fixtures["rt-c16"]["expect"]["result_type"] == "Completed"
    assert "issue workflow" in fixtures["rt-c16"]["expect"]["target_any"]
    assert fixtures["rt-c17"]["expect"] == {
        "result_type": "RoutedTo",
        "target": "cs-feedback",
    }

    for fixture_id in ("rt-c02", "rt-c03", "rt-c04", "rt-c13", "rt-c15"):
        assert "must_not_target" not in fixtures[fixture_id]["expect"]
