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
    "cs-feat": "[--stage design|design-review|impl|qa|accept] [--mode fastforward] <feature>",
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
