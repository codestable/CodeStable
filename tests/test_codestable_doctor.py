from __future__ import annotations

import importlib.util
import json
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


doctor = load_tool("codestable_doctor", "codestable-doctor.py")
worktree_gate = load_tool("codestable_worktree_gate", "codestable-worktree-gate.py")
runtime_tool = load_tool("codestable_runtime", "codestable_runtime.py")


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
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
        ".codestable/reference/agent-conventions.md",
        ".codestable/reference/worktree-conventions.md",
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


def test_idle_repo_reports_idle_without_mutation(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    before = run(repo, "status", "--porcelain").stdout

    report = doctor.diagnose(repo)

    after = run(repo, "status", "--porcelain").stdout
    assert report["status"] == "idle"
    assert report["findings"] == []
    assert before == after == ""


def test_missing_runtime_assets_are_blocked_with_refresh_hint(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".codestable/tools/codestable-workflow-next.py").unlink()

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    runtime = report["tooling"]["runtime"]
    assert runtime["status"] == "runtime-incomplete"
    assert runtime["capabilities"]["workflow-next"]["missing"] == [".codestable/tools/codestable-workflow-next.py"]
    assert "runtime sync" in runtime["hint"]
    assert "CodeStable runtime assets are incomplete or stale" in report["findings"][0]["message"]


def test_missing_attention_reports_onboard_incomplete_not_refresh(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".codestable/attention.md").unlink()

    report = doctor.diagnose(repo)

    runtime = report["tooling"]["runtime"]
    assert runtime["status"] == "onboard-incomplete"
    assert "cs-onboard`" in runtime["hint"]
    assert "runtime sync does not create attention.md" in runtime["hint"]
    assert "CodeStable onboarding is incomplete" in report["findings"][0]["message"]


def test_runtime_version_mismatch_is_blocked_with_sync_hint(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    manifest = repo / ".codestable/runtime-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["plugin_version"] = "0.9.0"
    manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    runtime = report["tooling"]["runtime"]
    assert runtime["status"] == "version-mismatch"
    assert runtime["installed_plugin_version"] == "0.9.0"
    assert runtime["expected_plugin_version"] == "1.0.0"
    assert "runtime sync" in runtime["hint"]


def test_runtime_sync_refreshes_managed_assets_and_manifest(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "source-skill"
    for directory in ["gates", "tools", "references", "hooks"]:
        (source / directory).mkdir(parents=True)
    (source / "gates/roadmap-goal-gates.yaml").write_text("version: 2\n", encoding="utf-8")
    (source / "tools/codestable-workflow-next.py").write_text("new workflow\n", encoding="utf-8")
    (source / "references/tools.md").write_text("new tools\n", encoding="utf-8")
    (source / "hooks/hooks.codex.json").write_text("{}\n", encoding="utf-8")
    (source / "codestable.gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (source / ".codex-plugin").mkdir()
    (source / ".codex-plugin/plugin.json").write_text('{"version": "1.1.0"}\n', encoding="utf-8")

    result = runtime_tool.sync_runtime(repo, source)

    assert result["ok"]
    assert (repo / ".codestable/tools/codestable-workflow-next.py").read_text(encoding="utf-8") == "new workflow\n"
    manifest = json.loads((repo / ".codestable/runtime-manifest.json").read_text(encoding="utf-8"))
    assert manifest["plugin_version"] == "1.1.0"
    assert ".codestable/tools" in manifest["managed_paths"]


def test_runtime_sync_refuses_dirty_managed_paths_without_force(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "source-skill"
    (source / "tools").mkdir(parents=True)
    (source / "tools/validate-yaml.py").write_text("new\n", encoding="utf-8")
    (repo / ".codestable/tools/validate-yaml.py").write_text("local edit\n", encoding="utf-8")

    result = runtime_tool.sync_runtime(repo, source)

    assert not result["ok"]
    assert result["status"] == "managed-paths-dirty"
    assert ".codestable/tools/validate-yaml.py" in result["dirty_paths"]


def test_docs_only_dirty_state_is_planning_safe(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs/plan.md").write_text("plan\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "planning-safe"
    assert report["dirty_buckets"] == {"docs": ["docs/plan.md"]}
    assert report["implementation_changes"] == []


def test_dirty_implementation_on_main_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["implementation_changes"] == ["src/app.py"]
    assert "outside a linked execution worktree" in report["findings"][0]["message"]


def test_completed_unit_without_review_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["findings"][0]["path"] == ".codestable/features/2026-06-03-demo/demo-review.md"


def test_backlog_terms_are_reported_with_line_numbers(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (repo / ".codestable/attention.md").write_text("## attention.md Candidates\n- add test command\n", encoding="utf-8")
    (unit / "demo-acceptance.md").write_text(
        "status: needs-human-review\n"
        "Human review required before publish.\n"
        "Follow-up: convert risk into issue.\n"
        "accepted P2: reviewer allowed delayed cleanup.\n",
        encoding="utf-8",
    )

    report = doctor.diagnose(repo)

    kinds = {item["kind"] for item in report["backlog"]}
    assert {"attention-candidate", "needs-human-review", "human-review", "follow-up", "accepted-p2"} <= kinds
    assert all(item["line"] >= 1 for item in report["backlog"])


def test_clean_main_with_post_baseline_implementation_commit_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "worktree-override.md").write_text(
        "reason: test\nscope: demo\napproval: approved\n",
        encoding="utf-8",
    )
    payload = worktree_gate.start_gate(repo, ".codestable/features/2026-06-03-demo")
    assert payload["ok"]
    assert run(repo, "status", "--porcelain").stdout == "?? .codestable/features/\n"

    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add unit")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(repo, "add", "src/app.py")
    run(repo, "commit", "-m", "implement on main")
    assert run(repo, "status", "--porcelain").stdout == ""

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["post_baseline_blocks"][0]["implementation_changes"] == ["src/app.py"]
