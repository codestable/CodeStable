from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/collect_feedback_context.py"
REPORT_SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/report_feedback_issue.py"


def load_collector():
    spec = importlib.util.spec_from_file_location("collect_feedback_context", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collector = load_collector()


def load_reporter():
    spec = importlib.util.spec_from_file_location("report_feedback_issue", REPORT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


reporter = load_reporter()


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_collects_codestable_tool_failures_and_user_corrections(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".codex/sessions/2026/07/03/rollout-test-session.jsonl"
    write_jsonl(
        transcript,
        [
            {
                "timestamp": "2026-07-03T01:00:00Z",
                "type": "session_meta",
                "payload": {"session_id": "test-session", "cwd": "/repo"},
            },
            {
                "timestamp": "2026-07-03T01:01:00Z",
                "type": "response_item",
                "payload": {"type": "function_call", "name": "read_file", "arguments": "cs-feat references/design/protocol.md"},
            },
            {
                "timestamp": "2026-07-03T01:02:00Z",
                "type": "response_item",
                "payload": {"type": "function_call_output", "output": "tool call failed: file read failed for .codestable reference"},
            },
            {
                "timestamp": "2026-07-03T01:03:00Z",
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "不对，你没有按 cs-feat 的 goal driver 规则走。token=secret123456"},
            },
        ],
    )

    output = tmp_path / "evidence.json"
    exit_code = collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--feedback",
            "cs-feat file read failed and user corrected agent",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["privacy"] == "local-private"
    assert payload["public_upload_allowed"] is False
    assert payload["public_issue_context"]["privacy"] == "public-preview"
    assert payload["matched_events"]
    reasons = {reason for event in payload["matched_events"] for reason in event["reasons"]}
    assert {"codestable", "failure", "user-correction"} <= reasons
    match_types = {match_type for event in payload["matched_events"] for match_type in event["match_types"]}
    assert {"tool-failure", "user-correction", "skill-reference"} <= match_types
    public_event = payload["public_issue_context"]["events"][0]
    assert set(public_event) == {
        "provider",
        "session_label",
        "timestamp_bucket",
        "failure_type",
        "match_type",
        "tool_name",
        "skill_or_reference",
        "sanitized_excerpt",
    }
    assert "secret123456" not in output.read_text(encoding="utf-8")
    assert "<redacted>" in output.read_text(encoding="utf-8")


def test_feedback_tokens_do_not_select_unrelated_events(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".codex/sessions/2026/07/03/noise-session.jsonl"
    write_jsonl(
        transcript,
        [
            {
                "timestamp": "2026-07-03T01:00:00Z",
                "type": "session_meta",
                "payload": {"session_id": "noise-session", "cwd": "/repo"},
            },
            {
                "timestamp": "2026-07-03T01:01:00Z",
                "type": "event_msg",
                "payload": {"message": "I am thinking about cs-feat but there is no incident here."},
            },
            {
                "timestamp": "2026-07-03T01:02:00Z",
                "type": "event_msg",
                "payload": {"message": "Plain unrelated discussion about lunch."},
            },
            {
                "timestamp": "2026-07-03T01:03:00Z",
                "type": "event_msg",
                "payload": {"message": "plain tool failed without any related marker"},
            },
        ],
    )

    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--feedback",
            "cs-feat tool failed",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["matched_events"]) == 1
    assert payload["matched_events"][0]["reasons"] == ["codestable", "feedback-token"]
    public_payload = json.loads((tmp_path / "public-issue-context.json").read_text(encoding="utf-8"))
    assert public_payload["privacy"] == "public-preview"


def test_collects_claude_json_history_and_goal_mentions(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".claude/sessions/claude-feedback.json"
    write_json(
        transcript,
        {
            "session_id": "claude-session-123",
            "cwd": "/repo",
            "messages": [
                {"timestamp": "2026-07-03T02:00:00Z", "role": "assistant", "content": "I should print /goal but skipped it."},
                {
                    "timestamp": "2026-07-03T02:01:00Z",
                    "role": "user",
                    "content": "不是，cs-epic 规则要求所有 feature design review 通过后再 /goal。",
                },
            ],
        },
    )

    output = tmp_path / "evidence.json"
    exit_code = collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--session",
            "claude-session-123",
            "--feedback",
            "cs-epic should use /goal",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["searched_files"] == [str(transcript)]
    assert payload["matched_events"]
    assert {event["provider"] for event in payload["matched_events"]} == {"claude"}
    assert all(event["session"] == "claude-session-123" for event in payload["matched_events"])


def test_current_session_reports_ambiguity_when_multiple_recent_candidates(tmp_path: Path) -> None:
    home = tmp_path / "home"
    for session in ["a", "b"]:
        write_jsonl(
            home / f".codex/sessions/2026/07/03/rollout-{session}.jsonl",
            [
                {
                    "timestamp": "2026-07-03T01:00:00Z",
                    "type": "session_meta",
                    "payload": {"session_id": session, "cwd": "/same/repo"},
                },
                {
                    "timestamp": "2026-07-03T01:01:00Z",
                    "type": "event_msg",
                    "payload": {"message": "cs-epic 没有继续下一个 feature design"},
                },
            ],
        )

    output = tmp_path / "evidence.json"
    exit_code = collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--session",
            "current",
            "--cwd",
            "/same/repo",
            "--feedback",
            "cs-epic current session",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["ambiguity"]["candidates"]) == 2
    assert payload["searched_files"] == []


def test_current_session_does_not_auto_select_without_cwd_metadata(tmp_path: Path) -> None:
    home = tmp_path / "home"
    for session in ["a", "b"]:
        write_jsonl(
            home / f".codex/sessions/2026/07/03/no-cwd-{session}.jsonl",
            [
                {
                    "timestamp": "2026-07-03T01:00:00Z",
                    "type": "session_meta",
                    "payload": {"session_id": session},
                },
                {
                    "timestamp": "2026-07-03T01:01:00Z",
                    "type": "event_msg",
                    "payload": {"message": "cs-feedback rule unclear"},
                },
            ],
        )

    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--session",
            "current",
            "--cwd",
            "/same/repo",
            "--feedback",
            "cs-feedback current session",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["ambiguity"]["candidates"]) == 2
    assert payload["searched_files"] == []


def test_current_session_can_select_single_claude_json_candidate(tmp_path: Path) -> None:
    home = tmp_path / "home"
    write_json(
        home / ".claude/sessions/current-session.json",
        {
            "sessionId": "current-claude",
            "cwd": "/same/repo",
            "messages": [
                {
                    "timestamp": "2026-07-03T03:00:00Z",
                    "content": "cs-feat tool call failed after reading reference",
                }
            ],
        },
    )

    output = tmp_path / "evidence.json"
    exit_code = collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--session",
            "current",
            "--cwd",
            "/same/repo",
            "--feedback",
            "cs-feat tool call failed",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["ambiguity"]["candidates"] == []
    assert len(payload["searched_files"]) == 1
    assert payload["matched_events"]


def test_public_summary_redacts_paths_and_remotes(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".codex/sessions/2026/07/03/private-paths.jsonl"
    write_jsonl(
        transcript,
        [
            {
                "timestamp": "2026-07-03T04:00:00Z",
                "type": "session_meta",
                "payload": {"session_id": "private-session", "cwd": "/Users/me/private/repo"},
            },
            {
                "timestamp": "2026-07-03T04:01:00Z",
                "type": "event_msg",
                "payload": {
                    "message": (
                        "cs-feat failed reading /Users/me/private/repo/.codestable/attention.md, "
                        "~/work/private-client/secrets.md, and /opt/acme/customer_data.md from "
                        "https://github.com/acme/private?token=abc and git@gitlab.company.com:secret/private-repo.git"
                    )
                },
            },
        ],
    )

    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "9999",
            "--feedback",
            "cs-feat file read failed",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    excerpt = payload["public_issue_context"]["events"][0]["sanitized_excerpt"]
    assert "/Users/me" not in excerpt
    assert "~/work" not in excerpt
    assert "/opt/acme" not in excerpt
    assert "acme/private" not in excerpt
    assert "secret/private-repo" not in excerpt
    assert "gitlab.company.com" not in excerpt
    assert "token=abc" not in excerpt
    assert "<local-path>" in excerpt
    assert "<repo-remote>" in excerpt


def test_reporter_falls_back_when_gh_is_missing(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("## Summary\n\ncs-feedback issue\n", encoding="utf-8")
    output = tmp_path / "result.json"
    monkeypatch.setattr(reporter.shutil, "which", lambda name: None)

    exit_code = reporter.main_with_args_for_test(
        [
            "--repo",
            "owner/repo",
            "--title",
            "Feedback: cs skill failed",
            "--body-file",
            str(body),
            "--json-output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "manual"
    assert payload["reason"] == "gh not found"
    assert "gh issue create" in payload["command"]
    assert "'Feedback: cs skill failed'" in payload["command"]


def test_reporter_refuses_local_private_evidence(tmp_path: Path, monkeypatch) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps({"privacy": "local-private", "public_upload_allowed": False}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(reporter.shutil, "which", lambda name: None)

    try:
        reporter.main_with_args_for_test(
            [
                "--repo",
                "owner/repo",
                "--title",
                "Feedback: cs skill failed",
                "--body-file",
                str(evidence),
            ]
        )
    except SystemExit as exc:
        assert "refusing to upload local-private" in str(exc)
    else:
        raise AssertionError("expected reporter to reject evidence.json")
