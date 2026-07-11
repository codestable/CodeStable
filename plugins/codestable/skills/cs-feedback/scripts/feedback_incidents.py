from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from feedback_models import (
    Event,
    FeedbackIncident,
    NormalizedRecord,
    PUBLIC_INCIDENT_FIELDS,
    V1_FAILURE_MAP,
)
from feedback_privacy import public_redact, redact
from feedback_repo_context import build_repo_context, environment_context, session_label
from feedback_transcripts import (
    event_kind,
    event_text,
    normalize_records,
    provider_from_path,
    read_transcript_snapshot,
    session_id_from,
)


CS_PATTERN = re.compile(
    r"(?:\b(?:cs-[a-z0-9-]+|codestable)\b|\.codestable\b|/goal\b)", re.IGNORECASE
)
FAILURE_PATTERN = re.compile(
    r"(failed|failure|error|exception|traceback|timeout|timed out|permission|denied|not found|"
    r"no such file|tool call|apply_patch|file read|read failed|mcp|paseo|gh issue|git clone|early EOF)",
    re.IGNORECASE,
)
USER_CORRECTION_PATTERN = re.compile(
    r"(不对|不是|应该|应当|需要|必须|你没有|你刚才|绕|错|确认后|没有用|没用|wrong|should have|"
    r"you didn't|not what|instead)",
    re.IGNORECASE,
)
GOAL_PATTERN = re.compile(
    r"/goal|CS_FEATURE_GOAL_|CS_ROADMAP_GOAL_|goal driver|handoff", re.IGNORECASE
)
INSTALL_PATTERN = re.compile(
    r"(plugin|marketplace|install|update|cache|version|codex|claude)", re.IGNORECASE
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
    if any(
        match_type in match_types
        for match_type in (
            "skill-reference",
            "user-correction",
            "goal-driver",
            "install-distribution",
        )
    ):
        return True
    return "tool-failure" in match_types and "feedback-token" in reasons


def incident_kind_for(match_types: list[str], text: str) -> str:
    if re.search(r"(privacy|隐私|上传|public preview|reporting)", text, re.IGNORECASE):
        return "privacy-reporting"
    if re.search(r"(missing artifact|缺少.{0,8}(?:产物|文件)|未生成)", text, re.IGNORECASE):
        return "missing-artifact"
    if re.search(r"(绕路|多余|unnecessary|detour)", text, re.IGNORECASE):
        return "unnecessary-detour"
    if "user-correction" in match_types and re.search(
        r"(gate|review|确认后|跳过|skipped)", text, re.IGNORECASE
    ):
        return "skipped-gate"
    if "goal-driver" in match_types:
        return "goal-driver"
    if "tool-failure" in match_types:
        return "tool-failure"
    if "install-distribution" in match_types:
        return "install-version"
    if "user-correction" in match_types:
        if re.search(
            r"(规则|没讲清|unclear|should have|应该|没有用|没用)", text, re.IGNORECASE
        ):
            return "unclear-rule"
        return "wrong-route"
    return "unknown"


def failure_type_for(match_types: list[str], text: str) -> str:
    return V1_FAILURE_MAP.get(incident_kind_for(match_types, text), "unknown")


def skill_reference_from(text: str) -> str:
    match = re.search(
        r"\b(cs-[a-z0-9-]+)(?:/(references/[^\s`'\"<>]+\.md|scripts/[^\s`'\"<>]+\.py))?",
        text,
        re.IGNORECASE,
    )
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


def public_summary_for(
    record: dict[str, Any],
    provider: str,
    session: str,
    timestamp: str,
    text: str,
    match_types: list[str],
) -> dict[str, str]:
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


def collect_file(
    path: Path,
    feedback: str,
    max_events: int,
    context_window: int,
    records: list[dict[str, Any]] | None = None,
) -> list[Event]:
    if records is None:
        records, _capture = read_transcript_snapshot(path)
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


def _trigger_cutoff(records: list[NormalizedRecord]) -> int | None:
    for index in range(len(records) - 1, -1, -1):
        if records[index].role == "user":
            return index
    return None


def public_incident(
    incident: dict[str, object], triage: dict[str, object]
) -> dict[str, str]:
    assessment = (
        triage.get("assessment", {}) if isinstance(triage.get("assessment"), dict) else {}
    )

    def value(name: str) -> str:
        item = assessment.get(name, {})
        if isinstance(item, dict):
            return public_redact(str(item.get("value") or "unknown"))
        return "unknown"

    projected = {
        "incident_kind": public_redact(str(incident.get("incident_kind") or "unknown")),
        "target_skill": public_redact(str(incident.get("target_skill") or "unknown")),
        "stage_hint": public_redact(str(incident.get("stage_hint") or "unknown")),
        "expected_behavior": value("expected_behavior"),
        "actual_behavior": value("actual_behavior"),
        "impact": value("impact"),
        "proposed_fix": value("proposed_fix"),
    }
    return {field: projected[field] for field in PUBLIC_INCIDENT_FIELDS}


def _incident_windows(
    records: list[NormalizedRecord], cutoff: int | None
) -> list[list[NormalizedRecord]]:
    eligible = records[: cutoff + 1] if cutoff is not None else records
    if cutoff is None:
        return [eligible] if eligible else []
    windows: list[list[NormalizedRecord]] = []
    start = 0
    for index, record in enumerate(eligible):
        if record.role == "user":
            windows.append(eligible[start : index + 1])
            start = index + 1
    return windows


def _merge_correlated_windows(
    windows: list[list[NormalizedRecord]],
) -> list[list[NormalizedRecord]]:
    merged: list[list[NormalizedRecord]] = []
    for window in windows:
        correlations = {record.correlation_id for record in window if record.correlation_id}
        merge_at = [
            index
            for index, existing in enumerate(merged)
            if correlations
            & {record.correlation_id for record in existing if record.correlation_id}
        ]
        if not merge_at:
            merged.append(window)
        else:
            insert_at = merge_at[0]
            combined = [*window]
            for index in reversed(merge_at):
                combined.extend(merged.pop(index))
            unique = {
                (record.provider, record.session, record.id): record for record in combined
            }
            merged.insert(
                insert_at,
                sorted(
                    unique.values(),
                    key=lambda record: int(record.id.rsplit("-", 1)[-1]),
                ),
            )
    return merged


INCIDENT_KIND_PRIORITY = [
    "privacy-reporting",
    "skipped-gate",
    "missing-artifact",
    "wrong-route",
    "unnecessary-detour",
    "goal-driver",
    "tool-failure",
    "install-version",
    "unclear-rule",
]


def _incident_kind(records: list[NormalizedRecord]) -> str:
    kinds = {
        incident_kind_for(match_types_for(record.text), record.text) for record in records
    }
    return next((kind for kind in INCIDENT_KIND_PRIORITY if kind in kinds), "unknown")


def _incident_from_window(
    window: list[NormalizedRecord],
    feedback: str,
    incident_number: int,
    observation_start: int,
    environment: dict[str, object],
    repo_context: dict[str, object],
) -> tuple[dict[str, object], int] | None:
    meaningful = [record for record in window if record.record_type != "session_meta"]
    relevant = []
    for record in meaningful:
        score, reasons = score_text(record.text, feedback)
        match_types = match_types_for(record.text)
        if is_relevant_event(match_types, reasons):
            relevant.append(record)
    if not relevant:
        return None

    correction_records = [
        record
        for record in meaningful
        if record.role == "user" and USER_CORRECTION_PATTERN.search(record.text)
    ]
    target_skill = "unknown"
    for record in [*reversed(correction_records), *relevant]:
        target_skill = skill_reference_from(record.text)
        if target_skill != "unknown":
            target_skill = target_skill.split("/", 1)[0]
            break
    stage_hint = "unknown"
    for record in [*reversed(correction_records), *relevant]:
        stage_match = re.search(
            r"\b(design-review|design|review|qa|acceptance|implementation|goal)\b",
            record.text,
            re.IGNORECASE,
        )
        if stage_match:
            stage_hint = stage_match.group(1).lower()
            break

    observations: list[dict[str, object]] = []
    for offset, record in enumerate(meaningful):
        observations.append(
            {
                "id": f"obs-{observation_start + offset:04d}",
                "record_id": record.id,
                "source_index": record.source_index,
                "role": record.role,
                "record_type": record.record_type,
                "text": record.text,
            }
        )
    obs_by_record = {
        str(observation["record_id"]): str(observation["id"])
        for observation in observations
    }
    timeline = [
        {
            "record_id": record.id,
            "role": record.role,
            "record_type": record.record_type,
            "tool_name": record.tool_name,
            "correlation_id": record.correlation_id,
            "correlation_source": record.correlation_source,
            "observation_id": obs_by_record.get(record.id, ""),
        }
        for record in meaningful
    ]
    correction_ids = {record.id for record in correction_records}
    user_correction = next(
        (
            observation
            for observation in reversed(observations)
            if observation["record_id"] in correction_ids
        ),
        {},
    )
    user_records = [record for record in meaningful if record.role == "user"]
    incident = FeedbackIncident(
        id=f"incident-{incident_number:02d}",
        target_skill=target_skill,
        stage_hint=stage_hint,
        incident_kind=_incident_kind(relevant),
        observations=observations,
        timeline=timeline,
        environment_context=environment,
        repo_context=repo_context,
        user_correction=user_correction,
        capture_cutoff=user_records[-1].id if user_records else "unknown",
    )
    return asdict(incident), observation_start + len(observations)


def build_incident_payload(
    paths: list[Path],
    feedback: str,
    cwd: str | None,
    records_by_path: dict[Path, list[dict[str, Any]]] | None = None,
    captures_by_path: dict[Path, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    incidents: list[dict[str, object]] = []
    primary_candidates: list[dict[str, object]] = []
    observation_number = 1
    repo_context = build_repo_context(cwd)
    for path in paths:
        if records_by_path is not None and path in records_by_path:
            raw_records = records_by_path[path]
            capture = (captures_by_path or {}).get(path, {})
        else:
            raw_records, capture = read_transcript_snapshot(path)
        records = normalize_records(path, raw_records)
        cutoff = _trigger_cutoff(records)
        trigger_id = records[cutoff].id if cutoff is not None else None
        windows = _merge_correlated_windows(_incident_windows(records, cutoff))
        environment = environment_context(path, raw_records, capture)
        for window in windows:
            built = _incident_from_window(
                window,
                feedback,
                len(incidents) + 1,
                observation_number,
                environment,
                repo_context,
            )
            if built is None:
                continue
            incident, observation_number = built
            incidents.append(incident)
            if trigger_id and any(
                item.get("record_id") == trigger_id
                for item in incident.get("timeline", [])
                if isinstance(item, dict)
            ):
                primary_candidates.append(incident)
    primary = primary_candidates[0] if len(primary_candidates) == 1 else None
    return incidents, primary


def records_through_trigger(
    path: Path, records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    normalized = normalize_records(path, records)
    cutoff = _trigger_cutoff(normalized)
    if cutoff is None:
        return records
    return records[: normalized[cutoff].source_index + 1]
