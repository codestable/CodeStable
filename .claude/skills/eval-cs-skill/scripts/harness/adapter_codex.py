#!/usr/bin/env python3
"""Codex CLI headless 适配器：`codex exec --json`。

隔离：独立 workdir + Seatbelt + ephemeral + env 白名单；JSONL 回收 usage，不保留 session id。
CLI 缺失/超时/非零退出抛 HarnessError。真实运行前请对齐本机 codex 版本的 exec 参数。
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import threading
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from .base import (
    HarnessError,
    HarnessResult,
    macos_sandbox_profile,
    register,
    whitelisted_env,
)


_sandbox_profile = macos_sandbox_profile
_PROVIDER_NAME = re.compile(r"[A-Za-z0-9_-]+")
_PROVIDER_FIELDS = {
    "name": str,
    "base_url": str,
    "wire_api": str,
    "requires_openai_auth": bool,
}
_MAX_HOST_CONFIG_BYTES = 1024 * 1024
_MAX_PROXY_BODY_BYTES = 16 * 1024 * 1024
_DEFAULT_PROVIDER_BASE_URL = "https://api.openai.com/v1"
_PROXY_PROVIDER = "cs_eval_proxy"
_CODEX_CHILD_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "TERM")
_HOP_BY_HOP_HEADERS = {
    "accept-encoding",
    "authorization",
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


@dataclass(frozen=True)
class _ProviderRoute:
    base_url: str
    wire_api: str
    requires_openai_auth: bool


class _QuietThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
    ) -> None:
        super().__init__(server_address, handler_class)
        self.credentials_active = threading.Event()
        self.credentials_active.set()
        self.forward_lock = threading.Lock()
        self._connections_lock = threading.Lock()
        self._connections: set[socket.socket] = set()

    def get_request(self) -> tuple[socket.socket, tuple[str, int]]:
        request, address = super().get_request()
        with self._connections_lock:
            self._connections.add(request)
        return request, address

    def shutdown_request(self, request: socket.socket) -> None:
        try:
            super().shutdown_request(request)
        finally:
            with self._connections_lock:
                self._connections.discard(request)

    def revoke_credentials(self) -> None:
        self.credentials_active.clear()
        self.shutdown()
        with self.forward_lock:
            pass
        with self._connections_lock:
            connections = tuple(self._connections)
            self._connections.clear()
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()

    def handle_error(self, _request: object, _client_address: object) -> None:
        return


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: object, **_kwargs: object) -> None:
        return None


def _encode_overrides(values: list[tuple[str, str | bool]]) -> list[str]:
    overrides: list[str] = []
    for key, value in values:
        encoded = json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value).lower()
        overrides.extend(("-c", f"{key}={encoded}"))
    return overrides


def _validate_provider_api_key(value: object, *, source: str) -> str:
    if type(value) is not str or re.fullmatch(r"[\x21-\x7e]+", value) is None:
        raise HarnessError(f"codex-cli 的 {source} 缺少有效 API key")
    return value


def _read_host_file(
    path: Path,
    *,
    label: str,
    missing_ok: bool,
    private: bool = False,
) -> bytes | None:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HarnessError(f"当前平台无法安全读取 {label}")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise HarnessError(f"codex-cli 缺少 {label}") from None
    except OSError:
        raise HarnessError(f"codex-cli 无法安全读取 {label}") from None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise HarnessError(f"codex-cli 要求 {label} 为普通文件")
        mode = stat.S_IMODE(info.st_mode)
        if info.st_uid != os.getuid() or mode & 0o022:
            raise HarnessError(f"codex-cli 要求 {label} 由当前用户控制")
        if private and mode & 0o077:
            raise HarnessError(f"codex-cli 要求 {label} 仅当前用户可读写")
        if info.st_size > _MAX_HOST_CONFIG_BYTES:
            raise HarnessError(f"codex-cli 的 {label} 超过大小限制")
        chunks: list[bytes] = []
        remaining = _MAX_HOST_CONFIG_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > _MAX_HOST_CONFIG_BYTES:
            raise HarnessError(f"codex-cli 的 {label} 超过大小限制")
        return raw
    finally:
        os.close(descriptor)


def _selected_provider(source_home: Path) -> tuple[str, dict[str, str | bool]] | None:
    config_path = source_home / "config.toml"
    raw = _read_host_file(
        config_path,
        label="CODEX_HOME/config.toml",
        missing_ok=True,
    )
    if raw is None:
        return None
    try:
        config = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError):
        raise HarnessError("codex-cli 无法解析 CODEX_HOME/config.toml") from None
    provider = config.get("model_provider")
    if provider is None:
        return None
    providers = config.get("model_providers")
    if (
        type(provider) is not str
        or not provider
        or _PROVIDER_NAME.fullmatch(provider) is None
        or type(providers) is not dict
        or type(providers.get(provider)) is not dict
    ):
        raise HarnessError("codex-cli 的 selected provider 无法安全迁移")
    provider_config = providers[provider]
    if set(provider_config) != set(_PROVIDER_FIELDS):
        raise HarnessError("codex-cli 的 selected provider 字段不受支持")
    for field, expected_type in _PROVIDER_FIELDS.items():
        value = provider_config.get(field)
        if type(value) is not expected_type or (expected_type is str and not value.strip()):
            raise HarnessError("codex-cli 的 selected provider 字段无效")
    return provider, provider_config


def _provider_overrides(source_home: Path) -> list[str]:
    selected = _selected_provider(source_home)
    if selected is None:
        return []
    provider, provider_config = selected
    values: list[tuple[str, str | bool]] = [("model_provider", provider)]
    values.extend(
        (f"model_providers.{provider}.{field}", provider_config[field])
        for field in _PROVIDER_FIELDS
    )
    return _encode_overrides(values)


def _proxy_provider_overrides(base_url: str, wire_api: str) -> list[str]:
    provider = _PROXY_PROVIDER
    return _encode_overrides([
        ("model_provider", provider),
        (f"model_providers.{provider}.name", provider),
        (f"model_providers.{provider}.base_url", base_url),
        (f"model_providers.{provider}.wire_api", wire_api),
        (f"model_providers.{provider}.requires_openai_auth", False),
    ])


def _route_from_base_url(base_url: str | None) -> _ProviderRoute:
    if base_url is not None and not base_url.strip():
        raise HarnessError("codex-cli 的显式 OPENAI_BASE_URL 不能为空")
    return _ProviderRoute(
        base_url=base_url or _DEFAULT_PROVIDER_BASE_URL,
        wire_api="responses",
        requires_openai_auth=True,
    )


@contextmanager
def _credential_proxy(
    route: _ProviderRoute,
    provider_api_key: str,
    timeout_s: int,
) -> Iterator[str]:
    upstream = urllib.parse.urlsplit(route.base_url)
    if (
        upstream.scheme not in {"http", "https"}
        or not upstream.hostname
        or upstream.username is not None
        or upstream.password is not None
        or upstream.query
        or upstream.fragment
    ):
        raise HarnessError("codex-cli 的 provider base_url 不受支持")
    upstream_path = upstream.path.rstrip("/")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400)
                return
            if length < 0 or length > _MAX_PROXY_BODY_BYTES:
                self.send_error(413)
                return
            raw = self.rfile.read(length)
            incoming = urllib.parse.urlsplit(self.path)
            suffix = incoming.path.removeprefix("/v1")
            target_path = f"{upstream_path}/{suffix.lstrip('/')}"
            target_url = urllib.parse.urlunsplit((
                upstream.scheme,
                upstream.netloc,
                target_path,
                incoming.query,
                "",
            ))
            headers = {
                key: value for key, value in self.headers.items()
                if key.lower() not in _HOP_BY_HOP_HEADERS
            }
            proxy_server = self.server
            assert isinstance(proxy_server, _QuietThreadingHTTPServer)
            with proxy_server.forward_lock:
                if not proxy_server.credentials_active.is_set():
                    self.send_error(503)
                    return
                if route.requires_openai_auth:
                    headers["Authorization"] = f"Bearer {provider_api_key}"
                request = urllib.request.Request(
                    target_url,
                    data=raw,
                    headers=headers,
                    method="POST",
                )
                try:
                    response = urllib.request.build_opener(_NoRedirectHandler()).open(
                        request,
                        timeout=timeout_s,
                    )
                except urllib.error.HTTPError as exc:
                    response = exc
                except (OSError, urllib.error.URLError, ValueError):
                    self.send_error(502)
                    return
                try:
                    body = response.read(_MAX_PROXY_BODY_BYTES + 1)
                    if len(body) > _MAX_PROXY_BODY_BYTES:
                        self.send_error(502)
                        return
                    status = response.status
                    content_type = response.headers.get("Content-Type")
                finally:
                    response.close()
            self.send_response(status)
            if content_type:
                self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = _QuietThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01),
        daemon=True,
    )
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.revoke_credentials()
        thread.join(timeout=5)
        server.server_close()


def _provider_api_key(source_home: Path) -> str:
    raw = _read_host_file(
        source_home / "auth.json",
        label="CODEX_HOME/auth.json",
        missing_ok=False,
        private=True,
    )
    assert raw is not None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise HarnessError("codex-cli 无法解析 CODEX_HOME/auth.json") from None
    if type(payload) is not dict or payload.get("auth_mode") != "apikey":
        raise HarnessError("codex-cli 只支持受控的 apikey auth.json")
    return _validate_provider_api_key(
        payload.get("OPENAI_API_KEY"),
        source="auth.json",
    )


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
        workdir = workdir.resolve()
        source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
        selected = _selected_provider(source_home)
        if selected is not None:
            provider_api_key = _provider_api_key(source_home)
            _, provider = selected
            provider_route = _ProviderRoute(
                base_url=str(provider["base_url"]),
                wire_api=str(provider["wire_api"]),
                requires_openai_auth=bool(provider["requires_openai_auth"]),
            )
        else:
            explicit_key = os.environ.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in os.environ else None
            if explicit_key is None:
                provider_api_key = _provider_api_key(source_home)
                if os.environ.get("OPENAI_BASE_URL"):
                    raise HarnessError("codex-cli 的 ambient provider route 缺少受控 selected provider")
                provider_route = _route_from_base_url(None)
            else:
                provider_api_key = _validate_provider_api_key(
                    explicit_key,
                    source="显式 OPENAI_API_KEY",
                )
                provider_route = _route_from_base_url(os.environ.get("OPENAI_BASE_URL"))
        with tempfile.TemporaryDirectory(prefix="cs-eval-codex-", dir=workdir.parent) as tmp:
            runtime = Path(tmp).resolve()
            codex_home = runtime / "codex-home"
            home = runtime / "home"
            tmpdir = runtime / "tmp"
            for path in (codex_home, home, tmpdir):
                path.mkdir()
            with _credential_proxy(provider_route, provider_api_key, timeout_s) as proxy_base_url:
                inner = [
                    str(binary_path), "exec", "--skip-git-repo-check", "--ephemeral", "--json",
                    # Descendant tools inherit the outer Seatbelt; macOS rejects a nested sandbox_apply.
                    "--ignore-user-config", "--ignore-rules", "--sandbox", "danger-full-access",
                    "--disable", "plugins",
                    "-c", 'shell_environment_policy.inherit="core"',
                ]
                if model:
                    inner += ["--model", model]
                inner += _proxy_provider_overrides(proxy_base_url, provider_route.wire_api)
                inner.append(prompt)
                cmd = [
                    sandbox,
                    "-p",
                    _sandbox_profile(workdir, runtime, binary_path, binary_read_roots),
                    *inner,
                ]
                env = whitelisted_env(
                    include=_CODEX_CHILD_ENV_KEYS,
                    extra={
                        "HOME": str(home),
                        "CODEX_HOME": str(codex_home),
                        "TMPDIR": str(tmpdir),
                        "NO_PROXY": "127.0.0.1,localhost",
                        "no_proxy": "127.0.0.1,localhost",
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
            stderr = completed.stderr[-500:].replace(provider_api_key, "[REDACTED]")
            raise HarnessError(f"codex 退出码 {completed.returncode}: {stderr}")
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
