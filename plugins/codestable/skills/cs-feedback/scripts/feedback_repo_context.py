from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # Repo context degrades to unknown without optional PyYAML.
    yaml = None

from feedback_privacy import public_redact
from feedback_transcripts import METADATA_TYPES, provider_from_path, session_id_from


ENVIRONMENT_METADATA_TYPES = METADATA_TYPES | {"turn_context"}
BODY_FIELDS = {"message", "content", "text", "output", "arguments", "input"}


def session_label(session: str) -> str:
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()[:10]
    return f"session-{digest}"


def _artifact_metadata(path: Path, root: Path) -> dict[str, str] | None:
    if yaml is None:
        return None
    try:
        if path.suffix in {".yaml", ".yml"}:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        elif path.suffix == ".md":
            prefix = path.read_text(encoding="utf-8", errors="ignore")[:8192]
            if not prefix.startswith("---\n") or "\n---\n" not in prefix[4:]:
                return None
            frontmatter = prefix[4:].split("\n---\n", 1)[0]
            loaded = yaml.safe_load(frontmatter)
        else:
            return None
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    if not isinstance(loaded, dict):
        return None
    keys = ("doc_type", "status", "stage", "feature", "issue", "goal", "refactor")
    metadata = {
        key: str(loaded[key])
        for key in keys
        if loaded.get(key) is not None and not isinstance(loaded.get(key), (dict, list))
    }
    if not metadata or not {"doc_type", "status", "stage"}.intersection(metadata):
        return None
    return {"path": path.relative_to(root).as_posix(), **metadata}


def _repo_root(cwd: Path) -> Path:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            root = Path(completed.stdout.strip()).resolve()
            if root.is_dir():
                return root
    except (OSError, subprocess.TimeoutExpired):
        pass
    return cwd.resolve()


def build_repo_context(cwd: str | None) -> dict[str, object]:
    empty = {
        "runtime": {"status": "unknown"},
        "artifacts": [],
        "git_status": [],
    }
    if not cwd:
        return empty
    requested_root = Path(cwd)
    if not requested_root.is_dir():
        return empty
    root = _repo_root(requested_root)

    runtime: dict[str, object] = {"status": "unknown"}
    manifest = root / ".codestable/runtime-manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            runtime_version = str(data.get("runtime_version") or "unknown")
            plugin_version = str(data.get("plugin_version") or "unknown")
            runtime = {
                "status": "present" if runtime_version == plugin_version else "mismatch",
                "runtime_version": runtime_version,
                "plugin_version": plugin_version,
            }
        except (OSError, json.JSONDecodeError):
            runtime = {"status": "invalid"}

    artifacts: list[dict[str, str]] = []
    codestable = root / ".codestable"
    if codestable.is_dir():
        for path in sorted(codestable.rglob("*")):
            if not path.is_file() or path == manifest:
                continue
            metadata = _artifact_metadata(path, root)
            if metadata:
                artifacts.append(metadata)
            if len(artifacts) >= 30:
                break

    git_status: list[dict[str, str]] = []
    try:
        completed = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if completed.returncode == 0:
            for line in completed.stdout.splitlines()[:100]:
                if len(line) >= 4:
                    git_status.append({"status": line[:2], "path": line[3:]})
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {"runtime": runtime, "artifacts": artifacts, "git_status": git_status}


def environment_context(
    path: Path,
    records: list[dict[str, Any]],
    capture: dict[str, Any],
) -> dict[str, object]:
    model = "unknown"
    host_version = "unknown"
    for record in records:
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else record
        record_type = str(record.get("type") or payload.get("type") or "")
        top_level_metadata = any(
            key in record for key in ("session_id", "sessionId", "sessionid", "cwd")
        ) and not BODY_FIELDS.intersection(record)
        if record_type not in ENVIRONMENT_METADATA_TYPES and not top_level_metadata:
            continue
        if model == "unknown" and payload.get("model"):
            model = public_redact(str(payload["model"]), limit=120)
        if host_version == "unknown" and (
            payload.get("version")
            or payload.get("client_version")
            or payload.get("cli_version")
        ):
            host_version = public_redact(
                str(
                    payload.get("version")
                    or payload.get("client_version")
                    or payload.get("cli_version")
                ),
                limit=120,
            )
        if model != "unknown" and host_version != "unknown":
            break
    return {
        "provider": provider_from_path(path),
        "session": session_label(session_id_from(path, records)),
        "model": model,
        "host_version": host_version,
        "capture": capture,
    }
