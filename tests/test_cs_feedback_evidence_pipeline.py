from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/collect_feedback_context.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collector = load_module(COLLECTOR_SCRIPT, "collect_feedback_context_v2")
transcripts = sys.modules["feedback_transcripts"]
triage_module = sys.modules.get("feedback_triage")
incidents_module = sys.modules["feedback_incidents"]
models_module = sys.modules["feedback_models"]
privacy_module = sys.modules["feedback_privacy"]
repo_context_module = sys.modules["feedback_repo_context"]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_current_session_metadata_only_ignores_stale_mtime_and_body_cwd(tmp_path: Path) -> None:
    home = tmp_path / "home"
    stale = home / ".codex/sessions/2026/01/01/stale.jsonl"
    body_only = home / ".codex/sessions/2026/01/01/body-only.jsonl"
    write_jsonl(
        stale,
        [
            {"type": "session_meta", "timestamp": "2026-01-01T00:00:00Z", "payload": {"session_id": "stale", "cwd": "/repo"}},
            {"type": "event_msg", "timestamp": "2026-01-01T00:01:00Z", "payload": {"message": "cs-feedback failed"}},
        ],
    )
    write_jsonl(
        body_only,
        [
            {"type": "event_msg", "timestamp": "2026-01-01T00:00:00Z", "payload": {"message": "cwd=/repo secret-token-123456"}},
        ],
    )
    old = 1_700_000_000
    os.utime(stale, (old, old))
    os.utime(body_only, (old, old))
    stale.chmod(0o600)
    body_only.chmod(0o600)

    output = tmp_path / "evidence.json"
    rc = collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--since-days",
            "0",
            "--session",
            "current",
            "--cwd",
            "/repo",
            "--feedback",
            "cs-feedback failed",
            "--output",
            str(output),
        ]
    )

    assert rc == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["searched_files"] == [str(stale)]
    assert payload["since_days_ignored"] is True
    assert "secret-token-123456" not in json.dumps(payload["ambiguity"], ensure_ascii=False)


