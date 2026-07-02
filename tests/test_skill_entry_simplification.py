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


def test_compatibility_entries_delegate_to_main_protocols() -> None:
    for skill, (main, key, value) in COMPATIBILITY_ENTRIES.items():
        path = SKILLS / skill / "SKILL.md"
        text = path.read_text(encoding="utf-8")

        assert "兼容入口" in text
        assert (SKILLS / main / "SKILL.md").is_file(), main
        assert f"按已安装 skill 名称加载 `{main}`" in text
        assert "../" not in text
        assert f"{key}: {value}" in text
        assert "不维护独立流程规则" in text
        assert len(text.splitlines()) <= 40


MAIN_ENTRY_SKILLS = [
    "cs",
    "cs-feat",
    "cs-issue",
    "cs-refactor",
    "cs-docs",
    "cs-epic",
    "cs-code-review",
    "cs-docs-neat",
]

MAIN_ENTRY_ARGUMENT_HINTS = {
    "cs": "[request]",
    "cs-feat": "[--stage design|design-review|impl|qa|accept|goal-package] [--mode fastforward] <feature>",
    "cs-issue": "[--stage report|analyze|fix] <issue>",
    "cs-refactor": "[--stage scan|design|apply] [--mode standard|fastforward] <target>",
    "cs-docs": "[--mode tutorial|api] <topic>",
    "cs-epic": "[--stage planning|review|goal-package] <epic>",
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


def test_feat_and_epic_document_goal_driver_dispatch() -> None:
    feat = (SKILLS / "cs-feat/SKILL.md").read_text(encoding="utf-8")
    epic = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")
    router = (SKILLS / "cs/SKILL.md").read_text(encoding="utf-8")
    conventions = (SKILLS / "cs-onboard/references/execution-conventions.md").read_text(encoding="utf-8")
    feat_goal = (SKILLS / "cs-feat/references/goal/protocol.md").read_text(encoding="utf-8")
    epic_goal = (SKILLS / "cs-epic/references/goal/protocol.md").read_text(encoding="utf-8")

    assert "--stage goal-package" in feat
    assert "references/goal/protocol.md" in feat
    assert "goal 包、impl" in router
    assert "可见 driver 长程执行" in router
    assert "Goal driver" in conventions
    assert "可见 Task agent" in conventions
    assert "派发失败" in feat_goal
    assert "派发失败" in epic_goal
    assert "fenced `/goal`" in feat_goal
    assert "fenced `/goal`" in epic_goal


def test_goal_mode_overrides_stage_user_waits() -> None:
    impl = (SKILLS / "cs-feat/references/implementation/protocol.md").read_text(encoding="utf-8")
    impl_reference = (SKILLS / "cs-feat/references/implementation/support/reference.md").read_text(encoding="utf-8")
    accept = (SKILLS / "cs-feat/references/acceptance/protocol.md").read_text(encoding="utf-8")
    conventions = (SKILLS / "cs-onboard/references/execution-conventions.md").read_text(encoding="utf-8")
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
    assert "只有同时满足下面两条才可用" in conventions
    assert "不能靠 driver 自审" in conventions
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
    assert "driver_kind" in conventions
    assert "不重复派发" in conventions
    assert "driver_kind: none" in feat_goal
    assert "driver_kind: none" in epic_goal


def test_epic_defers_child_design_approval_to_batch_checkpoint() -> None:
    epic_skill = (SKILLS / "cs-epic/SKILL.md").read_text(encoding="utf-8")

    # 子 design 逐项推进时保持 draft，用户确认统一发生在批量 checkpoint，
    # 避免 agent 按 cs-feat 普通模式逐个停等用户。
    assert "design 保持 `draft`，不逐个让用户确认" in epic_skill
    assert "统一确认所有 design" in epic_skill


CANONICAL_PREFLIGHT = (
    "开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；"
    "缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。"
)

PREFLIGHT_CANONICAL_SKILLS = [
    "cs",
    "cs-feat",
    "cs-issue",
    "cs-refactor",
    "cs-docs",
    "cs-epic",
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
    assert "不要回退到外部 AI 入口文件" in note

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
    for skill in COMPATIBILITY_ENTRIES:
        assert skill in common.KNOWN_SKILL_DIRS
