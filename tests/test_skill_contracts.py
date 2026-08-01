"""CodeStable skills 的直接语义守卫与 routing fixture 回归。"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"
# 工具 skill（authoring/eval，不随插件交付）也必须使用标准 frontmatter。
LOCAL_SKILLS = ROOT / ".claude/skills"

THIN_SKILL_SAFETY_INVARIANTS = {
    "cs": ("同轮直转", "只推荐入口", "不写任何文件"),
    "cs-review": (
        "只读",
        "叶子执行器",
        "禁止创建、委派或唤醒任何子 agent",
        "不得再次调用 `cs-review`",
        "不保存复审轮次",
        "blocking 未解决",
    ),
    "cs-code-review": (
        "兼容别名",
        "canonical entry `cs-review`",
        "不得读取 sibling skill 文件",
    ),
    "cs-epic": (
        "拆解方案必须经用户确认",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
        "不代替用户做整体验收",
    ),
    "cs-feat": (
        "不得代替用户确认设计",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
        "与声明相称的可核验证据",
    ),
    "cs-issue": (
        "能明确变红的验证",
        "变红的验证必须变绿",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
    ),
    "cs-keep": ("没有可追溯证据不写", "先合并"),
    "cs-onboard": ("存量文件一律不动", "不复制"),
    "cs-refactor": (
        "行为等价",
        "先有能自证等价的验证",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
    ),
}

THIN_SKILL_FORBIDDEN_TEXT = {
    "cs": ("L0-L4",),
    "cs-review": (
        "git push",
        "read all references",
        "用独立 subagent reviewer",
        "派发 reviewer 时",
        "探测全部已配置的审查 agent/model",
        "累计最多 3 轮",
    ),
    "cs-code-review": ("按 `cs-review` 的 SKILL.md 执行",),
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

    review_openai = yaml.safe_load(
        (SKILLS / "cs-review/agents/openai.yaml").read_text(encoding="utf-8")
    )
    review_frontmatter, _ = _read_skill(SKILLS / "cs-review/SKILL.md")
    review_prompt = review_openai["interface"]["default_prompt"]
    assert str(review_frontmatter["description"]).startswith("只读审查叶子执行器")
    assert "$cs-review" in review_prompt
    assert "不创建任何子 agent" in review_prompt
    assert "独立" not in review_openai["interface"]["short_description"]
    assert "独立" not in review_prompt
    assert "派发独立 subagent reviewer" not in review_prompt


def test_review_delegation_discovers_subagent_management_then_selects() -> None:
    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "当前主流程创建 reviewer 前" in caller, skill_name
        assert "当前会话可调用的 subagent 创建与管理能力" in caller, skill_name
        assert "项目上下文有显式创建方式/model 约束时先遵守" in caller, skill_name
        assert "达到审查质量基线后" in caller, skill_name
        assert "优先选择与实现者异构的 agent" in caller, skill_name
        assert "受管理的结构化委派能力" in caller, skill_name
        assert "宿主 subagent" in caller, skill_name
        assert "本机有界 agent CLI 回退" in caller, skill_name
        assert "不得只扫 PATH" in caller, skill_name
        assert "显式指定最强稳定 `model`" in caller, skill_name
        assert "禁止依赖默认模型" in caller, skill_name
        assert "最终创建方式、agent/model 与回退原因写入 task packet" in caller, skill_name
        assert "通道" not in caller, skill_name
        anchors = (
            "当前主流程创建 reviewer 前",
            "当前会话可调用的 subagent 创建与管理能力",
            "项目上下文有显式创建方式/model 约束时先遵守",
            "达到审查质量基线后",
            "优先选择与实现者异构的 agent",
            "受管理的结构化委派能力",
            "宿主 subagent",
            "本机有界 agent CLI 回退",
            "最终创建方式、agent/model 与回退原因写入 task packet",
        )
        positions = [caller.index(anchor) for anchor in anchors]
        assert positions == sorted(positions), skill_name


def test_review_delegation_keeps_a_healthy_run_bound() -> None:
    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "reviewer 创建后绑定该运行" in caller, skill_name
        assert "状态健康时等待终态报告" in caller, skill_name
        assert "`Awaiting` 携带可查询的同一 run identity" in caller, skill_name
        assert "后来发现更优创建方式" in caller, skill_name
        assert "取消、重复创建或并行补发" in caller, skill_name
        assert "能力不满足或目标失效" in caller, skill_name


def test_shipped_skills_do_not_bind_review_backend_products() -> None:
    forbidden = (
        "cs-agent-mcp",
        "cs_agent",
        "paseo",
        "claude",
        "codex",
        "anthropic",
        "openai",
        "gpt-",
    )
    paths = [path for path in sorted(SKILLS.rglob("*")) if path.is_file()]
    assert paths
    # Host registration filenames are packaging surfaces, not runtime backend selection.
    allowed_product_named_paths = {Path("cs-review/agents/openai.yaml")}
    product_named_paths = {
        path.relative_to(SKILLS)
        for path in paths
        if any(name in path.relative_to(SKILLS).as_posix().lower() for name in forbidden)
    }
    assert product_named_paths == allowed_product_named_paths
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for product_name in forbidden:
            assert product_name not in text, f"{path}: bound to {product_name!r}"


def test_review_snapshots_and_milestone_commits_are_not_conflated() -> None:
    _, review = _read_skill(SKILLS / "cs-review/SKILL.md")
    assert "冻结一个明确的审查目标" in review
    assert "审查目标标识" in review
    assert "reviewer 返回前不得移动该目标" in review
    assert "diff review 优先 staged diff" in review
    assert "design review 冻结对应文档版本" in review
    assert "audit 冻结 commit + 范围标识" in review

    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "diff review 优先 staged diff" in caller, skill_name
        assert "design review 冻结对应文档版本" in caller, skill_name
        assert "audit 冻结 commit + 范围标识" in caller, skill_name
        assert "目标标识写入 task packet" in caller, skill_name
        assert "重新冻结审查目标" in caller, skill_name
        assert "有 blocking 或未被用户明确接受的 important 时不提交当前候选" in caller, skill_name
        assert "正式里程碑 commit" in caller, skill_name
        assert "WIP/checkpoint commit" in caller, skill_name
        assert "不代表 review 通过" in caller, skill_name

    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "每次只推进一个已确认子项" in epic
    assert "不把多个子项堆进同一 diff" in epic
    assert "未获 commit 授权" in epic


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
    assert "discover subagent creation and management capabilities callable in the current session" in build
    assert "Reviewer creation methods prefer" in build
    assert "Do not substitute a `PATH` executable scan for capability discovery" in build
    assert "A healthy running delegation stays bound" in build
    assert "idle without a return payload and no recoverable run identity" in " ".join(
        build.split()
    )
    assert "subagent 创建与管理能力契约" in spec
    assert "健康运行的 delegation" in gates
    assert "无可恢复 run identity" in gates
    assert "能力不匹配" in gates
    assert "target 失效" in gates
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
    fixtures = (build_root / "references/cs-skill-fixture-patterns.md").read_text(
        encoding="utf-8"
    )
    normalized_build = " ".join(build.split())
    assert "data DelegationRole = Orchestrator | LeafExecutor" in build
    assert "A `LeafExecutor` must not dispatch another agent" in build
    assert "idle without a return payload" in normalized_build
    assert "The calling orchestrator owns integration" in normalized_build
    assert "outermost orchestrator" not in build
    assert "`LeafExecutor`" in spec
    assert "不得创建、委派、唤醒或跟进子 agent" in spec
    assert "调用该 `LeafExecutor` 的 `Orchestrator`" in spec
    assert "最外层 `Orchestrator`" not in spec
    assert "idle/silence without return payload" in gates
    assert "calling `Orchestrator`" in gates
    assert "最外层 agent" not in gates
    assert "review-leaf-does-not-delegate" in fixtures
    assert "spawn_subagent" in fixtures
    assert "wake_subagent" in fixtures
    assert "follow_up_child" in fixtures
    assert "invoke_cs_code_review" in fixtures
    assert "return_idle_without_report" in fixtures
    assert "review-prefers-managed-subagent-creation" in fixtures
    assert "review-cli-is-bounded-fallback" in fixtures
    assert "healthy-review-run-stays-bound" in fixtures
    assert fixtures.count("step: selectReviewCreationMethod") >= 2
    assert fixtures.count("step: monitorReviewRun") >= 2
    assert "path_only_discovery" in fixtures
    assert "selected_creation_method" in fixtures
    assert "selected_channel" not in fixtures
    assert "cancel_reviewer" in fixtures
    assert "spawn_duplicate_reviewer" in fixtures
    assert "当前 v2 活动 skill 不因历史 goal driver" not in fixtures
    assert "read `.codestable/attention.md` just to author" not in build
