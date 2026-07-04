from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
TOOLS_DIR = Path(__file__).resolve().parents[1] / "plugins/codestable/skills/cs-onboard/tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = load_tool("codestable_worktree_gate_for_tests", "codestable-worktree-gate.py")
common = load_tool("codestable_common_for_tests", "codestable_common.py")
finish_gate = load_tool("codestable_finish_worktree_for_tests", "codestable-finish-worktree.py")
inbox_tool = load_tool("codestable_worktree_inbox_for_tests", "codestable-worktree-inbox.py")
doctor_tool = load_tool("codestable_doctor_for_worktree_tests", "codestable-doctor.py")


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run(repo, "init", "-b", "main")
    run(repo, "config", "user.email", "test@example.com")
    run(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    install_runtime(repo)
    run(repo, "add", ".")
    run(repo, "commit", "-m", "init")
    return repo


def install_runtime(repo: Path) -> None:
    for path in [
        ".codestable/attention.md",
        ".codestable/reference/execution-conventions.md",
        ".codestable/reference/shared-conventions.md",
        ".codestable/reference/tools.md",
        ".codestable/runtime-manifest.json",
        ".codestable/tools/validate-yaml.py",
        ".codestable/tools/search-yaml.py",
        ".codestable/tools/codestable-workflow-next.py",
        ".codestable/tools/codestable-worktree-gate.py",
        ".codestable/tools/validate-implementation-review.py",
        ".codestable/gates/roadmap-goal-gates.yaml",
        ".codestable/tools/codestable-scope-gate.py",
        ".codestable/tools/codestable-dod-contract-gate.py",
        ".codestable/tools/codestable-dod-runner.py",
        ".codestable/tools/codestable-evidence-pack.py",
        ".codestable/tools/codestable-goal-consistency-gate.py",
    ]:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.name == "runtime-manifest.json":
            target.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "plugin": "codestable",
                        "plugin_version": "1.0.0",
                        "runtime_version": "1.0.0",
                        "managed_paths": [".codestable/tools", ".codestable/gates", ".codestable/reference", ".codestable/hooks"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            target.write_text("runtime\n", encoding="utf-8")


def make_feature_unit(repo: Path) -> Path:
    unit = repo / ".codestable/features/2026-06-03-demo"
    unit.mkdir(parents=True)
    return unit


def make_completed_feature_unit(repo: Path) -> Path:
    unit = make_feature_unit(repo)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )
    (unit / "demo-review.md").write_text(
        "reviewer: subagent\nfindings: none\n",
        encoding="utf-8",
    )
    return unit


def make_completed_feature_unit_with_subagent_ocr(repo: Path) -> Path:
    unit = make_feature_unit(repo)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )
    (unit / "demo-review.md").write_text(
        "reviewer: subagent+ocr\nfindings: none\n",
        encoding="utf-8",
    )
    return unit


def approved_override(unit: Path) -> None:
    (unit / "worktree-override.md").write_text(
        "reason: test\nscope: demo\napproval: approved\n",
        encoding="utf-8",
    )


def test_start_gate_blocks_implementation_unit_on_main(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)

    payload = gate.start_gate(repo, ".codestable/features/2026-06-03-demo")

    assert not payload["ok"]
    assert "linked execution worktree" in payload["findings"][0]["message"]
    assert not Path(payload["baseline_path"]).exists()


def test_start_gate_passes_in_real_linked_worktree_and_keeps_status_clean(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "demo-design.md").write_text("design\n", encoding="utf-8")
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add feature unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())

    payload = gate.start_gate(worktree, ".codestable/features/2026-06-03-demo")

    assert payload["ok"]
    assert payload["linked_worktree"] is True
    assert payload["baseline"]["timestamp"] > 0
    assert Path(payload["baseline_path"]).exists()
    assert run(worktree, "status", "--porcelain").stdout == ""


