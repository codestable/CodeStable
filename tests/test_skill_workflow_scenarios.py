from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"


AFFECTED_SKILLS = {
    "cs",
    "cs-feat",
    "cs-feat-design",
    "cs-feat-design-review",
    "cs-feat-impl",
    "cs-feat-qa",
    "cs-feat-accept",
    "cs-feat-ff",
    "cs-issue",
    "cs-issue-report",
    "cs-issue-analyze",
    "cs-issue-fix",
    "cs-refactor",
    "cs-refactor-ff",
    "cs-docs",
    "cs-doc-tutorial",
    "cs-doc-api",
    "cs-docs-neat",
    "cs-epic",
    "cs-feedback",
    "cs-roadmap",
    "cs-roadmap-review",
    "cs-roadmap-impl-goal",
    "cs-code-review",
    "cs-brainstorm",
    "cs-req",
    "cs-onboard",
}


SCENARIO_COVERAGE = {
    "router": {"cs", "cs-brainstorm", "cs-req", "cs-onboard"},
    "feature-long-range": {
        "cs-feat",
        "cs-feat-design",
        "cs-feat-design-review",
        "cs-feat-impl",
        "cs-feat-qa",
        "cs-feat-accept",
        "cs-feat-ff",
        "cs-code-review",
    },
    "epic-long-range": {
        "cs-epic",
        "cs-roadmap",
        "cs-roadmap-review",
        "cs-roadmap-impl-goal",
        "cs-feat",
        "cs-code-review",
    },
    "issue": {"cs-issue", "cs-issue-report", "cs-issue-analyze", "cs-issue-fix", "cs-code-review"},
    "refactor": {"cs-refactor", "cs-refactor-ff", "cs-code-review"},
    "docs": {"cs-docs", "cs-doc-tutorial", "cs-doc-api", "cs-docs-neat"},
    "feedback": {"cs-feedback"},
    "goal-driver": {"cs-onboard", "cs-feat", "cs-epic"},
}


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


@dataclass(frozen=True)
class Action:
    name: str
    target: str


def skill_text(skill: str, rel_path: str = "SKILL.md") -> str:
    return (SKILLS / skill / rel_path).read_text(encoding="utf-8")


