from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from feedback_models import Candidate, NormalizedRecord, SessionMeta
from feedback_privacy import public_redact, redact


METADATA_TYPES = {"session_meta", "metadata", "system_meta"}
TOOL_CALL_TYPES = {"function_call", "tool_call", "tool_use"}
TOOL_RESULT_TYPES = {"function_call_output", "tool_result", "tool_output"}


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key in (
            "message",
            "text",
            "output",
            "content",
            "arguments",
            "input",
            "name",
            "type",
            "role",
        ):
            if key in value:
                parts.append(flatten(value[key]))
        if parts:
            return "\n".join(part for part in parts if part)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def event_text(record: dict[str, Any]) -> str:
    payload = record.get("payload", record)
    return flatten(payload)


def event_kind(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    if isinstance(payload, dict):
        for key in ("type", "name", "role"):
            if payload.get(key):
                return str(payload[key])
    message = record.get("message")
    if isinstance(message, dict):
        for key in ("type", "name", "role"):
            if message.get(key):
                return str(message[key])
    return str(record.get("type", record.get("role", "unknown")))


def normalize_json_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item if isinstance(item, dict) else {"payload": item} for item in value]
    if not isinstance(value, dict):
        return [{"payload": value}]

    collection_keys = ("messages", "events", "entries", "items", "transcript")
    records: list[dict[str, Any]] = []
    meta = {key: item for key, item in value.items() if key not in collection_keys}
    if meta:
        records.append(meta)
    for key in collection_keys:
        items = value.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            records.append(item if isinstance(item, dict) else {"payload": item})
    return records or [value]


