from __future__ import annotations

from dataclasses import dataclass


V1_FAILURE_MAP = {
    "wrong-route": "agent-detour",
    "skipped-gate": "agent-detour",
    "missing-artifact": "agent-detour",
    "unnecessary-detour": "agent-detour",
    "tool-failure": "tool-failure",
    "goal-driver": "goal-driver",
    "install-version": "install-distribution",
    "unclear-rule": "unclear-rule",
    "privacy-reporting": "unknown",
    "unknown": "unknown",
}

PUBLIC_EVENT_FIELDS = [
    "provider",
    "session_label",
    "timestamp_bucket",
    "failure_type",
    "match_type",
    "tool_name",
    "skill_or_reference",
    "sanitized_excerpt",
]

PUBLIC_INCIDENT_FIELDS = [
    "incident_kind",
    "target_skill",
    "stage_hint",
    "expected_behavior",
    "actual_behavior",
    "impact",
    "proposed_fix",
]


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


@dataclass(frozen=True)
class SessionMeta:
    session: str
    cwd: str


@dataclass
class NormalizedRecord:
    id: str
    provider: str
    session: str
    timestamp: str
    role: str
    record_type: str
    tool_name: str
    correlation_id: str
    correlation_source: str
    text: str
    source_index: int


@dataclass
class FeedbackIncident:
    id: str
    target_skill: str
    stage_hint: str
    incident_kind: str
    observations: list[dict[str, object]]
    timeline: list[dict[str, object]]
    environment_context: dict[str, object]
    repo_context: dict[str, object]
    user_correction: dict[str, object]
    capture_cutoff: str
