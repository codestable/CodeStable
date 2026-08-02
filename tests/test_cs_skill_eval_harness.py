"""eval-cs-skill harness 的宿主隔离契约。"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
sys.path.insert(0, str(SCRIPTS))


def _write_private_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def test_target_probe_requires_explicit_blocked_markers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets
    from _model import ExecutionTarget, HarnessResult

    host_home = tmp_path / "host-home"
    host_home.mkdir()

    class SkippingHarness:
        name = "skipping"

        def invoke(self, prompt, model, workdir, timeout_s):
            assert timeout_s == 180
            token = re.search(r"exact token ([0-9a-f]+)", prompt).group(1)
            (workdir / "inside.txt").write_text(token, encoding="utf-8")
            return HarnessResult(
                output="done",
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.setattr(probe_targets, "get_harness", lambda _name: SkippingHarness())
    monkeypatch.setattr(probe_targets, "_run_sandbox_probe", lambda _workdir, _runtime: None)
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="skipping",
        model="mock-model",
    )

    with pytest.raises(RuntimeError, match="host_read_blocked,sibling_read_blocked,host_write_blocked"):
        probe_targets._probe_target(target)

    assert not list(host_home.glob(".cs-eval-probe-*"))


def test_target_probe_separates_model_write_from_deterministic_sandbox_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets
    from _model import ExecutionTarget, HarnessResult

    host_home = tmp_path / "host-home"
    host_home.mkdir()

    model_workdirs: list[Path] = []

    class CellWriteHarness:
        name = "cell-write"

        def invoke(self, prompt, model, workdir, timeout_s):
            model_workdirs.append(workdir)
            token = re.search(r"exact token ([0-9a-f]+)", prompt).group(1)
            assert "inside.txt" in prompt
            assert "host-read-link" not in prompt
            assert "sibling-read-link" not in prompt
            assert "host-write-link" not in prompt
            (workdir / "inside.txt").write_text(token, encoding="utf-8")
            return HarnessResult(
                output="done",
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    sandbox_calls = []

    def run_sandbox_probe(workdir, runtime):
        sandbox_calls.append((workdir, runtime))
        (workdir / "host-read-result.txt").write_text("BLOCKED", encoding="utf-8")
        (workdir / "sibling-read-result.txt").write_text("BLOCKED", encoding="utf-8")
        (workdir / "host-write-result.txt").write_text("BLOCKED", encoding="utf-8")

    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.setattr(probe_targets, "get_harness", lambda _name: CellWriteHarness())
    monkeypatch.setattr(probe_targets, "_run_sandbox_probe", run_sandbox_probe)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="cell-write",
        model="mock-model",
    )

    evidence = probe_targets._probe_target(target)

    assert all(evidence[name] is True for name in probe_targets._PROBE_ORACLES)
    assert len(sandbox_calls) == 1
    assert sandbox_calls[0][0].name == "sandbox-cell"
    assert sandbox_calls[0][0] not in model_workdirs
    assert sandbox_calls[0][1].name == "sandbox-runtime"
    assert not list(host_home.glob(".cs-eval-probe-*"))


def test_target_probe_rejects_a_symlinked_model_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets
    from _model import ExecutionTarget, HarnessResult

    host_home = tmp_path / "host-home"
    host_home.mkdir()
    external_output = tmp_path / "external-output.txt"

    class SymlinkHarness:
        name = "symlink-output"

        def invoke(self, prompt, model, workdir, timeout_s):
            token = re.search(r"exact token ([0-9a-f]+)", prompt).group(1)
            external_output.write_text(token, encoding="utf-8")
            (workdir / "inside.txt").symlink_to(external_output)
            return HarnessResult(output="done", model=model, harness=self.name, wall_ms=1)

    def run_sandbox_probe(workdir, _runtime):
        for name in ("host-read-result.txt", "sibling-read-result.txt", "host-write-result.txt"):
            (workdir / name).write_text("BLOCKED", encoding="utf-8")

    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.setattr(probe_targets, "get_harness", lambda _name: SymlinkHarness())
    monkeypatch.setattr(probe_targets, "_run_sandbox_probe", run_sandbox_probe)
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="symlink-output",
        model="mock-model",
    )

    with pytest.raises(RuntimeError, match="cell_write"):
        probe_targets._probe_target(target)


def test_target_probe_does_not_reuse_model_controlled_result_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets
    from _model import ExecutionTarget, HarnessResult

    host_home = tmp_path / "host-home"
    host_home.mkdir()
    external_results = [tmp_path / f"external-{index}.txt" for index in range(3)]
    for path in external_results:
        path.write_text("unchanged", encoding="utf-8")

    class ResultSymlinkHarness:
        name = "result-symlinks"

        def invoke(self, prompt, model, workdir, timeout_s):
            token = re.search(r"exact token ([0-9a-f]+)", prompt).group(1)
            (workdir / "inside.txt").write_text(token, encoding="utf-8")
            for name, target in zip(
                ("host-read-result.txt", "sibling-read-result.txt", "host-write-result.txt"),
                external_results,
                strict=True,
            ):
                (workdir / name).symlink_to(target)
            return HarnessResult(output="done", model=model, harness=self.name, wall_ms=1)

    def run_sandbox_probe(workdir, _runtime):
        for name in ("host-read-result.txt", "sibling-read-result.txt", "host-write-result.txt"):
            (workdir / name).write_text("BLOCKED", encoding="utf-8")

    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.setattr(probe_targets, "get_harness", lambda _name: ResultSymlinkHarness())
    monkeypatch.setattr(probe_targets, "_run_sandbox_probe", run_sandbox_probe)
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="result-symlinks",
        model="mock-model",
    )

    evidence = probe_targets._probe_target(target)

    assert all(evidence[name] is True for name in probe_targets._PROBE_ORACLES)
    assert [path.read_text(encoding="utf-8") for path in external_results] == ["unchanged"] * 3


def test_target_probe_removes_host_sentinel_when_initial_snapshot_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets
    from _model import ExecutionTarget

    host_home = tmp_path / "host-home"
    host_home.mkdir()
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.setattr(probe_targets, "get_harness", lambda _name: object())
    monkeypatch.setattr(
        probe_targets,
        "_config_snapshot",
        lambda: (_ for _ in ()).throw(OSError("snapshot failed")),
    )
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="failing-snapshot",
        model="mock-model",
    )

    with pytest.raises(OSError, match="snapshot failed"):
        probe_targets._probe_target(target)

    assert not list(host_home.glob(".cs-eval-probe-*"))


def test_target_probe_snapshots_the_host_claude_root_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets

    host_home = tmp_path / "host-home"
    host_home.mkdir()
    root_config = host_home / ".claude.json"
    root_config.write_text('{"version":1}\n', encoding="utf-8")
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)

    before = probe_targets._config_snapshot()
    root_config.write_text('{"version":2}\n', encoding="utf-8")

    assert probe_targets._config_snapshot() != before


@pytest.mark.parametrize("symlink_root", [False, True], ids=("file-symlink", "root-symlink"))
def test_target_probe_hashes_symlinked_host_config_targets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    symlink_root: bool,
) -> None:
    import probe_targets

    host_home = tmp_path / "host-home"
    host_home.mkdir()
    real_claude = tmp_path / "real-claude"
    real_claude.mkdir()
    target = real_claude / "settings.json"
    target.write_text('{"version":1}\n', encoding="utf-8")
    if symlink_root:
        (host_home / ".claude").symlink_to(real_claude, target_is_directory=True)
    else:
        logical_claude = host_home / ".claude"
        logical_claude.mkdir()
        (logical_claude / "settings.json").symlink_to(target)
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)

    before = probe_targets._config_snapshot()
    target.write_text('{"version":2}\n', encoding="utf-8")

    assert probe_targets._config_snapshot() != before


@pytest.mark.parametrize(
    "relative",
    [
        Path(".codex/state_5.sqlite"),
        Path(".codex/sessions/2026/run.jsonl"),
        Path(".codex/rollout/run.jsonl"),
        Path(".claude/projects/repo/session.jsonl"),
    ],
)
def test_target_probe_ignores_existing_session_activity_but_detects_new_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    relative: Path,
) -> None:
    import probe_targets

    host_home = tmp_path / "host-home"
    state_file = host_home / relative
    state_file.parent.mkdir(parents=True)
    state_file.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.delenv("CODEX_HOME", raising=False)

    before = probe_targets._config_snapshot()
    state_file.write_text("after!\n", encoding="utf-8")

    assert probe_targets._config_snapshot() == before

    new_state = state_file.with_name(f"new-{state_file.name}")
    new_state.write_text("new state\n", encoding="utf-8")

    assert probe_targets._config_snapshot() != before


@pytest.mark.parametrize(
    "relative",
    [Path(".claude/CLAUDE.md"), Path(".codex/AGENTS.md")],
)
def test_target_probe_hashes_stable_host_instruction_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    relative: Path,
) -> None:
    import probe_targets

    host_home = tmp_path / "host-home"
    instruction = host_home / relative
    instruction.parent.mkdir(parents=True)
    instruction.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.delenv("CODEX_HOME", raising=False)

    before = probe_targets._config_snapshot()
    instruction.write_text("after!\n", encoding="utf-8")

    assert probe_targets._config_snapshot() != before


def test_target_probe_detects_new_unknown_top_level_state_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets

    host_home = tmp_path / "host-home"
    codex_home = host_home / ".codex"
    codex_home.mkdir(parents=True)
    monkeypatch.setattr(probe_targets, "physical_home", lambda: host_home)
    monkeypatch.delenv("CODEX_HOME", raising=False)

    before = probe_targets._config_snapshot()
    (codex_home / "new-persistent-state").mkdir()

    assert probe_targets._config_snapshot() != before


def test_probe_result_read_is_nonblocking(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets

    observed: dict[str, int] = {}

    def fake_open(_path, flags):
        observed["flags"] = flags
        raise FileNotFoundError

    monkeypatch.setattr(probe_targets.os, "open", fake_open)

    assert probe_targets._read_probe_result(tmp_path / "inside.txt") == ""
    assert observed["flags"] & os.O_NONBLOCK


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt 专用")
def test_deterministic_sandbox_probe_does_not_treat_eof_as_blocked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import probe_targets

    workdir = tmp_path / "cell"
    workdir.mkdir()
    runtime = tmp_path / "sandbox-runtime"
    host_secret = tmp_path / "host-secret.txt"
    sibling_secret = tmp_path / "sibling-secret.txt"
    host_write = tmp_path / "host-write.txt"
    host_secret.write_text("host-secret", encoding="utf-8")
    sibling_secret.write_text("sibling-secret", encoding="utf-8")
    (workdir / "host-read-link").symlink_to(host_secret)
    (workdir / "sibling-read-link").symlink_to(sibling_secret)
    (workdir / "host-write-link").symlink_to(host_write)
    monkeypatch.setattr(
        probe_targets,
        "macos_sandbox_profile",
        lambda *_args: "(version 1)\n(allow default)",
    )

    probe_targets._run_sandbox_probe(workdir, runtime)

    assert (workdir / "host-read-result.txt").read_text(encoding="utf-8") == "host-secret"
    assert (workdir / "sibling-read-result.txt").read_text(encoding="utf-8") == "sibling-secret"
    assert (workdir / "host-write-result.txt").read_text(encoding="utf-8") == "WRITTEN"
    assert host_write.read_text(encoding="utf-8") == "PROBE"


def test_sandbox_profile_rejects_control_characters_and_protects_physical_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from harness import base

    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    workdir = tmp_path / "pair/cell"
    runtime = tmp_path / "pair/runtime"
    binary = tmp_path / "binary"
    for path in (workdir, runtime):
        path.mkdir(parents=True)
    binary.touch()

    profile = base.macos_sandbox_profile(workdir, runtime, binary)

    assert str(base.physical_home()) in profile
    assert str(fake_home.resolve()) in profile
    assert "(deny process-info*)" in profile
    assert "(allow process-info* (target self))" in profile
    with pytest.raises(ValueError, match="NUL 或换行"):
        base.macos_sandbox_profile(tmp_path / "bad\npath", runtime, binary)


@pytest.mark.real_cli
@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt 专用")
def test_claude_seatbelt_runs_cli_and_confines_file_access(tmp_path: Path) -> None:
    import harness.adapter_claude as adapter_claude

    sandbox = shutil.which("sandbox-exec")
    binary = shutil.which("claude")
    if not sandbox or not binary:
        pytest.skip("需要本机 sandbox-exec 与 claude CLI")

    workdir = tmp_path / "cell"
    runtime = tmp_path / "runtime"
    home = runtime / "home"
    runtime_tmp = runtime / "tmp"
    for path in (workdir, runtime, home, runtime_tmp):
        path.mkdir()
    secret = ROOT / "AGENTS.md"
    secret_marker = "# Agent Rules"

    resolved_binary = Path(binary).resolve()
    profile = adapter_claude._sandbox_profile(workdir, runtime, resolved_binary)
    sandbox_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "TMPDIR": str(runtime_tmp),
    }

    version = subprocess.run(
        [sandbox, "-p", profile, str(resolved_binary), "--version"],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert version.returncode == 0, version.stderr

    inside = subprocess.run(
        [
            sandbox,
            "-p",
            profile,
            "/bin/sh",
            "-c",
            'printf cell > "$1" && test "$(cat "$1")" = cell',
            "sh",
            str(workdir / "inside.txt"),
        ],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert inside.returncode == 0, inside.stderr

    secret_link = workdir / "host-secret-link"
    secret_link.symlink_to(secret)
    outside_read = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'cat "$1"', "sh", str(secret_link)],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert outside_read.returncode != 0
    assert secret_marker not in outside_read.stdout

    sibling_secret = tmp_path / "sibling-secret.txt"
    sibling_secret.write_text("sibling-must-not-cross\n", encoding="utf-8")
    sibling_read = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'cat "$1"', "sh", str(sibling_secret)],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert sibling_read.returncode != 0
    assert "sibling-must-not-cross" not in sibling_read.stdout

    forbidden = ROOT / f".cs-eval-forbidden-{os.getpid()}-{tmp_path.name}"
    assert not forbidden.exists()
    forbidden_link = workdir / "host-write-link"
    forbidden_link.symlink_to(forbidden)
    try:
        outside_write = subprocess.run(
            [sandbox, "-p", profile, "/bin/sh", "-c", ': > "$1"', "sh", str(forbidden_link)],
            cwd=workdir,
            env=sandbox_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert outside_write.returncode != 0
        assert not forbidden.exists()
    finally:
        forbidden.unlink(missing_ok=True)


@pytest.mark.real_cli
@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt 专用")
def test_codex_seatbelt_runs_cli_and_confines_file_access(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    sandbox = shutil.which("sandbox-exec")
    binary = shutil.which("codex")
    if not sandbox or not binary:
        pytest.skip("需要本机 sandbox-exec 与 codex CLI")

    workdir = tmp_path / "cell"
    runtime = tmp_path / "runtime"
    home = runtime / "home"
    runtime_tmp = runtime / "tmp"
    codex_home = runtime / "codex-home"
    for path in (workdir, runtime, home, runtime_tmp, codex_home):
        path.mkdir()
    secret = ROOT / "AGENTS.md"
    secret_marker = "# Agent Rules"

    resolved_binary, binary_read_roots = adapter_codex._native_codex_runtime(binary)
    profile = adapter_codex._sandbox_profile(
        workdir,
        runtime,
        resolved_binary,
        binary_read_roots,
    )
    sandbox_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "CODEX_HOME": str(codex_home),
        "TMPDIR": str(runtime_tmp),
    }

    version = subprocess.run(
        [sandbox, "-p", profile, str(resolved_binary), "--version"],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert version.returncode == 0, version.stderr

    canonical_home = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'cd "$CODEX_HOME" && pwd -P'],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert canonical_home.returncode == 0, canonical_home.stderr
    assert canonical_home.stdout.strip() == str(codex_home.resolve())

    sibling_secret = tmp_path / "sibling-secret.txt"
    sibling_secret.write_text("sibling-must-not-cross\n", encoding="utf-8")
    parent_listing = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'ls "$1"', "sh", str(workdir.parent)],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert parent_listing.returncode != 0
    assert "sibling-secret.txt" not in parent_listing.stdout

    inside = subprocess.run(
        [
            sandbox,
            "-p",
            profile,
            "/bin/sh",
            "-c",
            'printf cell > "$1" && test "$(cat "$1")" = cell',
            "sh",
            str(workdir / "inside.txt"),
        ],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert inside.returncode == 0, inside.stderr

    secret_link = workdir / "host-secret-link"
    secret_link.symlink_to(secret)
    outside_read = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'cat "$1"', "sh", str(secret_link)],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert outside_read.returncode != 0
    assert secret_marker not in outside_read.stdout

    sibling_read = subprocess.run(
        [sandbox, "-p", profile, "/bin/sh", "-c", 'cat "$1"', "sh", str(sibling_secret)],
        cwd=workdir,
        env=sandbox_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert sibling_read.returncode != 0
    assert "sibling-must-not-cross" not in sibling_read.stdout

    forbidden = ROOT / f".cs-eval-codex-forbidden-{os.getpid()}-{tmp_path.name}"
    assert not forbidden.exists()
    forbidden_link = workdir / "host-write-link"
    forbidden_link.symlink_to(forbidden)
    try:
        outside_write = subprocess.run(
            [sandbox, "-p", profile, "/bin/sh", "-c", ': > "$1"', "sh", str(forbidden_link)],
            cwd=workdir,
            env=sandbox_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert outside_write.returncode != 0
        assert not forbidden.exists()
    finally:
        forbidden.unlink(missing_ok=True)


def test_claude_harness_uses_an_ephemeral_provider_scoped_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_claude as adapter_claude

    binary_target = tmp_path / "claude-native"
    binary_target.touch()
    binary_link = tmp_path / "claude"
    binary_link.symlink_to(binary_target)
    workdir = tmp_path / "repo"
    observed: dict[str, object] = {}

    def fake_which(name: str) -> str | None:
        if name == "claude":
            return str(binary_link)
        if name == "sandbox-exec":
            return "/usr/bin/sandbox-exec"
        return None

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"result": "done", "num_turns": 1}),
            stderr="",
        )

    monkeypatch.setattr(adapter_claude.shutil, "which", fake_which)
    monkeypatch.setattr(adapter_claude.subprocess, "run", fake_run)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-must-not-cross")
    monkeypatch.setenv("CODEX_API_KEY", "codex-must-not-cross")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "host-codex"))
    monkeypatch.setenv("PWD", str(ROOT))

    result = adapter_claude.ClaudeHarness().invoke(
        "task",
        "claude-haiku-4-5",
        workdir,
        30,
    )

    assert result.output == "done"
    command = observed["command"]
    assert isinstance(command, list)
    assert command[3] == str(binary_target.resolve())
    assert "--no-session-persistence" in command
    assert "--safe-mode" in command
    assert command[command.index("--permission-mode") + 1] == "bypassPermissions"

    env = observed["env"]
    assert isinstance(env, dict)
    assert env["ANTHROPIC_API_KEY"] == "anthropic-test-token"
    for forbidden_key in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_HOME", "PWD"):
        assert forbidden_key not in env
    for key in ("HOME", "TMPDIR"):
        runtime_path = Path(env[key])
        assert runtime_path.parent.parent == tmp_path
        assert not runtime_path.exists()


def test_claude_harness_imports_only_provider_env_from_host_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_claude as adapter_claude

    host_home = tmp_path / "host-home"
    settings = host_home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({
            "env": {
                "ANTHROPIC_AUTH_TOKEN": "claude-settings-token",
                "ANTHROPIC_BASE_URL": "https://api.example.invalid",
                "OPENAI_API_KEY": "must-not-cross",
                "PROJECT_SECRET": "must-not-cross",
            }
        }),
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"result": "done"}),
            stderr="",
        )

    monkeypatch.setattr(adapter_claude.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(adapter_claude.subprocess, "run", fake_run)
    monkeypatch.setenv("HOME", str(host_home))
    for key in adapter_claude._SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    adapter_claude.ClaudeHarness().invoke(
        "task",
        "claude-haiku-4-5",
        tmp_path / "repo",
        30,
    )

    env = observed["env"]
    assert isinstance(env, dict)
    assert env["ANTHROPIC_AUTH_TOKEN"] == "claude-settings-token"
    assert env["ANTHROPIC_BASE_URL"] == "https://api.example.invalid"
    assert "OPENAI_API_KEY" not in env
    assert "PROJECT_SECRET" not in env
    assert Path(env["HOME"]) != host_home


def test_codex_harness_uses_ephemeral_config_and_provider_scoped_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    workdir = tmp_path / "repo"
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-must-not-cross")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "anthropic-must-not-cross")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "claude-must-not-cross")
    monkeypatch.setenv("HOME", str(tmp_path / "host-home"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "host-codex"))
    monkeypatch.setenv("PWD", str(ROOT))
    proxy_keys = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    )
    for key in proxy_keys:
        monkeypatch.setenv(key, "http://proxy-user:proxy-secret@proxy.invalid:8080")
    monkeypatch.setenv("NO_PROXY", "host.internal")
    monkeypatch.setenv("no_proxy", "host.internal")

    result = adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", workdir, 30)

    assert result.output == "done"
    command = observed["command"]
    assert isinstance(command, list)
    assert command[0] == "/usr/bin/sandbox-exec"
    profile = command[command.index("-p") + 1]
    assert "(deny file-read*" in profile
    assert "(deny file-write*" in profile
    assert "(deny process-info*)" in profile
    assert "(allow process-info* (target self))" in profile
    assert str(workdir.resolve()) in profile
    for flag in ("--ephemeral", "--json", "--ignore-user-config", "--ignore-rules"):
        assert flag in command
    assert command[command.index("--disable") + 1] == "plugins"
    assert command[command.index("--sandbox") + 1] == "danger-full-access"

    env = observed["env"]
    assert isinstance(env, dict)
    assert "CODEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert env["NO_PROXY"] == "127.0.0.1,localhost"
    assert env["no_proxy"] == "127.0.0.1,localhost"
    assert all(key not in env for key in proxy_keys)
    for forbidden_key in (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "PWD",
    ):
        assert forbidden_key not in env
    for key in ("HOME", "CODEX_HOME", "TMPDIR"):
        runtime_path = Path(env[key])
        assert str(runtime_path).startswith(str(tmp_path))
        assert not runtime_path.exists()


def test_codex_harness_canonicalizes_ephemeral_runtime_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    observed: dict[str, str] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.update(dict(kwargs["env"]))
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-token")

    adapter_codex.CodexHarness().invoke(
        "task",
        "gpt-5.6-terra",
        alias_parent / "repo",
        30,
    )

    for key in ("HOME", "CODEX_HOME", "TMPDIR"):
        runtime_path = Path(observed[key])
        assert runtime_path == runtime_path.resolve()


def test_codex_harness_keeps_provider_credentials_out_of_the_tool_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    source_auth = source_home / "auth.json"
    _write_private_text(
        source_auth,
        '{"auth_mode":"apikey","OPENAI_API_KEY":"copied-route-token",'
        '"must_not_cross":"private"}',
    )
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = dict(kwargs["env"])
        isolated_home = Path(env["CODEX_HOME"])
        observed["command"] = command
        observed["env"] = env
        observed["isolated_auth_exists"] = (isolated_home / "auth.json").exists()
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    assert observed["isolated_auth_exists"] is False
    env = observed["env"]
    assert isinstance(env, dict)
    assert "CODEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "copied-route-token" not in "\n".join(observed["command"])
    overrides = [
        observed["command"][index + 1]
        for index, value in enumerate(observed["command"])
        if value == "-c"
    ]
    assert 'shell_environment_policy.inherit="core"' in overrides
    assert Path(env["CODEX_HOME"]) != source_home
    assert not Path(env["CODEX_HOME"]).exists()


@pytest.mark.real_cli
@pytest.mark.skipif(
    sys.platform != "darwin" or not shutil.which("codex") or not shutil.which("sandbox-exec"),
    reason="需要 macOS Seatbelt 与真实 Codex CLI",
)
def test_codex_harness_keeps_provider_credentials_out_of_a_real_tool_call(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    provider_key = "dummy-provider-key-for-local-test"
    ambient_codex_key = "dummy-ambient-codex-key-for-local-test"
    requests: list[dict[str, object]] = []
    sibling_secret = tmp_path / "sibling-secret.txt"
    sibling_secret.write_text("must-not-cross\n", encoding="utf-8")
    tool_command = (
        'if [ "${CODEX_API_KEY+x}" = x ] || [ "${OPENAI_API_KEY+x}" = x ]; then '
        "credential=exposed; else credential=clean; fi; "
        f"if /bin/cat {shlex.quote(str(sibling_secret))} >/dev/null 2>&1; then "
        "sibling=exposed; else sibling=blocked; fi; "
        'printf "%s:%s" "$credential" "$sibling" > env-state.txt'
    )

    def response_events(index: int) -> list[dict[str, object]]:
        response_id = f"resp-{index}"
        output: dict[str, object]
        if index == 1:
            output = {
                "type": "function_call",
                "call_id": "call-env",
                "name": "exec_command",
                "arguments": json.dumps({"cmd": tool_command, "login": False}),
            }
        else:
            output = {
                "type": "message",
                "role": "assistant",
                "id": "msg-1",
                "content": [{"type": "output_text", "text": "done"}],
            }
        return [
            {"type": "response.created", "response": {"id": response_id}},
            {"type": "response.output_item.done", "item": output},
            {
                "type": "response.completed",
                "response": {
                    "id": response_id,
                    "usage": {
                        "input_tokens": 0,
                        "input_tokens_details": None,
                        "output_tokens": 0,
                        "output_tokens_details": None,
                        "total_tokens": 0,
                    },
                },
            },
        ]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            request = {
                "authorization": self.headers.get("Authorization"),
                "body": json.loads(raw),
                "raw": raw.decode("utf-8"),
            }
            requests.append(request)
            events = response_events(len(requests))
            body = "".join(
                f"event: {event['type']}\ndata: "
                f"{json.dumps(event, separators=(',', ':'))}\n\n"
                for event in events
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    workdir = tmp_path / "repo"
    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("OPENAI_API_KEY", provider_key)
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("CODEX_API_KEY", ambient_codex_key)
    monkeypatch.setenv("CODEX_HOME", str(source_home))
    try:
        result = adapter_codex.CodexHarness().invoke(
            "Use the provided tool once, then finish.",
            "gpt-5.6-terra",
            workdir,
            60,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert result.output == "done"
    assert len(requests) == 2
    assert all(request["authorization"] == f"Bearer {provider_key}" for request in requests)
    second_input = requests[1]["body"]["input"]
    tool_outputs = [
        item for item in second_input
        if item.get("type") == "function_call_output" and item.get("call_id") == "call-env"
    ]
    assert tool_outputs
    env_state = workdir / "env-state.txt"
    assert env_state.exists(), tool_outputs
    assert env_state.read_text(encoding="utf-8") == "clean:blocked"
    combined_bodies = "\n".join(str(request["raw"]) for request in requests)
    assert provider_key not in combined_bodies
    assert ambient_codex_key not in combined_bodies


def test_codex_credential_proxy_revokes_incomplete_requests_on_exit() -> None:
    import harness.adapter_codex as adapter_codex

    upstream_auth: list[str | None] = []
    forwarded = threading.Event()

    class UpstreamHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            upstream_auth.append(self.headers.get("Authorization"))
            forwarded.set()
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    route = adapter_codex._ProviderRoute(
        base_url=f"http://127.0.0.1:{upstream.server_port}/v1",
        wire_api="responses",
        requires_openai_auth=True,
    )
    client: socket.socket | None = None
    try:
        with adapter_codex._credential_proxy(route, "dummy-lifetime-key", 10) as proxy:
            parsed = urllib.parse.urlsplit(proxy)
            assert parsed.port is not None
            client = socket.create_connection(("127.0.0.1", parsed.port), timeout=2)
            client.sendall(
                b"POST /v1/responses HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Content-Length: 2\r\n\r\n"
            )
        try:
            client.sendall(b"{}")
        except OSError:
            pass
        forwarded.wait(0.5)
    finally:
        if client is not None:
            client.close()
        upstream.shutdown()
        upstream_thread.join(timeout=5)
        upstream.server_close()

    assert not forwarded.is_set()
    assert upstream_auth == []


def test_codex_credential_proxy_does_not_forward_auth_across_redirects() -> None:
    import harness.adapter_codex as adapter_codex

    upstream_auth: list[str | None] = []
    redirected_requests: list[bool] = []

    class SinkHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            redirected_requests.append(True)
            self.send_response(204)
            self.end_headers()

    sink = ThreadingHTTPServer(("127.0.0.1", 0), SinkHandler)

    class RedirectHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            upstream_auth.append(self.headers.get("Authorization"))
            self.send_response(307)
            self.send_header("Location", f"http://127.0.0.1:{sink.server_port}/capture")
            self.end_headers()

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    sink_thread = threading.Thread(target=sink.serve_forever, daemon=True)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    sink_thread.start()
    upstream_thread.start()
    route = adapter_codex._ProviderRoute(
        base_url=f"http://127.0.0.1:{upstream.server_port}/v1",
        wire_api="responses",
        requires_openai_auth=True,
    )
    try:
        with adapter_codex._credential_proxy(route, "dummy-redirect-key", 10) as proxy:
            request = urllib.request.Request(
                f"{proxy}/responses",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as captured:
                urllib.request.build_opener(adapter_codex._NoRedirectHandler()).open(request)
            assert captured.value.code == 307
    finally:
        upstream.shutdown()
        sink.shutdown()
        upstream_thread.join(timeout=5)
        sink_thread.join(timeout=5)
        upstream.server_close()
        sink.server_close()

    assert upstream_auth == ["Bearer dummy-redirect-key"]
    assert redirected_requests == []


def test_codex_harness_imports_only_the_minimal_provider_route(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    _write_private_text(
        source_home / "auth.json",
        '{"auth_mode":"apikey","OPENAI_API_KEY":"route-token"}',
    )
    (source_home / "config.toml").write_text(
        """model_provider = "gateway"
