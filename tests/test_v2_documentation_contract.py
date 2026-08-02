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

CURRENT_CONTRACT_DOCS = (
    "README.md",
    "README.en.md",
    "WORKFLOW.md",
    "WORKFLOW.en.md",
    "SKILL_CATALOG.md",
    "SKILL_CATALOG.en.md",
)

SUPPORTING_PUBLIC_DOCS = (
    "UPGRADE.md",
    "UPGRADE.en.md",
    "ROADMAP.md",
    "ROADMAP.en.md",
    "docs/why-codestable.md",
    "docs/why-codestable.en.md",
)

PUBLIC_DOCS = CURRENT_CONTRACT_DOCS + SUPPORTING_PUBLIC_DOCS

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


def _contains_contract(text: str, anchor: str) -> bool:
    return "".join(anchor.split()) in "".join(text.split())


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


def _ordinary_prose_paragraphs(text: str) -> list[str]:
    without_code = re.sub(r"```.*?```", "", text, flags=re.S)
    paragraphs: list[str] = []
    excluded_prefixes = ("#", "|", "<", ">", "- ", "* ")
    for block in re.split(r"\n\s*\n", without_code):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or any(line.startswith(excluded_prefixes) for line in lines):
            continue
        paragraphs.append(" ".join(lines))
    return paragraphs


def test_public_docs_present_the_exact_v2_skill_family() -> None:
    zh_catalog = _read("SKILL_CATALOG.md")
    en_catalog = _read("SKILL_CATALOG.en.md")

    assert _skill_table(zh_catalog, "## 当前入口", "## v1.0.4") == V2_SKILLS
    assert _skill_table(en_catalog, "## Current Entries", "## Retired") == V2_SKILLS

    zh_readme = _read("README.md")
    en_readme = _read("README.en.md")
    assert "8 个 skill" in zh_readme
    assert "8 skills" in en_readme
    assert "cs--skills-8" in zh_readme
    assert "cs--skills-8" in en_readme
    for skill in V2_SKILLS:
        assert f"`{skill}`" in zh_readme
        assert f"`{skill}`" in en_readme
    assert "已退役，不随 v2 交付" in zh_catalog
    assert "retired and not shipped in v2" in en_catalog


def test_skills_cli_major_upgrade_removes_exactly_the_retired_v1_names() -> None:
    legacy = json.loads(
        _read("tests/fixtures/skills-cli/legacy-cs-inventory.json")
    )
    retired = set(legacy["skills"]) - V2_SKILLS - SHIM_SKILLS

    assert len(retired) == 24
    zh = _read("UPGRADE.md")
    en = _read("UPGRADE.en.md")

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


def test_readme_is_a_compact_first_evaluator_entry() -> None:
    zh = _read("README.md")
    en = _read("README.en.md")
    headings = {
        "README.md": (
            "## 30 秒运行模型",
            "## 5 分钟开始",
            "## 三个核心原则",
            "## 项目记忆",
            "## 适用边界",
            "## 深入文档",
        ),
        "README.en.md": (
            "## 30-Second Model",
            "## Start in 5 Minutes",
            "## Three Principles",
            "## Project Memory",
            "## Fit",
            "## Go Deeper",
        ),
    }
    for filename, ordered_headings in headings.items():
        text = _read(filename)
        positions = [text.index(heading) for heading in ordered_headings]
        assert positions == sorted(positions)
        assert len(text.splitlines()) <= 300
        assert all(len(paragraph) <= 240 for paragraph in _ordinary_prose_paragraphs(text))
        assert "asset/PromotionalImage.png" not in text

    for anchor in (
        "轻量 skill 契约",
        "不编排 Agent 团队",
        "不为项目建立第二套文档系统",
        "明确行动默认同轮直转",
        "未收敛讨论不承诺跨会话恢复",
        "直接执行 / 当前会话讨论 / 给出建议",
        "thin harness, thick context",
        "证据先于结论",
        "一个事实，一个 canonical owner",
        "永久 Epic 文档",
        "临时 work 游标",
        "叶子执行器",
    ):
        assert anchor in zh
    for anchor in (
        "lightweight skill contracts",
        "does not orchestrate agent teams",
        "does not create a second documentation system",
        "Explicit actions dispatch in the same turn by default",
        "Unresolved discussion is not recoverable across sessions",
        "execute directly / discuss in this session / advise",
        "thin harness, thick context",
        "Evidence before conclusions",
        "One fact, one canonical owner",
        "permanent Epic document",
        "temporary work cursor",
        "leaf executor",
    ):
        assert anchor in en

    for text in (zh, en):
        for anchor in (
            "codex plugin marketplace add codestable/CodeStable",
            "/plugin marketplace add codestable/CodeStable",
            "npx skills@latest add codestable/CodeStable/plugins/codestable",
            "/cs-onboard",
            "/cs",
            "attention.md",
            "lessons/",
            "work/",
        ):
            assert anchor in text
        assert "codex plugin marketplace upgrade codestable" not in text
        assert "npx skills@latest remove" not in text

    assert "[升级指南](./UPGRADE.md#从-v104-升级到-v2)" in zh
    assert "精确删除 24 个退役入口" in zh
    assert "[upgrade guide](./UPGRADE.en.md#upgrade-from-v104-to-v2)" in en
    assert "remove the 24 retired entries" in en

    assert (
        "作者 [@liuzhengdong](https://github.com/liuzhengdong)、"
        "[@dafang](https://github.com/dafang)、Codex、Claude"
    ) in zh
    assert (
        "Authors [@liuzhengdong](https://github.com/liuzhengdong), "
        "[@dafang](https://github.com/dafang), Codex, and Claude"
    ) in en
    assert "liuzhengdongfortest" not in zh
    assert "liuzhengdongfortest" not in en


