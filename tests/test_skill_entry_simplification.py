from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"

COMPATIBILITY_ENTRIES = {
    "cs-feat-design": ("cs-feat", "requested_stage", "design"),
    "cs-feat-design-review": ("cs-feat", "requested_stage", "design-review"),
    "cs-feat-impl": ("cs-feat", "requested_stage", "implementation"),
    "cs-feat-qa": ("cs-feat", "requested_stage", "qa"),
    "cs-feat-accept": ("cs-feat", "requested_stage", "acceptance"),
    "cs-feat-ff": ("cs-feat", "requested_mode", "fastforward"),
    "cs-issue-report": ("cs-issue", "requested_stage", "report"),
    "cs-issue-analyze": ("cs-issue", "requested_stage", "analyze"),
    "cs-issue-fix": ("cs-issue", "requested_stage", "fix"),
    "cs-refactor-ff": ("cs-refactor", "requested_mode", "fastforward"),
    "cs-doc-tutorial": ("cs-docs", "requested_mode", "tutorial"),
    "cs-doc-api": ("cs-docs", "requested_mode", "api"),
    "cs-roadmap": ("cs-epic", "requested_stage", "planning"),
    "cs-roadmap-review": ("cs-epic", "requested_stage", "review"),
    "cs-roadmap-impl-goal": ("cs-epic", "requested_stage", "goal-package"),
}

MAIN_REFERENCE_PATHS = [
    "cs-feat/references/design/protocol.md",
    "cs-feat/references/design-review/protocol.md",
    "cs-feat/references/implementation/protocol.md",
    "cs-feat/references/qa/protocol.md",
    "cs-feat/references/acceptance/protocol.md",
    "cs-feat/references/fastforward/protocol.md",
    "cs-feat/references/goal/protocol.md",
    "cs-issue/references/report/protocol.md",
    "cs-issue/references/analyze/protocol.md",
    "cs-issue/references/fix/protocol.md",
    "cs-refactor/references/standard/protocol.md",
    "cs-refactor/references/fastforward/protocol.md",
    "cs-docs/references/tutorial/protocol.md",
    "cs-docs/references/api/protocol.md",
    "cs-epic/references/planning/protocol.md",
    "cs-epic/references/review/protocol.md",
    "cs-epic/references/goal/protocol.md",
    "cs-code-review/references/independent-review/protocol.md",
]

REFACTOR_LIBRARY_PATHS = [
    "cs-refactor/references/library/methods.md",
    "cs-refactor/references/library/methods-l4.md",
    "cs-refactor/references/library/methods-architecture.md",
    "cs-refactor/references/library/refusal-routing.md",
    "cs-refactor/references/library/scan-checklist-format.md",
]

REFERENCE_MIGRATION_MARKERS = [
    "不是独立 skill 入口",
    "SKILL.md 只保留",
    "按 `SKILL.md` 所在目录",
    "同包 `reference.md`",
    "## 启动必读",
]

LEGACY_STAGE_SKILL_NAMES = [
    "cs-feat-design",
    "cs-feat-design-review",
    "cs-feat-impl",
    "cs-feat-qa",
    "cs-feat-accept",
    "cs-feat-ff",
    "cs-issue-report",
    "cs-issue-analyze",
    "cs-issue-fix",
    "cs-doc-tutorial",
    "cs-doc-api",
    "cs-roadmap",
    "cs-roadmap-review",
    "cs-roadmap-impl-goal",
    "cs-refactor-ff",
]

USER_ROUTING_GUIDANCE_PATHS = [
    "cs-brainstorm/SKILL.md",
    "cs-brainstorm/reference.md",
    "cs-req/SKILL.md",
]

LEGACY_ROUTING_PHRASES = [
    "`cs-roadmap`",
    "cs-roadmap",
    "`cs-feat-design`",
    "`cs-feat-impl`",
    "`cs-feat-qa`",
    "`cs-feat-accept`",
    "`cs-doc-tutorial`",
    "`cs-doc-api`",
    "`cs-issue-report`",
    "`cs-issue-analyze`",
    "`cs-issue-fix`",
    "`cs-refactor-ff`",
]


