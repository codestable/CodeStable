"""CodeStable v2 的安装单元、项目骨架与历史兼容边界。"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_v2_runtime_ownership_supersedes_v1_distribution() -> None:
    adr1 = ROOT / "docs/adr/001-skill-global-tool-runtime.md"
    adr2 = ROOT / "docs/adr/002-codestable-does-not-own-worktree-strategy.md"
    adr4 = ROOT / "docs/adr/004-project-knowledge-not-runtime-distribution.md"
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert _frontmatter(adr1)["status"] == "Superseded"
    assert adr4.is_file()
    assert _frontmatter(adr4)["status"] == "Accepted"
    adr4_text = adr4.read_text(encoding="utf-8")
    assert "supersedes: [\"001\"]" in adr4_text
    assert "只含 canonical route 与 shim 边界" in adr4_text
    assert "只转发不含规则" not in adr4_text
    assert "runtime refresh" not in adr2.read_text(encoding="utf-8")

    for entry_file in (agents, claude):
        assert "plugins/codestable/skills/cs-onboard/references/" not in entry_file
        assert "<cs-onboard skill 目录>/tools/" not in entry_file
        assert "codestable-runtime-sync.py --check --json" not in entry_file
        assert "owning skill" in entry_file
        assert "attention.md`、`lessons/`、`work/" in entry_file


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