def test_readme_links_to_canonical_deep_docs() -> None:
    links = {
        "README.md": (
            ("./WORKFLOW.md", "WORKFLOW.md"),
            ("./SKILL_CATALOG.md", "SKILL_CATALOG.md"),
            ("./UPGRADE.md", "UPGRADE.md"),
            ("./docs/why-codestable.md", "docs/why-codestable.md"),
            ("./ROADMAP.md", "ROADMAP.md"),
            ("./CHANGELOG.md", "CHANGELOG.md"),
        ),
        "README.en.md": (
            ("./WORKFLOW.en.md", "WORKFLOW.en.md"),
            ("./SKILL_CATALOG.en.md", "SKILL_CATALOG.en.md"),
            ("./UPGRADE.en.md", "UPGRADE.en.md"),
            ("./docs/why-codestable.en.md", "docs/why-codestable.en.md"),
            ("./ROADMAP.en.md", "ROADMAP.en.md"),
            ("./CHANGELOG.md", "CHANGELOG.md"),
        ),
    }
    for readme, targets in links.items():
        text = _read(readme)
        for link, target in targets:
            assert link in text
            assert (ROOT / target).is_file()


def test_public_document_local_links_resolve() -> None:
    for filename in PUBLIC_DOCS:
        document = ROOT / filename
        for target in re.findall(r"!?\[[^]]*\]\(([^)]+)\)", _read(filename)):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            relative = target.split("#", 1)[0]
            if relative:
                assert (document.parent / relative).resolve().exists(), (
                    f"{filename} links to missing local target {target}"
                )


def test_upgrade_docs_keep_legacy_assets_without_owning_runtime_policy() -> None:
    zh = _read("UPGRADE.md")
    en = _read("UPGRADE.en.md")

    assert "升级不会删除项目里的 v1 历史资产" in zh
    assert "检索与写入政策以 [WORKFLOW.md](./WORKFLOW.md#v1-升级边界) 为准" in zh
    assert "does not delete historical v1 project assets" in en
    assert "retrieval and write policy remains owned by [WORKFLOW.en.md](./WORKFLOW.en.md#v1-upgrade-boundary)" in en
    assert ".codestable/reference/" not in zh
    assert ".codestable/reference/" not in en


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


def test_cs_session_discussion_and_handoff_contract_is_bilingual() -> None:
    zh_workflow = " ".join(_read("WORKFLOW.md").split())
    en_workflow = " ".join(_read("WORKFLOW.en.md").split())

    for anchor in (
        "明确行动默认优先同轮直转",
        "用户显式要求先讨论",
        "讨论只存在于当前会话",
        "不创建 discussion work 游标",
        "未收敛讨论不跨会话恢复",
        "已有执行授权时同轮移交",
        "不再询问“是否继续”",
        "handoff 不扩大授权",
        "原始问答、未决讨论和候选分支不落盘",
        "三个已确认出口之外",
    ):
        assert anchor in zh_workflow

    for anchor in (
        "Explicit action dispatches in the same turn by default",
        "the user explicitly asks to discuss first",
        "Discussion exists only in the current session",
        "does not create a discussion work cursor",
        "Unresolved discussion is not recoverable across sessions",
        "existing execution authorization",
        "must not ask whether to continue",
        "The handoff does not expand authorization",
        "Raw questions, answers, unresolved discussion, and candidate branches are not persisted",
        "When no canonical home exists, ask the owner to choose one",
        "Outside the three confirmed handoff targets",
    ):
        assert anchor in en_workflow

    zh_readme = _read("README.md")
    en_readme = _read("README.en.md")
    zh_catalog = _read("SKILL_CATALOG.md")
    en_catalog = _read("SKILL_CATALOG.en.md")
    assert "先讨论的请求在当前会话收敛后同轮移交" in zh_readme
    assert "先讨论的请求在当前会话收敛后同轮移交" in zh_catalog
    assert "Requests to discuss first converge in the current session and hand off in the same turn" in en_readme
    assert "Requests to discuss first converge in the current session and hand off in the same turn" in en_catalog
    assert "稳定资产由 owning skill 按 canonical 归宿毕业" in zh_catalog
    assert "stable assets graduate through the owning skill into their canonical homes" in en_catalog