def load_codestable_common():
    module_path = SKILLS / "cs-onboard/tools/codestable_common.py"
    spec = importlib.util.spec_from_file_location("codestable_common", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_skill_markdown_files_stay_under_line_limit() -> None:
    oversized = []
    for path in SKILLS.rglob("*.md"):
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 300:
            oversized.append((path.relative_to(ROOT).as_posix(), line_count))

    assert oversized == []


def test_codestable_skill_markdown_has_no_default_worktree_contract_residue() -> None:
    forbidden = [
        "worktree",
        "work tree",
        "worktree-conventions",
        "worktree-gate",
        "branch-guard",
        "branch-guard-hooks",
        "codestable-ai-branch-guard",
        "codestable-finish-worktree",
        "codestable-worktree-inbox",
        "validate-implementation-review",
        "linked execution",
        "linked worktree",
    ]
    findings: list[tuple[str, str]] = []
    for path in SKILLS.rglob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        for term in forbidden:
            if term in text:
                findings.append((path.relative_to(ROOT).as_posix(), term))

    assert findings == []


def test_global_tool_sources_do_not_advertise_repo_local_tool_entrypoints() -> None:
    forbidden = [
        "python .codestable/tools/",
        "python3 .codestable/tools/",
        "python codestable/tools/",
        "python3 codestable/tools/",
    ]
    findings: list[tuple[str, str]] = []
    for path in (SKILLS / "cs-onboard/tools").glob("*"):
        if path.suffix not in {".py", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                findings.append((path.relative_to(ROOT).as_posix(), term))

    assert findings == []


def test_compatibility_entries_delegate_to_main_protocols() -> None:
    for skill, (main, key, value) in COMPATIBILITY_ENTRIES.items():
        path = SKILLS / skill / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        frontmatter = frontmatter_of(text)

        assert "description: Deprecated 兼容入口" in frontmatter, skill
        assert "新请求不要主动选择" in frontmatter, skill
        assert "兼容入口" in text
        assert (SKILLS / main / "SKILL.md").is_file(), main
        assert f"按已安装 skill 名称加载 `{main}`" in text
        assert "../" not in text
        assert f"{key}: {value}" in text
        assert "不维护独立流程规则" in text
        assert len(text.splitlines()) <= 40


MAIN_ENTRY_SKILLS = [
    "cs",
    "cs-onboard",
    "cs-feat",
    "cs-issue",
    "cs-refactor",
    "cs-docs",
    "cs-epic",
    "cs-feedback",
    "cs-code-review",
    "cs-docs-neat",
]

MAIN_ENTRY_ARGUMENT_HINTS = {
    "cs": "[request]",
    "cs-onboard": "[--mode refresh-runtime]",
    "cs-feat": "[--stage design|design-review|impl|qa|accept|goal-package] [--mode fastforward] <feature>",
    "cs-issue": "[--stage report|analyze|fix] <issue>",
    "cs-refactor": "[--stage scan|design|apply] [--mode standard|fastforward] <target>",
    "cs-docs": "[--mode tutorial|api] <topic>",
    "cs-epic": "[--stage planning|review|goal-package] <epic>",
    "cs-feedback": "[--since-days N] [--session current|<id-or-path>] [--github] <feedback>",
    "cs-code-review": "[--range <git-range>] [scope]",
    "cs-docs-neat": "[scope]",
}


def frontmatter_of(text: str) -> str:
    return text.split("---", 2)[1]


def test_main_entries_declare_argument_hint_and_intent_fallback() -> None:
    for skill in MAIN_ENTRY_SKILLS:
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = frontmatter_of(text)

        assert f"argument-hint: \"{MAIN_ENTRY_ARGUMENT_HINTS[skill]}\"" in frontmatter, skill
        assert "$ARGUMENTS" in text, skill
        # 宿主不替换参数时必须优雅降级，不能把字面 $ARGUMENTS 当诉求。
        assert "字面 `$ARGUMENTS`" in text, skill
        assert "无参数默认行为" in text, skill


def test_main_entry_argument_hints_use_flags_for_control_intents() -> None:
    flag_entries = {
        "cs-feat": ["--stage", "--mode"],
        "cs-issue": ["--stage"],
        "cs-refactor": ["--stage", "--mode"],
        "cs-docs": ["--mode"],
        "cs-epic": ["--stage"],
        "cs-code-review": ["--range"],
    }

    for skill, flags in flag_entries.items():
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = frontmatter_of(text)
        for flag in flags:
            assert flag in frontmatter, skill
        assert "首个 token 命中" not in text, skill


def test_skill_catalog_documents_no_argument_default() -> None:
    zh_text = (ROOT / "SKILL_CATALOG.md").read_text(encoding="utf-8")
    en_text = (ROOT / "SKILL_CATALOG.en.md").read_text(encoding="utf-8")

    assert "不传参数时按仓库事实和用户原话恢复或路由" in zh_text
    assert "no-argument calls recover or route" in en_text


def test_router_docs_project_direct_dispatch_in_both_languages() -> None:
    zh_phrase = "行动请求同轮直转，咨询请求只给建议"
    zh_paths = (
        ROOT / "README.md",
        ROOT / "WORKFLOW.md",
        ROOT / "SKILL_CATALOG.md",
        SKILLS / "cs-onboard/references/system-overview.md",
    )
    for path in zh_paths:
        text = path.read_text(encoding="utf-8")
        assert zh_phrase in text, path
        assert "只分诊到主入口" not in text, path

    en_phrase = "Action requests dispatch to the target skill in the current run; advice requests only recommend."
    en_paths = (ROOT / "README.en.md", ROOT / "WORKFLOW.en.md", ROOT / "SKILL_CATALOG.en.md")
    for path in en_paths:
        text = path.read_text(encoding="utf-8")
        assert en_phrase in text, path
        assert "Lightweight triage to the right main entry" not in text, path

    assert "告诉你这次该走哪个" not in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "tells you which `cs-xxx` to run" not in (ROOT / "README.en.md").read_text(encoding="utf-8")


def test_onboard_runtime_refresh_is_explicit_and_repeatable() -> None:
    onboard = (SKILLS / "cs-onboard/SKILL.md").read_text(encoding="utf-8")
    conventions = (SKILLS / "cs-onboard/references/execution-conventions.md").read_text(encoding="utf-8")
    tools_doc = (SKILLS / "cs-onboard/references/tools.md").read_text(encoding="utf-8")
    shared_conventions = (SKILLS / "cs-onboard/references/shared-conventions.md").read_text(encoding="utf-8")
    feat = (SKILLS / "cs-feat/SKILL.md").read_text(encoding="utf-8")
    feat_design = (SKILLS / "cs-feat/references/design/protocol.md").read_text(encoding="utf-8")
    epic = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")

    assert "--mode refresh-runtime" in onboard
    assert "可重复执行" in onboard
    assert "只想刷新 runtime、不审计或迁移文档时，显式传 `--mode refresh-runtime`" in onboard
    assert "不重新审计 / 迁移文档" in onboard
    assert "不移动用户文件" in onboard
    assert "不改 `attention.md` 的实质内容" in onboard
    for managed_path in [".codestable/gates/", ".codestable/reference/"]:
        assert managed_path in onboard
    assert "旧项目已有 `.codestable/tools/` 只作兼容副本" in onboard
    assert "不删除或覆盖旧 `.codestable/tools/`" in onboard
    assert ".codestable/runtime-manifest.json" in onboard
    assert "codestable-runtime-sync.py" in onboard

    assert "Runtime 资产恢复" in conventions
    assert "runtime capability" in conventions
    assert ".codestable/runtime-manifest.json" in conventions
    assert "用当前插件包里的\n`cs-onboard/tools/codestable-runtime-sync.py` 自动同步" in conventions
    assert "--check --json" in conventions
    assert "去掉 `--check`" in conventions
    assert "不要用项目\n`.codestable/tools/` 里的旧副本做版本判定或新版工具入口" in conventions
    assert "skill_tool_paths" in conventions
    assert "managed-paths-dirty" in conventions
    assert "不自动覆盖" in conventions
    assert ".codestable/reference/agent-conventions.md" in conventions
    assert ".codestable/reference/worktree-conventions.md" not in conventions
    assert "worktree-gate" not in conventions
    assert "<cs-onboard skill 目录>/tools/" in tools_doc
    assert "不作为新版技能入口" in tools_doc
    assert "version-mismatch" in tools_doc
    assert "tooling.runtime.capabilities" in tools_doc
    assert "Python 工具脚本从已安装的 `cs-onboard` skill 包运行，不再复制到每个 repo" in readme
    assert "Python tool scripts run from the installed `cs-onboard` skill package instead of being copied into each repo" in readme_en
    assert "每个已接入项目中显式执行 `/cs-onboard --mode refresh-runtime`" in readme
    assert "下一次 CodeStable preflight" in readme
    assert "in every onboarded project" in readme_en
    assert "the next CodeStable preflight" in readme_en

    default_runtime_text = "\n".join([onboard, conventions, tools_doc, feat, feat_design, epic, epic_goal])
    assert "codestable-worktree-gate.py" not in default_runtime_text
    assert "branch-guard-hooks.md" not in default_runtime_text
    for text in [shared_conventions, readme, readme_en]:
        assert "tools/                 跨工作流共享脚本" not in text
        assert "shared workflow scripts released by onboard" not in text
        assert "tools、hooks" not in text
        assert "tools, hooks" not in text

    for text in [feat, feat_design, epic, epic_goal]:
        assert "runtime capability" not in text
        assert "Runtime 资产恢复" not in text


def test_feat_and_epic_document_goal_driver_dispatch() -> None:
    feat = (SKILLS / "cs-feat/SKILL.md").read_text(encoding="utf-8")
    epic = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")
    router = (SKILLS / "cs/SKILL.md").read_text(encoding="utf-8")
    agent_conventions = (SKILLS / "cs-onboard/references/agent-conventions.md").read_text(encoding="utf-8")
    feat_goal = (SKILLS / "cs-feat/references/goal/protocol.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")

    assert "--stage goal-package" in feat
    assert "references/goal/protocol.md" in feat
    assert "goal 包、impl" in router
    assert "可见 driver 长程执行" in router
    assert "Goal Driver 派发" in agent_conventions
    assert "可见 Task agent" in agent_conventions
    assert "派发失败" in feat_goal
    assert "派发失败" in epic_goal
    assert "fenced `/goal`" in feat_goal
    assert "fenced `/goal`" in epic_goal


def test_goal_mode_overrides_stage_user_waits() -> None:
    impl = (SKILLS / "cs-feat/references/implementation/protocol.md").read_text(encoding="utf-8")
    impl_reference = (SKILLS / "cs-feat/references/implementation/support/reference.md").read_text(encoding="utf-8")
    accept = (SKILLS / "cs-feat/references/acceptance/protocol.md").read_text(encoding="utf-8")
    agent_conventions = (SKILLS / "cs-onboard/references/agent-conventions.md").read_text(encoding="utf-8")
    feat_goal = (SKILLS / "cs-feat/references/goal/protocol.md").read_text(encoding="utf-8")
    epic_goal_support = (SKILLS / "cs-epic/references/goal/support/protocol.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")

    # implementation 的"停等用户 review"必须有 goal 模式例外，否则 driver 长程会被打断。
    assert "Goal 模式例外" in impl
    assert "Goal 模式汇报后不停等用户" in impl_reference
    assert "按 goal 协议更新 `goal-state.yaml`" in impl_reference
    # acceptance 的 goal 例外要同时覆盖单 feature goal 和 epic goal。
    assert "`cs-feat` / `cs-epic` 的 goal 协议" in accept
    # 原生子 agent 当 driver 前必须确认它还能启动独立 reviewer；不能就回退打印 /goal。
    assert "只有同时满足两条才可用" in agent_conventions
    assert "不能靠 driver 自审" in agent_conventions
    # 自动 driver 也必须以 literal /goal 启动，不能退化成普通 implementation prompt。
    assert "literal `/goal` 指令作为 driver 初始任务" in agent_conventions
    assert "普通“执行/实现这个 feature”" in agent_conventions
    assert "driver 初始 prompt 必须是上面生成的同一条 literal `/goal` 指令" in feat_goal
    assert "literal `/goal` 指令作为 driver 初始任务启动 driver" in epic_goal
    # 单 feature goal 包必须带接管条款和 handoff 标记，与 epic goal 包对齐。
    assert "合法状态机" in feat_goal
    assert "| review | fixing |" in feat_goal
    assert "| handoff | blocked |" in feat_goal
    assert "Goal 模式接管" in feat_goal
    assert "CS_FEATURE_GOAL_HANDOFF" in feat_goal
    assert "goal 模式下改为写入报告" in epic_goal_support
    assert "CS_ROADMAP_GOAL_HANDOFF" in epic_goal_support
    assert "与单 feature goal 不同" in epic_goal
    # README 不应暗示 issue/refactor 有标准 QA checkpoint。
    assert "review、blocking 或用户确认 checkpoint" in readme
    assert "review, blocking, or user-confirmation checkpoints" in readme_en
    # 重入不重复派发：派发成功要写回 driver 标识，重入按派发规则判定。
    assert "driver_kind" in agent_conventions
    assert "不重复派发" in agent_conventions
    assert "driver_kind: none" in feat_goal
    assert "driver_kind: none" in epic_goal


def test_feature_implementation_requires_tdd_for_behavior_steps() -> None:
    impl = (SKILLS / "cs-feat/references/implementation/protocol.md").read_text(encoding="utf-8")
    tdd = (SKILLS / "cs-feat/references/implementation/support/tdd.md").read_text(encoding="utf-8")
    impl_reference = (SKILLS / "cs-feat/references/implementation/support/reference.md").read_text(encoding="utf-8")
    feat_goal = (SKILLS / "cs-feat/references/goal/protocol.md").read_text(encoding="utf-8")

    assert "代码行为变化默认先 RED 测试、再 GREEN 最小实现" in impl
    assert "行为改动默认 TDD" in impl
    assert "不能先批量实现再补测试" in impl
    assert "TDD exception" in impl
    assert "需求迭代边界" in impl

    assert "默认必须使用 TDD micro-loop" in tdd
    assert "不能先把实现写完再补测试" in tdd
    assert "改变 public behavior、接口、错误语义、feature 范围或公开契约" in tdd
    assert "review-fix / qa-fix" in tdd
    assert "RED：{测试名 / 命令 / 失败摘要，确认失败原因是目标行为未实现}" in tdd

    assert "### TDD 证据" in impl_reference
    assert "RED / GREEN / VERIFY evidence" in impl_reference

    assert "implementation TDD policy" in feat_goal
    assert "Goal driver 不得绕过 implementation 的 TDD policy" in feat_goal
    assert "必须留下 RED/GREEN/VERIFY evidence" in feat_goal


def test_epic_defers_child_design_approval_to_batch_checkpoint() -> None:
    epic_skill = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")
    feat_skill = (SKILLS / "cs-feat/SKILL.md").read_text(encoding="utf-8")
    feat_design = (SKILLS / "cs-feat/references/design/protocol.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")
    tools_doc = (SKILLS / "cs-onboard/references/tools.md").read_text(encoding="utf-8")

    # 子 design 逐项推进时保持 draft，用户确认统一发生在批量 checkpoint，
    # 避免 agent 按 cs-feat 普通模式逐个停等用户。
    assert "design 保持 `draft`，不逐个让用户确认" in epic_skill
    assert "统一确认所有 design" in epic_skill
    assert "epic_child_batch: true" in epic_skill
    assert "仍有子 feature 未完成 design-review" in epic_skill
    assert "不要在第一个或任一单独子 feature design-review passed 后停下来" in epic_skill
    assert "Child design batch loop" in epic_skill
    assert "codestable-workflow-next.py epic" in epic_skill
    assert "完成某一个 child 的 design + design-review `passed` 只是内部进度" in epic_skill
    assert "不得 final answer" in epic_skill
    assert "本轮必须继续调用 `cs-feat`" in epic_skill
    assert "final_answer_allowed: false" in epic_skill
    assert "child design batch loop 只在全部 child design-review passed" in epic_skill
    assert "不执行单 feature 的人工整体 review checkpoint" in feat_skill
    assert "不在这里停，回到 `cs-epic` 继续下一个子 feature" in feat_skill
    assert "不得用 final answer 要用户确认单个 child" in feat_skill
    assert "codestable-workflow-next.py feature" in feat_skill
    assert "`epic_child_batch: true` 时不要停用户" in feat_design
    assert "codestable-workflow-next.py feature --epic-child-batch" in feat_design
    # batch loop 纪律唯一权威在 cs-epic SKILL.md 的「Child design batch loop」；goal protocol 只保留 hook 引用
    assert "取下一个 planned / in-progress 且缺 design、checklist" in epic_skill
    assert "不得要求用户确认该 child" in epic_skill
    assert "codestable-workflow-next.py epic" in epic_goal
    assert "`next_action`、`must_continue` 和 `final_answer_allowed`" in tools_doc


CANONICAL_PREFLIGHT = (
    "动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；"
    "不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。"
)

PREFLIGHT_CANONICAL_SKILLS = [
    "cs",
    "cs-feat",
    "cs-issue",
    "cs-refactor",
    "cs-docs",
    "cs-epic",
    "cs-feedback",
    "cs-code-review",
    "cs-docs-neat",
    "cs-audit",
    "cs-req",
    "cs-goal",
]

# 这三个技能把 preflight 融进自己的启动节奏（语义等价变体）。
PREFLIGHT_VARIANT_SKILLS = ["cs-brainstorm", "cs-domain", "cs-keep"]


def test_public_skills_run_codestable_preflight() -> None:
    for skill in PREFLIGHT_CANONICAL_SKILLS:
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert CANONICAL_PREFLIGHT in text, skill

    for skill in PREFLIGHT_VARIANT_SKILLS:
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "CodeStable preflight" in text, skill
        assert ".codestable/attention.md" in text, skill

    # cs-note 是约定认可的唯一例外：attention.md 缺失时可先建骨架再写入。
    note = (SKILLS / "cs-note/SKILL.md").read_text(encoding="utf-8")
    assert "只有 attention.md 缺失时" in note
    assert "不要用 `AGENTS.md` / `CLAUDE.md` 等外部入口代替它" in note

    # 兼容入口保持薄壳，不自带 preflight；preflight 由主入口协议执行。
    for skill in COMPATIBILITY_ENTRIES:
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "preflight" not in text.lower(), skill


def test_compatibility_entries_do_not_declare_argument_hint() -> None:
    for skill in COMPATIBILITY_ENTRIES:
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")

        assert "argument-hint" not in text, skill
        assert "$ARGUMENTS" not in text, skill


def test_main_entry_references_exist() -> None:
    for rel_path in MAIN_REFERENCE_PATHS:
        assert (SKILLS / rel_path).is_file(), rel_path


def test_protocol_references_are_not_shadow_skills() -> None:
    for rel_path in MAIN_REFERENCE_PATHS:
        path = SKILLS / rel_path
        text = path.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:5])

        assert text.startswith("# "), rel_path
        assert not text.startswith("---"), rel_path
        assert "\nname:" not in head, rel_path
        assert "\ndescription:" not in head, rel_path
        assert "## 启动必读" not in text, rel_path


