"""CodeStable skills 的直接语义守卫与 routing fixture 回归。"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"
# 工具 skill（authoring/eval，不随插件交付）也必须使用标准 frontmatter。
LOCAL_SKILLS = ROOT / ".claude/skills"

THIN_SKILL_SAFETY_INVARIANTS = {
    "cs": ("只解释和推荐", "不启动流程", "不写文件"),
    "cs-code-review": ("只读", "独立 subagent reviewer", "blocking 未解决"),
    "cs-epic": ("拆解方案必须经用户确认", "不代替用户做整体验收"),
    "cs-feat": ("不得代替用户确认设计", "与声明相称的可核验证据"),
    "cs-issue": ("能明确变红的验证", "变红的验证必须变绿"),
    "cs-keep": ("没有可追溯证据不写", "先合并"),
    "cs-onboard": ("存量文件一律不动", "不复制"),
    "cs-refactor": ("行为等价", "先有能自证等价的验证"),
}

THIN_SKILL_FORBIDDEN_TEXT = {
    "cs": ("L0-L4",),
    "cs-code-review": ("git push", "read all references"),
    "cs-epic": ("ConfirmGoalCommitAuthorization", "git push", "read all references"),
    "cs-feat": ("git push", "read all references"),
    "cs-issue": ("git push", "read all references"),
    "cs-refactor": ("git push", "read all references"),
}


def _read_skill(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, frontmatter, body = text.split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def test_active_skills_do_not_use_legacy_frontmatter_contracts() -> None:
    for root in (SKILLS, LOCAL_SKILLS):
        for path in sorted(root.glob("*/SKILL.md")):
            frontmatter, _ = _read_skill(path)
            assert "contracts" not in frontmatter, path


def test_thin_skills_keep_explicit_safety_invariants() -> None:
    active_skills = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert set(THIN_SKILL_SAFETY_INVARIANTS) == active_skills

    for skill_name, invariants in THIN_SKILL_SAFETY_INVARIANTS.items():
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for invariant in invariants:
            assert invariant in body, f"{skill_name}: missing {invariant!r}"

    for skill_name, forbidden_texts in THIN_SKILL_FORBIDDEN_TEXT.items():
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for forbidden in forbidden_texts:
            assert forbidden not in body, f"{skill_name}: forbidden {forbidden!r}"


def test_build_cs_skill_requires_semantic_and_host_safe_validation() -> None:
    build_root = LOCAL_SKILLS / "build-cs-skill"
    build = (build_root / "SKILL.md").read_text(encoding="utf-8")
    openai = yaml.safe_load(
        (build_root / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    spec = (build_root / "references/cs-skill-spec-standard.md").read_text(
        encoding="utf-8"
    )
    gates = (build_root / "references/cs-skill-quality-gates.md").read_text(
        encoding="utf-8"
    )

    for path in build_root.rglob("*.md"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 300, path
    assert "$build-cs-skill" in openai["interface"]["default_prompt"]
    assert "thin harness" in build
    assert "thick context" in build
    assert "data SkillShape" in build
    assert "ThinOperator" in build
    assert "ContextualWorkflow" in build
    assert "ToolBackedWorkflow" in build
    assert "data RulePlacement" in build
    assert "placeRule :: Rule -> RulePlacement" in build
    assert "not (independentSkillNeeded kind source) = NoActiveSkill" in build
    assert "CompatibilityShim -> ShimSkill" in build
    assert "ContextPlan" in build
    assert "buildContextPlan" in build
    assert "Haskell Contract Gate" in build
    assert "CompatibilityShim -> ShimRoute" in build
    assert "lifecycleDriven source -> LifecycleProtocol" in build
    assert "algorithmic source -> AlgorithmProtocol" in build
    placement = build[build.index("placeRule r"):build.index("buildContextPlan ::")]
    placement_guards = (
        "mechanizable r",
        "nonMechanizableSafety r",
        "projectSpecific r",
        "stageSpecific r",
        "everyInvocationNeeds r",
        "otherwise",
    )
    positions = [placement.index(guard) for guard in placement_guards]
    assert positions == sorted(positions)
    assert "data RulePlacement" in spec
    assert "NoActiveSkill" in spec
    assert "ShimSkill" in spec
    assert "ReferenceSkill" in spec
    assert "placeRule :: Rule ->" not in spec
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
    assert "read `.codestable/attention.md` just to author" not in build