def assert_doc_contains(skill: str, rel_path: str, *phrases: str) -> None:
    text = skill_text(skill, rel_path)
    missing = [phrase for phrase in phrases if phrase not in text]
    assert missing == [], f"{skill}/{rel_path} missing {missing}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_isolated_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "isolated-repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Workflow Test")
    git(repo, "config", "user.email", "workflow-test@example.invalid")
    write(repo / ".codestable/attention.md", "# Attention\n\n- Report language: zh.\n")
    write(repo / ".codestable/reference/execution-conventions.md", skill_text("cs-onboard", "references/execution-conventions.md"))
    write(repo / "src/app.py", "def hello():\n    return 'hello'\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "baseline")
    return repo


def frontmatter(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    result = {}
    for line in block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def top_level_yaml(path: Path) -> dict[str, str]:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def replace_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^status: .+$", f"status: {status}", text, count=1)
    path.write_text(text, encoding="utf-8")


def feature_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/features" / f"2026-07-02-{slug}"


def write_feature_design(repo: Path, slug: str, status: str = "draft", roadmap: str | None = None) -> Path:
    directory = feature_dir(repo, slug)
    roadmap_fields = ""
    if roadmap:
        roadmap_fields = f"roadmap: {roadmap}\nroadmap_item: {slug}\n"
    write(
        directory / f"{slug}-design.md",
        f"---\ndoc_type: feature-design\nfeature: 2026-07-02-{slug}\n{roadmap_fields}status: {status}\n---\n# Design\n",
    )
    write(
        directory / f"{slug}-checklist.yaml",
        f"feature: 2026-07-02-{slug}\nsteps:\n  - id: step-1\n    status: pending\nchecks:\n  - id: check-1\n    status: pending\n",
    )
    return directory


def write_feature_design_review(repo: Path, slug: str, status: str = "passed") -> None:
    directory = feature_dir(repo, slug)
    write(
        directory / f"{slug}-design-review.md",
        f"---\ndoc_type: feature-design-review\nfeature: 2026-07-02-{slug}\nstatus: {status}\n---\n# Design Review\n",
    )


def write_feature_goal_state(repo: Path, slug: str, stage: str, status: str, driver: str = "none") -> None:
    directory = feature_dir(repo, slug)
    driver_id = "paseo-123" if driver != "none" else ""
    write(
        directory / "goal-state.yaml",
        f"feature: {slug}\nstatus: {status}\nbaseline_ref: baseline\nstage: {stage}\ndriver_kind: {driver}\ndriver_id: \"{driver_id}\"\n",
    )
    write(directory / "goal-plan.md", "# Goal Plan\n")
    write(directory / "goal-protocol.md", "# Goal Protocol\n")


def feature_next(repo: Path, slug: str) -> Action:
    directory = feature_dir(repo, slug)
    design = directory / f"{slug}-design.md"
    review = directory / f"{slug}-design-review.md"
    goal_state = directory / "goal-state.yaml"
    if not design.exists():
        return Action("load-reference", "cs-feat/references/design/protocol.md")

    design_status = frontmatter(design).get("status")
    review_status = frontmatter(review).get("status")
    if design_status == "draft" and review_status != "passed":
        return Action("load-reference", "cs-feat/references/design-review/protocol.md")
    if review_status in {"changes-requested", "blocked"}:
        return Action("load-reference", "cs-feat/references/design/protocol.md")
    if review_status == "passed" and design_status != "approved":
        return Action("user-checkpoint", "feature-design-confirmation")
    if design_status == "approved" and not goal_state.exists():
        return Action("load-reference", "cs-feat/references/goal/protocol.md")

    state = top_level_yaml(goal_state)
    if state.get("driver_kind") in {"paseo", "native"} and state.get("driver_id"):
        return Action("report-visible-driver", state["driver_id"])
    stage = state.get("stage")
    status = state.get("status")
    if (stage, status) == ("implementation", "ready-to-dispatch"):
        return Action("dispatch-goal-driver", "feature")
    if (stage, status) == ("implementation", "running"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md")
    if (stage, status) == ("review", "ready"):
        return Action("load-skill", "cs-code-review")
    if (stage, status) == ("review", "fixing"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md#review-fix")
    if (stage, status) == ("qa", "ready"):
        return Action("load-reference", "cs-feat/references/qa/protocol.md")
    if (stage, status) == ("qa", "fixing"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md#qa-fix")
    if (stage, status) == ("acceptance", "ready"):
        return Action("load-reference", "cs-feat/references/acceptance/protocol.md")
    if (stage, status) == ("complete", "passed"):
        return Action("complete", "CS_FEATURE_GOAL_COMPLETE")
    if (stage, status) == ("handoff", "blocked"):
        return Action("user-checkpoint", "CS_FEATURE_GOAL_HANDOFF")
    return Action("blocked", "unknown-feature-state")


def roadmap_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/roadmap" / slug


def write_roadmap(repo: Path, slug: str, status: str = "draft") -> Path:
    directory = roadmap_dir(repo, slug)
    write(directory / f"{slug}-roadmap.md", f"---\ndoc_type: roadmap\nslug: {slug}\nstatus: {status}\n---\n# Roadmap\n")
    write(
        directory / f"{slug}-items.yaml",
        f"roadmap: {slug}\nitems:\n  - slug: api-seed\n    status: planned\n    feature: null\n  - slug: ui-seed\n    status: planned\n    feature: null\n",
    )
    return directory


def write_roadmap_review(repo: Path, slug: str, status: str = "passed") -> None:
    directory = roadmap_dir(repo, slug)
    write(directory / f"{slug}-roadmap-review.md", f"---\ndoc_type: roadmap-review\nstatus: {status}\n---\n# Review\n")


def roadmap_item_slugs(repo: Path, slug: str) -> list[str]:
    items = roadmap_dir(repo, slug) / f"{slug}-items.yaml"
    return re.findall(r"(?m)^\s*-\s+slug:\s+([A-Za-z0-9_-]+)\s*$", items.read_text(encoding="utf-8"))


def write_epic_goal_state(repo: Path, slug: str, status: str, driver: str = "none") -> None:
    directory = roadmap_dir(repo, slug)
    driver_id = "paseo-roadmap-123" if driver != "none" else ""
    write(
        directory / "goal-state.yaml",
        f"roadmap: {slug}\nstatus: {status}\nbaseline_ref: baseline\ndriver_kind: {driver}\ndriver_id: \"{driver_id}\"\ncurrent_feature_index: 0\nfeatures:\n  - slug: api-seed\n    status: pending\n",
    )
    write(directory / "goal-plan.md", "# Goal Plan\n")
    write(directory / "goal-protocol.md", "# Goal Protocol\n")


def epic_next(repo: Path, slug: str) -> Action:
    directory = roadmap_dir(repo, slug)
    roadmap = directory / f"{slug}-roadmap.md"
    review = directory / f"{slug}-roadmap-review.md"
    goal_state = directory / "goal-state.yaml"
    if not roadmap.exists():
        return Action("load-reference", "cs-epic/references/planning/protocol.md")
    roadmap_status = frontmatter(roadmap).get("status")
    review_status = frontmatter(review).get("status")
    if review_status != "passed":
        return Action("load-reference", "cs-epic/references/review/protocol.md")
    if roadmap_status != "active":
        return Action("user-checkpoint", "epic-roadmap-confirmation")

    child_designs = sorted((repo / ".codestable/features").glob("*/**/*-design.md"))
    roadmap_child_designs = [path for path in child_designs if frontmatter(path).get("roadmap") == slug]
    child_items = {
        frontmatter(path).get("roadmap_item") or path.name.removesuffix("-design.md") for path in roadmap_child_designs
    }
    if any(item_slug not in child_items for item_slug in roadmap_item_slugs(repo, slug)):
        return Action("load-skill", "cs-feat design/design-review")
    if not roadmap_child_designs:
        return Action("load-skill", "cs-feat design/design-review")
    child_review_statuses = []
    child_design_statuses = []
    for design in roadmap_child_designs:
        child_slug = design.name.removesuffix("-design.md")
        child_review = design.parent / f"{child_slug}-design-review.md"
        child_review_statuses.append(frontmatter(child_review).get("status"))
        child_design_statuses.append(frontmatter(design).get("status"))
    if any(status != "passed" for status in child_review_statuses):
        return Action("load-skill", "cs-feat design/design-review")
    if any(status != "approved" for status in child_design_statuses):
        return Action("user-checkpoint", "all-feature-designs-confirmation")
    if not goal_state.exists():
        return Action("load-reference", "cs-epic/references/goal/protocol.md")

    state = top_level_yaml(goal_state)
    if state.get("driver_kind") in {"paseo", "native"} and state.get("driver_id"):
        return Action("report-visible-driver", state["driver_id"])
    if state.get("status") == "ready-to-dispatch":
        return Action("dispatch-goal-driver", "epic")
    if state.get("status") == "complete":
        return Action("complete", "CS_ROADMAP_GOAL_COMPLETE")
    return Action("blocked", "unknown-epic-state")


def issue_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/issues" / f"2026-07-02-{slug}"


def write_issue_doc(repo: Path, slug: str, name: str, status: str = "draft") -> None:
    write(
        issue_dir(repo, slug) / f"{slug}-{name}.md",
        f"---\ndoc_type: issue-{name}\nissue: 2026-07-02-{slug}\nstatus: {status}\n---\n# {name}\n",
    )


def issue_next(repo: Path, slug: str) -> Action:
    directory = issue_dir(repo, slug)
    if not (directory / f"{slug}-report.md").exists():
        return Action("load-reference", "cs-issue/references/report/protocol.md")
    if not (directory / f"{slug}-analysis.md").exists():
        return Action("load-reference", "cs-issue/references/analyze/protocol.md")
    if not (directory / f"{slug}-fix-note.md").exists():
        return Action("load-reference", "cs-issue/references/fix/protocol.md")
    review_status = frontmatter(directory / f"{slug}-review.md").get("status")
    if not review_status:
        return Action("load-skill", "cs-code-review")
    if review_status in {"changes-requested", "blocked"}:
        return Action("load-reference", "cs-issue/references/fix/protocol.md#review-fix")
    if review_status == "passed":
        return Action("complete", "issue-reviewed")
    return Action("blocked", "unknown-issue-state")


def refactor_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/refactors" / f"2026-07-02-{slug}"


def write_refactor_doc(repo: Path, slug: str, name: str, status: str = "draft") -> None:
    write(
        refactor_dir(repo, slug) / f"{slug}-{name}.md",
        f"---\ndoc_type: refactor-{name}\nrefactor: 2026-07-02-{slug}\nstatus: {status}\n---\n# {name}\n",
    )


def refactor_next(repo: Path, slug: str, mode: str | None = None, small_scope: bool = False) -> Action:
    if mode == "fastforward" and small_scope:
        return Action("load-reference", "cs-refactor/references/fastforward/protocol.md")
    directory = refactor_dir(repo, slug)
    scan = directory / f"{slug}-scan.md"
    design = directory / f"{slug}-refactor-design.md"
    apply_notes = directory / f"{slug}-apply-notes.md"
    if not scan.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#scan")
    if "selected: true" not in scan.read_text(encoding="utf-8"):
        return Action("user-checkpoint", "refactor-scan-selection")
    if not design.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#design")
    if frontmatter(design).get("status") != "approved":
        return Action("user-checkpoint", "refactor-design-confirmation")
    if "verification: HUMAN" in (directory / f"{slug}-checklist.yaml").read_text(encoding="utf-8"):
        return Action("user-checkpoint", "refactor-human-validation")
    if not apply_notes.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#apply")
    review_status = frontmatter(directory / f"{slug}-review.md").get("status")
    if review_status != "passed":
        return Action("load-skill", "cs-code-review")
    return Action("complete", "refactor-reviewed")


def docs_next(repo: Path, request: str, mode: str | None = None) -> Action:
    if "sync" in request or "neat" in request or "memory" in request:
        return Action("load-skill", "cs-docs-neat")
    if mode == "api" or "api" in request:
        return Action("load-reference", "cs-docs/references/api/protocol.md")
    guide = repo / "docs/dev/widget-guide.md"
    if guide.exists() and frontmatter(guide).get("status") == "current" and "small edit" in request:
        return Action("focused-edit", "docs/dev/widget-guide.md")
    return Action("load-reference", "cs-docs/references/tutorial/protocol.md")


def code_review_next(repo: Path, feature_slug: str | None = None, range_arg: str | None = None) -> Action:
    if range_arg:
        diff = subprocess.run(["git", "diff", range_arg], cwd=repo, text=True, stdout=subprocess.PIPE, check=True).stdout
        return Action("ad-hoc-range-review", range_arg) if diff else Action("blocked", "empty-range")
    if feature_slug:
        directory = feature_dir(repo, feature_slug)
        review = directory / f"{feature_slug}-review.md"
        if frontmatter(review).get("status") == "passed":
            diff = git(repo, "diff", "--stat").stdout
            if not diff:
                return Action("downstream", "cs-feat QA")
        diff = git(repo, "diff", "--stat").stdout
        if diff:
            return Action("run-review", f".codestable/features/2026-07-02-{feature_slug}")
    return Action("blocked", "no-review-scope")


def goal_driver_decision(
    *,
    paseo: bool = False,
    native: bool = False,
    visible: bool = False,
    nested_reviewer: bool = False,
) -> Action:
    if paseo:
        return Action("dispatch", "paseo")
    if native and visible and nested_reviewer:
        return Action("dispatch", "native")
    return Action("fallback", "fenced-/goal")


def route_request(has_codestable: bool, request: str) -> str:
    if not has_codestable:
        return "cs-onboard"
    request = request.lower()
    if "bug" in request or "error" in request:
        return "cs-issue"
    if "refactor" in request or "optimize" in request:
        return "cs-refactor"
    if "api doc" in request or "guide" in request:
        return "cs-docs"
    if "feedback" in request or "skill failed" in request or "rule unclear" in request:
        return "cs-feedback"
    if "epic" in request or "roadmap" in request or "system" in request:
        return "cs-epic"
    if "remember" in request:
        return "cs-keep"
    if "unclear" in request or "brainstorm" in request:
        return "cs-brainstorm"
    if "requirement" in request:
        return "cs-req"
    return "cs-feat"


def test_scenario_matrix_covers_every_refactored_skill() -> None:
    covered = set().union(*SCENARIO_COVERAGE.values())
    assert AFFECTED_SKILLS - covered == set()


def test_router_scenarios_route_to_main_entries_only(tmp_path: Path) -> None:
    assert_doc_contains("cs", "SKILL.md", "只把开放式诉求路由到推荐主入口", "主路径不再路由到它们")
    repo = init_isolated_repo(tmp_path)

    assert route_request(False, "add search") == "cs-onboard"
    assert route_request((repo / ".codestable").exists(), "fix login bug") == "cs-issue"
    assert route_request(True, "refactor this module") == "cs-refactor"
    assert route_request(True, "write api docs") == "cs-docs"
    assert route_request(True, "feedback: cs skill failed because the rule unclear") == "cs-feedback"
    assert route_request(True, "plan the billing roadmap") == "cs-epic"
    assert route_request(True, "this idea is unclear, brainstorm first") == "cs-brainstorm"
    assert route_request(True, "update requirement boundary") == "cs-req"
    assert route_request(True, "add export button") == "cs-feat"


def test_feature_long_range_scenario_simulates_human_design_confirmation(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "design gate 停下来等用户确认",
        "默认生成单 feature goal 包",
        "可见 Task agent goal driver 长程执行",
    )
    assert_doc_contains(
        "cs-feat",
        "references/goal/protocol.md",
        "Goal 模式接管",
        "CS_FEATURE_GOAL_COMPLETE",
        "CS_FEATURE_GOAL_HANDOFF",
    )
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"

    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/design/protocol.md")
    write_feature_design(repo, slug, status="draft")
    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/design-review/protocol.md")
    write_feature_design_review(repo, slug, status="passed")
    assert feature_next(repo, slug) == Action("user-checkpoint", "feature-design-confirmation")

    # Simulated human gate: user approved the reviewed design, so the workflow can continue.
    replace_status(feature_dir(repo, slug) / f"{slug}-design.md", "approved")
    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/goal/protocol.md")

    write_feature_goal_state(repo, slug, "implementation", "ready-to-dispatch")
    assert feature_next(repo, slug) == Action("dispatch-goal-driver", "feature")
    write_feature_goal_state(repo, slug, "implementation", "running", driver="paseo")
    assert feature_next(repo, slug) == Action("report-visible-driver", "paseo-123")


@pytest.mark.parametrize(
    ("stage", "status", "expected"),
    [
        ("implementation", "running", Action("load-reference", "cs-feat/references/implementation/protocol.md")),
        ("review", "ready", Action("load-skill", "cs-code-review")),
        ("review", "fixing", Action("load-reference", "cs-feat/references/implementation/protocol.md#review-fix")),
        ("qa", "ready", Action("load-reference", "cs-feat/references/qa/protocol.md")),
        ("qa", "fixing", Action("load-reference", "cs-feat/references/implementation/protocol.md#qa-fix")),
        ("acceptance", "ready", Action("load-reference", "cs-feat/references/acceptance/protocol.md")),
        ("complete", "passed", Action("complete", "CS_FEATURE_GOAL_COMPLETE")),
        ("handoff", "blocked", Action("user-checkpoint", "CS_FEATURE_GOAL_HANDOFF")),
    ],
)
def test_feature_goal_state_machine_routes_each_long_range_stage(tmp_path: Path, stage: str, status: str, expected: Action) -> None:
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"
    write_feature_design(repo, slug, status="approved")
    write_feature_design_review(repo, slug, status="passed")
    write_feature_goal_state(repo, slug, stage, status)

    assert feature_next(repo, slug) == expected


def test_epic_long_range_scenario_simulates_both_human_confirmations(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "roadmap review passed 但用户未确认",
        "用户统一确认所有 design",
        "可见 Task agent goal driver",
    )
    assert_doc_contains("cs-epic", "references/goal/protocol.md", "两次确认门禁", "CS_ROADMAP_GOAL_COMPLETE")
    repo = init_isolated_repo(tmp_path)
    slug = "billing-system"

    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/planning/protocol.md")
    write_roadmap(repo, slug, status="draft")
    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/review/protocol.md")
    write_roadmap_review(repo, slug, status="passed")
    assert epic_next(repo, slug) == Action("user-checkpoint", "epic-roadmap-confirmation")

    # Simulated human gate 1: roadmap is approved by the user.
    replace_status(roadmap_dir(repo, slug) / f"{slug}-roadmap.md", "active")
    assert epic_next(repo, slug) == Action("load-skill", "cs-feat design/design-review")

    for child in ["api-seed", "ui-seed"]:
        write_feature_design(repo, child, status="draft", roadmap=slug)
        write_feature_design_review(repo, child, status="passed")
    assert epic_next(repo, slug) == Action("user-checkpoint", "all-feature-designs-confirmation")

    # Simulated human gate 2: all child designs are approved as a batch.
    for child in ["api-seed", "ui-seed"]:
        replace_status(feature_dir(repo, child) / f"{child}-design.md", "approved")
    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/goal/protocol.md")

    write_epic_goal_state(repo, slug, "ready-to-dispatch")
    assert epic_next(repo, slug) == Action("dispatch-goal-driver", "epic")
    write_epic_goal_state(repo, slug, "running", driver="paseo")
    assert epic_next(repo, slug) == Action("report-visible-driver", "paseo-roadmap-123")


def test_epic_child_design_batch_continues_after_one_child_review_passed(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "Child design batch loop",
        "codestable-workflow-next.py epic",
        "完成某一个 child 的 design + design-review `passed` 只是内部进度",
        "不得 final answer",
        "本轮必须继续调用 `cs-feat`",
    )
    assert_doc_contains(
        "cs-epic",
        "references/goal/protocol.md",
        "单个 child 完成不是本阶段退出条件",
        "不能用 final answer",
        "codestable-workflow-next.py epic",
        "继续 batch loop",
    )

    repo = init_isolated_repo(tmp_path)
    slug = "billing-system"
    write_roadmap(repo, slug, status="active")
    write_roadmap_review(repo, slug, status="passed")

    write_feature_design(repo, "api-seed", status="draft", roadmap=slug)
    write_feature_design_review(repo, "api-seed", status="passed")

    assert epic_next(repo, slug) == Action("load-skill", "cs-feat design/design-review")


def test_missing_workflow_next_hook_uses_runtime_manifest_preflight() -> None:
    assert_doc_contains(
        "cs-onboard",
        "SKILL.md",
        "--mode refresh-runtime",
        "可重复执行",
        "不重新审计 / 迁移文档",
        "只想刷新 runtime、不审计或迁移文档时，显式传 `--mode refresh-runtime`",
        ".codestable/runtime-manifest.json",
        "codestable-runtime-sync.py",
        "不移动用户文件",
    )
    assert_doc_contains(
        "cs-onboard",
        "references/execution-conventions.md",
        "Runtime 资产恢复",
        "runtime capability",
        ".codestable/runtime-manifest.json",
        "当前插件包里的 `cs-onboard/tools/codestable-runtime-sync.py` 自动同步",
        "--check --json",
        "`--check` 自动同步",
        "`workflow-next`",
        "managed paths 有未提交改动",
    )
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "CodeStable preflight 已确认的 `workflow-next` runtime capability",
    )
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "CodeStable preflight 已确认的 `workflow-next` runtime capability",
    )
    assert_doc_contains(
        "cs-epic",
        "references/goal/protocol.md",
        "CodeStable preflight 已确认的 `workflow-next` runtime capability",
        "若 preflight 刚完成同步，从仓库事实恢复 batch loop",
    )


def test_goal_driver_selection_requires_visibility_and_nested_reviewer() -> None:
    assert_doc_contains(
        "cs-onboard",
        "references/execution-conventions.md",
        "宿主显式暴露用户可见的 run id",
        "宿主显式支持 driver 在其运行环境内再启动独立 Task agent reviewer",
        "直接回退打印 `/goal`",
    )

    assert goal_driver_decision(paseo=True) == Action("dispatch", "paseo")
    assert goal_driver_decision(native=True, visible=True, nested_reviewer=True) == Action("dispatch", "native")
    assert goal_driver_decision(native=True, visible=True, nested_reviewer=False) == Action("fallback", "fenced-/goal")
    assert goal_driver_decision(native=True, visible=False, nested_reviewer=True) == Action("fallback", "fenced-/goal")
    assert goal_driver_decision() == Action("fallback", "fenced-/goal")


def test_task_agent_lifecycle_closes_consumed_agents_and_cleans_only_on_capacity_failure() -> None:
    assert_doc_contains(
        "cs-onboard",
        "references/execution-conventions.md",
        "## Task agent 生命周期",
        "先消费并落盘结果，再调用宿主提供的 `close_agent`",
        "不要关闭 still-running、pending、permission-needed",
        "不要预先批量清理旧 agent",
        "`agent thread limit reached`",
        "按最老优先关闭一小批，再重试本次 create/spawn 一次",
    )
    assert_doc_contains(
        "cs-goal",
        "SKILL.md",
        "按 Task agent 生命周期关闭该验收 agent",
        "先按 Task agent 生命周期处理容量失败重试",
    )
    assert_doc_contains(
        "cs-goal",
        "reference.md",
        "Task agent id / run id、关闭结果或关闭失败 warning",
        "Task agent 结果消费后",
    )
    assert_doc_contains(
        "cs-code-review",
        "references/independent-review/protocol.md",
        "Task agent 生命周期关闭该 reviewer",
        "只在失败后按最老已完成 agent 清理并重试一次",
    )
    assert_doc_contains("cs-feat", "references/qa/protocol.md", "Task agent 生命周期关闭该 runner")
    assert_doc_contains("cs-feat", "references/acceptance/protocol.md", "auditor 输出被消费后按 Task agent 生命周期关闭")
    assert_doc_contains("cs-epic", "references/goal/support/protocol-gates.md", "结果消费后按 Task agent 生命周期关闭")


def test_issue_scenario_progresses_through_main_entry_references(tmp_path: Path) -> None:
    assert_doc_contains("cs-issue", "SKILL.md", "report、analyze、fix、review", "仓库事实")
    repo = init_isolated_repo(tmp_path)
    slug = "login-error"

    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/report/protocol.md")
    write_issue_doc(repo, slug, "report")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/analyze/protocol.md")
    write_issue_doc(repo, slug, "analysis")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/fix/protocol.md")
    write_issue_doc(repo, slug, "fix-note")
    assert issue_next(repo, slug) == Action("load-skill", "cs-code-review")
    write_issue_doc(repo, slug, "review", status="changes-requested")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/fix/protocol.md#review-fix")
    replace_status(issue_dir(repo, slug) / f"{slug}-review.md", "passed")
    assert issue_next(repo, slug) == Action("complete", "issue-reviewed")


def test_refactor_scenario_respects_scan_design_and_human_validation_gates(tmp_path: Path) -> None:
    assert_doc_contains("cs-refactor", "SKILL.md", "scan → 用户勾选 → design → 用户确认 → apply → cs-code-review")
    assert_doc_contains("cs-refactor", "references/standard/protocol.md", "用户勾选", "HUMAN 验证")
    repo = init_isolated_repo(tmp_path)
    slug = "split-helper"

    assert refactor_next(repo, slug, mode="fastforward", small_scope=True) == Action(
        "load-reference", "cs-refactor/references/fastforward/protocol.md"
    )
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#scan")
    write_refactor_doc(repo, slug, "scan")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-scan-selection")
    write(refactor_dir(repo, slug) / f"{slug}-scan.md", "selected: true\n")
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#design")
    write_refactor_doc(repo, slug, "refactor-design", status="draft")
    write(refactor_dir(repo, slug) / f"{slug}-checklist.yaml", "steps:\n  - id: visual\n    verification: HUMAN\n")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-design-confirmation")
    replace_status(refactor_dir(repo, slug) / f"{slug}-refactor-design.md", "approved")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-human-validation")
    write(refactor_dir(repo, slug) / f"{slug}-checklist.yaml", "steps:\n  - id: visual\n    verification: AI\n")
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#apply")
    write_refactor_doc(repo, slug, "apply-notes")
    assert refactor_next(repo, slug) == Action("load-skill", "cs-code-review")


def test_docs_scenario_selects_docs_entry_or_neat_hygiene(tmp_path: Path) -> None:
    assert_doc_contains("cs-docs", "SKILL.md", "不做全局同步", "转 `cs-docs-neat`")
    assert_doc_contains("cs-docs-neat", "SKILL.md", "不是 `cs-docs`", "Phase 1：机械式枚举")
    repo = init_isolated_repo(tmp_path)

    assert docs_next(repo, "write api docs", mode="api") == Action("load-reference", "cs-docs/references/api/protocol.md")
    assert docs_next(repo, "write a developer guide") == Action(
        "load-reference", "cs-docs/references/tutorial/protocol.md"
    )
    write(
        repo / "docs/dev/widget-guide.md",
        "---\ndoc_type: dev-guide\nstatus: current\n---\n# Widget Guide\n",
    )
    assert docs_next(repo, "small edit to widget guide") == Action("focused-edit", "docs/dev/widget-guide.md")
    assert docs_next(repo, "sync memory and README") == Action("load-skill", "cs-docs-neat")


def test_code_review_scenario_handles_feature_diff_and_ad_hoc_range(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-code-review",
        "SKILL.md",
        "ad-hoc range 审查允许工作区干净",
        "横切代码审查 gate",
        "references/independent-review/protocol.md",
    )
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"
    write_feature_design(repo, slug, status="approved")
    write_feature_design_review(repo, slug, status="passed")
    write(feature_dir(repo, slug) / f"{slug}-checklist.yaml", "steps:\n  - id: step-1\n    status: done\nchecks:\n  - id: check-1\n    status: pending\n")
    write(repo / "src/app.py", "def hello():\n    return 'hello export'\n")
    assert code_review_next(repo, feature_slug=slug) == Action("run-review", ".codestable/features/2026-07-02-export-csv")

    git(repo, "add", ".")
    git(repo, "commit", "-m", "feature change")
    assert code_review_next(repo, range_arg="HEAD~1..HEAD") == Action("ad-hoc-range-review", "HEAD~1..HEAD")

    write(
        feature_dir(repo, slug) / f"{slug}-review.md",
        "---\ndoc_type: feature-review\nstatus: passed\nreviewer: subagent\n---\n# Review\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "add review")
    assert code_review_next(repo, feature_slug=slug) == Action("downstream", "cs-feat QA")


@pytest.mark.parametrize("entry,expected", sorted(COMPATIBILITY_ENTRIES.items()))
def test_compatibility_entry_scenarios_delegate_without_rerun(entry: str, expected: tuple[str, str, str]) -> None:
    main, key, value = expected
    text = skill_text(entry)

    assert f"加载 `{main}`" in text
    assert f"{key}: {value}" in text
    assert "不要要求用户重新调用" in text
    assert "不维护独立流程规则" in text
    assert "../" not in text
