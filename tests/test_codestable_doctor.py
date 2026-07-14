from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CURRENT_PLUGIN_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
TOOLS_DIR = ROOT / "plugins/codestable/skills/cs-onboard/tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


doctor = load_tool("codestable_doctor", "codestable-doctor.py")
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
        ".codestable/reference/tools.md",
        ".codestable/runtime-manifest.json",
        ".codestable/gates/roadmap-goal-gates.yaml",
    ]:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.name == "runtime-manifest.json":
            target.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "plugin": "codestable",
                        "plugin_version": CURRENT_PLUGIN_VERSION,
                        "runtime_version": CURRENT_PLUGIN_VERSION,
                        "tool_runtime": "skill-global",
                        "managed_paths": [".codestable/gates", ".codestable/reference"],
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


def test_missing_repo_runtime_assets_are_blocked_with_refresh_hint(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".codestable/gates/roadmap-goal-gates.yaml").unlink()

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    runtime = report["tooling"]["runtime"]
    assert runtime["status"] == "runtime-incomplete"
    assert runtime["capabilities"]["goal-gates"]["missing_repo"] == [".codestable/gates/roadmap-goal-gates.yaml"]
    assert "runtime sync" in runtime["hint"]
    assert "CodeStable runtime assets are incomplete or stale" in report["findings"][0]["message"]


