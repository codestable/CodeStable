"""eval-cs-skill harness 的宿主隔离契约。"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
sys.path.insert(0, str(SCRIPTS))


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
    target = ExecutionTarget(
        id="fake-target",
        family="fake-family",
        harness="skipping",
        model="mock-model",
    )

    with pytest.raises(RuntimeError, match="host_read_blocked,sibling_read_blocked,host_write_blocked"):
        probe_targets._probe_target(target)

    assert not list(host_home.glob(".cs-eval-probe-*"))


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


@pytest.mark.parametrize(
    "relative",
    [
        Path(".codex/state_5.sqlite"),
        Path(".codex/sessions/2026/run.jsonl"),
        Path(".codex/rollout/run.jsonl"),
        Path(".claude/projects/repo/session.jsonl"),
    ],
)
def test_target_probe_snapshots_known_host_session_state(
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
    state_file.write_text("after-state-change\n", encoding="utf-8")

    assert probe_targets._config_snapshot() != before


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
    with pytest.raises(ValueError, match="NUL 或换行"):
        base.macos_sandbox_profile(tmp_path / "bad\npath", runtime, binary)


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

    result = adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", workdir, 30)

    assert result.output == "done"
    command = observed["command"]
    assert isinstance(command, list)
    assert command[0] == "/usr/bin/sandbox-exec"
    profile = command[command.index("-p") + 1]
    assert "(deny file-read*" in profile
    assert "(deny file-write*" in profile
    assert str(workdir.resolve()) in profile
    for flag in ("--ephemeral", "--json", "--ignore-user-config", "--ignore-rules"):
        assert flag in command
    assert command[command.index("--sandbox") + 1] == "workspace-write"

    env = observed["env"]
    assert isinstance(env, dict)
    assert env["OPENAI_API_KEY"] == "openai-test-token"
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


def test_codex_harness_copies_auth_into_the_ephemeral_codex_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import harness.adapter_codex as adapter_codex

    source_home = tmp_path / "source-codex"
    source_home.mkdir()
    source_auth = source_home / "auth.json"
    source_auth.write_text('{"auth_mode":"test"}', encoding="utf-8")
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = dict(kwargs["env"])
        isolated_home = Path(env["CODEX_HOME"])
        observed["env"] = env
        observed["copied_auth"] = (isolated_home / "auth.json").read_text(encoding="utf-8")
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

    assert observed["copied_auth"] == source_auth.read_text(encoding="utf-8")
    env = observed["env"]
    assert isinstance(env, dict)
    assert Path(env["CODEX_HOME"]) != source_home
    assert not Path(env["CODEX_HOME"]).exists()