def test_references_do_not_keep_migration_markers() -> None:
    offenders = []
    for path in (SKILLS).rglob("references/**/*.md"):
        text = path.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:5])
        if re.search(r"(?m)^name:", head):
            offenders.append((path.relative_to(ROOT).as_posix(), "frontmatter name"))
        for marker in REFERENCE_MIGRATION_MARKERS:
            if marker in text:
                offenders.append((path.relative_to(ROOT).as_posix(), marker))

    assert offenders == []


def test_references_prefer_main_entries_over_legacy_stage_skills() -> None:
    offenders = []
    for path in (SKILLS).rglob("references/**/*.md"):
        text = path.read_text(encoding="utf-8")
        for legacy_name in LEGACY_STAGE_SKILL_NAMES:
            if legacy_name in text:
                offenders.append((path.relative_to(ROOT).as_posix(), legacy_name))

    assert offenders == []


def test_user_routing_guidance_prefers_main_entries() -> None:
    offenders = []
    for rel_path in USER_ROUTING_GUIDANCE_PATHS:
        path = SKILLS / rel_path
        text = path.read_text(encoding="utf-8")
        for phrase in LEGACY_ROUTING_PHRASES:
            if phrase in text:
                offenders.append((rel_path, phrase))

    assert offenders == []


def test_code_review_ad_hoc_git_range_uses_range_diff() -> None:
    text = (SKILLS / "cs-code-review/SKILL.md").read_text(encoding="utf-8")

    assert "--range <git-range>" in text
    assert "ad-hoc 参数如果含 `--range`" in text
    assert "git diff {range}" in text
    assert "ad-hoc range 审查允许工作区干净" in text


