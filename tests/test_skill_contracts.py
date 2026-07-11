"""校验 cs-* skill 的 frontmatter `contracts` 对 SKILL.md body 成立。

contracts 是 prompt-as-code 的机器护栏：`grep` 锚点保护关键骨架不被删，
`not-grep` 锚点禁止危险/退化写法。此前 CodeStable 本地没有校验器，
contracts 只是声明；本测试让它们真正生效。

关键：只扫 **body**（剥掉 frontmatter），否则 `not-grep` 会命中 frontmatter
里 contract 声明行自身，造成假阳性。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"
# 工具 skill（authoring/eval，不随插件交付）也纳入 contracts 护栏
LOCAL_SKILLS = ROOT / ".claude/skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# 刚经 build-cs-skill 重构、已声明 contracts 的主入口。删除其 contracts 应是
# 有意识的动作——此清单防止护栏被静默移除。
CORE_SKILLS_WITH_CONTRACTS = {
    "cs", "cs-feat", "cs-epic", "cs-issue", "cs-refactor", "cs-docs", "cs-goal",
    "cs-code-review", "cs-audit", "cs-domain", "cs-req",
}


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """返回 (frontmatter, body)。无 frontmatter 时 frontmatter 为 None。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), match.group(2)


def _skills_with_contracts() -> list[Path]:
    found: list[Path] = []
    for root in (SKILLS, LOCAL_SKILLS):
        for path in sorted(root.glob("*/SKILL.md")):
            frontmatter, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
            if frontmatter and "contracts:" in frontmatter:
                found.append(path)
    return found


SKILLS_WITH_CONTRACTS = _skills_with_contracts()


@pytest.mark.parametrize(
    "skill_md", SKILLS_WITH_CONTRACTS, ids=lambda p: p.parent.name
)
def test_frontmatter_contracts_hold_against_body(skill_md: Path) -> None:
    frontmatter, body = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    meta = yaml.safe_load(frontmatter)
    contracts = meta.get("contracts") or []

    failures: list[str] = []
    for entry in contracts:
        if not isinstance(entry, dict) or (
            "grep" not in entry and "not-grep" not in entry
        ):
            failures.append(f"contract 缺 grep/not-grep: {entry!r}")
            continue
        # literal 子串匹配；只针对 body，不含 frontmatter 声明本身。
        if "grep" in entry and entry["grep"] not in body:
            failures.append(f"grep 锚点缺失: {entry['grep']!r}")
        if "not-grep" in entry and entry["not-grep"] in body:
            failures.append(f"not-grep 锚点命中: {entry['not-grep']!r}")

    assert not failures, (
        f"{skill_md.parent.name} contract 违反:\n  " + "\n  ".join(failures)
    )


def test_core_skills_declare_contracts() -> None:
    """cs-feat / cs-epic 必须保留 contracts，防止护栏被静默删除。"""
    declared = {p.parent.name for p in SKILLS_WITH_CONTRACTS}
    missing = CORE_SKILLS_WITH_CONTRACTS - declared
    assert not missing, f"这些主入口应声明 contracts 却未声明: {sorted(missing)}"


