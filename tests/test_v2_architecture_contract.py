"""CodeStable v2 的安装单元、项目骨架与历史兼容边界。"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SHIPPED_SKILLS = ROOT / "plugins/codestable/skills"


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_v2_runtime_ownership_supersedes_v1_distribution() -> None:
    adr1 = ROOT / "docs/adr/001-skill-global-tool-runtime.md"
    adr2 = ROOT / "docs/adr/002-codestable-does-not-own-worktree-strategy.md"
    adr4 = ROOT / "docs/adr/004-project-knowledge-not-runtime-distribution.md"
    adr5 = ROOT / "docs/adr/005-project-knowledge-and-epic-lifecycle.md"
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert _frontmatter(adr1)["status"] == "Superseded"
    assert adr4.is_file()
    assert _frontmatter(adr4)["status"] == "Superseded"
    assert _frontmatter(adr4)["superseded-by"] == "005"
    assert adr5.is_file()
    assert _frontmatter(adr5)["status"] == "Accepted"
    adr4_text = adr4.read_text(encoding="utf-8")
    adr5_text = adr5.read_text(encoding="utf-8")
    adr5_flat = " ".join(adr5_text.split())
    adr5_compact = "".join(adr5_text.split())
    assert "supersedes: [\"001\"]" in adr4_text
    assert "supersedes: [\"004\"]" in adr5_text
    assert "八个主 skill" in adr5_text
    assert "否则按需创建 `.codestable/epics/`" in adr5_text
    assert "`cs-onboard` 不预建空目录" in adr5_text
    assert "只读历史知识源" in adr5_text
    assert "不得继续生成、原地改写、批量迁移" in adr5_text
    assert "`.codestable/attention.md` 明确记录其为 canonical" in adr5_text
    assert "不默认创建 `.codestable/requirements/`" in adr5_text
    assert "串行约束，不是每个子项的人工 gate" in adr5_flat
    for anchor in (
        "路线尚不清晰",
        "永久 Epic 文档就是唯一路线文档",
        "文档内路线地图",
        "frontier",
        "`AFK`",
        "`HITL`",
        "不得替 owner 回答",
        "route clear 前不得保留未解决的 `HITL`",
        "agent 不得单方判定其超出范围或失效",
        "prerequisite",
        "仍须另获对应权限或确认",
        "不新增独立 map、issue 或第三套状态",
        "route clear 不是新的 owner gate",
        "起草 proposed 永久 Epic 时同步创建 planning work 游标",
        "不创建重复 Epic",
    ):
        assert "".join(anchor.split()) in adr5_compact
    for field in ("item_progression", "milestone_commit", "remote_publish"):
        assert field in adr5_text
    assert "`item_progression: parallel` 只能搭配 `milestone_commit: authorized`" in adr5_flat
    assert "唯一编排者与唯一游标 writer" in adr5_flat
    assert "并行推进不改变 owner gate 与文档职责" in adr5_flat
    assert "不恢复 `cs-goal` 入口" in adr5_text
    assert "`state.yaml`" in adr5_text
    assert "逐轮 iteration 报告" in adr5_text
    assert "runtime refresh" not in adr2.read_text(encoding="utf-8")

    for entry_file in (agents, claude):
        assert "plugins/codestable/skills/cs-onboard/references/" not in entry_file
        assert "<cs-onboard skill 目录>/tools/" not in entry_file
        assert "codestable-runtime-sync.py --check --json" not in entry_file
        assert "owning skill" in entry_file
        for anchor in ("attention.md", "lessons/", "work/", "epics/"):
            assert anchor in entry_file
        assert "只读" in entry_file
        assert "legacy" in entry_file
        assert "普通子项完成不是 owner gate" in entry_file


def test_active_adrs_do_not_enforce_deleted_v1_tests_or_assets() -> None:
    active_adrs = []
    for path in sorted((ROOT / "docs/adr").glob("*.md")):
        if _frontmatter(path)["status"] == "Accepted":
            active_adrs.append(path.read_text(encoding="utf-8"))
    active = "\n".join(active_adrs)

    for stale in (
        "tests/test_codestable_doctor.py",
        "tests/test_codestable_workflow_next.py",
        "tests/test_skill_entry_simplification.py",
        "tests/test_cs_skill_bootstrap.py",
        "plugins/codestable/skills/cs-feedback/",
        "plugins/codestable/skills/cs-onboard/tools/",
        "plugins/codestable/skills/cs-onboard/references/",
    ):
        assert stale not in active


def test_default_pytest_config_does_not_leak_into_eval_checks() -> None:
    pytest_config = (ROOT / "pytest.ini").read_text(encoding="utf-8")

    assert pytest_config == "[pytest]\ntestpaths = tests\n"
    assert not (ROOT / "conftest.py").exists()


def test_v1_feedback_promoter_is_explicitly_legacy_only() -> None:
    promoter = (
        ROOT
        / ".claude/skills/eval-cs-skill/scripts/promote_feedback_fixture.py"
    ).read_text(encoding="utf-8")
    eval_skill = (ROOT / ".claude/skills/eval-cs-skill/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "LEGACY_ONLY = True" in promoter
    assert "not a CodeStable v2 production-feedback entry" in promoter
    assert "仅用于显式导入冻结的 v1" in eval_skill
    assert "新反馈如何进入 regression 不在当前协议中定义" in eval_skill


def test_project_learning_lifecycle_is_an_accepted_narrow_staging_contract() -> None:
    adr6 = ROOT / "docs/adr/006-project-learning-lifecycle.md"
    epic = ROOT / ".codestable/epics/cs-continuous-learning-lifecycle.md"

    assert adr6.is_file()
    assert epic.is_file()
    assert _frontmatter(adr6)["status"] == "Accepted"
    text = adr6.read_text(encoding="utf-8")
    for anchor in (
        "在任务中静默观察",
        "最多保留 3 条候选",
        "read-repair",
        "一次有界、最低成本的定向核实",
        "具体且合理的错误路径",
        "必须优先机械化",
        "`observed -> validated`",
        "本次通过的验收证据",
        "`observed|validated -> retired`",
        "显式授权",
        "feedback runtime",
        "transcript",
        "全局 lessons",
        "集中 runtime",
        "第九个 skill",
        "不新增逐项暂停或确认",
    ):
        assert anchor in text

    epic_text = epic.read_text(encoding="utf-8")
    for anchor in (
        "一次有界、最低成本的定向核实",
        "明确排除一个具体且合理的错误路径",
        "本次通过的验收证据",
    ):
        assert anchor in epic_text


def test_project_learning_does_not_restore_feedback_or_global_runtime_state() -> None:
    active_skills = {
        path.parent.name for path in SHIPPED_SKILLS.glob("*/SKILL.md")
    }
    assert active_skills == {
        "cs",
        "cs-code-review",
        "cs-epic",
        "cs-feat",
        "cs-issue",
        "cs-keep",
        "cs-onboard",
        "cs-refactor",
        "cs-review",
    }

    for path in (
        SHIPPED_SKILLS / "cs-feedback",
        ROOT / ".codestable/learning",
        ROOT / ".codestable/global-lessons",
        ROOT / ".codestable/state.yaml",
        ROOT / ".codestable/session-state.yaml",
    ):
        assert not path.exists(), path

    runtime_artifacts = {
        path.relative_to(SHIPPED_SKILLS).as_posix().lower()
        for path in SHIPPED_SKILLS.rglob("*")
        if path.is_file()
        and ("transcript" in path.name.lower() or path.name == "state.yaml")
    }
    assert runtime_artifacts == set()


def test_minimum_sufficient_assurance_is_an_accepted_risk_contract() -> None:
    adr7 = ROOT / "docs/adr/007-minimum-sufficient-assurance.md"

    assert adr7.is_file()
    assert _frontmatter(adr7)["status"] == "Accepted"
    text = adr7.read_text(encoding="utf-8")
    flat = " ".join(text.split())

    for anchor in (
        "执行流程 = 最小闭环 + 每个未排除风险所要求的最少保障",
        "一次静默、有界核对",
        "不能排除时先按风险存在处理",
        "不声称每个旧步骤原样保留",
        "有意用可核验证据与独立审查替代无条件预确认",
        "语义风险高于语法规模",
        "风险事实 → 增加的保障",
        "公开契约",
        "信任边界",
        "持久化数据",
        "并发、顺序或一致性语义",
        "不可恢复的代码外副作用",
        "性能回退或性能敏感路径",
        "失败可跨模块传播",
        "独立 review 不是默认步骤",
        "不是无条件跳过安全门槛",
        "连续性需要不是风险门槛",
        "Epic 保留三道 owner gate",
        "固定全流程",
        "行数、文件数或文案/代码类型",
        "伪精确风险分数",
        "Quick / Standard / Goal",
        "不新增 lane、状态机或 runtime helper",
    ):
        assert anchor in flat


def test_shared_language_is_an_accepted_conditional_design_contract() -> None:
    adr8 = ROOT / "docs/adr/008-shared-language-before-design-execution.md"

    assert adr8.is_file()
    assert _frontmatter(adr8)["status"] == "Accepted"
    text = " ".join(adr8.read_text(encoding="utf-8").split())

    for anchor in (
        "可审查不等于 owner 可理解",
        "条件式共享语言",
        "普通改动零新增产物",
        "Feature 局部语义清晰",
        "Epic 概念体系清晰",
        "领域术语与架构角色分开归属",
        "不新增 owner gate",
        "不强制创建 `CONTEXT.md`",
        "不依赖外部 domain-modeling skill",
        "静态测试不冒充 owner 理解或模型行为证据",
        "未选择不阻塞当前交付",
        "`cs-issue` 与 `cs-refactor` 不新增共享语言设计分支",
    ):
        assert anchor in text