def read_transcript_snapshot(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read one immutable byte snapshot and report the last complete record boundary."""
    raw = path.read_bytes()
    if path.suffix == ".json":
        try:
            value = json.loads(raw.decode("utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return [], {"format": "json", "byte_length": len(raw), "complete_record_eof": 0}
        return normalize_json_records(value), {
            "format": "json",
            "byte_length": len(raw),
            "complete_record_eof": len(raw),
        }

    records: list[dict[str, Any]] = []
    offset = 0
    complete_record_eof = 0
    for raw_line in raw.splitlines(keepends=True):
        offset += len(raw_line)
        line = raw_line.strip()
        if not line:
            continue
        try:
            value = json.loads(line.decode("utf-8", errors="ignore"))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
            complete_record_eof = offset
    return records, {
        "format": "jsonl",
        "byte_length": len(raw),
        "complete_record_eof": complete_record_eof,
    }


def read_records(path: Path) -> list[dict[str, Any]]:
    records, _capture = read_transcript_snapshot(path)
    return records


def _session_id_from_record(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    if isinstance(payload, dict):
        session_id = (
            payload.get("session_id")
            or payload.get("sessionId")
            or payload.get("sessionid")
            or payload.get("id")
        )
        if session_id:
            return str(session_id)
    session_id = (
        record.get("session_id")
        or record.get("sessionId")
        or record.get("sessionid")
        or record.get("id")
    )
    return str(session_id) if session_id else ""


def _cwd_from_record(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    payload_type = payload.get("type") if isinstance(payload, dict) else None
    record_type = record.get("type")
    if (
        isinstance(payload, dict)
        and payload.get("cwd")
        and (record_type == "session_meta" or payload_type == "session_meta")
    ):
        return str(payload["cwd"])
    body_keys = {"message", "content", "text", "output", "arguments", "input"}
    if record.get("cwd") and not body_keys.intersection(record):
        return str(record["cwd"])
    return ""


def read_session_metadata(path: Path) -> SessionMeta:
    """Read only top-level or session-meta fields; never normalize message bodies."""
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_bytes().decode("utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return SessionMeta(path.stem, "")
        if isinstance(value, dict):
            session = str(
                value.get("session_id")
                or value.get("sessionId")
                or value.get("id")
                or path.stem
            )
            cwd = str(value.get("cwd") or "")
            return SessionMeta(session, cwd)
        return SessionMeta(path.stem, "")

    session = ""
    cwd = ""
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if not session:
                session = _session_id_from_record(record)
            if not cwd:
                cwd = _cwd_from_record(record)
            if session and cwd:
                break
    return SessionMeta(session or path.stem, cwd)


def session_id_from(path: Path, records: list[dict[str, Any]]) -> str:
    for record in records:
        session_id = _session_id_from_record(record)
        if session_id:
            return session_id
    return path.stem


def cwd_from(records: list[dict[str, Any]]) -> str:
    for record in records:
        cwd = _cwd_from_record(record)
        if cwd:
            return cwd
    return ""


def provider_from_path(path: Path) -> str:
    text = str(path)
    if ".codex" in text:
        return "codex"
    if ".claude" in text:
        return "claude"
    return "unknown"


def candidate_for(path: Path, cwd: str | None) -> Candidate:
    meta = read_session_metadata(path)
    score = 0
    if cwd and meta.cwd == cwd:
        score += 5
    elif cwd and meta.cwd and (cwd.startswith(meta.cwd) or meta.cwd.startswith(cwd)):
        score += 2
    score += int(path.stat().st_mtime // 60)
    return Candidate(
        path=str(path),
        provider=provider_from_path(path),
        session=meta.session,
        cwd=meta.cwd,
        mtime=path.stat().st_mtime,
        score=score,
    )


def resolve_current_session(
    files: list[Path], cwd: str | None
) -> tuple[list[Path], list[Candidate]]:
    candidates = [
        candidate_for(path, cwd) for path in files if path.suffix in {".jsonl", ".json"}
    ]
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    if not candidates:
        return [], []
    if cwd:
        exact = [candidate for candidate in candidates if candidate.cwd == cwd]
        if len(exact) == 1:
            return [Path(exact[0].path)], []
        if len(exact) > 1:
            return [], exact[:5]
        containing = [
            candidate
            for candidate in candidates
            if candidate.cwd and (cwd.startswith(candidate.cwd) or candidate.cwd.startswith(cwd))
        ]
        if containing:
            return [], containing[:5]
    return [], candidates[:5]


def _history_files(home: Path) -> list[Path]:
    roots = [
        home / ".codex/sessions",
        home / ".claude/projects",
        home / ".claude/sessions",
    ]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".jsonl", ".json"}:
                files.append(path)
    return sorted(files)


def discover_files(
    home: Path,
    since_days: int,
    session_filter: str | None,
    cwd: str | None,
) -> tuple[list[Path], list[Candidate]]:
    if session_filter and session_filter != "current":
        candidate = Path(session_filter).expanduser()
        if candidate.is_file():
            return [candidate], []

    all_files = _history_files(home)
    if session_filter == "current":
        return resolve_current_session(all_files, cwd)

    cutoff = time.time() - since_days * 86400
    files: list[Path] = []
    for path in all_files:
        if path.stat().st_mtime < cutoff:
            continue
        if session_filter and session_filter != "current":
            if session_filter in path.name or session_filter in str(path):
                files.append(path)
                continue
            if session_filter not in read_session_metadata(path).session:
                continue
        files.append(path)
    return files, []


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else record


def _metadata_record(record: dict[str, Any]) -> bool:
    payload = _payload(record)
    kind = str(payload.get("type") or record.get("type") or "")
    if kind in METADATA_TYPES:
        return True
    body_keys = {"message", "content", "text", "output", "arguments", "input"}
    has_meta = any(
        key in record for key in ("session_id", "sessionId", "sessionid", "cwd")
    )
    return has_meta and not body_keys.intersection(record)


def _message_container(record: dict[str, Any]) -> dict[str, Any] | None:
    message = record.get("message")
    if isinstance(message, dict):
        return message
    if "content" in record and (record.get("role") or record.get("type") in {"user", "assistant"}):
        return record
    return None


def _expanded_records(record: dict[str, Any]) -> list[dict[str, Any]]:
    if _metadata_record(record):
        return [
            {
                "role": "system",
                "record_type": "session_meta",
                "tool_name": "unknown",
                "call_id": "",
                "text": "",
            }
        ]

    container = _message_container(record)
    if container is not None:
        role = str(container.get("role") or record.get("role") or record.get("type") or "unknown")
        content = container.get("content")
        blocks = content if isinstance(content, list) else [content]
        expanded: list[dict[str, Any]] = []
        for block in blocks:
            if block is None:
                continue
            if isinstance(block, dict):
                kind = str(block.get("type") or "")
                if kind in TOOL_CALL_TYPES:
                    name = str(block.get("name") or block.get("tool_name") or "unknown")
                    expanded.append(
                        {
                            "role": "assistant",
                            "record_type": "tool_call",
                            "tool_name": name,
                            "call_id": str(block.get("id") or block.get("call_id") or ""),
                            "text": "\n".join(
                                part
                                for part in (name, flatten(block.get("input") or block.get("arguments")))
                                if part
                            ),
                        }
                    )
                    continue
                if kind in TOOL_RESULT_TYPES:
                    expanded.append(
                        {
                            "role": "tool",
                            "record_type": "tool_result",
                            "tool_name": str(block.get("name") or block.get("tool_name") or "unknown"),
                            "call_id": str(
                                block.get("tool_use_id")
                                or block.get("tool_call_id")
                                or block.get("call_id")
                                or ""
                            ),
                            "text": flatten(block.get("content") or block.get("output")),
                        }
                    )
                    continue
                text = flatten(block.get("text") if kind == "text" else block)
            else:
                text = flatten(block)
            if text:
                expanded.append(
                    {
                        "role": role if role in {"user", "assistant", "system"} else "unknown",
                        "record_type": "message",
                        "tool_name": "unknown",
                        "call_id": "",
                        "text": text,
                    }
                )
        if expanded:
            return expanded

    payload = _payload(record)
    kind = str(payload.get("type") or record.get("type") or "unknown")
    role = str(payload.get("role") or record.get("role") or "")
    if kind in TOOL_CALL_TYPES:
        name = str(payload.get("name") or payload.get("tool_name") or payload.get("tool") or "unknown")
        return [
            {
                "role": "assistant",
                "record_type": "tool_call",
                "tool_name": name,
                "call_id": str(
                    payload.get("call_id")
                    or payload.get("tool_call_id")
                    or payload.get("id")
                    or ""
                ),
                "text": event_text(record),
            }
        ]
    if kind in TOOL_RESULT_TYPES:
        return [
            {
                "role": "tool",
                "record_type": "tool_result",
                "tool_name": str(payload.get("name") or payload.get("tool_name") or "unknown"),
                "call_id": str(
                    payload.get("call_id")
                    or payload.get("tool_call_id")
                    or payload.get("tool_use_id")
                    or ""
                ),
                "text": event_text(record),
            }
        ]
    if not role:
        if "user" in kind:
            role = "user"
        elif "assistant" in kind:
            role = "assistant"
    return [
        {
            "role": role if role in {"user", "assistant", "tool", "system"} else "unknown",
            "record_type": "message" if "message" in kind or role else kind,
            "tool_name": "unknown",
            "call_id": "",
            "text": event_text(record),
        }
    ]


def _fallback_tool_name(text: str) -> str:
    for candidate in ("apply_patch", "read_file", "git", "gh", "paseo", "mcp"):
        if candidate in text.lower():
            return candidate
    return "unknown"


def normalize_records(path: Path, records: list[dict[str, Any]]) -> list[NormalizedRecord]:
    provider = provider_from_path(path)
    session = session_id_from(path, records)
    entries: list[dict[str, Any]] = []
    for source_index, record in enumerate(records):
        timestamp = str(record.get("timestamp") or record.get("created_at") or "")
        for expanded in _expanded_records(record):
            text = redact(str(expanded["text"]), limit=800)
            tool_name = str(expanded["tool_name"])
            if tool_name == "unknown":
                tool_name = _fallback_tool_name(text)
            entries.append(
                {
                    **expanded,
                    "timestamp": timestamp,
                    "text": text,
                    "tool_name": public_redact(tool_name, limit=80),
                    "source_index": source_index,
                    "correlation_id": "",
                    "correlation_source": "unpaired",
                }
            )

    calls_by_id: dict[str, list[int]] = defaultdict(list)
    results_by_id: dict[str, list[int]] = defaultdict(list)
    for index, entry in enumerate(entries):
        call_id = str(entry["call_id"])
        if not call_id:
            continue
        if entry["record_type"] == "tool_call":
            calls_by_id[call_id].append(index)
        elif entry["record_type"] == "tool_result":
            results_by_id[call_id].append(index)
    for call_id in set(calls_by_id) & set(results_by_id):
        calls = calls_by_id[call_id]
        results = results_by_id[call_id]
        if len(calls) == 1 and len(results) == 1:
            for index in (calls[0], results[0]):
                entries[index]["correlation_id"] = call_id
                entries[index]["correlation_source"] = "provider"

    pending_calls: list[int] = []
    previous_significant: int | None = None
    for index, entry in enumerate(entries):
        if entry["record_type"] in METADATA_TYPES:
            continue
        record_type = entry["record_type"]
        call_id = str(entry["call_id"])
        if entry["correlation_source"] == "provider" or call_id:
            pending_calls = []
        elif record_type == "tool_call":
            pending_calls.append(index)
        elif record_type == "tool_result":
            if len(pending_calls) == 1 and previous_significant == pending_calls[0]:
                call_index = pending_calls[0]
                correlation_id = f"adjacent-record-{call_index:04d}"
                entries[call_index]["correlation_id"] = correlation_id
                entries[call_index]["correlation_source"] = "adjacency"
                entry["correlation_id"] = correlation_id
                entry["correlation_source"] = "adjacency"
            pending_calls = []
        else:
            pending_calls = []
        previous_significant = index

    return [
        NormalizedRecord(
            id=f"record-{index:04d}",
            provider=provider,
            session=session,
            timestamp=str(entry["timestamp"]),
            role=str(entry["role"]),
            record_type=str(entry["record_type"]),
            tool_name=str(entry["tool_name"]),
            correlation_id=str(entry["correlation_id"]),
            correlation_source=str(entry["correlation_source"]),
            text=str(entry["text"]),
            source_index=int(entry["source_index"]),
        )
        for index, entry in enumerate(entries)
    ]