def test_current_session_ambiguity_never_reads_or_returns_message_bodies(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    for session, marker in (("a", "PRIVATE_TOOL_ALPHA"), ("b", "PRIVATE_TOOL_BETA")):
        write_jsonl(
            home / f".codex/sessions/2026/07/03/{session}.jsonl",
            [
                {
                    "type": "session_meta",
                    "payload": {"session_id": session, "cwd": "/same/repo"},
                },
                {"type": "event_msg", "payload": {"message": marker}},
            ],
        )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("ambiguity resolution must not read or flatten transcript bodies")

    monkeypatch.setattr(transcripts, "read_records", forbidden)
    monkeypatch.setattr(transcripts, "flatten", forbidden)
    output = tmp_path / "evidence.json"
    assert (
        collector.main_with_args_for_test(
            [
                "--history-root",
                str(home),
                "--session",
                "current",
                "--cwd",
                "/same/repo",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    ambiguity_text = json.dumps(payload["ambiguity"], ensure_ascii=False)
    assert payload["searched_files"] == []
    assert len(payload["ambiguity"]["candidates"]) == 2
    assert "PRIVATE_TOOL_ALPHA" not in ambiguity_text
    assert "PRIVATE_TOOL_BETA" not in ambiguity_text


def test_current_session_weak_cwd_match_requires_user_selection(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".codex/sessions/2026/07/03/parent.jsonl"
    write_jsonl(
        transcript,
        [
            {
                "type": "session_meta",
                "payload": {"session_id": "parent", "cwd": "/repo"},
            },
            {"type": "event_msg", "payload": {"message": "cs-feat failed"}},
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        [
            "--history-root",
            str(home),
            "--session",
            "current",
            "--cwd",
            "/repo/subdir",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["searched_files"] == []
    assert [item["session"] for item in payload["ambiguity"]["candidates"]] == ["parent"]


def test_jsonl_snapshot_freezes_only_complete_records_at_eof(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/frozen.jsonl"
    complete = (
        json.dumps({"type": "session_meta", "payload": {"session_id": "s1"}}) + "\n"
        + json.dumps({"type": "event_msg", "payload": {"message": "first"}})
        + "\n"
    ).encode()
    transcript.parent.mkdir(parents=True)
    transcript.write_bytes(complete + b'{"type":"event_msg"')

    records, capture = transcripts.read_transcript_snapshot(transcript)
    frozen = json.dumps(records, sort_keys=True)
    with transcript.open("ab") as handle:
        handle.write(b',"payload":{"message":"late"}}\n')

    assert len(records) == 2
    assert json.dumps(records, sort_keys=True) == frozen
    assert capture["complete_record_eof"] == len(complete)
    assert capture["byte_length"] > capture["complete_record_eof"]


def test_collector_reads_each_selected_transcript_snapshot_once(tmp_path: Path, monkeypatch) -> None:
    transcript = tmp_path / ".codex/sessions/once.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
        ],
    )
    real_read = collector.read_transcript_snapshot
    calls: list[Path] = []

    def counting_read(path: Path):
        calls.append(path)
        return real_read(path)

    monkeypatch.setattr(collector, "read_transcript_snapshot", counting_read)
    collector.main_with_args_for_test(
        ["--session", str(transcript), "--output", str(tmp_path / "evidence.json")]
    )
    assert calls == [transcript]


def test_evidence_v2_incident_triage_and_public_projection_are_structured(tmp_path: Path) -> None:
    home = tmp_path / "home"
    transcript = home / ".codex/sessions/2026/07/03/incident.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "timestamp": "2026-07-03T01:00:00Z", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {
                "type": "response_item",
                "timestamp": "2026-07-03T01:01:00Z",
                "payload": {"type": "function_call", "call_id": "call-1", "name": "read_file", "arguments": "cs-feat gate"},
            },
            {
                "type": "response_item",
                "timestamp": "2026-07-03T01:02:00Z",
                "payload": {"type": "function_call_output", "call_id": "call-1", "output": "tool call failed: /Users/me/private token=secret123456"},
            },
            {
                "type": "event_msg",
                "timestamp": "2026-07-03T01:03:00Z",
                "payload": {"type": "user_message", "message": "不对，应该执行 cs-feat design review gate。"},
            },
            {"type": "event_msg", "timestamp": "2026-07-03T01:04:00Z", "payload": {"message": "anchor 后的内容不应进入 incident"}},
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
            "cs-feat tool failed should execute gate",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["incidents"][0]["target_skill"] == "cs-feat"
    assert payload["incidents"][0]["capture_cutoff"] == "record-0003"
    assert "anchor 后" not in json.dumps(payload["incidents"], ensure_ascii=False)
    assert payload["incidents"][0]["timeline"][1]["correlation_source"] == "provider"
    assert "triage" not in payload
    triage = json.loads((tmp_path / "triage.json").read_text(encoding="utf-8"))
    assert triage["quality"]["triage_ready"] is True
    assert triage["quality"]["regression_ready"] is False
    assert triage["assessment"]["expected_behavior"]["source"] == "user"
    public_payload = payload["public_issue_context"]
    assert set(public_payload["events"][0]) == {
        "provider",
        "session_label",
        "timestamp_bucket",
        "failure_type",
        "match_type",
        "tool_name",
        "skill_or_reference",
        "sanitized_excerpt",
    }
    public_text = json.dumps(public_payload, ensure_ascii=False)
    assert "/Users/me" not in public_text
    assert "secret123456" not in public_text
    assert "incident_kind" in public_payload["incidents"][0]
    assert set(public_payload["incidents"][0]) == {
        "incident_kind",
        "target_skill",
        "stage_hint",
        "expected_behavior",
        "actual_behavior",
        "impact",
        "proposed_fix",
    }


def test_missing_user_anchor_keeps_incident_but_blocks_triage(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/no-anchor.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "c1",
                    "name": "read_file",
                    "arguments": "cs-feat gate",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "c1",
                    "output": "tool call failed",
                },
            },
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        ["--session", str(transcript), "--feedback", "cs-feat failed", "--output", str(output)]
    )

    evidence = json.loads(output.read_text(encoding="utf-8"))
    triage = json.loads((tmp_path / "triage.json").read_text(encoding="utf-8"))
    public = json.loads((tmp_path / "public-issue-context.json").read_text(encoding="utf-8"))
    assert evidence["incidents"][0]["capture_cutoff"] == "unknown"
    assert triage["quality"]["triage_ready"] is False
    assert "trigger_cutoff" in triage["quality"]["missing_fields"]
    assert public["events"] == []
    assert public["incidents"] == []


def test_tool_pairing_prefers_provider_ids_and_fails_closed_on_ambiguity(tmp_path: Path) -> None:
    path = tmp_path / ".codex/sessions/pairing.jsonl"
    records = [
        {"payload": {"type": "function_call", "call_id": "p1", "name": "one"}},
        {"payload": {"type": "function_call_output", "call_id": "p1", "output": "ok"}},
        {"payload": {"type": "function_call", "name": "two"}},
        {"type": "session_meta", "payload": {"session_id": "s1"}},
        {"payload": {"type": "function_call_output", "output": "ok"}},
        {"payload": {"type": "function_call", "name": "three"}},
        {"payload": {"type": "function_call", "name": "four"}},
        {"payload": {"type": "function_call_output", "output": "ambiguous"}},
        {"payload": {"type": "function_call", "name": "five"}},
        {"payload": {"type": "function_call_output", "call_id": "missing", "output": "no"}},
    ]

    normalized = collector.normalize_records(path, records)
    assert [record.correlation_source for record in normalized[:2]] == ["provider", "provider"]
    assert normalized[2].correlation_source == "adjacency"
    assert normalized[4].correlation_source == "adjacency"
    assert len({normalized[2].correlation_id, normalized[4].correlation_id}) == 1
    assert [record.correlation_source for record in normalized[5:8]] == [
        "unpaired",
        "unpaired",
        "unpaired",
    ]
    assert [record.correlation_source for record in normalized[8:10]] == ["unpaired", "unpaired"]


def test_non_overlapping_user_turns_create_separate_incidents(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/two-incidents.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {
                "type": "response_item",
                "payload": {"type": "function_call_output", "output": "cs-feat tool call failed"},
            },
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "不对，应该先运行 cs-feat design review。"},
            },
            {
                "type": "response_item",
                "payload": {"type": "function_call_output", "output": "cs-feat second tool call failed"},
            },
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "又错了，应该进入 cs-feat QA。"},
            },
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        ["--session", str(transcript), "--feedback", "cs-feat failed", "--output", str(output)]
    )

    incidents = json.loads(output.read_text(encoding="utf-8"))["incidents"]
    assert len(incidents) == 2
    first = json.dumps(incidents[0], ensure_ascii=False)
    second = json.dumps(incidents[1], ensure_ascii=False)
    assert "design review" in first and "进入 cs-feat QA" not in first
    assert "进入 cs-feat QA" in second and "design review" not in second


def _semantic_timeline(module, path: Path) -> list[tuple[str, str, str, str]]:
    records = module.read_records(path)
    normalized = collector.normalize_records(path, records)
    return [
        (record.role, record.record_type, record.tool_name, record.correlation_source)
        for record in normalized
        if record.record_type != "session_meta"
    ]


