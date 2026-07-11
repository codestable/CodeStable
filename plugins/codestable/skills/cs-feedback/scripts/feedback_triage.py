from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any


ROUTING_INCIDENT_KINDS = {
    "wrong-route",
    "skipped-gate",
    "missing-artifact",
    "goal-driver",
    "unnecessary-detour",
}
FINDINGS_INCIDENT_KINDS = {
    "tool-failure",
    "install-version",
    "privacy-reporting",
    "unclear-rule",
}
ASSESSMENT_SOURCES = {"user", "transcript", "inferred"}
TASK_KIND_BY_TARGET = {
    "cs-code-review": "review",
    "cs-issue": "fix",
    "cs-audit": "audit",
    "cs-feat": "design",
    "cs-refactor": "design",
    "cs-epic": "design",
    "cs-req": "design",
    "cs-domain": "design",
    "cs-docs": "docs",
    "cs-docs-neat": "docs",
}
EXPECTED_PATTERN = re.compile(
    r"(应该|应当|本应|必须|需要|要先|要再|正确.{0,8}(?:是|为)|should|expected|must|instead)",
    re.IGNORECASE,
)


def field(
    value: str,
    source: str,
    refs: list[str],
    confidence: str | None = None,
) -> dict[str, object]:
    out: dict[str, object] = {
        "value": value,
        "source": source,
        "evidence_refs": refs,
    }
    if source == "inferred":
        out["confidence"] = confidence or "medium"
    return out


def profile_for(incident_kind: str) -> str:
    if incident_kind in ROUTING_INCIDENT_KINDS:
        return "routing-decision"
    if incident_kind in FINDINGS_INCIDENT_KINDS:
        return "findings-recall"
    return "unknown"


def task_kind_for(target_skill: str, profile: str) -> str:
    if profile == "routing-decision":
        return "routing"
    if profile == "findings-recall":
        return TASK_KIND_BY_TARGET.get(target_skill, "unknown")
    return "unknown"


def empty_triage() -> dict[str, Any]:
    triage = {
        "schema_version": 2,
        "privacy": "local-private",
        "incident_id": "",
        "incident_fingerprint": "",
        "observation_ids": [],
        "trigger_cutoff": "unknown",
        "target": {
            "skill": "unknown",
            "stage_hint": "unknown",
            "suspected_area": "unknown",
        },
        "incident_kind": "unknown",
        "assessment": {
            "expected_behavior": field("unknown", "unknown", []),
            "actual_behavior": field("unknown", "unknown", []),
            "impact": field("unknown", "unknown", []),
            "proposed_fix": field("unknown", "unknown", []),
            "cause_status": "unclassified",
        },
        "reproduction": {
            "eval_profile": "unknown",
            "task_kind": "unknown",
            "input": None,
            "oracle": None,
            "evidence_refs": [],
        },
        "environment_context": {"provider": "unknown", "session": "unknown"},
        "repo_context": {
            "runtime": {"status": "unknown"},
            "artifacts": [],
            "git_status": [],
        },
        "quality": {},
        "privacy_review": {"status": "pending"},
    }
    triage["quality"] = recompute_quality(triage)
    return triage


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "todo", "tbd"}
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _assessment_from_incident(incident: dict[str, Any]) -> dict[str, Any]:
    observations = [
        observation
        for observation in incident.get("observations", [])
        if isinstance(observation, dict)
    ]
    correction = incident.get("user_correction")
    if not isinstance(correction, dict):
        correction = {}
    correction_text = str(correction.get("text") or "")
    expected = field("unknown", "unknown", [])
    if correction_text and EXPECTED_PATTERN.search(correction_text):
        expected = field(correction_text, "user", [str(correction.get("id"))])

    correction_index = correction.get("source_index")
    actual_candidates = [
        observation
        for observation in observations
        if observation.get("role") in {"assistant", "tool"}
        and (
            not isinstance(correction_index, int)
            or not isinstance(observation.get("source_index"), int)
            or int(observation["source_index"]) < correction_index
        )
    ]
    actual = field("unknown", "unknown", [])
    if actual_candidates:
        observation = actual_candidates[-1]
        actual = field(
            str(observation.get("text") or "unknown"),
            "transcript",
            [str(observation.get("id"))],
        )

    expected_refs = list(expected.get("evidence_refs") or [])
    actual_refs = list(actual.get("evidence_refs") or [])
    impact = field("unknown", "unknown", [])
    if expected_refs and actual_refs:
        impact = field(
            "反馈 gate 或工具行为偏离预期，需要维护者分诊",
            "inferred",
            [*actual_refs, *expected_refs],
            "medium",
        )
    return {
        "expected_behavior": expected,
        "actual_behavior": actual,
        "impact": impact,
        "proposed_fix": field("unknown", "unknown", []),
        "cause_status": "unclassified",
    }


