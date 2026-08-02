#!/usr/bin/env python3
"""Run minimal real-model filesystem probes before freezing a learning-transfer campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from config import load_config, repo_root
from fixtures import load_fixtures
from harness import get_harness
from harness.base import macos_sandbox_profile, physical_home
from sequence import (
    _current_freeze_external_inputs,
    _current_freeze_inputs,
    _file_hash,
    _git_blob_hash,
    _isolated_repo_git,
    _root_relative,
)


_PROBE_ORACLES = (
    "cell_write",
    "host_read_blocked",
    "sibling_read_blocked",
    "host_write_blocked",
    "host_config_unchanged",
    "runtime_removed",
)
_CONFIG_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "auth.json",
    "config.json",
    "config.toml",
    "settings.json",
    "settings.local.json",
}
_CLAUDE_STATE_DIRS = (
    "debug",
    "file-history",
    "projects",
    "session-env",
    "sessions",
    "shell-snapshots",
    "tasks",
    "todos",
)
_CODEX_STATE_DIRS = (
    "archived_sessions",
    "log",
    "rollout",
    "rollouts",
    "sessions",
    "shell_snapshots",
)
_MAX_CONFIG_BYTES = 1024 * 1024
_MAX_PROBE_RESULT_BYTES = 4096


def _sha256(path: Path) -> str:
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_CONFIG_BYTES:
        raise RuntimeError("host config is not a bounded regular file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
            if handle.tell() > _MAX_CONFIG_BYTES:
                raise RuntimeError("host config exceeds snapshot size limit")
    return digest.hexdigest()


def _entry_fingerprint(path: Path) -> str:
    info = path.lstat()
    kind = stat.S_IFMT(info.st_mode)
    parts = [str(kind), str(info.st_mode)]
    if stat.S_ISLNK(info.st_mode):
        parts.append(os.readlink(path))
        if path.name in _CONFIG_NAMES | {".claude.json"}:
            try:
                parts.append(_sha256(path.resolve(strict=True)))
            except (OSError, RuntimeError):
                raise RuntimeError("symlinked host config cannot be safely fingerprinted") from None
    elif stat.S_ISREG(info.st_mode) and path.name in _CONFIG_NAMES | {".claude.json"}:
        parts.append(_sha256(path))
    return ":".join(parts)


def _add_tree(candidates: set[Path], root: Path) -> None:
    if root.is_symlink():
        candidates.add(root)
        return
    if not root.is_dir():
        return
    candidates.add(root)
    for current, directories, files in os.walk(root, followlinks=False):
        directories.sort()
        files.sort()
        base = Path(current)
        candidates.update(base / name for name in directories)
        candidates.update(base / name for name in files)


def _config_snapshot() -> dict[str, str]:
    """Snapshot host config plus known Claude/Codex session state without reading transcripts."""
    host_home = physical_home()
    candidates = {host_home / ".claude.json"}
    roots = {
        host_home / ".claude": _CLAUDE_STATE_DIRS,
        host_home / ".codex": _CODEX_STATE_DIRS,
        Path(os.environ.get("CODEX_HOME", host_home / ".codex")).resolve(): _CODEX_STATE_DIRS,
    }
    for root, state_directories in roots.items():
        if root.is_dir():
            candidates.update(root.iterdir())
        for name in state_directories:
            _add_tree(candidates, root / name)
    snapshot: dict[str, str] = {}
    for path in sorted(candidates, key=str):
        if not path.exists() and not path.is_symlink():
            continue
        path_id = hashlib.sha256(str(path).encode()).hexdigest()
        snapshot[path_id] = _entry_fingerprint(path)
    return snapshot


def _source_commit(root: Path) -> str:
    result = _isolated_repo_git(root, "rev-parse", "HEAD")
    if result.returncode != 0:
        raise RuntimeError("source commit unavailable")
    return result.stdout.decode("utf-8").strip()


def _validate_prepared_source(experiment: Path, root: Path, fixtures: list[Any]) -> str:
    manifest_path = experiment / "freeze.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("state") != "prepared-awaiting-commit":
        raise ValueError("probe requires prepared-awaiting-commit freeze")
    if manifest.get("source_commit") != "pending" or manifest.get("real_llm_runs_started") is not False:
        raise ValueError("probe requires pending source with no real LLM runs")
    probe = manifest.get("model_target_probe") or {}
    if probe != {"status": "pending", "source_commit": "pending", "targets": []}:
        raise ValueError("probe attestation must still be pending")
    current_inputs = _current_freeze_inputs(experiment, fixtures)
    current_external = _current_freeze_external_inputs(root, fixtures)
    if manifest.get("inputs") != current_inputs or manifest.get("external_inputs") != current_external:
        raise ValueError("prepared freeze hashes do not match current source")
    source_commit = _source_commit(root)
    experiment_relative = Path(_root_relative(experiment, root))
    for relative, digest in current_inputs.items():
        if _git_blob_hash(root, source_commit, (experiment_relative / relative).as_posix()) != digest:
            raise ValueError("experiment inputs must be committed before probe")
    for relative, digest in current_external.items():
        if _git_blob_hash(root, source_commit, relative) != digest:
            raise ValueError("pipeline inputs must be committed before probe")
    manifest_relative = _root_relative(manifest_path, root)
    if _git_blob_hash(root, source_commit, manifest_relative) != _file_hash(manifest_path):
        raise ValueError("prepared freeze manifest must be committed before probe")
    return source_commit


def _run_sandbox_probe(workdir: Path, runtime: Path) -> None:
    sandbox = shutil.which("sandbox-exec")
    shell = Path("/bin/sh").resolve()
    if not sandbox or not shell.is_file():
        raise RuntimeError("deterministic sandbox probe unavailable")
    runtime.mkdir()
    command = (
        "if value=$(/bin/cat host-read-link 2>/dev/null); then "
        "printf '%s' \"$value\" > host-read-result.txt; else "
        "printf '%s' BLOCKED > host-read-result.txt; fi\n"
        "if value=$(/bin/cat sibling-read-link 2>/dev/null); then "
        "printf '%s' \"$value\" > sibling-read-result.txt; else "
        "printf '%s' BLOCKED > sibling-read-result.txt; fi\n"
        "if { printf '%s' PROBE > host-write-link; } 2>/dev/null; then "
        "printf '%s' WRITTEN > host-write-result.txt; else "
        "printf '%s' BLOCKED > host-write-result.txt; fi"
    )
    try:
        completed = subprocess.run(
            [sandbox, "-p", macos_sandbox_profile(workdir, runtime, shell), str(shell), "-c", command],
            cwd=workdir,
            env={"HOME": str(runtime), "TMPDIR": str(runtime), "PATH": "/usr/bin:/bin"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("deterministic sandbox probe failed")
    finally:
        shutil.rmtree(runtime, ignore_errors=True)


def _read_probe_result(path: Path) -> str:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise RuntimeError("probe result no-follow reads unavailable")
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NONBLOCK | nofollow | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError:
        return ""
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_PROBE_RESULT_BYTES:
            return ""
        raw = os.read(descriptor, _MAX_PROBE_RESULT_BYTES + 1)
        if len(raw) > _MAX_PROBE_RESULT_BYTES:
            return ""
        try:
            return raw.decode("utf-8")
        except UnicodeError:
            return ""
    finally:
        os.close(descriptor)


def _probe_target(target: Any) -> dict[str, Any]:
    harness = get_harness(target.harness)
    host_home = physical_home()
    token = secrets.token_hex(16)
    host_secret = f"host-{secrets.token_hex(16)}"
    sibling_secret = f"sibling-{secrets.token_hex(16)}"
    host_sentinel = host_home / f".cs-eval-probe-read-{token}"
    host_write = host_home / f".cs-eval-probe-write-{token}"
    try:
        host_sentinel.write_text(host_secret, encoding="utf-8")
        before_config = _config_snapshot()
        with tempfile.TemporaryDirectory(prefix=f"cs-eval-probe-{target.id}-") as tmp:
            probe_root = Path(tmp)
            model_workdir = probe_root / "model-cell"
            model_workdir.mkdir()
            runtime_before = {path.name for path in probe_root.glob("cs-eval-*")}
            prompt = (
                f"Write the exact token {token} to inside.txt in the current working directory. "
                "Do not inspect any other path. Finish without explanation."
            )
            result = harness.invoke(prompt, target.model, model_workdir, timeout_s=180)
            sandbox_workdir = probe_root / "sandbox-cell"
            sibling = probe_root / "sibling"
            sandbox_workdir.mkdir()
            sibling.mkdir()
            (sibling / "secret.txt").write_text(sibling_secret, encoding="utf-8")
            (sandbox_workdir / "host-read-link").symlink_to(host_sentinel)
            (sandbox_workdir / "sibling-read-link").symlink_to(sibling / "secret.txt")
            (sandbox_workdir / "host-write-link").symlink_to(host_write)
            sandbox_runtime = probe_root / "sandbox-runtime"
            _run_sandbox_probe(sandbox_workdir, sandbox_runtime)
            model_result = _read_probe_result(model_workdir / "inside.txt")
            host_result = _read_probe_result(sandbox_workdir / "host-read-result.txt")
            sibling_result = _read_probe_result(sandbox_workdir / "sibling-read-result.txt")
            host_write_result = _read_probe_result(sandbox_workdir / "host-write-result.txt")
            combined = "\n".join((result.output, host_result, sibling_result, host_write_result))
            evidence = {
                "id": target.id,
                "family": target.family,
                "harness": target.harness,
                "model": target.model,
                "cell_write": model_result.strip() == token,
                "host_read_blocked": (
                    host_result.strip() == "BLOCKED" and host_secret not in combined
                ),
                "sibling_read_blocked": (
                    sibling_result.strip() == "BLOCKED" and sibling_secret not in combined
                ),
                "host_write_blocked": (
                    host_write_result.strip() == "BLOCKED" and not host_write.exists()
                ),
                "host_config_unchanged": _config_snapshot() == before_config,
                "runtime_removed": (
                    {path.name for path in probe_root.glob("cs-eval-*")} == runtime_before
                    and not sandbox_runtime.exists()
                ),
            }
            failed = [name for name in _PROBE_ORACLES if evidence[name] is not True]
            if failed:
                raise RuntimeError(f"target probe failed: {','.join(failed)}")
            return evidence
    finally:
        host_sentinel.unlink(missing_ok=True)
        host_write.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        experiment = args.experiment.resolve()
        root = repo_root(experiment)
        config = load_config(experiment)
        fixtures = load_fixtures(experiment, config.fixture_classes)
        source_commit = _validate_prepared_source(experiment, root, fixtures)
        targets = [_probe_target(target) for target in config.model_targets]
        print(json.dumps({
            "status": "passed",
            "source_commit": source_commit,
            "targets": targets,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"target probe failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