def test_codex_and_claude_json_variants_normalize_tool_incidents_isomorphically(tmp_path: Path) -> None:
    codex = tmp_path / ".codex/sessions/codex.jsonl"
    codex_records = [
        {"type": "session_meta", "payload": {"session_id": "cx", "cwd": "/repo"}},
        {
            "type": "response_item",
            "payload": {"type": "function_call", "call_id": "c1", "name": "read_file", "arguments": "cs-feat review"},
        },
        {
            "type": "response_item",
            "payload": {"type": "function_call_output", "call_id": "c1", "output": "tool call failed"},
        },
        {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
    ]
    write_jsonl(codex, codex_records)

    claude_messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "c1", "name": "read_file", "input": {"intent": "cs-feat review"}}
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "tool call failed"}],
        },
        {"role": "user", "content": "不对，应该 review。"},
    ]
    claude_json = tmp_path / ".claude/sessions/claude.json"
    write_json(claude_json, {"session_id": "cl", "cwd": "/repo", "messages": claude_messages})
    claude_jsonl = tmp_path / ".claude/sessions/claude.jsonl"
    write_jsonl(
        claude_jsonl,
        [
            {"type": "session_meta", "session_id": "cl", "cwd": "/repo"},
            *claude_messages,
        ],
    )

    expected = _semantic_timeline(transcripts, codex)
    assert _semantic_timeline(transcripts, claude_json) == expected
    assert _semantic_timeline(transcripts, claude_jsonl) == expected


def test_repo_context_records_runtime_artifacts_and_file_level_git_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    child = repo / "nested/child"
    (repo / ".codestable/features/demo").mkdir(parents=True)
    child.mkdir(parents=True)
    write_json(
        repo / ".codestable/runtime-manifest.json",
        {"schema_version": 1, "runtime_version": "9.9.9", "plugin_version": "9.9.9"},
    )
    (repo / ".codestable/features/demo/demo-design.md").write_text(
        "---\ndoc_type: feature-design\nstatus: approved\n---\n# Demo\n",
        encoding="utf-8",
    )
    (repo / ".codestable/features/demo/goal-state.yaml").write_text(
        "stage: implementation\nstatus: running\n",
        encoding="utf-8",
    )
    (repo / "changed.txt").write_text("private business content", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    transcript = tmp_path / ".codex/sessions/repo-context.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": str(child)}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(
        ["--session", str(transcript), "--cwd", str(child), "--output", str(output)]
    )

    context = json.loads(output.read_text(encoding="utf-8"))["incidents"][0]["repo_context"]
    assert context["runtime"]["runtime_version"] == "9.9.9"
    artifact_paths = {item["path"] for item in context["artifacts"]}
    assert ".codestable/features/demo/demo-design.md" in artifact_paths
    assert ".codestable/features/demo/goal-state.yaml" in artifact_paths
    assert any(item["path"] == "changed.txt" for item in context["git_status"])
    assert "private business content" not in json.dumps(context, ensure_ascii=False)
    triage = json.loads((tmp_path / "triage.json").read_text(encoding="utf-8"))
    assert triage["repo_context"]["runtime"]["runtime_version"] == "9.9.9"


def test_environment_context_uses_metadata_records_not_tool_payload_fields() -> None:
    path = Path("/tmp/.codex/sessions/environment.jsonl")
    tool_record = {
        "type": "response_item",
        "payload": {
            "type": "function_call_output",
            "model": "business-model-name",
            "version": "internal-service-v42",
            "output": "tool failed",
        },
    }

    contaminated = repo_context_module.environment_context(
        path,
        [
            {"type": "session_meta", "payload": {"session_id": "s1"}},
            tool_record,
        ],
        {"format": "jsonl"},
    )
    assert contaminated["model"] == "unknown"
    assert contaminated["host_version"] == "unknown"

    metadata = repo_context_module.environment_context(
        path,
        [
            {
                "type": "session_meta",
                "payload": {"session_id": "s1", "cli_version": "codex-cli-1"},
            },
            {"type": "turn_context", "model": "review-model"},
            tool_record,
        ],
        {"format": "jsonl"},
    )
    assert metadata["model"] == "review-model"
    assert metadata["host_version"] == "codex-cli-1"


def test_collector_rejects_invalid_existing_triage_without_overwriting(tmp_path: Path) -> None:
    invalid_payloads = (
        "{broken",
        "[]\n",
        '{"schema_version":2,"privacy":"public-preview"}\n',
    )
    for index, invalid in enumerate(invalid_payloads):
        case = tmp_path / f"invalid-{index}"
        transcript = case / ".codex/sessions/feedback.jsonl"
        write_jsonl(
            transcript,
            [
                {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
                {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
                {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
            ],
        )
        output = case / "evidence.json"
        triage_path = case / "triage.json"
        triage_path.write_text(invalid, encoding="utf-8")

        assert collector.main_with_args_for_test(
            ["--session", str(transcript), "--output", str(output)]
        ) == 2
        assert triage_path.read_text(encoding="utf-8") == invalid
        assert not output.exists()
        assert not (case / "public-issue-context.json").exists()


def test_collector_rejects_colliding_output_paths_without_writing(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/feedback.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
        ],
    )
    collision = tmp_path / "same.json"

    assert collector.main_with_args_for_test(
        [
            "--session",
            str(transcript),
            "--output",
            str(collision),
            "--triage-output",
            str(collision),
            "--public-output",
            str(collision),
        ]
    ) == 2
    assert not collision.exists()


def test_collector_atomically_replaces_each_output(tmp_path: Path, monkeypatch) -> None:
    transcript = tmp_path / ".codex/sessions/feedback.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
        ],
    )
    replaced: list[tuple[Path, Path]] = []
    real_replace = Path.replace

    def track_replace(source: Path, target: Path) -> Path:
        replaced.append((source, Path(target)))
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", track_replace)
    output = tmp_path / "evidence.json"

    assert collector.main_with_args_for_test(
        ["--session", str(transcript), "--output", str(output)]
    ) == 0
    assert {target.name for _source, target in replaced} == {
        "evidence.json",
        "triage.json",
        "public-issue-context.json",
    }
    assert all(source.parent == target.parent and source != target for source, target in replaced)
    assert not list(tmp_path.glob(".*.tmp"))


