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


def test_review_docs_publish_single_level_agent_orchestration() -> None:
    zh_readme = _read("README.md")
    en_readme = _read("README.en.md")
    zh_workflow = _read("WORKFLOW.md")
    en_workflow = _read("WORKFLOW.en.md")
    en_workflow_compact = " ".join(en_workflow.split())

    assert "叶子执行器" in zh_readme
    assert "leaf executor" in en_readme
    assert "外层主流程创建 reviewer" in zh_workflow
    assert "outer workflow creates the reviewer" in en_workflow
    assert "冻结一个明确的审查目标" in zh_workflow
    assert "当前主流程创建 reviewer 前" in zh_workflow
    assert "当前会话可调用的 subagent 创建与管理能力" in zh_workflow
    assert "本机有界 agent CLI 回退" in zh_workflow
    assert "具体后端与 model 约束属于项目上下文" in zh_workflow
    assert "健康运行中的 reviewer" in zh_workflow
    assert "Awaiting 携带同一可查询 run identity" in zh_workflow
    assert "有 blocking 或未被用户明确接受的 important 时" in zh_workflow
    assert "freeze an explicit review target" in en_workflow_compact
    assert "discovers the subagent creation and management capabilities callable in the current session" in en_workflow_compact
    assert "A bounded local agent CLI is only a fallback" in en_workflow_compact
    assert "Exact backend and model constraints belong to project context" in en_workflow_compact
    assert "When no qualified heterogeneous candidate exists" in en_workflow_compact
    assert "never rely on a default model" in en_workflow_compact
    assert "healthy running reviewer" in en_workflow_compact
    assert "Awaiting carries the same queryable run identity" in en_workflow_compact
    assert "does not consume a review round" in en_workflow_compact
    assert "blocking findings or important findings not explicitly accepted by the user" in en_workflow_compact

    public = "\n".join(_read(path) for path in PUBLIC_DOCS)
    assert "独立 subagent 视角" not in public
    assert "independent subagent perspective" not in public


def test_epic_and_legacy_knowledge_contracts_are_bilingual() -> None:
    zh_workflow = " ".join(_read("WORKFLOW.md").split())
    en_workflow = " ".join(_read("WORKFLOW.en.md").split())

    legacy_dirs = (
        "roadmap/",
        "features/",
        "issues/",
        "refactors/",
        "goals/",
        "compound/",
        "audits/",
        "brainstorms/",
        "feedback/",
    )
    for directory in legacy_dirs:
        assert directory in zh_workflow
        assert directory in en_workflow

    for anchor in (
        "只读历史知识源",
        "owning task skills",
        "按任务关键词覆盖",
        "其他 skill 只检索自身契约明确点名的历史源",
        "不得继续生成",
        "原地改写",
        "批量迁移",
        "永久 Epic 文档",
        "临时执行游标",
        "按需建立 `.codestable/epics/{slug}.md`",
        "`cs-onboard` 不预建 `.codestable/epics/`",
        "Epic 保留三道 owner gate",
        "最新 owner 已批准的验收标准",
        "owner 最终接受",
        "不恢复 `cs-goal` 入口",
    ):
        assert anchor in zh_workflow

    for anchor in (
        "read-only historical knowledge sources",
        "cover all nine by task keyword",
        "Other skills retrieve only historical sources explicitly named by their own contracts",
        "No skill may generate",
        "rewrite in place",
        "bulk-migrate",
        "permanent Epic document",
        "temporary execution cursor",
        "create `.codestable/epics/{slug}.md` on demand",
        "`cs-onboard` does not precreate `.codestable/epics/`",
        "An Epic retains three owner gates",
        "latest owner-approved criteria",
        "owner's final acceptance",
        "Do not restore the `cs-goal` entry",
    ):
        assert anchor in en_workflow

    for workflow in (zh_workflow, en_workflow):
        assert ".codestable/requirements/" in workflow
        assert ".codestable/attention.md" in workflow
        assert "canonical requirement" in workflow

    zh_readme = _read("README.md")
    en_readme = _read("README.en.md")
    zh_catalog = _read("SKILL_CATALOG.md")
    en_catalog = _read("SKILL_CATALOG.en.md")
    assert "九个历史知识目录" in zh_readme
    assert "nine v1 historical knowledge directories" in en_readme
    assert "每个 skill 动手前按任务关键词检索" not in zh_readme
    assert "every skill searches" not in en_readme
    for task_skill in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        assert task_skill in zh_readme
        assert task_skill in en_readme
    assert "永久 Epic 文档" in zh_catalog
    assert "permanent Epic doc" in en_catalog
