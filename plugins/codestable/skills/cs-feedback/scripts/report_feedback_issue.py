#!/usr/bin/env python3
"""Create or prepare a GitHub issue for CodeStable feedback."""

from __future__ import annotations

import argparse
import os
import json
import re
import shlex
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlparse
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from feedback_privacy import (  # noqa: E402
    CREDENTIAL_REDACTIONS,
    EMAIL_PATTERN,
    ENV_PATTERN,
    ENV_NAME_PATTERN,
    PATH_PATTERN,
    REMOTE_PATTERN,
    URL_PATTERN,
    contains_secret_assignment,
    contains_inline_json,
)


NETWORK_ERROR_PATTERN = (
    "could not resolve host",
    "failed to connect",
    "connection refused",
    "connection reset",
    "connection timed out",
    "tls handshake timeout",
    "i/o timeout",
    "proxyconnect",
    "early eof",
)


def public_body_private_reasons(text: str) -> list[str]:
    checks = {
        "absolute-path": PATH_PATTERN,
        "remote": REMOTE_PATTERN,
        "url": URL_PATTERN,
        "email": EMAIL_PATTERN,
        "environment": ENV_PATTERN,
        "environment-name": ENV_NAME_PATTERN,
    }
    reasons = [name for name, pattern in checks.items() if pattern.search(text)]
    if contains_secret_assignment(text) or any(
        pattern.search(text) for pattern, _replacement in CREDENTIAL_REDACTIONS
    ):
        reasons.append("secret")
    if contains_inline_json(text):
        reasons.append("raw-json")
    if "```" in text:
        reasons.append("code-block")
    if re.search(r"(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})", text):
        reasons.append("secret-token")
    return reasons


def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def is_network_error(result: subprocess.CompletedProcess[str]) -> bool:
    text = f"{result.stdout}\n{result.stderr}".lower()
    return any(pattern in text for pattern in NETWORK_ERROR_PATTERN)


def proxy_reachable(proxy_url: str) -> bool:
    parsed = urlparse(proxy_url)
    host = parsed.hostname
    port = parsed.port
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def proxy_env_candidates() -> list[dict[str, str]]:
    proxies: list[str] = []
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        value = os.environ.get(key)
        if value and value not in proxies:
            proxies.append(value)
    for value in (
        "http://127.0.0.1:7890",
        "http://localhost:7890",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:1087",
    ):
        if value not in proxies and proxy_reachable(value):
            proxies.append(value)

    candidates: list[dict[str, str]] = []
    for proxy in proxies:
        env = os.environ.copy()
        env.update({"HTTPS_PROXY": proxy, "HTTP_PROXY": proxy, "https_proxy": proxy, "http_proxy": proxy})
        candidates.append(env)
    return candidates


def run_with_proxy_retry(command: list[str]) -> tuple[subprocess.CompletedProcess[str], str | None]:
    result = run(command)
    if result.returncode == 0 or not is_network_error(result):
        return result, None
    for env in proxy_env_candidates():
        proxy = env["HTTPS_PROXY"]
        retry = run(command, env=env)
        if retry.returncode == 0:
            return retry, proxy
        result = retry
        if not is_network_error(retry):
            return retry, proxy
    return result, None


def main_with_args_for_test(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub repo, e.g. owner/name")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--json-output", default=None)
    parser.add_argument(
        "--confirm-public-preview",
        action="store_true",
        help="Confirm the reviewed public preview may be sent to GitHub",
    )
    args = parser.parse_args(argv)

    body_file = Path(args.body_file).expanduser()
    if not body_file.is_file():
        raise SystemExit(f"body file not found: {body_file}")
    if body_file.name in {"evidence.json", "triage.json", "regression-candidate.json"}:
        raise SystemExit(f"refusing to upload local-private {body_file.name}; use github-issue.md public preview")
    if body_file.suffix == ".json":
        try:
            payload = json.loads(body_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict) and payload.get("privacy") == "local-private":
            raise SystemExit("refusing to upload local-private evidence; generate a public preview first")
    if args.confirm_public_preview:
        if body_file.name != "github-issue.md":
            raise SystemExit("confirmed upload requires the reviewed github-issue.md public preview")
        reasons = public_body_private_reasons(body_file.read_text(encoding="utf-8"))
        if reasons:
            raise SystemExit(
                "public preview contains private content: " + ", ".join(reasons)
            )
        title_reasons = public_body_private_reasons(args.title)
        if title_reasons:
            raise SystemExit(
                "issue title contains private content: " + ", ".join(title_reasons)
            )

    gh = shutil.which("gh")
    command = [
        "gh",
        "issue",
        "create",
        "--repo",
        args.repo,
        "--title",
        args.title,
        "--body-file",
        str(body_file),
    ]
    result_payload: dict[str, object]

    if gh and not args.confirm_public_preview:
        result_payload = {
            "status": "manual",
            "reason": "public preview confirmation required",
            "command": shell_join(command),
            "body_file": str(body_file),
        }
    elif not gh:
        result_payload = {
            "status": "manual",
            "reason": "gh not found",
            "command": shell_join(command),
            "body_file": str(body_file),
        }
    else:
        auth, auth_proxy = run_with_proxy_retry([gh, "auth", "status"])
        if auth.returncode != 0:
            result_payload = {
                "status": "manual",
                "reason": "gh auth status failed",
                "command": shell_join(command),
                "body_file": str(body_file),
                "proxy_used": auth_proxy,
                "stderr": auth.stderr.strip(),
            }
        else:
            create, create_proxy = run_with_proxy_retry([gh, *command[1:]])
            if create.returncode == 0:
                result_payload = {
                    "status": "created",
                    "url": create.stdout.strip(),
                    "body_file": str(body_file),
                    "proxy_used": create_proxy,
                }
            else:
                result_payload = {
                    "status": "manual",
                    "reason": "gh issue create failed",
                    "command": shell_join(command),
                    "body_file": str(body_file),
                    "proxy_used": create_proxy,
                    "stdout": create.stdout.strip(),
                    "stderr": create.stderr.strip(),
                }

    text = json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n"
    if args.json_output:
        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


def main() -> int:
    return main_with_args_for_test()


if __name__ == "__main__":
    raise SystemExit(main())