def test_atomic_writer_cleans_private_temps_when_staging_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    targets = [tmp_path / name for name in ("triage.json", "evidence.json", "public.json")]
    for target in targets:
        target.write_text(f"old-{target.name}", encoding="utf-8")

    def fail_fsync(_fd: int) -> None:
        raise OSError("injected fsync failure")

    monkeypatch.setattr(collector.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="injected fsync failure"):
        collector._write_text_files_atomically(
            [(target, f"new-{target.name}") for target in targets]
        )

    for target in targets:
        assert target.read_text(encoding="utf-8") == f"old-{target.name}"
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize("operation", ["write", "flush"])
def test_atomic_writer_tracks_temp_before_write_or_flush_failure(
    tmp_path: Path,
    monkeypatch,
    operation: str,
) -> None:
    target = tmp_path / "triage.json"
    target.write_text("old-triage", encoding="utf-8")
    real_named_temporary_file = collector.tempfile.NamedTemporaryFile

    class FailingHandle:
        def __init__(self, handle) -> None:
            self.handle = handle

        @property
        def name(self) -> str:
            return self.handle.name

        def __enter__(self):
            self.handle.__enter__()
            return self

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

        def write(self, text: str) -> int:
            if operation == "write":
                raise OSError("injected write failure")
            return self.handle.write(text)

        def flush(self) -> None:
            if operation == "flush":
                raise OSError("injected flush failure")
            self.handle.flush()

        def fileno(self) -> int:
            return self.handle.fileno()

    def failing_named_temporary_file(*args, **kwargs):
        return FailingHandle(real_named_temporary_file(*args, **kwargs))

    monkeypatch.setattr(
        collector.tempfile,
        "NamedTemporaryFile",
        failing_named_temporary_file,
    )
    with pytest.raises(OSError, match=f"injected {operation} failure"):
        collector._write_text_files_atomically([(target, "new-triage")])

    assert target.read_text(encoding="utf-8") == "old-triage"
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize("failure_at", [1, 2, 3])
def test_atomic_writer_rolls_back_all_outputs_when_replace_fails(
    tmp_path: Path,
    monkeypatch,
    failure_at: int,
) -> None:
    targets = [tmp_path / name for name in ("triage.json", "evidence.json", "public.json")]
    for target in targets:
        target.write_text(f"old-{target.name}", encoding="utf-8")
    real_replace = Path.replace
    calls = 0

    def fail_replace(source: Path, target: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == failure_at:
            raise OSError(f"injected replace failure {failure_at}")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        collector._write_text_files_atomically(
            [(target, f"new-{target.name}") for target in targets]
        )

    for target in targets:
        assert target.read_text(encoding="utf-8") == f"old-{target.name}"
    assert not list(tmp_path.glob(".*.tmp"))


def test_onboard_gitignore_excludes_only_feedback_private_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runtime_dir = repo / ".codestable"
    feedback_dir = runtime_dir / "feedback/2026-07-11-private-case"
    feedback_dir.mkdir(parents=True)
    source_gitignore = ROOT / "plugins/codestable/skills/cs-onboard/codestable.gitignore"
    runtime_gitignore = ROOT / ".codestable/.gitignore"
    assert source_gitignore.read_text(encoding="utf-8") == runtime_gitignore.read_text(
        encoding="utf-8"
    )
    (runtime_dir / ".gitignore").write_text(
        source_gitignore.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    private_names = (
        "private-case-report.md",
        "evidence.json",
        "triage.json",
        "regression-candidate.json",
    )
    public_names = ("public-issue-context.json", "github-issue.md")
    for name in private_names + public_names:
        (feedback_dir / name).write_text("synthetic\n", encoding="utf-8")

    for name in private_names:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", str(feedback_dir / name)],
            cwd=repo,
            check=False,
        )
        assert result.returncode == 0, name
    for name in public_names:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", str(feedback_dir / name)],
            cwd=repo,
            check=False,
        )
        assert result.returncode == 1, name


def test_quality_gate_rejects_assessment_without_observation_reference() -> None:
    assert triage_module is not None
    triage = {
        "incident_id": "incident-01",
        "observation_ids": ["obs-02"],
        "trigger_cutoff": "record-0003",
        "target": {"skill": "cs-feat"},
        "incident_kind": "wrong-route",
        "assessment": {
            "expected_behavior": {"value": "route to design", "source": "user", "evidence_refs": []},
            "actual_behavior": {"value": "route to QA", "source": "transcript", "evidence_refs": ["obs-02"]},
        },
        "reproduction": {
            "eval_profile": "routing-decision",
            "task_kind": "routing",
            "input": {"utterance": "continue"},
            "oracle": {"expect": {"result_type": "RoutedTo"}},
        },
    }

    quality = triage_module.recompute_quality(triage)
    assert quality["triage_ready"] is False
    assert quality["regression_ready"] is False
    assert "assessment.expected_behavior.evidence_refs" in quality["missing_fields"]