def test_missing_skill_tools_are_blocked_without_requiring_repo_tools(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "source-skill"
    source.mkdir()

    runtime = runtime_tool.runtime_health(repo, source_skill_dir=source, plugin_version=CURRENT_PLUGIN_VERSION)

    assert runtime["status"] == "runtime-incomplete"
    assert runtime["tool_runtime"] == "skill-global"
    assert "tools/codestable-workflow-next.py" in runtime["capabilities"]["workflow-next"]["missing_skill_tools"]
    assert ".codestable/tools/codestable-workflow-next.py" not in runtime["missing"]


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
    assert runtime["expected_plugin_version"] == CURRENT_PLUGIN_VERSION
    assert "runtime sync" in runtime["hint"]


def test_runtime_manifest_without_version_is_treated_as_needing_sync(tmp_path: Path) -> None:
    # 老项目：version 探测引入前的 manifest 没有 plugin_version 字段 → installed=None。
    # 必须默认判定需同步（None != expected），不能被当成 ok 漏过。
    repo = init_repo(tmp_path)
    manifest = repo / ".codestable/runtime-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data.pop("plugin_version", None)
    manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    runtime = report["tooling"]["runtime"]
    assert runtime["status"] == "version-mismatch"
    assert runtime["installed_plugin_version"] is None
    assert runtime["expected_plugin_version"] == CURRENT_PLUGIN_VERSION
    assert "runtime sync" in runtime["hint"]


def test_runtime_sync_refreshes_managed_assets_manifest_and_preserves_legacy_assets(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    for legacy in [
        ".codestable/reference/worktree-conventions.md",
        ".codestable/reference/branch-guard-hooks.md",
        ".codestable/tools/codestable-worktree-gate.py",
        ".codestable/tools/validate-implementation-review.py",
        ".codestable/hooks/hooks.codex.json",
    ]:
        target = repo / legacy
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old\n", encoding="utf-8")
    (repo / ".codestable/hooks/custom.json").write_text("keep\n", encoding="utf-8")
    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add obsolete runtime")
    source = tmp_path / "source-skill"
    for directory in ["gates", "tools", "references"]:
        (source / directory).mkdir(parents=True)
    (source / "gates/roadmap-goal-gates.yaml").write_text("version: 2\n", encoding="utf-8")
    for tool in [
        "validate-yaml.py",
        "search-yaml.py",
        "codestable-doctor.py",
        "build-review-packet.py",
        "codestable-workflow-next.py",
        "codestable-scope-gate.py",
        "codestable-dod-contract-gate.py",
        "codestable-dod-runner.py",
        "codestable-evidence-pack.py",
        "codestable-goal-consistency-gate.py",
    ]:
        (source / f"tools/{tool}").write_text(f"{tool}\n", encoding="utf-8")
    (source / "tools/codestable-worktree-gate.py").write_text("should not copy\n", encoding="utf-8")
    (source / "references/tools.md").write_text("new tools\n", encoding="utf-8")
    (source / "references/worktree-conventions.md").write_text("should not copy\n", encoding="utf-8")
    (source / "codestable.gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (source / ".codex-plugin").mkdir()
    (source / ".codex-plugin/plugin.json").write_text('{"version": "1.1.0"}\n', encoding="utf-8")

    result = runtime_tool.sync_runtime(repo, source)

    assert result["ok"]
    assert not (repo / ".codestable/tools/codestable-workflow-next.py").exists()
    assert (repo / ".codestable/tools/codestable-worktree-gate.py").read_text(encoding="utf-8") == "old\n"
    assert (repo / ".codestable/tools/validate-implementation-review.py").read_text(encoding="utf-8") == "old\n"
    assert (repo / ".codestable/reference/worktree-conventions.md").read_text(encoding="utf-8") == "old\n"
    assert (repo / ".codestable/reference/branch-guard-hooks.md").read_text(encoding="utf-8") == "old\n"
    assert (repo / ".codestable/hooks/hooks.codex.json").read_text(encoding="utf-8") == "old\n"
    assert (repo / ".codestable/hooks/custom.json").read_text(encoding="utf-8") == "keep\n"
    manifest = json.loads((repo / ".codestable/runtime-manifest.json").read_text(encoding="utf-8"))
    assert manifest["plugin_version"] == "1.1.0"
    assert manifest["tool_runtime"] == "skill-global"
    assert ".codestable/tools" not in manifest["managed_paths"]


def test_standalone_runtime_sync_discovers_packaged_version(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    standalone = tmp_path / "standalone/cs-onboard"
    shutil.copytree(ROOT / "plugins/codestable/skills/cs-onboard", standalone)

    result = runtime_tool.sync_runtime(repo, standalone)

    assert result["ok"] is True
    assert result["plugin_version"] == CURRENT_PLUGIN_VERSION
    manifest = json.loads((repo / ".codestable/runtime-manifest.json").read_text(encoding="utf-8"))
    assert manifest["plugin_version"] == CURRENT_PLUGIN_VERSION
    assert manifest["runtime_version"] == CURRENT_PLUGIN_VERSION


def test_runtime_sync_without_version_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "standalone/cs-onboard"
    shutil.copytree(ROOT / "plugins/codestable/skills/cs-onboard", source)
    version_file = source / "VERSION"
    if version_file.exists():
        version_file.unlink()
    before = (repo / ".codestable/runtime-manifest.json").read_text(encoding="utf-8")

    for force in (False, True):
        result = runtime_tool.sync_runtime(repo, source, force=force)

        assert result["ok"] is False
        assert result["status"] == "version-unavailable"
        assert (repo / ".codestable/runtime-manifest.json").read_text(encoding="utf-8") == before


def test_runtime_sync_refuses_dirty_managed_paths_without_force(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "source-skill"
    (source / "references").mkdir(parents=True)
    (source / "references/tools.md").write_text("new\n", encoding="utf-8")
    (repo / ".codestable/reference/tools.md").write_text("local edit\n", encoding="utf-8")

    result = runtime_tool.sync_runtime(repo, source)

    assert not result["ok"]
    assert result["status"] == "managed-paths-dirty"
    assert ".codestable/reference/tools.md" in result["dirty_paths"]


def test_runtime_sync_does_not_block_on_dirty_preserved_legacy_assets(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    source = tmp_path / "source-skill"
    for directory in ["gates", "tools", "references"]:
        (source / directory).mkdir(parents=True)
    (source / "gates/roadmap-goal-gates.yaml").write_text("version: 2\n", encoding="utf-8")
    (source / "references/tools.md").write_text("new tools\n", encoding="utf-8")
    for tool in [
        "validate-yaml.py",
        "search-yaml.py",
        "codestable-doctor.py",
        "build-review-packet.py",
        "codestable-workflow-next.py",
        "codestable-scope-gate.py",
        "codestable-dod-contract-gate.py",
        "codestable-dod-runner.py",
        "codestable-evidence-pack.py",
        "codestable-goal-consistency-gate.py",
    ]:
        (source / f"tools/{tool}").write_text(f"{tool}\n", encoding="utf-8")

    for legacy in [
        ".codestable/reference/worktree-conventions.md",
        ".codestable/reference/branch-guard-hooks.md",
        ".codestable/hooks/hooks.codex.json",
    ]:
        target = repo / legacy
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("dirty legacy edit\n", encoding="utf-8")

    result = runtime_tool.sync_runtime(repo, source, plugin_version="1.1.0")

    assert result["ok"]
    assert (repo / ".codestable/reference/worktree-conventions.md").read_text(encoding="utf-8") == "dirty legacy edit\n"


def test_docs_only_dirty_state_is_planning_safe(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs/plan.md").write_text("plan\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "planning-safe"
    assert report["dirty_buckets"] == {"docs": ["docs/plan.md"]}
    assert report["implementation_changes"] == []


def test_dirty_implementation_is_reported_without_worktree_block(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "implementation-active"
    assert report["implementation_changes"] == ["src/app.py"]
    assert report["findings"] == []


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
