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

# v2 交付 skill 不带 contracts frontmatter（owner 决策：交付物不含自测元数据）。
# 硬门槛锚由本文件直接对 SKILL.md 正文断言，保护等价、交付更薄。
SHIPPED_HARD_GATE_ANCHORS = {
    "cs-feat": ["不得代替用户确认设计", "与声明相称的可核验证据", "写入 `.codestable/work/"],
    "cs-issue": ["能明确变红的验证", "变红的验证必须变绿"],
    "cs-refactor": ["行为等价", "先有能自证等价的验证"],
    "cs-code-review": ["只读", "blocking 未解决", "最多 2 轮"],
    "cs-epic": ["拆解方案必须经用户确认", "不代替用户做整体验收"],
    "cs-keep": ["没有可追溯证据不写", "先合并"],
    "cs-onboard": ["存量文件一律不动", "不复制"],
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


def test_shipped_skills_keep_hard_gate_anchors() -> None:
    """交付 skill 的硬门槛锚：防止演进/汰换时把硬约束静默削掉。

    锚是行为不变量短语，不是措辞快照；改写措辞时同步更新此清单是
    有意识的动作。同时锁定外发禁令：正文不得出现 git push 指令。
    """
    shipped = {p.parent.name for p in SKILLS.glob("*/SKILL.md")}
    assert shipped == set(SHIPPED_HARD_GATE_ANCHORS) | {"cs"}, (
        "交付 skill 清单变化，先更新 SHIPPED_HARD_GATE_ANCHORS"
    )
    for skill, anchors in SHIPPED_HARD_GATE_ANCHORS.items():
        body = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        for anchor in anchors:
            assert anchor in body, f"{skill} 缺硬门槛锚: {anchor!r}"
        assert "git push" not in body, f"{skill} 出现外发指令字样"


def test_shipped_skills_carry_no_contracts_frontmatter() -> None:
    """owner 决策：交付 skill 不带 contracts frontmatter（自测元数据留在仓库测试）。"""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        frontmatter, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        assert frontmatter is None or "contracts:" not in frontmatter, path.parent.name


def test_not_grep_ignores_frontmatter_declaration() -> None:
    """回归护栏：校验器必须扫 body 而非全文件。

    build-cs-skill 的 frontmatter 含 not-grep 声明行；若校验器错误地扫
    全文件，会命中声明行自身而误报。此测试锁死"只扫 body"的语义。
    """
    text = (LOCAL_SKILLS / "build-cs-skill" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    assert frontmatter is not None
    assert "not-grep:" in frontmatter  # 声明确实在 frontmatter
    meta = yaml.safe_load(frontmatter)
    not_greps = [e["not-grep"] for e in meta.get("contracts", []) if "not-grep" in e]
    assert not_greps, "样本 skill 需至少一条 not-grep 声明"
    for phrase in not_greps:
        assert phrase not in body  # body 干净——not-grep 应通过


def test_thin_harness_skills_stay_free_of_v1_state_machines() -> None:
    """v2 契约：交付 skill 不得回退出现 Haskell 状态机或 v1 runtime 词汇。"""
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        body = path.read_text(encoding="utf-8")
        assert "```haskell" not in body, path.parent.name
        assert "restoreFeatureStage" not in body, path.parent.name
        assert "goalRunState" not in body, path.parent.name


def test_build_cs_skill_requires_semantic_and_host_safe_validation() -> None:
    build_root = LOCAL_SKILLS / "build-cs-skill"
    build = (build_root / "SKILL.md").read_text(encoding="utf-8")
    spec = (build_root / "references/cs-skill-spec-standard.md").read_text(
        encoding="utf-8"
    )
    gates = (build_root / "references/cs-skill-quality-gates.md").read_text(
        encoding="utf-8"
    )

    assert "thin harness" in build
    assert "thick context" in build
    assert "data SkillShape" in build
    assert "ThinOperator" in build
    assert "ContextualWorkflow" in build
    assert "ToolBackedWorkflow" in build
    assert "data RulePlacement" in build
    assert "placeRule :: Rule -> RulePlacement" in build
    assert "ContextPlan" in build
    assert "buildContextPlan" in build
    assert "Haskell Contract Gate" in build
    assert "CompatibilityShim -> ShimRoute" in build
    assert "lifecycleDriven source -> LifecycleProtocol" in build
    assert "algorithmic source -> AlgorithmProtocol" in build
    assert "Responsibility Contract" in spec
    assert "Context Contract" in spec
    assert "Collaboration Contract" in spec
    assert "contractDecision :: Input -> State -> Outcome" in spec
    assert "contractDecision _ _ = Blocked InvalidTransition" in spec
    assert "`HumanCheckpoint` only for an actual owner decision" in spec
    assert "`Awaiting` for already-started external work" in spec
    assert "Every `HumanCheckpoint` must have an explicit resume input" in spec
    assert "cross-skill handoff must retain its target and complete context" in spec
    assert "## Haskell Contract Semantics Gate" in gates
    assert "## Thin Harness Gate" in gates
    assert "## Context Plan Gate" in gates
    assert "## Evolution Compression Gate" in gates
    assert "## Regression Ladder" in gates
    assert "## Live Host Safety Gate" in gates
    assert "## Family Audit Coverage Gate" in gates
    assert "compare it with the reviewed/classified set by equality" in gates
    assert "target the canonical main entry without selecting its internal stage/lane" in gates
    assert "process start identity" in gates
    assert "CI or a quiet disposable host" in gates


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


def test_cs_router_fixtures_cover_modes_conflicts_and_recovery() -> None:
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

    # result type 的禁止分支由精确 outcome 断言完成，不能误用只检查 target 的字段。
    for fixture_id in ("rt-c02", "rt-c03", "rt-c04", "rt-c13", "rt-c15"):
        assert "must_not_target" not in fixtures[fixture_id]["expect"]