[model_providers.gateway]
name = "gateway"
base_url = "https://gateway.example.invalid"
wire_api = "responses"
requires_openai_auth = true
[projects."/private/repo"]
trust_level = "trusted"
[mcp_servers.must_not_cross]
command = "must-not-cross"
""",
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    class FakeProxy:
        def __init__(self, route, key, timeout_s) -> None:
            observed["provider_route"] = route
            observed["provider_key"] = key
            observed["provider_timeout"] = timeout_s

        def __enter__(self) -> str:
            return "http://127.0.0.1:43123/v1"

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setattr(adapter_codex, "_credential_proxy", FakeProxy)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ambient.example.invalid")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    command = observed["command"]
    assert isinstance(command, list)
    overrides = [command[index + 1] for index, value in enumerate(command) if value == "-c"]
    assert 'model_provider="cs_eval_proxy"' in overrides
    assert 'model_providers.cs_eval_proxy.base_url="http://127.0.0.1:43123/v1"' in overrides
    assert 'model_providers.cs_eval_proxy.wire_api="responses"' in overrides
    assert "model_providers.cs_eval_proxy.requires_openai_auth=false" in overrides
    route = observed["provider_route"]
    assert route.base_url == "https://gateway.example.invalid"
    assert route.wire_api == "responses"
    assert route.requires_openai_auth is True
    assert observed["provider_key"] == "route-token"
    assert "must-not-cross" not in "\n".join(command)
    assert "/private/repo" not in "\n".join(command)
    assert "route-token" not in "\n".join(command)
    env = observed["env"]
    assert isinstance(env, dict)
    assert "CODEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "OPENAI_BASE_URL" not in env


def test_codex_harness_keeps_selected_provider_and_stored_auth_atomic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    _write_private_text(
        source_home / "auth.json",
        '{"auth_mode":"apikey","OPENAI_API_KEY":"stored-route-token"}',
    )
    (source_home / "config.toml").write_text(
        'model_provider="gateway"\n[model_providers.gateway]\n'
        'name="gateway"\nbase_url="https://gateway.example.invalid"\n'
        'wire_api="responses"\nrequires_openai_auth=true\n',
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    class FakeProxy:
        def __init__(self, route, key, timeout_s) -> None:
            observed["provider_route"] = route
            observed["provider_key"] = key
            observed["provider_timeout"] = timeout_s

        def __enter__(self) -> str:
            return "http://127.0.0.1:43125/v1"

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setattr(adapter_codex, "_credential_proxy", FakeProxy)
    monkeypatch.setenv("OPENAI_API_KEY", "ambient-unrelated-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ambient.example.invalid/v1")
    monkeypatch.setenv("CODEX_API_KEY", "ambient-codex-key")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    command = observed["command"]
    assert isinstance(command, list)
    assert 'shell_environment_policy.inherit="core"' in command
    route = observed["provider_route"]
    assert route.base_url == "https://gateway.example.invalid"
    assert route.wire_api == "responses"
    assert route.requires_openai_auth is True
    assert observed["provider_key"] == "stored-route-token"
    combined_command = "\n".join(command)
    assert "gateway.example.invalid" not in combined_command
    assert "ambient.example.invalid" not in combined_command
    assert "stored-route-token" not in combined_command
    assert "ambient-unrelated-key" not in combined_command
    assert "ambient-codex-key" not in combined_command
    env = observed["env"]
    assert isinstance(env, dict)
    assert "CODEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "OPENAI_BASE_URL" not in env


def test_codex_harness_does_not_fallback_to_ambient_auth_for_selected_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text(
        'model_provider="gateway"\n[model_providers.gateway]\n'
        'name="gateway"\nbase_url="https://gateway.example.invalid"\n'
        'wire_api="responses"\nrequires_openai_auth=true\n',
        encoding="utf-8",
    )
    provider_calls: list[list[str]] = []

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(
        adapter_codex.subprocess,
        "run",
        lambda command, **_kwargs: provider_calls.append(command),
    )
    monkeypatch.setenv("OPENAI_API_KEY", "ambient-unrelated-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ambient.example.invalid/v1")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    assert provider_calls == []


def test_codex_harness_maps_an_explicit_ambient_route_to_minimal_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    observed: dict[str, object] = {}

    class FakeProxy:
        def __init__(self, route, key, timeout_s) -> None:
            observed["provider_route"] = route
            observed["provider_key"] = key
            observed["provider_timeout"] = timeout_s

        def __enter__(self) -> str:
            return "http://127.0.0.1:43124/v1"

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = dict(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setattr(adapter_codex, "_credential_proxy", FakeProxy)
    monkeypatch.setenv("OPENAI_API_KEY", "explicit-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example.invalid/v1")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    adapter_codex.CodexHarness().invoke(
        "task",
        "gpt-5.6-terra",
        tmp_path / "repo",
        30,
    )

    command = observed["command"]
    assert isinstance(command, list)
    overrides = [command[index + 1] for index, value in enumerate(command) if value == "-c"]
    assert 'model_provider="cs_eval_proxy"' in overrides
    assert (
        'model_providers.cs_eval_proxy.base_url="http://127.0.0.1:43124/v1"'
        in overrides
    )
    assert 'model_providers.cs_eval_proxy.wire_api="responses"' in overrides
    assert "model_providers.cs_eval_proxy.requires_openai_auth=false" in overrides
    route = observed["provider_route"]
    assert route.base_url == "https://gateway.example.invalid/v1"
    assert route.wire_api == "responses"
    assert route.requires_openai_auth is True
    assert observed["provider_key"] == "explicit-key"
    env = observed["env"]
    assert isinstance(env, dict)
    assert "CODEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "OPENAI_BASE_URL" not in env


def test_codex_harness_rejects_ambient_route_without_a_selected_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    _write_private_text(
        source_home / "auth.json",
        '{"auth_mode":"apikey","OPENAI_API_KEY":"route-token"}',
    )
    provider_calls: list[list[str]] = []

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(
        adapter_codex.subprocess,
        "run",
        lambda command, **_kwargs: provider_calls.append(command),
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ambient.example.invalid")
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    assert provider_calls == []


def test_codex_harness_redacts_the_provider_key_from_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    _write_private_text(
        source_home / "auth.json",
        '{"auth_mode":"apikey","OPENAI_API_KEY":"route-token"}',
    )

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(
        adapter_codex.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr="provider rejected route-token",
        ),
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError) as captured:
        adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    assert "route-token" not in str(captured.value)
    assert "[REDACTED]" in str(captured.value)


@pytest.mark.parametrize(
    "auth_payload",
    [
        "{",
        "[]",
        '{"auth_mode":"test","OPENAI_API_KEY":"route-token"}',
        '{"OPENAI_API_KEY":"route-token"}',
        '{"auth_mode":"apikey"}',
        '{"auth_mode":"apikey","OPENAI_API_KEY":""}',
        '{"auth_mode":"apikey","OPENAI_API_KEY":" route-token"}',
        '{"auth_mode":"apikey","OPENAI_API_KEY":"route\\ntoken"}',
        '{"auth_mode":"apikey","OPENAI_API_KEY":123}',
    ],
    ids=(
        "malformed",
        "wrong-document-type",
        "unknown-mode",
        "missing-mode",
        "missing-key",
        "empty-key",
        "leading-space-key",
        "control-character-key",
        "wrong-key-type",
    ),
)
def test_codex_harness_rejects_invalid_provider_auth_before_invocation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    auth_payload: str,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    _write_private_text(source_home / "auth.json", auth_payload)
    provider_calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        provider_calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex.CodexHarness().invoke(
            "task",
            "gpt-5.6-terra",
            tmp_path / "repo",
            30,
        )

    assert provider_calls == []


def test_codex_harness_rejects_overexposed_provider_auth_before_invocation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    auth = source_home / "auth.json"
    auth.write_text(
        '{"auth_mode":"apikey","OPENAI_API_KEY":"route-token"}',
        encoding="utf-8",
    )
    auth.chmod(0o644)
    provider_calls: list[list[str]] = []

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(
        adapter_codex.subprocess,
        "run",
        lambda command, **_kwargs: provider_calls.append(command),
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path / "repo", 30)

    assert provider_calls == []


def test_codex_harness_rejects_symlinked_provider_auth_before_invocation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    external_auth = tmp_path / "external-auth.json"
    _write_private_text(
        external_auth,
        '{"auth_mode":"apikey","OPENAI_API_KEY":"external-token"}',
    )
    (source_home / "auth.json").symlink_to(external_auth)
    provider_calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        provider_calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(source_home))

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex.CodexHarness().invoke(
            "task",
            "gpt-5.6-terra",
            tmp_path / "repo",
            30,
        )

    assert provider_calls == []


def test_codex_provider_overrides_allow_only_a_truly_missing_config(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()

    assert adapter_codex._provider_overrides(source_home) == []

    (source_home / "config.toml").mkdir()
    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


def test_codex_provider_overrides_allow_a_config_without_a_selected_provider(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text('model="gpt-5.6-terra"\n', encoding="utf-8")

    assert adapter_codex._provider_overrides(source_home) == []


def test_codex_provider_overrides_reject_symlinked_config(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    external_config = tmp_path / "external-config.toml"
    external_config.write_text(
        'model_provider="gateway"\n[model_providers.gateway]\nname="gateway"\n',
        encoding="utf-8",
    )
    (source_home / "config.toml").symlink_to(external_config)

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


def test_codex_provider_overrides_reject_group_or_other_writable_config(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    config = source_home / "config.toml"
    config.write_text('model="gpt-5.6-terra"\n', encoding="utf-8")
    config.chmod(0o666)

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


def test_codex_provider_overrides_reject_config_not_owned_by_current_user(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text('model="gpt-5.6-terra"\n', encoding="utf-8")
    current_uid = os.getuid()
    monkeypatch.setattr(adapter_codex.os, "getuid", lambda: current_uid + 1)

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


@pytest.mark.parametrize(
    "config_text",
    [
        "model_provider =",
        "model_provider=1\n",
        'model_provider="gateway unsafe"\n'
        '[model_providers."gateway unsafe"]\nname="gateway"\n',
        'model_provider="missing"\n[model_providers.gateway]\nname="gateway"\n',
    ],
    ids=("malformed", "wrong-provider-type", "unsafe-provider-id", "selected-provider-missing"),
)
def test_codex_provider_overrides_reject_invalid_selected_provider(
    tmp_path: Path,
    config_text: str,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text(config_text, encoding="utf-8")

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("name", "1"),
        ("base_url", "false"),
        ("wire_api", '["responses"]'),
        ("requires_openai_auth", '"true"'),
    ],
    ids=("name", "base-url", "wire-api", "requires-auth"),
)
def test_codex_provider_overrides_reject_wrong_provider_field_types(
    tmp_path: Path,
    field: str,
    invalid_value: str,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    values = {
        "name": '"gateway"',
        "base_url": '"https://gateway.example.invalid"',
        "wire_api": '"responses"',
        "requires_openai_auth": "true",
    }
    values[field] = invalid_value
    provider_lines = "\n".join(f"{key}={value}" for key, value in values.items())
    (source_home / "config.toml").write_text(
        f'model_provider="gateway"\n[model_providers.gateway]\n{provider_lines}\n',
        encoding="utf-8",
    )

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


def test_codex_provider_overrides_reject_dotted_provider_ids(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text(
        'model_provider="gateway.prod"\n'
        '[model_providers."gateway.prod"]\n'
        'name="gateway"\n'
        'base_url="https://gateway.example.invalid"\n'
        'wire_api="responses"\n'
        'requires_openai_auth=true\n',
        encoding="utf-8",
    )

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)


def test_codex_provider_overrides_reject_extra_selected_provider_fields(tmp_path: Path) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    (source_home / "config.toml").write_text(
        'model_provider="gateway"\n'
        '[model_providers.gateway]\n'
        'name="gateway"\n'
        'base_url="https://gateway.example.invalid"\n'
        'wire_api="responses"\n'
        'requires_openai_auth=true\n'
        'http_headers={Authorization="must-not-cross"}\n',
        encoding="utf-8",
    )

    with pytest.raises(adapter_codex.HarnessError):
        adapter_codex._provider_overrides(source_home)
