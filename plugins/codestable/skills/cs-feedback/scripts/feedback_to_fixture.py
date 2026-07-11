#!/usr/bin/env python3
"""Convert cs-feedback triage into a local regression candidate artifact.

The shipped cs-feedback skill does not write official experiment fixtures.
It only creates `regression-candidate.json` next to `triage.json`; the
repo-local eval skill owns promotion into an experiment directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from feedback_triage import (  # noqa: E402
    incident_fingerprint,
    profile_for,
    recompute_quality,
    task_kind_for,
)


def _slug(text: str, n: int = 6) -> str:
    words = re.findall(r"[0-9a-zA-Z]+", text.lower())
    return "-".join(words[:n]) or "case"


def _field(data: dict, *path: str, default=None):
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _load_canonical_triage(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("triage must be a JSON object")
    if path.name != "triage.json":
        raise ValueError("canonical input must be named triage.json")
    if data.get("schema_version") != 2:
        raise ValueError("triage schema_version must be 2")
    if data.get("privacy") != "local-private":
        raise ValueError("triage privacy must be local-private")
    incident_id = data.get("incident_id")
    if not isinstance(incident_id, str) or not incident_id.strip():
        raise ValueError("triage incident_id must be selected")
    for key in ("target", "assessment", "reproduction", "privacy_review"):
        if not isinstance(data.get(key), dict):
            raise ValueError(f"triage {key} must be a JSON object")
    _validate_evidence_binding(path.with_name("evidence.json"), data)
    return data


def _validate_evidence_binding(path: Path, triage: dict) -> None:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be a JSON object")
    if evidence.get("schema_version") != 2 or evidence.get("privacy") != "local-private":
        raise ValueError("evidence must be canonical local-private schema v2")
    incidents = evidence.get("incidents")
    if not isinstance(incidents, list):
        raise ValueError("evidence incidents must be a JSON array")
    selected = [
        incident
        for incident in incidents
        if isinstance(incident, dict) and incident.get("id") == triage["incident_id"]
    ]
    if len(selected) != 1:
        raise ValueError("triage incident_id must select exactly one evidence incident")
    incident = selected[0]
    observations = incident.get("observations")
    if not isinstance(observations, list) or not all(
        isinstance(observation, dict) for observation in observations
    ):
        raise ValueError("selected evidence incident observations must be objects")
    canonical_ids = [observation.get("id") for observation in observations]
    if not all(isinstance(item, str) and item.strip() for item in canonical_ids):
        raise ValueError("selected evidence observations must have string ids")
    if len(set(canonical_ids)) != len(canonical_ids):
        raise ValueError("selected evidence observation ids must be unique")
    triage_ids = triage.get("observation_ids")
    if triage_ids != canonical_ids:
        raise ValueError("triage observation_ids do not match selected evidence incident")
    fingerprint = triage.get("incident_fingerprint")
    if not isinstance(fingerprint, str) or fingerprint != incident_fingerprint(incident):
        raise ValueError("triage incident_fingerprint does not match evidence")
    if triage.get("trigger_cutoff") != incident.get("capture_cutoff"):
        raise ValueError("triage trigger_cutoff does not match evidence")

    referenced_ids: list[str] = []
    assessment = triage["assessment"]
    for field_name in (
        "expected_behavior",
        "actual_behavior",
        "impact",
        "proposed_fix",
    ):
        field = assessment.get(field_name)
        if not isinstance(field, dict):
            continue
        refs = field.get("evidence_refs", [])
        if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
            raise ValueError(f"triage assessment.{field_name}.evidence_refs must be strings")
        referenced_ids.extend(refs)
    reproduction_refs = triage["reproduction"].get("evidence_refs", [])
    if not isinstance(reproduction_refs, list) or not all(
        isinstance(ref, str) for ref in reproduction_refs
    ):
        raise ValueError("triage reproduction.evidence_refs must be strings")
    referenced_ids.extend(reproduction_refs)
    if set(referenced_ids) - set(canonical_ids):
        raise ValueError("triage evidence_refs must belong to selected evidence incident")


def _candidate_from_triage(path: Path) -> dict:
    data = _load_canonical_triage(path)
    target_skill = _field(data, "target", "skill", default="unknown")
    incident_kind = data.get("incident_kind", "unknown")
    reproduction = data["reproduction"]
    profile = reproduction.get("eval_profile") or "unknown"
    expected_profile = profile_for(str(incident_kind))
    task_kind = task_kind_for(str(target_skill), str(profile))
    input_data = reproduction.get("input") if isinstance(reproduction.get("input"), dict) else {}
    oracle = reproduction.get("oracle") if isinstance(reproduction.get("oracle"), dict) else {}
    quality = recompute_quality(data)
    privacy_review = data["privacy_review"]

    candidate = {
        "id": (
            f"reg-{_slug(str(target_skill))}-{_slug(str(incident_kind), 3)}-"
            f"{_slug(str(data.get('incident_id') or 'unselected'), 2)}"
        ),
        "privacy": "local-private",
        "_source": "cs-feedback",
        "_status": "candidate",
        "_profile": profile,
        "incident_id": data.get("incident_id", ""),
        "target_skill": target_skill,
        "incident_kind": incident_kind,
        "quality": quality,
        "privacy_review": privacy_review,
    }
    if profile == "routing-decision":
        candidate.update(
            {
                "answerType": "routing-decision",
                "expect": oracle.get("expect", {}),
                "task": {
                    "kind": "routing",
                    **{
                        key: input_data[key]
                        for key in ("state", "intent", "utterance")
                        if key in input_data
                    },
                },
            }
        )
    elif profile == "findings-recall":
        candidate.update(
            {
                "answerType": "findings-recall",
                "answer": oracle.get("coverage_points")
                if isinstance(oracle.get("coverage_points"), list)
                else [],
                "task": {
                    "kind": task_kind,
                    **{
                        key: input_data[key]
                        for key in ("spec", "diff", "context", "audience")
                        if key in input_data
                    },
                },
            }
        )
    else:
        candidate.update({"answerType": "unknown", "task": {"kind": "unknown"}})
    missing = list(quality.get("missing_fields") or [])
    if not quality.get("regression_ready"):
        missing.append("quality.regression_ready")
    if profile != expected_profile:
        missing.append("reproduction.eval_profile")
    if privacy_review.get("status") != "approved":
        missing.append("privacy_review.status")
    candidate["promotion_blockers"] = sorted(set(missing))
    return candidate


def _candidate_from_v1_public_context(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("v1 public context must be a JSON object")
    events = data.get("events") or data.get("candidates") or []
    if not isinstance(events, list):
        raise ValueError("v1 public context events must be a JSON array")
    event = events[0] if events and isinstance(events[0], dict) else {}
    summary = event.get("actual_behavior") or event.get("sanitized_excerpt") or event.get("failure_type") or "unknown failure"
    return {
        "id": f"reg-{_slug(str(summary))}",
        "privacy": "local-private",
        "_source": "cs-feedback",
        "_status": "candidate",
        "answerType": "findings-recall",
        "answer": [str(summary)[:120]],
        "task": {"kind": event.get("kind", "review")},
        "quality": {"triage_ready": False, "regression_ready": False, "missing_fields": ["triage.json", "reproduction.input", "reproduction.oracle"]},
        "privacy_review": {"status": "pending"},
        "promotion_blockers": ["triage.json", "quality.regression_ready", "privacy_review.status"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="feedback triage -> local regression candidate")
    parser.add_argument("--triage", help="canonical triage.json")
    parser.add_argument("--evidence", help="compat public-issue-context.json; produces not-ready candidate")
    parser.add_argument("--experiment", help=argparse.SUPPRESS)
    parser.add_argument("--failure", help=argparse.SUPPRESS)
    parser.add_argument("--kind", default="review", help=argparse.SUPPRESS)
    parser.add_argument("--spec", default="", help=argparse.SUPPRESS)
    parser.add_argument("--diff", default="", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.experiment or args.failure:
        print("legacy direct fixture writing is disabled; run --triage and promote with eval-cs-skill", file=sys.stderr)
        return 2
    if bool(args.triage) == bool(args.evidence):
        print("需且只能提供 --triage 或 --evidence", file=sys.stderr)
        return 2

    source = Path(args.triage or args.evidence).expanduser()
    try:
        candidate = (
            _candidate_from_triage(source)
            if args.triage
            else _candidate_from_v1_public_context(source)
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"candidate blocked: {exc}", file=sys.stderr)
        return 2
    output = source.parent / "regression-candidate.json"
    output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[cs-feedback] wrote local regression candidate -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
