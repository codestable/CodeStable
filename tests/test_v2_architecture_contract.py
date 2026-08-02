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
    for field in ("item_progression", "milestone_commit", "remote_publish"):
        assert field in adr5_text
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