def test_quality_gate_keeps_unknown_expected_and_prioritizes_that_question(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/missing-expected.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat tool call failed"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "有问题。"}},
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(["--session", str(transcript), "--output", str(output)])

    triage = json.loads((tmp_path / "triage.json").read_text(encoding="utf-8"))
    assert triage["assessment"]["expected_behavior"] == {
        "value": "unknown",
        "source": "unknown",
        "evidence_refs": [],
    }
    assert triage["quality"]["triage_ready"] is False
    assert "assessment.expected_behavior" in triage["quality"]["missing_fields"]
    assert triage["quality"]["next_questions"] == ["assessment.expected_behavior"]


def test_public_projection_removes_tool_json_code_paths_env_remote_and_secrets(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/privacy.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "apply_patch",
                    "arguments": '{"path":"/Users/me/private.py","env":"API_TOKEN=topsecret123","remote":"https://github.com/acme/private"}',
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "output": (
                        'cs-feat failed {\n  "token": "multilinesecret123456",'
                        '\n  "path": "/repo"\n} token=secret123456 '
                        "```python\nprivate_code()\n```"
                    ),
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "不对，应该先 review，不要读取 /opt/private。"},
            },
        ],
    )
    output = tmp_path / "evidence.json"
    collector.main_with_args_for_test(["--session", str(transcript), "--output", str(output)])

    evidence_text = output.read_text(encoding="utf-8")
    public_path = tmp_path / "public-issue-context.json"
    public_text = public_path.read_text(encoding="utf-8")
    public_payload = json.loads(public_text)

    def strings(value) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [item for child in value for item in strings(child)]
        if isinstance(value, dict):
            return [item for child in value.values() for item in strings(child)]
        return []

    assert "secret123456" not in evidence_text
    for forbidden in (
        "/Users/me",
        "/opt/private",
        "topsecret123",
        "multilinesecret123456",
        "API_TOKEN",
        "github.com/acme/private",
        "/repo",
        '"token"',
        '"path"',
        "private_code()",
        "```",
    ):
        assert forbidden not in public_text
    for value in strings(public_payload):
        assert "{" not in value and "}" not in value
        assert "API_TOKEN" not in value


