#!/usr/bin/env python3
"""Collect local Codex/Claude history snippets for CodeStable feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CS_PATTERN = re.compile(r"(?:\b(?:cs-[a-z0-9-]+|codestable)\b|\.codestable\b|/goal\b)", re.IGNORECASE)
FAILURE_PATTERN = re.compile(
    r"(failed|failure|error|exception|traceback|timeout|timed out|permission|denied|not found|"
    r"no such file|tool call|apply_patch|file read|read failed|mcp|paseo|gh issue|git clone|early EOF)",
    re.IGNORECASE,
)
USER_CORRECTION_PATTERN = re.compile(
    r"(不对|不是|应该|你没有|你刚才|绕|错|确认后|没有用|没用|wrong|should have|"
    r"you didn't|not what|instead)",
    re.IGNORECASE,
)
GOAL_PATTERN = re.compile(r"/goal|CS_FEATURE_GOAL_|CS_ROADMAP_GOAL_|goal driver|handoff", re.IGNORECASE)
INSTALL_PATTERN = re.compile(r"(plugin|marketplace|install|update|cache|version|codex|claude)", re.IGNORECASE)
PATH_PATTERN = re.compile(r"(?:~[/\\][^\s`'\"<>]+|/(?:[^\s`'\"<>/]+/)+[^\s`'\"<>]+|[A-Za-z]:\\[^\s`'\"<>]+)")
URL_PATTERN = re.compile(r"(?:https?|ssh|git)://[^\s`'\"<>]+")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
REMOTE_PATTERN = re.compile(r"(?:[\w.+-]+@[\w.-]+:[^\s`'\"<>]+)")
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*['\"]?([A-Za-z0-9._~+/=-]{8,})"
)
FEEDBACK_TOKEN_STOPWORDS = {
    "agent",
    "call",
    "current",
    "error",
    "failed",
    "failure",
    "file",
    "read",
    "rule",
    "session",
    "should",
    "tool",
    "unclear",
}


@dataclass
class Event:
    provider: str
    session: str
    path: str
    timestamp: str
    kind: str
    score: int
    reasons: list[str]
    match_types: list[str]
    public_summary: dict[str, str]
    text: str
    context: list[str]


@dataclass(frozen=True)
class Candidate:
    path: str
    provider: str
    session: str
    cwd: str
    mtime: float
    score: int


def redact(text: str, limit: int = 1200) -> str:
    text = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "sk-<redacted>", text)
    text = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "gh_<redacted>", text)
    text = text.replace("\x00", "")
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def public_redact(text: str, limit: int = 300) -> str:
    text = redact(text, limit=limit * 2)
    text = REMOTE_PATTERN.sub("<repo-remote>", text)
    text = URL_PATTERN.sub("<url>", text)
    text = PATH_PATTERN.sub("<local-path>", text)
    text = EMAIL_PATTERN.sub("<email>", text)
    text = re.sub(r"```.*?```", "<code-block>", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key in ("message", "text", "output", "content", "arguments", "name", "type", "role"):
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
    return str(record.get("type", "unknown"))


def score_text(text: str, feedback: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if CS_PATTERN.search(text):
        score += 2
        reasons.append("codestable")
    if FAILURE_PATTERN.search(text):
        score += 3
        reasons.append("failure")
    if USER_CORRECTION_PATTERN.search(text):
        score += 3
        reasons.append("user-correction")
    for token in feedback_tokens(feedback):
        if token.lower() in text.lower():
            score += 1
            if "feedback-token" not in reasons:
                reasons.append("feedback-token")
    return score, reasons


def feedback_tokens(feedback: str) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[A-Za-z0-9_-]{4,}", feedback):
        normalized = token.lower()
        if normalized in FEEDBACK_TOKEN_STOPWORDS:
            continue
        if normalized.startswith("cs-") or "-" in normalized or len(normalized) >= 6:
            tokens.append(token)
    return tokens


def match_types_for(text: str) -> list[str]:
    match_types: list[str] = []
    if FAILURE_PATTERN.search(text):
        match_types.append("tool-failure")
    if GOAL_PATTERN.search(text):
        match_types.append("goal-driver")
    if USER_CORRECTION_PATTERN.search(text):
        match_types.append("user-correction")
    if CS_PATTERN.search(text):
        match_types.append("skill-reference")
    if INSTALL_PATTERN.search(text):
        match_types.append("install-distribution")
    return match_types


def is_relevant_event(match_types: list[str], reasons: list[str]) -> bool:
    if not match_types:
        return False
    if any(match_type in match_types for match_type in ("skill-reference", "user-correction", "goal-driver", "install-distribution")):
        return True
    return "tool-failure" in match_types and "feedback-token" in reasons


def failure_type_for(match_types: list[str], text: str) -> str:
    if "goal-driver" in match_types:
        return "goal-driver"
    if "tool-failure" in match_types:
        return "tool-failure"
    if "install-distribution" in match_types:
        return "install-distribution"
    if "user-correction" in match_types:
        if re.search(r"(规则|没讲清|unclear|should have|应该|没有用|没用)", text, re.IGNORECASE):
            return "unclear-rule"
        return "agent-detour"
    return "unknown"


def skill_reference_from(text: str) -> str:
    match = re.search(r"\b(cs-[a-z0-9-]+)(?:/(references/[^\s`'\"<>]+\.md|scripts/[^\s`'\"<>]+\.py))?", text, re.IGNORECASE)
    if not match:
        return "unknown"
    skill = match.group(1)
    rel = match.group(2)
    return f"{skill}/{rel}" if rel else skill


def tool_name_from(record: dict[str, Any], text: str) -> str:
    payload = record.get("payload")
    if isinstance(payload, dict):
        name = payload.get("name") or payload.get("tool_name") or payload.get("tool")
        if name:
            return public_redact(str(name), limit=80)
    for candidate in ("apply_patch", "read_file", "git", "gh", "paseo", "mcp"):
        if candidate in text.lower():
            return candidate
    return "unknown"


def session_label(session: str) -> str:
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()[:10]
    return f"session-{digest}"


def timestamp_bucket(timestamp: str) -> str:
    if not timestamp:
        return "unknown"
    day = timestamp[:10] if len(timestamp) >= 10 else timestamp
    hour_match = re.search(r"T(\d{2})", timestamp)
    if not hour_match:
        return day
    hour = int(hour_match.group(1))
    if hour < 6:
        part = "night"
    elif hour < 12:
        part = "morning"
    elif hour < 18:
        part = "afternoon"
    else:
        part = "evening"
    return f"{day} {part}"


def public_summary_for(record: dict[str, Any], provider: str, session: str, timestamp: str, text: str, match_types: list[str]) -> dict[str, str]:
    return {
        "provider": provider,
        "session_label": session_label(session),
        "timestamp_bucket": timestamp_bucket(timestamp),
        "failure_type": failure_type_for(match_types, text),
        "match_type": ",".join(match_types),
        "tool_name": tool_name_from(record, text),
        "skill_or_reference": skill_reference_from(text),
        "sanitized_excerpt": public_redact(text),
    }


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


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return []
        return normalize_json_records(value)

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                records.append(value)
    return records


def session_id_from(path: Path, records: list[dict[str, Any]]) -> str:
    for record in records:
        payload = record.get("payload")
        if isinstance(payload, dict):
            session_id = payload.get("session_id") or payload.get("sessionId") or payload.get("id")
            if session_id:
                return str(session_id)
        session_id = record.get("session_id") or record.get("sessionId") or record.get("sessionid") or record.get("id")
        if session_id:
            return str(session_id)
    return path.stem


def cwd_from(records: list[dict[str, Any]]) -> str:
    for record in records:
        payload = record.get("payload")
        if isinstance(payload, dict) and payload.get("cwd"):
            return str(payload["cwd"])
        if record.get("cwd"):
            return str(record["cwd"])
    return ""


def provider_from_path(path: Path) -> str:
    text = str(path)
    if ".codex" in text:
        return "codex"
    if ".claude" in text:
        return "claude"
    return "unknown"


def collect_file(path: Path, feedback: str, max_events: int, context_window: int) -> list[Event]:
    records = read_records(path)
    if not records:
        return []
    provider = provider_from_path(path)
    session = session_id_from(path, records)
    texts = [redact(event_text(record), limit=800) for record in records]
    events: list[Event] = []
    for index, record in enumerate(records):
        text = texts[index]
        score, reasons = score_text(text, feedback)
        match_types = match_types_for(text)
        if not is_relevant_event(match_types, reasons):
            continue
        start = max(0, index - context_window)
        end = min(len(texts), index + context_window + 1)
        timestamp = str(record.get("timestamp") or record.get("created_at") or "")
        summary = public_summary_for(record, provider, session, timestamp, text, match_types)
        events.append(
            Event(
                provider=provider,
                session=session,
                path=str(path),
                timestamp=timestamp,
                kind=event_kind(record),
                score=score,
                reasons=reasons,
                match_types=match_types,
                public_summary=summary,
                text=text,
                context=[texts[pos] for pos in range(start, end)],
            )
        )
    events.sort(key=lambda event: event.score, reverse=True)
    return events[:max_events]


def candidate_for(path: Path, cwd: str | None) -> Candidate:
    records = read_records(path)
    session = session_id_from(path, records)
    transcript_cwd = cwd_from(records)
    score = 0
    if cwd and transcript_cwd == cwd:
        score += 5
    elif cwd and transcript_cwd and (cwd.startswith(transcript_cwd) or transcript_cwd.startswith(cwd)):
        score += 2
    score += int(path.stat().st_mtime // 60)
    return Candidate(
        path=str(path),
        provider=provider_from_path(path),
        session=session,
        cwd=transcript_cwd,
        mtime=path.stat().st_mtime,
        score=score,
    )


def resolve_current_session(files: list[Path], cwd: str | None) -> tuple[list[Path], list[Candidate]]:
    candidates = [candidate_for(path, cwd) for path in files if path.suffix in {".jsonl", ".json"}]
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
        if len(containing) == 1:
            return [Path(containing[0].path)], []
        if len(containing) > 1:
            return [], containing[:5]
    return [], candidates[:5]


def discover_files(
    home: Path,
    since_days: int,
    session_filter: str | None,
    cwd: str | None,
) -> tuple[list[Path], list[Candidate]]:
    roots = [
        home / ".codex/sessions",
        home / ".claude/projects",
        home / ".claude/sessions",
    ]
    if session_filter and session_filter != "current":
        candidate = Path(session_filter).expanduser()
        if candidate.is_file():
            return [candidate], []
    cutoff = time.time() - since_days * 86400
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".jsonl", ".json"}:
                continue
            if path.stat().st_mtime < cutoff:
                continue
            if session_filter and session_filter != "current":
                if session_filter in path.name or session_filter in str(path):
                    files.append(path)
                    continue
                records = read_records(path)
                if session_filter not in session_id_from(path, records):
                    continue
            files.append(path)
    files = sorted(files)
    if session_filter == "current":
        return resolve_current_session(files, cwd)
    return files, []


def main_with_args_for_test(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", default="", help="User's short feedback text")
    parser.add_argument("--since-days", type=int, default=3)
    parser.add_argument("--session", default=None, help="Session id substring or transcript path")
    parser.add_argument("--output", required=True)
    parser.add_argument("--public-output", default=None, help="Write public allowlist context JSON")
    parser.add_argument("--history-root", default=None, help="Override home directory for tests")
    parser.add_argument("--cwd", default=None, help="Current working directory, used by --session current")
    parser.add_argument("--max-events-per-file", type=int, default=5)
    parser.add_argument("--context-window", type=int, default=2)
    args = parser.parse_args(argv)

    home = Path(args.history_root).expanduser() if args.history_root else Path.home()
    cwd = str(Path(args.cwd).expanduser()) if args.cwd else None
    files, ambiguity = discover_files(home, args.since_days, args.session, cwd)
    events: list[Event] = []
    for path in files:
        events.extend(collect_file(path, args.feedback, args.max_events_per_file, args.context_window))
    events.sort(key=lambda event: (event.score, event.timestamp), reverse=True)

    public_issue_context = {
        "privacy": "public-preview",
        "source": "derived-from-local-private-evidence",
        "allowed_fields": [
            "provider",
            "session_label",
            "timestamp_bucket",
            "failure_type",
            "match_type",
            "tool_name",
            "skill_or_reference",
            "sanitized_excerpt",
            "expected_behavior",
            "actual_behavior",
            "proposed_fix",
        ],
        "events": [event.public_summary for event in events[:8]],
    }
    payload = {
        "feedback": args.feedback,
        "privacy": "local-private",
        "public_upload_allowed": False,
        "redaction": "best-effort",
        "since_days": args.since_days,
        "session_filter": args.session,
        "history_root": str(home),
        "cwd": cwd,
        "searched_files": [str(path) for path in files],
        "ambiguity": {"candidates": [asdict(candidate) for candidate in ambiguity]},
        "matched_events": [asdict(event) for event in events],
        "public_issue_context": public_issue_context,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_output = Path(args.public_output).expanduser() if args.public_output else output.with_name("public-issue-context.json")
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(json.dumps(public_issue_context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    return main_with_args_for_test()


if __name__ == "__main__":
    raise SystemExit(main())
