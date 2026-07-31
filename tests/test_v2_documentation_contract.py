"""公开文档与 authoring 规范必须描述 v2，而不是已退役的 v1 runtime。"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

V2_SKILLS = {
    "cs",
    "cs-review",
    "cs-epic",
    "cs-feat",
    "cs-issue",
    "cs-keep",
    "cs-onboard",
    "cs-refactor",
}

# 发布契约显式交付的唯一兼容别名（v1 沿用名 -> v2 新名）；不算独立能力。
SHIM_SKILLS = {"cs-code-review"}

PUBLIC_DOCS = (
    "README.md",
    "README.en.md",
    "WORKFLOW.md",
    "WORKFLOW.en.md",
    "SKILL_CATALOG.md",
    "SKILL_CATALOG.en.md",
)

AUTHORING_DOCS = (
    ".claude/skills/build-cs-skill/SKILL.md",
    ".claude/skills/build-cs-skill/references/cs-skill-spec-standard.md",
    ".claude/skills/build-cs-skill/references/cs-skill-quality-gates.md",
    ".claude/skills/build-cs-skill/references/cs-skill-fixture-patterns.md",
    ".claude/skills/eval-cs-skill/SKILL.md",
    ".claude/skills/eval-cs-skill/references/author/protocol.md",
    ".claude/skills/eval-cs-skill/references/eval/protocol.md",
    ".claude/skills/eval-cs-skill/references/release/protocol.md",
)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _skill_table(text: str, start: str, end: str) -> set[str]:
    section = text.split(start, 1)[1].split(end, 1)[0]
    return set(re.findall(r"^\|[^|]+\|\s*`(cs(?:-[a-z0-9]+)*)`\s*\|", section, re.M))


def _skills_cli_upgrade_block(text: str) -> str:
    start = text.index("npx skills@latest remove")
    return text[start:text.index("```", start)]


def _upgrade_remove_tokens(text: str) -> list[str]:
    block = _skills_cli_upgrade_block(text).replace("\\\n", " ")
    command = next(
        line.strip()
        for line in block.splitlines()
        if line.strip().startswith("npx skills@latest remove")
    )
    return shlex.split(command)


def test_public_docs_present_the_exact_v2_skill_family() -> None:
    zh_catalog = _read("SKILL_CATALOG.md")
    en_catalog = _read("SKILL_CATALOG.en.md")

    assert _skill_table(zh_catalog, "## 当前入口", "## v1.0.4") == V2_SKILLS
    assert _skill_table(en_catalog, "## Current Entries", "## Retired") == V2_SKILLS

    assert "8 个 skill" in _read("README.md")
    assert "8 skills" in _read("README.en.md")
    assert "cs--skills-8" in _read("README.md")
    assert "cs--skills-8" in _read("README.en.md")
    assert "已退役，不随 v2 交付" in zh_catalog
    assert "retired and not shipped in v2" in en_catalog


def test_skills_cli_major_upgrade_removes_exactly_the_retired_v1_names() -> None:
    legacy = json.loads(
        _read("tests/fixtures/skills-cli/legacy-cs-inventory.json")
    )
    retired = set(legacy["skills"]) - V2_SKILLS - SHIM_SKILLS

    assert len(retired) == 24
    zh = _read("README.md")
    en = _read("README.en.md")

    for readme in (zh, en):
        block = _skills_cli_upgrade_block(readme)
        tokens = _upgrade_remove_tokens(readme)
        assert block.index("skills@latest remove") < block.index("skills@latest add")
        assert tokens[:3] == ["npx", "skills@latest", "remove"]
        assert tokens[-2:] == ["-g", "-y"]
        assert len(tokens[3:-2]) == len(retired)
        assert set(tokens[3:-2]) == retired

        assert "--all" not in tokens
        assert "--skill=*" not in tokens
        assert "-s=*" not in tokens
        for option in ("--skill", "-s"):
            if option in tokens:
                assert tokens[tokens.index(option) + 1] != "*"

    assert "按名称删除，不校验安装来源" in zh
    assert "name-based and does not verify the installation source" in en


def test_active_docs_do_not_publish_v1_runtime_as_current_contract() -> None:
    active = "\n".join(_read(path) for path in PUBLIC_DOCS + AUTHORING_DOCS)

    for stale in (
        "refresh-runtime",
        "cs-onboard/tools",
        ".codestable/reference/",
        "长期兼容入口",
        "Long-Term Compatibility Entries",
        "long-term compatibility entries",
    ):
        assert stale not in active


def test_eval_autonomy_example_targets_a_runnable_experiment() -> None:
    autonomy = _read(
        ".claude/skills/eval-cs-skill/references/autonomy/protocol.md"
    )
    assert "experiments/cs-code-review-001" in autonomy
    assert "experiments/cs-audit-001" not in autonomy


def test_authoring_docs_assign_context_and_helpers_to_real_owners() -> None:
    build = _read(".claude/skills/build-cs-skill/SKILL.md")
    fixtures = _read(
        ".claude/skills/build-cs-skill/references/cs-skill-fixture-patterns.md"
    )
    release = _read(".claude/skills/eval-cs-skill/references/release/protocol.md")

    assert "belong to the owning skill's" in build
    assert "`references/` and `scripts/`" in build
    assert "do not require sibling skill files" in build
    assert "retired v1 CodeStable name also selects `NoActiveSkill`" in build
    assert "retired-v1-entry-remains-absent" in fixtures
    assert "tests/test_skills_cli_distribution.py" in release
