#!/usr/bin/env python3
"""Claude Code headless 适配器：`claude -p <prompt> --output-format json`。

隔离：在独立 workdir 跑、env 白名单。尽量从 --output-format json 回收 usage（升为 measured）。
CLI 缺失或超时抛 HarnessError。真实运行才用，离线测试用 mock。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .base import (
    CLAUDE_ENV_KEYS,
    HarnessError,
    HarnessResult,
    macos_sandbox_profile,
    register,
    whitelisted_env,
)


_SETTINGS_ENV_KEYS = {
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
    "CLAUDE_CODE_ATTRIBUTION_HEADER",
}


def _provider_env() -> dict[str, str]:
    """复制显式 provider 变量；缺失项可从宿主 Claude settings 白名单补齐。"""
    env = whitelisted_env(include=CLAUDE_ENV_KEYS)
    settings_path = Path.home() / ".claude/settings.json"
    if not settings_path.is_file() or settings_path.is_symlink():
        return env
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return env
    settings_env = data.get("env") if isinstance(data, dict) else None
    if not isinstance(settings_env, dict):
        return env
    for key in _SETTINGS_ENV_KEYS:
        value = settings_env.get(key)
        if key not in env and isinstance(value, str) and value:
            env[key] = value
    return env


_sandbox_profile = macos_sandbox_profile


class ClaudeHarness:
    name = "claude-headless"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        binary = shutil.which("claude")
        if not binary:
            raise HarnessError("找不到 `claude` CLI，无法用 claude-headless harness")
        binary_path = Path(binary).resolve()
        sandbox = shutil.which("sandbox-exec")
        if not sandbox:
            raise HarnessError("claude-headless 需要 macOS sandbox-exec 外部文件系统隔离")
        workdir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cs-eval-claude-", dir=workdir.parent) as tmp:
            runtime = Path(tmp)
            (runtime / "home").mkdir()
            (runtime / "tmp").mkdir()
            inner = [
                str(binary_path), "-p", prompt, "--output-format", "json",
                "--no-session-persistence", "--safe-mode",
                "--permission-mode", "bypassPermissions",
            ]
            if model:
                inner += ["--model", model]
            cmd = [sandbox, "-p", _sandbox_profile(workdir, runtime, binary_path), *inner]
            env = _provider_env()
            env.update({"HOME": str(runtime / "home"), "TMPDIR": str(runtime / "tmp")})
            start = time.monotonic()
            try:
                completed = subprocess.run(
                    cmd,
                    cwd=workdir,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_s,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise HarnessError(f"claude-headless 超时 {timeout_s}s") from exc
        wall_ms = int((time.monotonic() - start) * 1000)
        if completed.returncode != 0:
            raise HarnessError(f"claude 退出码 {completed.returncode}: {completed.stderr[-500:]}")

        output, turns, usage = _parse(completed.stdout)
        return HarnessResult(
            output=output,
            model=model,
            harness=self.name,
            wall_ms=wall_ms,
            turns=turns,
            usage=usage,
        )


def _parse(stdout: str) -> tuple[str, int | None, dict | None]:
    """解析 claude -p --output-format json 输出：{result, usage, num_turns, ...}。"""
    text = stdout.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text, None, None
    output = data.get("result") or data.get("text") or json.dumps(data, ensure_ascii=False)
    turns = data.get("num_turns")
    usage = None
    raw_usage = data.get("usage") or {}
    if raw_usage:
        usage = {
            "input_tokens": raw_usage.get("input_tokens"),
            "output_tokens": raw_usage.get("output_tokens"),
            "cost_usd": data.get("total_cost_usd") or data.get("cost_usd"),
            "source": "claude-json",
        }
    return output, turns, usage


register(ClaudeHarness())
