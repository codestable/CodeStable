#!/usr/bin/env python3
"""Collect local Codex/Claude history for a CodeStable feedback evidence package."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from feedback_incidents import (  # noqa: E402,F401
    build_incident_payload,
    collect_file,
    failure_type_for,
    feedback_tokens,
    incident_kind_for,
    is_relevant_event,
    match_types_for,
    public_incident,
    public_summary_for,
    records_through_trigger,
    score_text,
    skill_reference_from,
    timestamp_bucket,
    tool_name_from,
)
from feedback_models import (  # noqa: E402,F401
    Event,
    PUBLIC_EVENT_FIELDS,
    PUBLIC_INCIDENT_FIELDS,
    V1_FAILURE_MAP,
)
from feedback_repo_context import session_label  # noqa: E402
from feedback_transcripts import (  # noqa: E402,F401
    discover_files,
    normalize_records,
    provider_from_path,
    read_transcript_snapshot,
    session_id_from,
)
from feedback_triage import (  # noqa: E402
    accept_pending_incident,
    build_triage,
    merge_existing_triage,
)


def _load_existing_triage(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"existing triage is not a file: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read existing triage: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("existing triage must be a JSON object")
    if loaded.get("schema_version") != 2 or loaded.get("privacy") != "local-private":
        raise ValueError("existing triage must be schema v2 local-private")
    for key in ("target", "assessment", "reproduction", "privacy_review"):
        if not isinstance(loaded.get(key), dict):
            raise ValueError(f"existing triage {key} must be a JSON object")
    return loaded


def _write_text_files_atomically(files: list[tuple[Path, str]]) -> None:
    staged: list[tuple[Path, Path]] = []
    backups: dict[Path, Path | None] = {}
    replaced: list[Path] = []
    try:
        for target, text in files:
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            )
            temporary = Path(handle.name)
            staged.append((temporary, target))
            with handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        for _temporary, target in staged:
            if not target.exists():
                backups[target] = None
                continue
            handle = tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.rollback.",
                suffix=".tmp",
                delete=False,
            )
            backup = Path(handle.name)
            backups[target] = backup
            with handle:
                handle.write(target.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
        try:
            for temporary, target in staged:
                temporary.replace(target)
                replaced.append(target)
        except OSError as exc:
            rollback_errors: list[str] = []
            for target in reversed(replaced):
                backup = backups[target]
                try:
                    if backup is None:
                        target.unlink(missing_ok=True)
                    else:
                        os.replace(backup, target)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{target}: {rollback_exc}")
            if rollback_errors:
                raise OSError(
                    "feedback output rollback failed: " + "; ".join(rollback_errors)
                ) from exc
            raise
    finally:
        for temporary, _target in staged:
            temporary.unlink(missing_ok=True)
        for backup in backups.values():
            if backup is not None:
                backup.unlink(missing_ok=True)


def main_with_args_for_test(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", default="", help="User's short feedback text")
    parser.add_argument("--since-days", type=int, default=3)
    parser.add_argument("--session", default=None, help="Session id substring or transcript path")
    parser.add_argument("--output", required=True)
    parser.add_argument("--triage-output", default=None, help="Write local-private triage JSON")
    parser.add_argument("--public-output", default=None, help="Write public allowlist context JSON")
    parser.add_argument("--history-root", default=None, help="Override home directory for tests")
    parser.add_argument("--cwd", default=None, help="Current working directory, used by --session current")
    parser.add_argument("--max-events-per-file", type=int, default=5)
    parser.add_argument("--context-window", type=int, default=2)
    parser.add_argument(
        "--accept-incident",
        default=None,
        help="Explicitly accept the current pending primary incident",
    )
    args = parser.parse_args(argv)

    output = Path(args.output).expanduser()
    triage_output = (
        Path(args.triage_output).expanduser()
        if args.triage_output
        else output.with_name("triage.json")
    )
    public_output = (
        Path(args.public_output).expanduser()
        if args.public_output
        else output.with_name("public-issue-context.json")
    )
    try:
        resolved_outputs = [path.resolve() for path in (output, triage_output, public_output)]
    except OSError as exc:
        print(f"feedback output blocked: {exc}", file=sys.stderr)
        return 2
    if len(set(resolved_outputs)) != len(resolved_outputs):
        print("feedback output blocked: output paths must be distinct", file=sys.stderr)
        return 2
    try:
        existing_triage = _load_existing_triage(triage_output)
    except ValueError as exc:
        print(f"feedback output blocked: {exc}", file=sys.stderr)
        return 2

    home = Path(args.history_root).expanduser() if args.history_root else Path.home()
    cwd = str(Path(args.cwd).expanduser()) if args.cwd else None
    files, ambiguity = discover_files(home, args.since_days, args.session, cwd)

    records_by_path: dict[Path, list[dict[str, Any]]] = {}
    captures_by_path: dict[Path, dict[str, Any]] = {}
    for path in files:
        records_by_path[path], captures_by_path[path] = read_transcript_snapshot(path)

    events: list[Event] = []
    for path in files:
        events.extend(
            collect_file(
                path,
                args.feedback,
                args.max_events_per_file,
                args.context_window,
                records_through_trigger(path, records_by_path[path]),
            )
        )
    events.sort(key=lambda event: (event.score, event.timestamp), reverse=True)
    incidents, primary_incident = build_incident_payload(
        files,
        args.feedback,
        cwd,
        records_by_path,
        captures_by_path,
    )

    generated_triage = build_triage(incidents, primary_incident)
    try:
        triage = (
            accept_pending_incident(
                generated_triage, existing_triage, args.accept_incident
            )
            if args.accept_incident
            else merge_existing_triage(generated_triage, existing_triage)
        )
    except ValueError as exc:
        print(f"incident acceptance blocked: {exc}", file=sys.stderr)
        return 2
    quality = triage.get("quality")
    public_projection_ready = (
        primary_incident is not None
        and triage.get("incident_id") == primary_incident.get("id")
        and isinstance(quality, dict)
        and quality.get("triage_ready") is True
    )
    public_incidents: list[dict[str, str]] = []
    if public_projection_ready:
        for incident in incidents:
            incident_triage = (
                triage
                if incident.get("id") == triage.get("incident_id")
                else build_triage([incident], incident)
            )
            public_incidents.append(public_incident(incident, incident_triage))

    public_issue_context = {
        "privacy": "public-preview",
        "source": "derived-from-local-private-evidence",
        "allowed_fields": list(
            dict.fromkeys(PUBLIC_EVENT_FIELDS + PUBLIC_INCIDENT_FIELDS)
        ),
        "events": (
            [event.public_summary for event in events[:8]]
            if public_projection_ready
            else []
        ),
        "incidents": public_incidents,
    }
    payload = {
        "schema_version": 2,
        "feedback": args.feedback,
        "privacy": "local-private",
        "public_upload_allowed": False,
        "redaction": "best-effort",
        "since_days": args.since_days,
        "since_days_ignored": args.session == "current",
        "session_filter": args.session,
        "history_root": str(home),
        "cwd": cwd,
        "searched_files": [str(path) for path in files],
        "ambiguity": {"candidates": [asdict(candidate) for candidate in ambiguity]},
        "captures": [
            {
                "provider": provider_from_path(path),
                "session_label": session_label(
                    session_id_from(path, records_by_path[path])
                ),
                **captures_by_path[path],
            }
            for path in files
        ],
        "matched_events": [asdict(event) for event in events],
        "incidents": incidents,
        "public_issue_context": public_issue_context,
    }
    try:
        _write_text_files_atomically(
            [
                (triage_output, json.dumps(triage, ensure_ascii=False, indent=2) + "\n"),
                (output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
                (
                    public_output,
                    json.dumps(public_issue_context, ensure_ascii=False, indent=2) + "\n",
                ),
            ]
        )
    except OSError as exc:
        print(f"feedback output blocked: {exc}", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    return main_with_args_for_test()


if __name__ == "__main__":
    raise SystemExit(main())