def test_path_named_worktree_dir_is_not_enough_for_linked_worktree(tmp_path: Path) -> None:
    repo_parent = tmp_path / ".worktree"
    repo_parent.mkdir(parents=True)
    repo = repo_parent / "plain-repo"
    repo.mkdir()
    run(repo, "init", "-b", "main")
    run(repo, "config", "user.email", "test@example.com")
    run(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    unit = make_feature_unit(repo)
    (unit / "demo-design.md").write_text("design\n", encoding="utf-8")
    run(repo, "add", ".")
    run(repo, "commit", "-m", "init")

    payload = gate.start_gate(repo, ".codestable/features/2026-06-03-demo")

    assert not payload["ok"]
    assert payload["linked_worktree"] is False
    assert "linked execution worktree" in payload["findings"][0]["message"]


def test_commit_gate_blocks_staged_implementation_on_default_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(repo, "add", "src/app.py")

    payload = gate.commit_gate(repo, ".codestable/features/2026-06-03-demo")

    assert not payload["ok"]
    assert "Staged implementation changes" in payload["findings"][0]["message"]


def test_commit_gate_catches_clean_main_with_post_baseline_implementation_commit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    approved_override(unit)
    payload = gate.start_gate(repo, ".codestable/features/2026-06-03-demo")
    assert payload["ok"]

    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add unit")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(repo, "add", "src/app.py")
    run(repo, "commit", "-m", "implement on main")
    assert run(repo, "status", "--porcelain").stdout == ""

    payload = gate.commit_gate(repo, ".codestable/features/2026-06-03-demo")

    assert not payload["ok"]
    assert payload["post_baseline_implementation"] == ["src/app.py"]


def test_commit_gate_blocks_completed_unit_missing_review(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )

    payload = gate.commit_gate(repo, ".codestable/features/2026-06-03-demo")

    assert not payload["ok"]
    assert payload["findings"][0]["path"] == ".codestable/features/2026-06-03-demo/demo-review.md"


def test_commit_gate_warns_but_does_not_fail_for_mixed_non_implementation_buckets(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)
    (repo / "docs").mkdir()
    (repo / "docs/plan.md").write_text("plan\n", encoding="utf-8")
    (repo / "data/output").mkdir(parents=True)
    (repo / "data/output/items.json").write_text("{}\n", encoding="utf-8")
    run(repo, "add", "docs/plan.md", "data/output/items.json")

    payload = gate.commit_gate(repo, ".codestable/features/2026-06-03-demo")

    assert payload["ok"]
    assert payload["warnings"][0]["message"].startswith("Staged files span multiple commit buckets")


def test_quarantine_dry_run_does_not_mutate_repo(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    before_status = run(repo, "status", "--porcelain").stdout
    before_branches = run(repo, "branch", "--list").stdout
    before_worktrees = run(repo, "worktree", "list", "--porcelain").stdout

    payload = gate.quarantine_gate(repo, ".codestable/features/2026-06-03-demo", False)

    assert payload["ok"]
    assert payload["dry_run"] is True
    assert run(repo, "status", "--porcelain").stdout == before_status
    assert run(repo, "branch", "--list").stdout == before_branches
    assert run(repo, "worktree", "list", "--porcelain").stdout == before_worktrees


def test_quarantine_apply_requires_approved_override(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)

    payload = gate.quarantine_gate(repo, ".codestable/features/2026-06-03-demo", True)

    assert not payload["ok"]
    assert "--apply requires worktree-override.md" in payload["findings"][0]["message"]


def test_quarantine_refuses_untracked_secret_like_files(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_feature_unit(repo)
    (repo / ".env.local").write_text("TOKEN=x\n", encoding="utf-8")

    payload = gate.quarantine_gate(repo, ".codestable/features/2026-06-03-demo", False)

    assert not payload["ok"]
    assert ".env.local" in payload["findings"][0]["path"]


def test_runtime_tool_paths_are_documented() -> None:
    root = Path(__file__).resolve().parents[1]
    tools_doc = (root / "plugins/codestable/skills/cs-onboard/references/tools.md").read_text(encoding="utf-8")
    tools_doc += "\n" + (root / "plugins/codestable/skills/cs-onboard/references/tools-context.md").read_text(encoding="utf-8")

    assert "python3 .codestable/tools/codestable-doctor.py --root . --json" in tools_doc
    assert "python3 .codestable/tools/codestable-worktree-gate.py --root . --json start" in tools_doc
    assert "python3 .codestable/tools/codestable-finish-worktree.py --root ." in tools_doc
    assert "python3 .codestable/tools/codestable-worktree-inbox.py --root . --json" in tools_doc
    hook_doc = (Path(__file__).resolve().parents[1] / "plugins/codestable/skills/cs-onboard/references/branch-guard-hooks.md").read_text(
        encoding="utf-8"
    )
    assert "codestable-ai-branch-guard.py" in hook_doc
    assert "Publishing `main` remains an owner workflow" in hook_doc


def test_missing_unit_cli_returns_json_finding(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    script = TOOLS_DIR / "codestable-worktree-gate.py"

    completed = subprocess.run(
        [sys.executable, script.as_posix(), "--root", repo.as_posix(), "--json", "start", "--unit", "missing"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["ok"] is False
    assert payload["findings"][0]["message"] == "unit not found: missing"
    assert "Traceback" not in completed.stderr


def test_missing_codestable_unit_path_returns_json_finding(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    script = TOOLS_DIR / "codestable-worktree-gate.py"

    completed = subprocess.run(
        [
            sys.executable,
            script.as_posix(),
            "--root",
            repo.as_posix(),
            "--json",
            "commit",
            "--unit",
            ".codestable/features/2026-06-03-missing",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["findings"][0]["message"] == "unit not found: .codestable/features/2026-06-03-missing"
    assert "Traceback" not in completed.stderr


def test_finish_gate_blocks_default_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)

    payload = finish_gate.finish(repo, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])

    assert not payload["ok"]
    assert any("linked execution worktree" in finding["message"] for finding in payload["findings"])


def test_finish_gate_accepts_subagent_ocr_review_evidence(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit_with_subagent_ocr(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")

    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])

    assert payload["ok"]


def test_finish_gate_creates_learning_report_and_cross_worktree_inbox(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    head = run(worktree, "rev-parse", "HEAD").stdout.strip()

    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])

    assert payload["ok"]
    assert payload["status"] == "ready-to-merge"
    assert payload["covered_head"] == head
    report = worktree / ".codestable/features/2026-06-03-demo/demo-learning-report.md"
    context_check = worktree / ".codestable/features/2026-06-03-demo/demo-learning-context-check.json"
    merge_readiness = worktree / ".codestable/features/2026-06-03-demo/demo-merge-readiness.json"
    assert report.exists()
    assert context_check.exists()
    assert merge_readiness.exists()
    assert f"covered_head: {head}" in report.read_text(encoding="utf-8")
    assert Path(payload["inbox_record"]).exists()

    inbox = inbox_tool.inbox(repo)
    assert inbox["ready_to_merge"][0]["branch"] == "feat/demo"
    assert inbox["ready_to_merge"][0]["covered_head"] == head

    doctor = doctor_tool.diagnose(repo)
    assert doctor["status"] == "attention-needed"
    assert doctor["ready_to_merge_worktrees"][0]["branch"] == "feat/demo"


def test_finish_gate_blocks_uncommitted_implementation_changes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    (worktree / "src/uncommitted.py").write_text("print('dirty')\n", encoding="utf-8")

    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])

    assert not payload["ok"]
    assert any(finding["path"] == "src/uncommitted.py" for finding in payload["findings"])
    assert any("clean working tree" in finding["message"] for finding in payload["findings"])


def test_worktree_inbox_marks_stale_after_new_branch_commit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]
    (worktree / "src/app.py").write_text("print('y')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "change after report")

    inbox = inbox_tool.inbox(repo)

    assert inbox["ok"] is False
    assert inbox["stale_reports"][0]["status"] == "stale-report"
    assert inbox["stale_reports"][0]["severity"] == "P1"


def test_worktree_inbox_marks_stale_when_only_covered_head_reaches_base(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]
    covered_head = payload["covered_head"]
    (worktree / "src/app.py").write_text("print('y')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "change after report")
    run(repo, "merge", "--ff-only", covered_head)

    inbox = inbox_tool.inbox(repo)

    assert inbox["ok"] is False
    assert inbox["stale_reports"][0]["branch"] == "feat/demo"
    assert inbox["stale_reports"][0]["severity"] == "P1"


def test_finish_gate_refreshes_stale_learning_report(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    first = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert first["ok"]
    (worktree / "src/app.py").write_text("print('y')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "change after report")
    second_head = run(worktree, "rev-parse", "HEAD").stdout.strip()

    refreshed = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed again"])
    inbox = inbox_tool.inbox(repo)

    assert refreshed["ok"]
    assert refreshed["covered_head"] == second_head
    assert inbox["ready_to_merge"][0]["covered_head"] == second_head
    assert inbox["stale_reports"] == []


def test_worktree_inbox_marks_merged_after_base_contains_head(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]

    run(repo, "merge", "--ff-only", "feat/demo")
    inbox = inbox_tool.inbox(repo)

    assert inbox["merged"][0]["status"] == "merged"
    assert inbox["merged"][0]["severity"] == "P3"


def test_worktree_inbox_allows_finish_artifact_only_commit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]
    run(worktree, "add", payload["learning_report"], payload["context_check"], payload["merge_readiness"])
    run(worktree, "commit", "-m", "add finish artifacts")

    inbox = inbox_tool.inbox(repo)

    assert inbox["ready_to_merge"][0]["branch"] == "feat/demo"
    assert "finish artifacts" in inbox["ready_to_merge"][0]["reasons"][0]
    assert inbox["stale_reports"] == []


def test_worktree_inbox_marks_merged_after_branch_deleted(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]
    run(repo, "merge", "--ff-only", "feat/demo")
    run(repo, "worktree", "remove", "--force", worktree.as_posix())
    run(repo, "branch", "-d", "feat/demo")

    inbox = inbox_tool.inbox(repo)

    assert inbox["ok"]
    assert inbox["merged"][0]["status"] == "merged"
    assert inbox["merged"][0]["severity"] == "P3"


def test_worktree_inbox_snooze_suppresses_ready_reminder_until_due(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    make_completed_feature_unit(repo)
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add completed unit")
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir()
    (worktree / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    run(worktree, "commit", "-m", "implement demo")
    payload = finish_gate.finish(worktree, ".codestable/features/2026-06-03-demo", ["pytest -> passed"])
    assert payload["ok"]

    snoozed = inbox_tool.snooze(repo, "feat/demo", "2999-01-01T00:00:00Z")
    inbox = inbox_tool.inbox(repo)

    assert snoozed["ok"]
    assert inbox["ok"]
    assert inbox["ready_to_merge"] == []
    assert inbox["snoozed"][0]["branch"] == "feat/demo"
    assert inbox["items"][0]["severity"] is None