def test_no_directory_contains_both_reference_spellings() -> None:
    conflicts = []
    for directory in [SKILLS, *[path for path in SKILLS.rglob("*") if path.is_dir()]]:
        if not (directory / "reference").is_dir() or not (directory / "references").is_dir():
            continue
        conflicts.append(directory.relative_to(ROOT).as_posix())

    assert conflicts == []


def test_skill_package_reference_directories_follow_agent_skills_convention() -> None:
    invalid = []
    for directory in [path for path in SKILLS.rglob("*") if path.is_dir()]:
        rel_parts = directory.relative_to(SKILLS).parts
        if directory.name == "reference":
            invalid.append(directory.relative_to(ROOT).as_posix())
        if directory.name == "references" and (len(rel_parts) != 2 or rel_parts[1] != "references"):
            invalid.append(directory.relative_to(ROOT).as_posix())

    assert invalid == []


def test_main_entry_reference_pointers_resolve_to_files() -> None:
    main_entries = [
        "cs-feat",
        "cs-issue",
        "cs-refactor",
        "cs-docs",
        "cs-epic",
        "cs-code-review",
        "cs-docs-neat",
    ]
    missing = []

    for skill in main_entries:
        skill_dir = SKILLS / skill
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for match in re.finditer(r"`(references/[^`]+?\.md)`", text):
            rel_path = match.group(1)
            if "*" in rel_path:
                if not list(skill_dir.glob(rel_path)):
                    missing.append(f"{skill}/{rel_path}")
            elif not (skill_dir / rel_path).is_file():
                missing.append(f"{skill}/{rel_path}")

    assert missing == []