def test_public_redaction_removes_absolute_paths_with_spaces() -> None:
    cases = (
        (r"error at C:\Users\bob\secret plan.docx", ("plan.docx",)),
        (
            "/Users/alice/customer contracts/acme-pricing-2026.md",
            ("contracts", "acme-pricing-2026.md"),
        ),
        (
            "/Users/alice/Library/Application Support/CodeStable/session.json",
            ("Support", "CodeStable", "session.json"),
        ),
        (
            'cat "/Users/alice/acme merger notes.txt" done',
            ("merger", "notes.txt"),
        ),
        (
            "cat '/Users/alice/acme merger notes.txt' done",
            ("merger", "notes.txt"),
        ),
        (
            "cat `/Users/alice/acme merger notes.txt` done",
            ("merger", "notes.txt"),
        ),
        (
            'open "C:\\Users\\bob\\secret plan.docx" now',
            ("plan.docx",),
        ),
        ("see /Users/bob/my report.docx.", ("report.docx",)),
        ("see /Users/bob/my report.docx!", ("report.docx",)),
        ("see /Users/bob/my report.docx?", ("report.docx",)),
        ("see /Users/bob/my report.docx。", ("report.docx",)),
        ("see /Users/bob/my report.docx！", ("report.docx",)),
        ("see /Users/bob/my report.docx？", ("report.docx",)),
        (
            'see "/Users/bob/my report.docx." next',
            ("report.docx",),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx，其中第二节有问题",
            ("合并", "计划.docx"),
        ),
        (
            "路径是 /Users/alice/acme 合并 计划.docx。下一步继续",
            ("合并", "计划.docx"),
        ),
        (
            "（详见 /Users/alice/merger plan.docx）之后再说",
            ("merger", "plan.docx"),
        ),
        (
            "见 /Users/alice/plan file.docx；继续",
            ("plan", "file.docx"),
        ),
        (
            "见“/Users/alice/acme 合并 计划.docx”，继续",
            ("合并", "计划.docx"),
        ),
        (
            "见 /Users/alice/plan long.presentation，继续",
            ("long.presentation",),
        ),
        (
            "见 /Users/alice/客户 合同.文档，继续",
            ("合同.文档",),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx…其中有问题",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx——其中有问题",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx（内含预算）",
            ("合并", "计划.docx"),
        ),
        (
            "see /Users/alice/acme merger plan.docx(v2)",
            ("merger", "plan.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx·补充",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx～补充",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx“重点”",
            ("合并", "计划.docx"),
        ),
        (
            "/tmp/x my report.docx 之后继续",
            ("my", "report.docx"),
        ),
        (
            r"open C:\Program Files\CodeStable\session.json",
            ("Files", "CodeStable", "session.json"),
        ),
        (
            "/Users/alice/项目 文档/计划.docx",
            ("文档", "计划.docx"),
        ),
        ("/tmp/x 合同.docx", ("合同.docx",)),
    )
    for raw, forbidden_parts in cases:
        public = privacy_module.public_redact(raw)
        assert "<local-path>" in public
        assert all(part not in public for part in forbidden_parts)


def test_public_redaction_preserves_text_after_absolute_paths() -> None:
    cases = (
        (
            "报错发生在 /tmp/build，随后 agent 跳过了 review gate",
            "，随后 agent 跳过了 review gate",
        ),
        (
            "/Users/alice/acme，其中第二节有问题",
            "，其中第二节有问题",
        ),
        (
            "cs-feat 在 /tmp/repo 之后 应该 先跑 design-review.md 再实现",
            "之后 应该 先跑 design-review.md 再实现",
        ),
        (
            "/tmp/a 运行 失败.详情如下：日志已附",
            "运行 失败.详情如下：日志已附",
        ),
        (
            "/tmp/build 失败 详见 3.2 节",
            "失败 详见 3.2 节",
        ),
        (
            "agent 在 /tmp/repo 没有读 .codestable/attention.md 就开工",
            "没有读 .codestable/attention.md 就开工",
        ),
        (
            "/tmp/build 失败 详见 docs/report.md",
            "失败 详见 docs/report.md",
        ),
        (
            "/tmp/app v1.2.3 crashed",
            "v1.2.3 crashed",
        ),
        (
            "/tmp/build 失败.详情如下 请看日志",
            "失败.详情如下 请看日志",
        ),
        (
            "/Users/a/b/c 详见 3.2 节",
            "详见 3.2 节",
        ),
        (
            "cs-feat 在 /tmp/repo 没生成.codestable/design.md",
            "没生成.codestable/design.md",
        ),
        (
            "报错在 /tmp/repo 后写到了build/output.json",
            "后写到了build/output.json",
        ),
        (
            "/tmp/x 输出在logs/a.txt 又读了docs/b.md 然后停了",
            "输出在logs/a.txt 又读了docs/b.md 然后停了",
        ),
    )
    for raw, expected_text in cases:
        public = privacy_module.public_redact(raw, limit=4000)
        assert "<local-path>" in public
        assert expected_text in public


def test_public_redaction_removes_nested_braced_and_unbounded_tool_json() -> None:
    nested = (
        'cs-feat failed {"patch":"def f() { return {} }",'
        '"note":"private business logic"}'
    )
    oversized = '{"note":"private prefix","payload":"' + ("x" * 2500) + '"}'

    for raw, forbidden in (
        (nested, "private business logic"),
        (oversized, "private prefix"),
    ):
        public = privacy_module.public_redact(raw, limit=4000)
        assert public == "cs-feat failed <tool-arguments>" or public == "<tool-arguments>"
        assert forbidden not in public
        assert "{" not in public and "}" not in public


def test_public_redaction_removes_six_and_seven_character_explicit_secrets() -> None:
    for raw in ("password=hunter2", "authorization=abcdefg", '"token":"secret"'):
        public = privacy_module.public_redact(raw)
        assert raw not in public
        assert "<redacted>" in public


def test_public_redaction_removes_special_and_quoted_secret_values() -> None:
    cases = (
        ("password=p@ssw0rd!123", ("p@ssw0rd!123",)),
        ('password: "correct horse battery staple"', ("correct", "horse", "battery", "staple")),
        ('export password="s3cr3tv@lue"', ("s3cr3tv@lue", "@lue")),
        ('token = "abc def ghi jkl"', ("abc", "def", "ghi", "jkl")),
        ("password=abc<def>ghi", ("abc<def>ghi",)),
        ("password=`s3cr3tv@l!`", ("s3cr3tv@l!",)),
        ("password：hunter22!", ("hunter22!",)),
        ("token＝abc<def>ghi", ("abc<def>ghi",)),
        ('password="s3cr3tv@lue', ("s3cr3tv@lue",)),
        ("token='unterminated secret value", ("unterminated", "secret", "value")),
        (r"password=secret\ pass", (r"secret\ pass", " pass")),
        ("password：`abc<def>ghi`", ("abc<def>ghi",)),
    )
    for raw, forbidden_parts in cases:
        public = privacy_module.public_redact(raw)
        assert "<redacted>" in public
        assert all(part not in public for part in forbidden_parts)


def test_public_redaction_removes_shell_segmented_secret_values() -> None:
    cases = (
        ("password=abc'def'ghi", ("abc", "def", "ghi")),
        ('password=abc"def"ghi', ("abc", "def", "ghi")),
        ("password=abc`def`ghi", ("abc", "def", "ghi")),
        ("password=abc\\\ndef", ("abc", "def")),
        ("password=$'abcd'", ("abcd",)),
        ("password=$(printf secretvalue)", ("secretvalue",)),
    )
    for raw, forbidden_parts in cases:
        public = privacy_module.public_redact(raw)
        assert "<redacted>" in public
        assert all(part not in public for part in forbidden_parts)


def test_multiline_shell_secret_values_are_removed_from_local_and_public_text() -> None:
    cases = (
        ('password="abcd\nsecretvalue"', ("abcd", "secretvalue")),
        ("password='ab\r\ncdefgh'", ("ab", "cdefgh")),
        ("password=$'a\nbcdefgh'", ("bcdefgh",)),
        ("password=$(\nprintf secretvalue\n)", ("printf", "secretvalue")),
        ("password=${TOKEN:-\nsecretvalue\n}", ("secretvalue",)),
    )
    for raw, forbidden_parts in cases:
        local = privacy_module.redact(raw, limit=4000)
        public = privacy_module.public_redact(raw, limit=4000)
        assert "<redacted>" in local
        assert "<redacted>" in public
        assert all(part not in local for part in forbidden_parts)
        assert all(part not in public for part in forbidden_parts)


def test_collector_removes_multiline_secret_from_private_and_public_artifacts(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / ".codex/sessions/multiline-secret.jsonl"
    write_jsonl(
        transcript,
        [
            {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "output": 'cs-feat failed password="abcd\nsecretvalue"',
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "不对，应该先 review。"},
            },
        ],
    )
    evidence = tmp_path / "evidence.json"

    assert (
        collector.main_with_args_for_test(
            ["--session", str(transcript), "--output", str(evidence)]
        )
        == 0
    )
    assert "secretvalue" not in evidence.read_text(encoding="utf-8")
    assert "secretvalue" not in (
        tmp_path / "public-issue-context.json"
    ).read_text(encoding="utf-8")


def test_public_redaction_fail_closes_unterminated_code_fence() -> None:
    public = privacy_module.public_redact(
        "cs-feat failed ```python\nprivate_code('customer logic')",
        limit=4000,
    )

    assert public == "cs-feat failed <code-block>"
    assert "private_code" not in public
    assert "customer logic" not in public
    assert "```" not in public


def test_public_secret_placeholders_do_not_self_lock_reporter() -> None:
    for sanitized in (
        "password=<redacted>",
        "password：<redacted>",
        "<auth-credential>",
        "<user-credential>",
        "<local-path>",
        "<url>",
        "<env>",
    ):
        assert privacy_module.public_redact(sanitized) == sanitized


def test_public_redaction_removes_http_auth_scheme_credentials() -> None:
    cases = (
        ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ("authorization: bearer abc123def", "abc123def"),
        ("Proxy-Authorization=Basic cHJveHk6cGFzcw==", "cHJveHk6cGFzcw=="),
        ("Bearer standalone123", "standalone123"),
    )
    for raw, credential in cases:
        public = privacy_module.public_redact(raw)
        assert credential not in public
        assert "<auth-credential>" in public


def test_public_redaction_removes_auth_headers_before_env_and_curl_userinfo() -> None:
    headers = (
        ("AUTHORIZATION=Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ("HTTP_AUTHORIZATION=Basic aHR0cDpwYXNz", "aHR0cDpwYXNz"),
        ("Authorization: token ghp_short12", "ghp_short12"),
        (
            'Authorization: Digest username="u", response="6629fae49393a05397450978507c4ef1"',
            "6629fae49393a05397450978507c4ef1",
        ),
    )
    for raw, credential in headers:
        public = privacy_module.public_redact(raw)
        assert credential not in public
        assert "<auth-credential>" in public

    userinfo = privacy_module.public_redact("curl -u deploy:password123 endpoint")
    assert "deploy:password123" not in userinfo
    assert "<user-credential>" in userinfo


def test_rerun_preserves_user_supplied_triage_fields(tmp_path: Path) -> None:
    transcript = tmp_path / ".codex/sessions/idempotent.jsonl"
    records = [
        {"type": "session_meta", "payload": {"session_id": "s1", "cwd": "/repo"}},
        {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feat failed"}},
        {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该 review。"}},
    ]
    write_jsonl(transcript, records)
    output = tmp_path / "evidence.json"
    args = ["--session", str(transcript), "--output", str(output)]
    collector.main_with_args_for_test(args)
    triage_path = tmp_path / "triage.json"
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    triage["reproduction"] = {
        "eval_profile": "routing-decision",
        "task_kind": "routing",
        "input": {"utterance": "synthetic user request"},
        "oracle": {"expect": {"result_type": "RoutedTo"}},
        "evidence_refs": ["obs-01"],
    }
    triage["privacy_review"] = {"status": "approved"}
    write_json(triage_path, triage)

    collector.main_with_args_for_test(args)
    rerun = json.loads(triage_path.read_text(encoding="utf-8"))
    assert rerun["reproduction"] == triage["reproduction"]
    assert rerun["privacy_review"] == {"status": "approved"}

    records.extend(
        [
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "cs-feedback failed again"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "不对，应该保留补充字段。"}},
        ]
    )
    write_jsonl(transcript, records)
    collector.main_with_args_for_test(args)
    shifted = json.loads(triage_path.read_text(encoding="utf-8"))
    assert shifted["reproduction"] == triage["reproduction"]
    assert shifted["privacy_review"] == {"status": "approved"}
    assert shifted["incident_id"] == ""
    assert shifted["previous_incident_id"] == "incident-01"
    assert shifted["pending_incident_id"] == "incident-02"
    assert shifted["previous_incident_fingerprint"]
    assert shifted["pending_incident_fingerprint"]
    assert shifted["previous_incident_fingerprint"] != shifted["pending_incident_fingerprint"]
    assert shifted["quality"]["triage_ready"] is False
    assert "incident_id_changed" in shifted["quality"]["reasons"]

    unresolved_again = triage_module.merge_existing_triage(
        triage_module.empty_triage(), shifted
    )
    assert unresolved_again["previous_incident_id"] == "incident-01"
    assert unresolved_again["pending_incident_id"] == "incident-02"
    assert (
        unresolved_again["pending_incident_fingerprint"]
        == shifted["pending_incident_fingerprint"]
    )

    before_invalid_accept = triage_path.read_text(encoding="utf-8")
    assert collector.main_with_args_for_test([*args, "--accept-incident", "incident-01"]) == 2
    assert triage_path.read_text(encoding="utf-8") == before_invalid_accept

    assert collector.main_with_args_for_test([*args, "--accept-incident", "incident-02"]) == 0
    accepted = json.loads(triage_path.read_text(encoding="utf-8"))
    assert accepted["incident_id"] == "incident-02"
    assert accepted["incident_fingerprint"] == shifted["pending_incident_fingerprint"]
    assert accepted["reproduction"] == triage["reproduction"]
    assert accepted["privacy_review"] == {"status": "pending"}
    assert accepted["previous_privacy_review"] == {"status": "approved"}
    assert accepted["previous_assessment"] == shifted["assessment"]
    assert "previous_incident_id" not in accepted
    assert "pending_incident_id" not in accepted
    assert accepted["quality"]["triage_ready"] is True

    unresolved = triage_module.merge_existing_triage(
        triage_module.empty_triage(), triage
    )
    assert unresolved["reproduction"] == triage["reproduction"]
    assert unresolved["incident_id"] == ""
    assert "incident_resolution_failed" in unresolved["quality"]["reasons"]


def test_same_position_incident_id_with_different_fingerprint_requires_reselection() -> None:
    def incident(session: str, cutoff: str, actual: str) -> dict:
        observations = [
            {
                "id": "obs-0001",
                "record_id": "record-0002",
                "source_index": 2,
                "role": "assistant",
                "record_type": "message",
                "text": actual,
            },
            {
                "id": "obs-0002",
                "record_id": cutoff,
                "source_index": 3,
                "role": "user",
                "record_type": "message",
                "text": "不对，应该先 review。",
            },
        ]
        return {
            "id": "incident-01",
            "target_skill": "cs-feat",
            "stage_hint": "review",
            "incident_kind": "skipped-gate",
            "observations": observations,
            "user_correction": observations[-1],
            "capture_cutoff": cutoff,
            "environment_context": {"provider": "codex", "session": session},
            "repo_context": {},
        }

    old_incident = incident("session-old", "record-0003", "skipped the old review")
    new_incident = incident("session-new", "record-0042", "skipped a different review")
    existing = triage_module.build_triage([old_incident], old_incident)
    existing["reproduction"]["input"] = {"utterance": "keep this input"}
    existing["privacy_review"] = {"status": "approved"}
    generated = triage_module.build_triage([new_incident], new_incident)

    assert existing["incident_id"] == generated["incident_id"] == "incident-01"
    assert existing["incident_fingerprint"] != generated["incident_fingerprint"]
    merged = triage_module.merge_existing_triage(generated, existing)
    assert merged["incident_id"] == ""
    assert merged["previous_incident_id"] == "incident-01"
    assert merged["pending_incident_id"] == "incident-01"
    assert merged["reproduction"]["input"] == {"utterance": "keep this input"}
    assert merged["privacy_review"] == {"status": "approved"}
    assert "incident_identity_changed" in merged["quality"]["reasons"]

    stale_incident = incident(
        "session-new", "record-0042", "the primary changed after selection"
    )
    stale_generated = triage_module.build_triage([stale_incident], stale_incident)
    try:
        triage_module.accept_pending_incident(
            stale_generated, merged, "incident-01"
        )
    except ValueError as exc:
        assert "fingerprint" in str(exc)
    else:
        raise AssertionError("stale pending incident acceptance must fail closed")


def test_quality_gate_blocks_missing_assessment_source_or_inferred_confidence() -> None:
    triage = {
        "incident_id": "incident-01",
        "observation_ids": ["obs-01", "obs-02"],
        "trigger_cutoff": "record-0003",
        "target": {"skill": "cs-feat"},
        "incident_kind": "wrong-route",
        "assessment": {
            "expected_behavior": {
                "value": "route to design",
                "source": "inferred",
                "evidence_refs": ["obs-01"],
            },
            "actual_behavior": {
                "value": "route to QA",
                "source": "",
                "evidence_refs": ["obs-02"],
            },
        },
        "reproduction": {
            "eval_profile": "routing-decision",
            "task_kind": "routing",
            "input": {"utterance": "continue"},
            "oracle": {"expect": {"result_type": "RoutedTo"}},
        },
    }

    quality = triage_module.recompute_quality(triage)
    assert quality["triage_ready"] is False
    assert quality["regression_ready"] is False
    assert "assessment.expected_behavior.confidence" in quality["missing_fields"]
    assert "assessment.actual_behavior.source" in quality["missing_fields"]
    assert quality["next_questions"] == ["assessment.expected_behavior.confidence"]


def test_quality_gate_rejects_unknown_source_values_and_dangling_observation_refs() -> None:
    triage = {
        "incident_id": "incident-01",
        "observation_ids": ["obs-01", "obs-02"],
        "trigger_cutoff": "record-0003",
        "target": {"skill": "cs-feat"},
        "incident_kind": "wrong-route",
        "assessment": {
            "expected_behavior": {
                "value": "route to design",
                "source": "fabricated",
                "evidence_refs": ["obs-01"],
            },
            "actual_behavior": {
                "value": "route to QA",
                "source": "transcript",
                "evidence_refs": ["obs-does-not-exist"],
            },
        },
        "reproduction": {
            "eval_profile": "routing-decision",
            "task_kind": "routing",
            "input": {"utterance": "continue"},
            "oracle": {"expect": {"result_type": "RoutedTo"}},
        },
    }

    quality = triage_module.recompute_quality(triage)
    assert quality["triage_ready"] is False
    assert quality["regression_ready"] is False
    assert "assessment.expected_behavior.source" in quality["missing_fields"]
    assert "assessment.actual_behavior.evidence_refs" in quality["missing_fields"]


def test_correlated_windows_keep_numeric_record_order_after_9999() -> None:
    def record(record_id: str):
        return models_module.NormalizedRecord(
            id=record_id,
            provider="codex",
            session="s1",
            timestamp="",
            role="tool",
            record_type="tool_result",
            tool_name="mcp",
            correlation_id="call-1",
            correlation_source="provider",
            text="failed",
            source_index=int(record_id.rsplit("-", 1)[-1]),
        )

    merged = incidents_module._merge_correlated_windows(
        [[record("record-9999")], [record("record-10000")]]
    )
    assert [item.id for item in merged[0]] == ["record-9999", "record-10000"]


def test_correlation_bridge_merges_every_connected_window_in_source_order() -> None:
    def record(record_id: str, correlation_id: str):
        return models_module.NormalizedRecord(
            id=record_id,
            provider="codex",
            session="s1",
            timestamp="",
            role="tool",
            record_type="tool_result",
            tool_name="mcp",
            correlation_id=correlation_id,
            correlation_source="provider",
            text="failed",
            source_index=int(record_id.rsplit("-", 1)[-1]),
        )

    merged = incidents_module._merge_correlated_windows(
        [
            [record("record-0001", "x")],
            [record("record-0002", "y")],
            [record("record-0003", "x"), record("record-0004", "y")],
        ]
    )

    assert len(merged) == 1
    assert [item.id for item in merged[0]] == [
        "record-0001",
        "record-0002",
        "record-0003",
        "record-0004",
    ]


def test_v1_failure_mapping_and_public_event_fields_remain_frozen() -> None:
    assert collector.V1_FAILURE_MAP == {
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
    assert collector.PUBLIC_EVENT_FIELDS == [
        "provider",
        "session_label",
        "timestamp_bucket",
        "failure_type",
        "match_type",
        "tool_name",
        "skill_or_reference",
        "sanitized_excerpt",
    ]
