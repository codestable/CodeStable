#!/usr/bin/env python3
"""Codex CLI headless 适配器：`codex exec --json`。

隔离：独立 workdir + Seatbelt + ephemeral + env 白名单；JSONL 回收 usage，不保留 session id。
CLI 缺失/超时/非零退出抛 HarnessError。真实运行前请对齐本机 codex 版本的 exec 参数。
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .base import (
    CODEX_ENV_KEYS,
    HarnessError,
    HarnessResult,
    macos_sandbox_profile,
    register,
    whitelisted_env,
)


_sandbox_profile = macos_sandbox_profile


def _native_codex_runtime(binary: str) -> tuple[Path, tuple[Path, ...]]:
    """Resolve the npm launcher to its native binary so Seatbelt need not expose the package tree."""
    resolved = Path(binary).resolve()
    if resolved.suffix != ".js":
        return resolved, (resolved.parent,)
    machine = platform.machine().lower()
    targets = {
        "arm64": ("codex-darwin-arm64", "aarch64-apple-darwin"),
        "aarch64": ("codex-darwin-arm64", "aarch64-apple-darwin"),
        "x86_64": ("codex-darwin-x64", "x86_64-apple-darwin"),
        "amd64": ("codex-darwin-x64", "x86_64-apple-darwin"),
    }
    if machine not in targets:
        raise HarnessError(f"codex-cli 不支持当前 macOS 架构: {machine}")
    package_name, target = targets[machine]
    package_root = resolved.parent.parent
    candidates = (
        package_root / "node_modules" / "@openai" / package_name / "vendor" / target / "bin" / "codex",
        package_root.parent / package_name / "vendor" / target / "bin" / "codex",
        package_root / "vendor" / target / "bin" / "codex",
    )
    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink():
            native = candidate.resolve()
            return native, (native.parent.parent,)
    raise HarnessError("无法从 Codex JavaScript launcher 解析受控 native binary")


def _native_codex_binary(binary: str) -> Path:
    return _native_codex_runtime(binary)[0]


class CodexHarness:
    name = "codex-cli"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        binary = shutil.which("codex")
        if not binary:
            raise HarnessError("找不到 `codex` CLI，无法用 codex-cli harness")
        binary_path, binary_read_roots = _native_codex_runtime(binary)
        sandbox = shutil.which("sandbox-exec")
        if not sandbox:
            raise HarnessError("codex-cli 需要 macOS sandbox-exec 外部文件系统隔离")
        workdir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cs-eval-codex-", dir=workdir.parent) as tmp:
            runtime = Path(tmp)
            codex_home = runtime / "codex-home"
            home = runtime / "home"
            tmpdir = runtime / "tmp"
            for path in (codex_home, home, tmpdir):
                path.mkdir()
            if "OPENAI_API_KEY" not in os.environ:
                source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
                source_auth = source_home / "auth.json"
                if not source_auth.is_file():
                    raise HarnessError("codex-cli 需要 OPENAI_API_KEY 或 CODEX_HOME/auth.json")
                shutil.copy2(source_auth, codex_home / "auth.json")
            inner = [
                str(binary_path), "exec", "--skip-git-repo-check", "--ephemeral", "--json",
                "--ignore-user-config", "--ignore-rules", "--sandbox", "workspace-write",
            ]
            if model:
                inner += ["--model", model]
            inner.append(prompt)
            cmd = [
                sandbox,
                "-p",
                _sandbox_profile(workdir, runtime, binary_path, binary_read_roots),
                *inner,
            ]
            env = whitelisted_env(
                include=CODEX_ENV_KEYS,
                extra={
                    "HOME": str(home),
                    "CODEX_HOME": str(codex_home),
                    "TMPDIR": str(tmpdir),
                },
            )
            start = time.monotonic()
            try:
                completed = subprocess.run(
                    cmd, cwd=workdir, env=env, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise HarnessError(f"codex-cli 超时 {timeout_s}s") from exc
        wall_ms = int((time.monotonic() - start) * 1000)
        if completed.returncode != 0:
            raise HarnessError(f"codex 退出码 {completed.returncode}: {completed.stderr[-500:]}")
        output, usage = _parse(completed.stdout)
        return HarnessResult(output=output, model=model, harness=self.name,
                             wall_ms=wall_ms, turns=None, usage=usage)


def _parse(stdout: str) -> tuple[str, dict | None]:
    """只提取最终 agent message 与 usage，丢弃 thread/session 标识。"""
    messages: list[str] = []
    usage = None
    parsed_any = False
    for raw in stdout.splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        parsed_any = True
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(str(item["text"]))
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            raw_usage = event["usage"]
            usage = {
                "input_tokens": raw_usage.get("input_tokens"),
                "output_tokens": raw_usage.get("output_tokens"),
                "source": "codex-json",
            }
    output = "\n".join(messages).strip()
    if not parsed_any:
        output = stdout.strip()
    return output, usage


register(CodexHarness())