def test_refactor_library_references_are_migrated() -> None:
    assert not (SKILLS / "cs-refactor/reference").exists()
    for rel_path in REFACTOR_LIBRARY_PATHS:
        assert (SKILLS / rel_path).is_file(), rel_path


def test_new_main_entries_are_registered() -> None:
    common = load_codestable_common()

    assert "cs-docs" in common.KNOWN_SKILL_DIRS
    assert "cs-epic" in common.KNOWN_SKILL_DIRS
    assert "cs-feedback" in common.KNOWN_SKILL_DIRS
    for skill in COMPATIBILITY_ENTRIES:
        assert skill in common.KNOWN_SKILL_DIRS


def test_feedback_skill_is_registered_and_uses_progressive_disclosure() -> None:
    feedback = (SKILLS / "cs-feedback/SKILL.md").read_text(encoding="utf-8")
    template = (SKILLS / "cs-feedback/references/report-template.md").read_text(encoding="utf-8")
    collector = SKILLS / "cs-feedback/scripts/collect_feedback_context.py"
    reporter = SKILLS / "cs-feedback/scripts/report_feedback_issue.py"
    router = (SKILLS / "cs/SKILL.md").read_text(encoding="utf-8")
    catalog = (ROOT / "SKILL_CATALOG.md").read_text(encoding="utf-8")
    catalog_en = (ROOT / "SKILL_CATALOG.en.md").read_text(encoding="utf-8")
    overview = (SKILLS / "cs-onboard/references/system-overview.md").read_text(encoding="utf-8")

    assert "CodeStable 使用反馈闭环" in feedback
    assert "--session current" in feedback
    assert "best-effort" in feedback
    assert "ambiguity.candidates" in feedback
    assert "Ask User（缺口驱动）" in feedback
    assert "不要固定三问" in feedback
    assert "即使用户传 `--github`，也必须先让用户确认 preview" in feedback
    assert "public-issue-context.json" in feedback
    assert "禁止公开" in feedback
    assert "local_private_evidence" in template
    assert "Public evidence fields" in template
    assert "完整 transcript" in template
    assert collector.is_file()
    assert reporter.is_file()
    assert "CodeStable skill 跑偏" in router
    assert "cs-feedback" in catalog
    assert "cs-feedback" in catalog_en
    assert ".codestable/feedback/" in overview or "cs-feedback" in overview