def test_workflow_owns_epic_and_legacy_knowledge_contracts() -> None:
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
        "串行约束，不是每个子项的人工 gate",
        "不得询问“是否继续下一项”",
        "不得把它作为终态返回",
        "`item_progression`",
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
        "serialization constraint, not a per-item owner gate",
        "must not ask whether to continue to the next item",
        "return that completion as terminal",
        "`item_progression`",
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
    assert "默认连续策略" not in zh_workflow
    assert "永久 Epic 文档" in zh_catalog
    assert "permanent Epic doc" in en_catalog
    assert "永久 Epic 文档" in zh_readme
    assert "临时 work 游标" in zh_readme
    assert "permanent Epic document" in en_readme
    assert "temporary work cursor" in en_readme
    assert "串行连续推进" in zh_catalog
    assert "serially and continuously" in en_catalog


def test_project_learning_lifecycle_is_bilingual_and_low_interruption() -> None:
    zh_workflow = _read("WORKFLOW.md")
    en_workflow = _read("WORKFLOW.en.md")
    for anchor in (
        "任务内静默观察",
        "经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}",
        "一次有界、最低成本的定向核实",
        "明确排除一个具体且合理的错误路径",
        "本次通过的验收证据",
        "observed / validated / retired",
        "普通任务最多展示一条",
        "Epic 子项不新增暂停",
        "机械 guard 优先",
        "新 lesson 仍需显式授权",
        "不保存 transcript",
    ):
        assert _contains_contract(zh_workflow, anchor)
    for anchor in (
        "observes silently during the task",
        "lesson hit: {path} ({status}); check: {fact}; impact: {plan_or_check}",
        "one bounded, lowest-cost targeted check",
        "explicitly rules out a concrete, plausible wrong path",
        "the task's passing acceptance evidence",
        "observed / validated / retired",
        "at most one candidate",
        "Epic items add no pause",
        "mechanical guards first",
        "New lessons still require explicit authorization",
        "does not save transcripts",
    ):
        assert _contains_contract(en_workflow, anchor)

    public_pairs = (
        ("README.md", "README.en.md", "边做边识别晶化时刻", "recognizes crystallization moments while working"),
        ("SKILL_CATALOG.md", "SKILL_CATALOG.en.md", "observed / validated / retired", "observed / validated / retired"),
        ("docs/why-codestable.md", "docs/why-codestable.en.md", "经验不是活动日志", "Experience is not an activity log"),
        (
            "docs/why-codestable.md",
            "docs/why-codestable.en.md",
            "排除一个具体且合理的错误路径",
            "rules out a concrete, plausible wrong path",
        ),
    )
    for zh_path, en_path, zh_anchor, en_anchor in public_pairs:
        assert _contains_contract(_read(zh_path), zh_anchor)
        assert _contains_contract(_read(en_path), en_anchor)

    assert not _contains_contract(zh_workflow, "把可复用经验写成 lesson")
    assert not _contains_contract(en_workflow, "reusable experience into lessons")
    assert "| `cs-keep` | 管理有证据的项目事实、lesson 生命周期与 canonical 归宿 |" in _read("README.md")
    assert (
        "| `cs-keep` | Manage evidence-backed project facts, lesson lifecycle, and canonical homes |"
        in _read("README.en.md")
    )
    assert _contains_contract(_read("docs/why-codestable.md"), "尚未被更强 owner 承接的经验暂存于 lessons")
    assert _contains_contract(
        _read("docs/why-codestable.en.md"),
        "experience without a stronger owner is staged in lessons",
    )