def incident_fingerprint(incident: dict[str, Any]) -> str:
    environment = incident.get("environment_context")
    environment = environment if isinstance(environment, dict) else {}
    observations = [
        {
            "record_id": str(observation.get("record_id") or ""),
            "role": str(observation.get("role") or "unknown"),
            "record_type": str(observation.get("record_type") or "unknown"),
            "text": str(observation.get("text") or ""),
        }
        for observation in incident.get("observations", [])
        if isinstance(observation, dict)
    ]
    identity = {
        "provider": str(environment.get("provider") or "unknown"),
        "session": str(environment.get("session") or "unknown"),
        "capture_cutoff": str(incident.get("capture_cutoff") or "unknown"),
        "target_skill": str(incident.get("target_skill") or "unknown"),
        "stage_hint": str(incident.get("stage_hint") or "unknown"),
        "incident_kind": str(incident.get("incident_kind") or "unknown"),
        "observations": observations,
    }
    encoded = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_triage(
    incidents: list[dict[str, Any]], primary_incident: dict[str, Any] | None
) -> dict[str, Any]:
    context_incident = primary_incident
    if context_incident is None and len(incidents) == 1:
        context_incident = incidents[0]
    if context_incident is None:
        return empty_triage()

    incident_kind = str(context_incident.get("incident_kind") or "unknown")
    target_skill = str(context_incident.get("target_skill") or "unknown")
    profile = profile_for(incident_kind)
    trigger_cutoff = (
        str(context_incident.get("capture_cutoff") or "unknown")
        if primary_incident is not None
        else "unknown"
    )
    triage = {
        "schema_version": 2,
        "privacy": "local-private",
        "incident_id": str(context_incident.get("id") or "")
        if primary_incident is not None
        else "",
        "incident_fingerprint": incident_fingerprint(context_incident)
        if primary_incident is not None
        else "",
        "observation_ids": [
            str(observation.get("id"))
            for observation in context_incident.get("observations", [])
            if isinstance(observation, dict) and _meaningful(observation.get("id"))
        ],
        "trigger_cutoff": trigger_cutoff,
        "target": {
            "skill": target_skill,
            "stage_hint": str(context_incident.get("stage_hint") or "unknown"),
            "suspected_area": "unknown",
        },
        "incident_kind": incident_kind,
        "assessment": _assessment_from_incident(context_incident),
        "reproduction": {
            "eval_profile": profile,
            "task_kind": task_kind_for(target_skill, profile),
            "input": None,
            "oracle": None,
            "evidence_refs": [],
        },
        "environment_context": copy.deepcopy(
            context_incident.get("environment_context")
            or {"provider": "unknown", "session": "unknown"}
        ),
        "repo_context": copy.deepcopy(
            context_incident.get("repo_context")
            or {"runtime": {"status": "unknown"}, "artifacts": [], "git_status": []}
        ),
        "quality": {},
        "privacy_review": {"status": "pending"},
    }
    triage["quality"] = recompute_quality(triage)
    return triage


