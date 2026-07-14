#!/usr/bin/env python3
"""Shared CodeStable runtime asset checks and sync helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


MANIFEST_PATH = ".codestable/runtime-manifest.json"
MANAGED_PATHS = [
    ".codestable/gates",
    ".codestable/reference",
    ".codestable/.gitignore",
    MANIFEST_PATH,
]
RUNTIME_IGNORE_PATTERNS = [
    "worktree-conventions.md",
    "branch-guard-hooks.md",
]
PRESERVED_LEGACY_RUNTIME_PATHS = {
    ".codestable/reference/worktree-conventions.md",
    ".codestable/reference/branch-guard-hooks.md",
    ".codestable/hooks/hooks.codex.json",
}
REPO_RUNTIME_CAPABILITIES: dict[str, list[str]] = {
    "base": [
        ".codestable/attention.md",
        ".codestable/reference/execution-conventions.md",
        ".codestable/reference/shared-conventions.md",
        ".codestable/reference/agent-conventions.md",
        ".codestable/reference/tools.md",
        MANIFEST_PATH,
    ],
    "goal-gates": [
        ".codestable/gates/roadmap-goal-gates.yaml",
    ],
}
SKILL_TOOL_CAPABILITIES: dict[str, list[str]] = {
    "base": [
        "tools/validate-yaml.py",
        "tools/search-yaml.py",
        "tools/codestable-doctor.py",
        "tools/build-review-packet.py",
    ],
    "workflow-next": [
        "tools/codestable-workflow-next.py",
    ],
    "goal-gates": [
        "tools/codestable-scope-gate.py",
        "tools/codestable-dod-contract-gate.py",
        "tools/codestable-dod-runner.py",
        "tools/codestable-evidence-pack.py",
        "tools/codestable-goal-consistency-gate.py",
    ],
}


def discover_plugin_version(source_skill_dir: Path | None) -> str | None:
    if source_skill_dir is None:
        return None
    current = source_skill_dir.resolve()
    for directory in [current, *current.parents]:
        version_file = directory / "VERSION"
        if version_file.is_file():
            version = version_file.read_text(encoding="utf-8").strip()
            if version:
                return version
        for rel in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            plugin_json = directory / rel
            if plugin_json.is_file():
                try:
                    data = json.loads(plugin_json.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                version = data.get("version") if isinstance(data, dict) else None
                if isinstance(version, str) and version:
                    return version
    return None


def read_manifest(root: Path) -> dict[str, Any] | None:
    path = root / MANIFEST_PATH
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def git_dirty_managed_paths(root: Path) -> list[str]:
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *MANAGED_PATHS],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if line:
            path = line[3:].strip('"')
            if path in PRESERVED_LEGACY_RUNTIME_PATHS:
                continue
            dirty.append(path)
    return dirty


def runtime_health(root: Path, source_skill_dir: Path | None = None, plugin_version: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    expected_version = plugin_version or discover_plugin_version(source_skill_dir)
    manifest = read_manifest(root)
    capabilities: dict[str, Any] = {}
    missing_all: list[str] = []
    source_skill_dir = source_skill_dir.resolve() if source_skill_dir else None
    for name in sorted(set(REPO_RUNTIME_CAPABILITIES) | set(SKILL_TOOL_CAPABILITIES)):
        repo_paths = REPO_RUNTIME_CAPABILITIES.get(name, [])
        skill_paths = SKILL_TOOL_CAPABILITIES.get(name, [])
        missing_repo = [path for path in repo_paths if not (root / path).exists()]
        missing_skill = [path for path in skill_paths if not source_skill_dir or not (source_skill_dir / path).exists()]
        capabilities[name] = {
            "ok": not missing_repo and not missing_skill,
            "required_paths": repo_paths + skill_paths,
            "repo_paths": repo_paths,
            "skill_tool_paths": skill_paths,
            "missing": missing_repo + missing_skill,
            "missing_repo": missing_repo,
            "missing_skill_tools": missing_skill,
        }
        missing_all.extend(missing_repo + missing_skill)

    installed_version = manifest.get("plugin_version") if manifest else None
    if not (root / ".codestable").exists():
        status = "not-onboarded"
        hint = "Run `cs-onboard` to create the CodeStable skeleton."
    elif ".codestable/attention.md" in missing_all:
        status = "onboard-incomplete"
        hint = "Run `cs-onboard` to complete the skeleton; runtime sync does not create attention.md."
    elif missing_all:
        status = "runtime-incomplete"
        hint = "Run runtime sync or `cs-onboard --mode refresh-runtime` to refresh repo-local assets; missing skill tools require reinstalling/updating CodeStable."
    elif expected_version is None:
        status = "version-unavailable"
        hint = "Reinstall or update cs-onboard; the installed skill package is missing CodeStable version metadata."
    elif installed_version != expected_version:
        status = "version-mismatch"
        hint = "Run runtime sync to refresh .codestable runtime assets for the installed CodeStable plugin."
    else:
        status = "ok"
        hint = "runtime assets ok"

    return {
        "status": status,
        "ok": status == "ok",
        "hint": hint,
        "manifest": manifest,
        "installed_plugin_version": installed_version,
        "expected_plugin_version": expected_version,
        "capabilities": capabilities,
        "missing": missing_all,
        "tool_runtime": "skill-global",
    }


def write_manifest(root: Path, plugin_version: str) -> None:
    path = root / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "plugin": "codestable",
        "plugin_version": plugin_version,
        "runtime_version": plugin_version,
        "tool_runtime": "skill-global",
        "managed_paths": MANAGED_PATHS,
        "updated_by": "codestable-runtime-sync",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_runtime(root: Path, source_skill_dir: Path, plugin_version: str | None = None, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    source_skill_dir = source_skill_dir.resolve()
    version = plugin_version or discover_plugin_version(source_skill_dir)
    if not (root / ".codestable/attention.md").is_file():
        return {
            "ok": False,
            "status": "onboard-incomplete",
            "hint": "Run `cs-onboard` first; runtime sync does not create attention.md.",
        }
    dirty = git_dirty_managed_paths(root)
    if dirty and not force:
        return {
            "ok": False,
            "status": "managed-paths-dirty",
            "dirty_paths": dirty,
            "hint": "Commit, stash, or explicitly allow overwriting managed runtime assets before sync.",
        }
    if version is None:
        return {
            "ok": False,
            "status": "version-unavailable",
            "hint": "Reinstall or update cs-onboard; the installed skill package is missing CodeStable version metadata.",
        }

    copies = [
        ("gates", ".codestable/gates"),
        ("references", ".codestable/reference"),
    ]
    for source_rel, target_rel in copies:
        source = source_skill_dir / source_rel
        target = root / target_rel
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", *RUNTIME_IGNORE_PATTERNS),
            )
    gitignore = source_skill_dir / "codestable.gitignore"
    if gitignore.is_file():
        shutil.copy2(gitignore, root / ".codestable/.gitignore")
    write_manifest(root, version)
    health = runtime_health(root, source_skill_dir=source_skill_dir, plugin_version=version)
    return {"ok": health["ok"], "status": health["status"], "plugin_version": version, "health": health}