def test_not_grep_ignores_frontmatter_declaration() -> None:
    """回归护栏：校验器必须扫 body 而非全文件。

    cs-feat 的 frontmatter 含 `- not-grep: "git push"` 声明行；若校验器错误
    地扫全文件，会命中该行而误报。此测试锁死"只扫 body"的语义。
    """
    text = (SKILLS / "cs-feat" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    assert frontmatter is not None
    assert 'not-grep: "git push"' in frontmatter  # 声明确实在 frontmatter
    assert "git push" not in body  # 但 body 干净——not-grep 应通过


def test_full_protocol_workflow_skills_keep_failure_and_output_contracts() -> None:
    for skill in ("cs-feat", "cs-epic"):
        body = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "## Failure Behavior" in body, skill
        assert "## Output Contract" in body, skill


def test_feat_and_epic_specs_match_goal_runtime_vocabulary() -> None:
    feat = (SKILLS / "cs-feat/SKILL.md").read_text(encoding="utf-8")
    epic = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")

    assert "designReviewStatus" in feat
    assert "goalRunState" in feat
    assert "reviewStatus     :" not in feat
    assert "hasGoalPackage" not in feat
    assert re.search(r"GoalReadyToDispatch\s+-> DispatchGoalDriver", feat)
    assert re.search(r"GoalComplete\s+-> Completed", feat)
    assert re.search(r"GoalHandoffBlocked reason\s+-> GoalHandoff", feat)

    assert "roadmapReviewStatus" in epic
    assert "goalRunState" in epic
    assert "hasGoalPackage" not in epic
    assert re.search(r"GoalReadyToDispatch\s+-> DispatchGoalDriver", epic)
    assert re.search(r"GoalComplete\s+-> Completed", epic)
    assert re.search(r"GoalHandoffBlocked reason\s+-> GoalHandoff", epic)

    build = (LOCAL_SKILLS / "build-cs-skill/SKILL.md").read_text(encoding="utf-8")
    assert "Runtime Alignment Gate" in build

    feat_goal = (SKILLS / "cs-feat/references/goal/protocol.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")
    epic_runtime = (SKILLS / "cs-epic/references/goal/support/protocol.md").read_text(encoding="utf-8")
    assert "handoff_reason" in feat_goal and "handoff_next" in feat_goal
    assert "终态" in feat_goal
    assert "handoff_reason" in epic_goal and "handoff_next" in epic_goal
    assert "status: complete" in epic_runtime and "status: handoff" in epic_runtime


def _routing_fixture_states(experiment: str) -> dict[str, dict[str, object]]:
    fixtures = ROOT / "experiments" / experiment / "fixtures/routing"
    result: dict[str, dict[str, object]] = {}
    for path in sorted(fixtures.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        result[payload["id"]] = payload
    return result


def test_goal_routing_fixtures_use_current_state_schema() -> None:
    feat = _routing_fixture_states("cs-feat-routing-001")
    epic = _routing_fixture_states("cs-epic-routing-001")
    deprecated = {"reviewStatus", "hasGoalPackage", "codeStatus", "qaStatus", "acceptanceStatus"}

    for payload in [*feat.values(), *epic.values()]:
        state = payload["task"].get("state", {})
        assert deprecated.isdisjoint(state), payload["id"]
        assert "终态优先" not in json.dumps(state, ensure_ascii=False), payload["id"]

    assert feat["rt-f10"]["expect"]["result_type"] == "DispatchGoalDriver"
    assert feat["rt-f11"]["expect"]["result_type"] == "ReportDriver"
    assert feat["rt-f12"]["expect"]["result_type"] == "GoalHandoff"
    assert feat["rt-f13"]["expect"]["result_type"] == "NeedsHuman"
    assert feat["rt-f14"]["expect"]["result_type"] == "HumanCheckpoint"

    assert epic["rt-p09"]["expect"]["result_type"] == "DispatchGoalDriver"
    assert epic["rt-p11"]["expect"]["result_type"] == "ReportDriver"
    assert epic["rt-p12"]["expect"]["result_type"] == "Completed"
    assert epic["rt-p13"]["expect"]["result_type"] == "GoalHandoff"
    assert epic["rt-p14"]["expect"]["result_type"] == "NeedsHuman"


def test_cs_router_fixtures_cover_modes_conflicts_and_recovery() -> None:
    fixtures = _routing_fixture_states("cs-routing-001")
    assert set(fixtures) == {f"rt-c{i:02d}" for i in range(1, 18)}

    assert fixtures["rt-c01"]["expect"]["result_type"] == "RoutedTo"
    assert fixtures["rt-c01"]["expect"]["target"] == "cs-issue"
    assert fixtures["rt-c02"]["expect"]["result_type"] == "Completed"
    assert fixtures["rt-c03"]["expect"]["result_type"] == "Completed"
    assert fixtures["rt-c04"]["expect"]["result_type"] == "HumanCheckpoint"

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

    # result type 的禁止分支由精确 outcome 断言完成，不能误用只检查 target 的字段。
    for fixture_id in ("rt-c02", "rt-c03", "rt-c04", "rt-c13", "rt-c15"):
        assert "must_not_target" not in fixtures[fixture_id]["expect"]