def _field_gaps(
    triage: dict[str, Any], name: str, *, required: bool = True
) -> list[str]:
    assessment = triage.get("assessment")
    value = assessment.get(name) if isinstance(assessment, dict) else None
    prefix = f"assessment.{name}"
    if not isinstance(value, dict):
        return [prefix] if required else []
    gaps: list[str] = []
    has_value = _meaningful(value.get("value"))
    active = required or has_value
    if required and not has_value:
        gaps.append(prefix)
    source = value.get("source")
    if active and source not in ASSESSMENT_SOURCES:
        gaps.append(f"{prefix}.source")
    refs = value.get("evidence_refs")
    observation_ids = triage.get("observation_ids")
    allowed_refs = (
        {ref for ref in observation_ids if isinstance(ref, str) and _meaningful(ref)}
        if isinstance(observation_ids, list)
        else set()
    )
    valid_refs = (
        isinstance(refs, list)
        and bool(refs)
        and all(isinstance(ref, str) and _meaningful(ref) for ref in refs)
        and set(refs).issubset(allowed_refs)
    )
    if active and not valid_refs:
        gaps.append(f"{prefix}.evidence_refs")
    if source == "inferred" and not (
        isinstance(value.get("confidence"), str)
        and _meaningful(value.get("confidence"))
    ):
        gaps.append(f"{prefix}.confidence")
    return gaps


def _reproduction_gaps(triage: dict[str, Any]) -> tuple[list[str], list[str]]:
    reproduction = triage.get("reproduction")
    if not isinstance(reproduction, dict):
        return ["reproduction"], []
    target = triage.get("target") if isinstance(triage.get("target"), dict) else {}
    target_skill = str(target.get("skill") or "unknown")
    incident_kind = str(triage.get("incident_kind") or "unknown")
    profile = str(reproduction.get("eval_profile") or "unknown")
    task_kind = str(reproduction.get("task_kind") or "unknown")
    input_data = reproduction.get("input")
    oracle = reproduction.get("oracle")
    gaps: list[str] = []
    reasons: list[str] = []

    if profile not in {"routing-decision", "findings-recall"}:
        gaps.extend(
            ["reproduction.eval_profile", "reproduction.input", "reproduction.oracle"]
        )
        return gaps, reasons
    if profile == "routing-decision":
        if incident_kind not in ROUTING_INCIDENT_KINDS:
            gaps.append("reproduction.eval_profile")
            reasons.append("profile_incident_kind_mismatch")
        if task_kind != "routing":
            gaps.append("reproduction.task_kind")
        if not isinstance(input_data, dict) or not any(
            _meaningful(input_data.get(key)) for key in ("state", "intent", "utterance")
        ):
            gaps.append("reproduction.input")
        expect = oracle.get("expect") if isinstance(oracle, dict) else None
        if not isinstance(expect, dict) or not _meaningful(expect.get("result_type")):
            gaps.append("reproduction.oracle.expect.result_type")
    else:
        if incident_kind not in FINDINGS_INCIDENT_KINDS:
            gaps.append("reproduction.eval_profile")
            reasons.append("profile_incident_kind_mismatch")
        derived_kind = TASK_KIND_BY_TARGET.get(target_skill)
        if not derived_kind:
            gaps.append("reproduction.task_kind")
            reasons.append("unsupported_target")
        elif task_kind != derived_kind:
            gaps.append("reproduction.task_kind")
        if not isinstance(input_data, dict):
            gaps.append("reproduction.input")
        else:
            if task_kind in {"review", "audit"} and not _meaningful(input_data.get("diff")):
                gaps.append("reproduction.input.diff")
            if task_kind == "fix" and (
                not _meaningful(input_data.get("spec"))
                or not _meaningful(input_data.get("diff"))
            ):
                gaps.append("reproduction.input.spec_or_diff")
            if task_kind == "design" and not _meaningful(input_data.get("spec")):
                gaps.append("reproduction.input.spec")
            if task_kind == "docs" and (
                not _meaningful(input_data.get("spec"))
                or not _meaningful(input_data.get("diff"))
            ):
                gaps.append("reproduction.input.spec_or_diff")
        coverage = oracle.get("coverage_points") if isinstance(oracle, dict) else None
        if not isinstance(coverage, list) or not coverage or not all(
            _meaningful(item) for item in coverage
        ):
            gaps.append("reproduction.oracle.coverage_points")
    return gaps, reasons


def recompute_quality(triage: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    incident_id = str(triage.get("incident_id") or "")
    if not incident_id:
        missing.append("incident")
    if str(triage.get("trigger_cutoff") or "unknown") == "unknown":
        missing.append("trigger_cutoff")
    target = triage.get("target") if isinstance(triage.get("target"), dict) else {}
    if not _meaningful(target.get("skill")):
        missing.append("target.skill")
    triage_gaps = [
        *_field_gaps(triage, "expected_behavior"),
        *_field_gaps(triage, "actual_behavior"),
        *_field_gaps(triage, "impact", required=False),
        *_field_gaps(triage, "proposed_fix", required=False),
    ]
    missing.extend(triage_gaps)
    identity_gaps = {"incident", "trigger_cutoff", "target.skill"}
    triage_ready = not identity_gaps.intersection(missing) and not triage_gaps

    reproduction_gaps, reasons = _reproduction_gaps(triage)
    missing.extend(reproduction_gaps)
    missing = list(dict.fromkeys(missing))
    if reproduction_gaps:
        reasons.insert(0, "regression_requires_replayable_input_and_oracle")
    priority = [
        "incident",
        "trigger_cutoff",
        "target.skill",
        *triage_gaps,
        *reproduction_gaps,
    ]
    next_question = next((item for item in priority if item in missing), None)
    return {
        "triage_ready": triage_ready,
        "regression_ready": triage_ready and not reproduction_gaps,
        "missing_fields": missing,
        "reasons": list(dict.fromkeys(reasons)),
        "next_questions": [next_question] if next_question else [],
    }


def _merge_prefer_existing(generated: Any, existing: Any) -> Any:
    if isinstance(generated, dict) and isinstance(existing, dict):
        return {
            key: _merge_prefer_existing(generated.get(key), existing.get(key))
            if key in existing
            else copy.deepcopy(value)
            for key, value in generated.items()
        } | {
            key: copy.deepcopy(value)
            for key, value in existing.items()
            if key not in generated
        }
    return copy.deepcopy(existing) if _meaningful(existing) else copy.deepcopy(generated)


def _has_user_supplements(existing: dict[str, Any]) -> bool:
    reproduction = existing.get("reproduction")
    if isinstance(reproduction, dict) and any(
        _meaningful(reproduction.get(key)) for key in ("input", "oracle", "evidence_refs")
    ):
        return True
    privacy_review = existing.get("privacy_review")
    if isinstance(privacy_review, dict):
        status = privacy_review.get("status")
        if _meaningful(status) and str(status) != "pending":
            return True
    assessment = existing.get("assessment")
    if isinstance(assessment, dict):
        return any(
            isinstance(item, dict) and _meaningful(item.get("value"))
            for item in assessment.values()
        )
    return False


def _preserve_unresolved_triage(
    generated: dict[str, Any], existing: dict[str, Any]
) -> dict[str, Any]:
    preserved = copy.deepcopy(existing)
    existing_id = str(existing.get("incident_id") or "")
    generated_id = str(generated.get("incident_id") or "")
    existing_fingerprint = str(existing.get("incident_fingerprint") or "")
    generated_fingerprint = str(generated.get("incident_fingerprint") or "")
    preserved["previous_incident_id"] = existing_id or str(
        existing.get("previous_incident_id") or ""
    )
    preserved["previous_incident_fingerprint"] = existing_fingerprint or str(
        existing.get("previous_incident_fingerprint") or ""
    )
    if generated_id:
        preserved["pending_incident_id"] = generated_id
        preserved["pending_incident_fingerprint"] = generated_fingerprint
    else:
        preserved["pending_incident_id"] = str(
            existing.get("pending_incident_id") or ""
        )
        preserved["pending_incident_fingerprint"] = str(
            existing.get("pending_incident_fingerprint") or ""
        )
    preserved["incident_id"] = ""
    preserved["incident_fingerprint"] = ""
    preserved["observation_ids"] = []
    preserved["trigger_cutoff"] = "unknown"
    preserved["environment_context"] = generated.get("environment_context", {})
    preserved["repo_context"] = generated.get("repo_context", {})
    quality = recompute_quality(preserved)
    if generated_id and existing_id == generated_id:
        reason = "incident_identity_changed"
    elif generated_id:
        reason = "incident_id_changed"
    else:
        reason = "incident_resolution_failed"
    quality["reasons"] = list(dict.fromkeys([reason, *quality["reasons"]]))
    preserved["quality"] = quality
    return preserved


def merge_existing_triage(
    generated: dict[str, Any], existing: dict[str, Any] | None
) -> dict[str, Any]:
    if not isinstance(existing, dict) or existing.get("privacy") != "local-private":
        return generated
    generated_id = str(generated.get("incident_id") or "")
    existing_id = str(existing.get("incident_id") or "")
    generated_fingerprint = str(generated.get("incident_fingerprint") or "")
    existing_fingerprint = str(existing.get("incident_fingerprint") or "")
    fingerprint_changed = bool(
        generated_id
        and generated_id == existing_id
        and generated_fingerprint != existing_fingerprint
    )
    if generated_id != existing_id or fingerprint_changed:
        if (
            existing_id
            or existing.get("pending_incident_id")
            or _has_user_supplements(existing)
        ):
            return _preserve_unresolved_triage(generated, existing)
        return generated
    if not generated_id:
        if existing.get("pending_incident_id") or _has_user_supplements(existing):
            return _preserve_unresolved_triage(generated, existing)
        return generated

    preserved = copy.deepcopy(existing)
    preserved.pop("quality", None)
    merged = _merge_prefer_existing(generated, preserved)
    merged["schema_version"] = 2
    merged["privacy"] = "local-private"
    merged["incident_fingerprint"] = generated_fingerprint
    merged["observation_ids"] = copy.deepcopy(generated.get("observation_ids", []))
    merged["trigger_cutoff"] = generated.get("trigger_cutoff", "unknown")
    merged["environment_context"] = generated.get("environment_context", {})
    merged["repo_context"] = generated.get("repo_context", {})
    merged.pop("previous_incident_id", None)
    merged.pop("previous_incident_fingerprint", None)
    merged.pop("pending_incident_id", None)
    merged.pop("pending_incident_fingerprint", None)
    merged["quality"] = recompute_quality(merged)
    return merged


def accept_pending_incident(
    generated: dict[str, Any],
    existing: dict[str, Any] | None,
    accepted_incident_id: str,
) -> dict[str, Any]:
    accepted_id = accepted_incident_id.strip()
    if not accepted_id:
        raise ValueError("accepted incident id must not be empty")
    if not isinstance(existing, dict) or existing.get("privacy") != "local-private":
        raise ValueError("existing local-private triage is required")
    pending_id = str(existing.get("pending_incident_id") or "")
    generated_id = str(generated.get("incident_id") or "")
    if pending_id != accepted_id:
        raise ValueError(
            f"accepted incident {accepted_id} does not match pending incident {pending_id or 'none'}"
        )
    if generated_id != accepted_id:
        raise ValueError(
            f"accepted incident {accepted_id} is not the current primary incident"
        )
    generated_fingerprint = str(generated.get("incident_fingerprint") or "")
    if not generated_fingerprint:
        raise ValueError("current primary incident has no fingerprint")
    pending_fingerprint = str(existing.get("pending_incident_fingerprint") or "")
    if pending_fingerprint and pending_fingerprint != generated_fingerprint:
        raise ValueError("pending incident fingerprint no longer matches current primary")

    accepted = copy.deepcopy(generated)
    reproduction = existing.get("reproduction")
    if isinstance(reproduction, dict):
        accepted["reproduction"] = copy.deepcopy(reproduction)
    assessment = existing.get("assessment")
    if isinstance(assessment, dict):
        accepted["previous_assessment"] = copy.deepcopy(assessment)
    privacy_review = existing.get("privacy_review")
    if isinstance(privacy_review, dict):
        accepted["previous_privacy_review"] = copy.deepcopy(privacy_review)
    accepted["privacy_review"] = {"status": "pending"}
    accepted["quality"] = recompute_quality(accepted)
    return accepted
