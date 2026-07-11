from __future__ import annotations

import ast
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONVERTER_SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/feedback_to_fixture.py"


def load_converter():
    spec = importlib.util.spec_from_file_location("feedback_to_fixture_candidate", CONVERTER_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


converter = load_converter()
triage_module = sys.modules["feedback_triage"]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def write_canonical_feedback_pair(path: Path, payload: dict) -> dict:
    triage = deepcopy(payload)
    triage.setdefault("trigger_cutoff", "record-0003")
    observations = [
        {
            "id": observation_id,
            "record_id": f"record-{index:04d}",
            "role": "assistant",
            "record_type": "message",
            "text": f"synthetic observation {observation_id}",
        }
        for index, observation_id in enumerate(triage.get("observation_ids", []), 1)
    ]
    incident = {
        "id": triage["incident_id"],
        "target_skill": triage.get("target", {}).get("skill", "unknown"),
        "stage_hint": triage.get("target", {}).get("stage_hint", "unknown"),
        "incident_kind": triage.get("incident_kind", "unknown"),
        "observations": observations,
        "capture_cutoff": triage["trigger_cutoff"],
        "environment_context": {"provider": "codex", "session": "session-test"},
    }
    triage["incident_fingerprint"] = triage_module.incident_fingerprint(incident)
    write_json(path, triage)
    write_json(
        path.with_name("evidence.json"),
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incidents": [incident],
        },
    )
    return triage


def test_feedback_converter_writes_local_candidate_and_rejects_legacy_direct_write(tmp_path: Path) -> None:
    feedback_dir = tmp_path / "feedback/case-1"
    triage = feedback_dir / "triage.json"
    write_canonical_feedback_pair(
        triage,
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incident_id": "incident-01",
            "observation_ids": ["obs-1", "obs-2"],
            "target": {"skill": "cs-code-review", "stage_hint": "review"},
            "incident_kind": "tool-failure",
            "assessment": {
                "expected_behavior": {
                    "value": "发现阻塞问题",
                    "source": "user",
                    "evidence_refs": ["obs-1"],
                },
                "actual_behavior": {
                    "value": "漏报阻塞问题",
                    "source": "transcript",
                    "evidence_refs": ["obs-2"],
                },
            },
            "reproduction": {
                "eval_profile": "findings-recall",
                "task_kind": "review",
                "input": {"spec": "review spec", "diff": "+ unsafe_call()"},
                "oracle": {"coverage_points": ["unsafe_call must be reported"]},
            },
            "quality": {"triage_ready": True, "regression_ready": True},
            "privacy_review": {"status": "approved"},
        },
    )

    assert converter.main(["--triage", str(triage)]) == 0
    candidate = feedback_dir / "regression-candidate.json"
    data = json.loads(candidate.read_text(encoding="utf-8"))
    assert data["_status"] == "candidate"
    assert data["privacy"] == "local-private"
    assert data["answerType"] == "findings-recall"

    legacy_exp = tmp_path / "experiment"
    assert converter.main(["--experiment", str(legacy_exp), "--failure", "old path"]) != 0
    assert not (legacy_exp / "fixtures/regression").exists()


def test_v1_public_context_only_creates_a_not_ready_candidate(tmp_path: Path) -> None:
    evidence = tmp_path / "feedback/public-issue-context.json"
    write_json(
        evidence,
        {
            "privacy": "public-preview",
            "events": [
                {
                    "failure_type": "tool-failure",
                    "sanitized_excerpt": "synthetic tool failure",
                }
            ],
        },
    )

    assert converter.main(["--evidence", str(evidence)]) == 0
    candidate = json.loads(
        (evidence.parent / "regression-candidate.json").read_text(encoding="utf-8")
    )
    assert candidate["quality"]["regression_ready"] is False
    assert "triage.json" in candidate["promotion_blockers"]


def test_feedback_converter_rejects_noncanonical_triage_without_writing(tmp_path: Path) -> None:
    triage = tmp_path / "feedback/triage.json"
    write_json(
        triage,
        {
            "schema_version": 2,
            "privacy": "public-preview",
            "incident_id": "incident-01",
            "target": {"skill": "cs-feat"},
            "incident_kind": "wrong-route",
        },
    )

    assert converter.main(["--triage", str(triage)]) != 0
    assert not (triage.parent / "regression-candidate.json").exists()


def test_feedback_converter_rejects_malformed_nested_triage_objects(tmp_path: Path) -> None:
    triage = tmp_path / "feedback/triage.json"
    base = {
        "schema_version": 2,
        "privacy": "local-private",
        "incident_id": "incident-01",
        "target": {},
        "assessment": {},
        "reproduction": {},
        "privacy_review": {},
    }
    for key in ("target", "assessment", "reproduction", "privacy_review"):
        payload = {**base, key: None}
        write_json(triage, payload)
        candidate = triage.parent / "regression-candidate.json"
        candidate.unlink(missing_ok=True)
        assert converter.main(["--triage", str(triage)]) != 0
        assert not candidate.exists()


def test_feedback_converter_rejects_unselected_incident_without_writing(tmp_path: Path) -> None:
    triage = tmp_path / "feedback/triage.json"
    write_json(
        triage,
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incident_id": " ",
            "target": {},
            "assessment": {},
            "reproduction": {},
            "privacy_review": {},
        },
    )

    assert converter.main(["--triage", str(triage)]) != 0
    assert not (triage.parent / "regression-candidate.json").exists()


def test_feedback_converter_rejects_triage_not_bound_to_canonical_evidence(
    tmp_path: Path,
) -> None:
    triage_path = tmp_path / "feedback/triage.json"
    base = write_canonical_feedback_pair(
        triage_path,
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incident_id": "incident-01",
            "observation_ids": ["obs-01", "obs-02"],
            "target": {"skill": "cs-code-review", "stage_hint": "review"},
            "incident_kind": "tool-failure",
            "assessment": {
                "expected_behavior": {
                    "value": "report the finding",
                    "source": "user",
                    "evidence_refs": ["obs-01"],
                },
                "actual_behavior": {
                    "value": "finding was missed",
                    "source": "transcript",
                    "evidence_refs": ["obs-02"],
                },
            },
            "reproduction": {
                "eval_profile": "findings-recall",
                "task_kind": "review",
                "input": {"spec": "synthetic spec", "diff": "+ unsafe_call()"},
                "oracle": {"coverage_points": ["report unsafe_call"]},
                "evidence_refs": ["obs-01", "obs-02"],
            },
            "quality": {"triage_ready": True, "regression_ready": True},
            "privacy_review": {"status": "approved"},
        },
    )
    mutations = (
        {**base, "incident_id": "incident-02"},
        {**base, "incident_fingerprint": "sha256:forged"},
        {
            **base,
            "observation_ids": ["obs-does-not-exist"],
            "assessment": {
                **base["assessment"],
                "expected_behavior": {
                    **base["assessment"]["expected_behavior"],
                    "evidence_refs": ["obs-does-not-exist"],
                },
                "actual_behavior": {
                    **base["assessment"]["actual_behavior"],
                    "evidence_refs": ["obs-does-not-exist"],
                },
            },
            "reproduction": {
                **base["reproduction"],
                "evidence_refs": ["obs-does-not-exist"],
            },
        },
    )
    for mutation in mutations:
        write_json(triage_path, mutation)
        candidate = triage_path.with_name("regression-candidate.json")
        candidate.unlink(missing_ok=True)
        assert converter.main(["--triage", str(triage_path)]) == 2
        assert not candidate.exists()


def test_feedback_converter_recomputes_blockers_and_never_copies_assessment_fallback(
    tmp_path: Path,
) -> None:
    triage = tmp_path / "feedback/triage.json"
    write_canonical_feedback_pair(
        triage,
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incident_id": "incident-01",
            "observation_ids": ["obs-02"],
            "target": {"skill": "cs-code-review", "stage_hint": "review"},
            "incident_kind": "tool-failure",
            "assessment": {
                "expected_behavior": {
                    "value": "PRIVATE ASSESSMENT MUST NOT BECOME ORACLE",
                    "source": "user",
                    "evidence_refs": [],
                },
                "actual_behavior": {
                    "value": "PRIVATE ACTUAL MUST NOT BECOME FIXTURE",
                    "source": "transcript",
                    "evidence_refs": ["obs-02"],
                },
            },
            "reproduction": {
                "eval_profile": "findings-recall",
                "task_kind": "review",
                "input": {"diff": "+ synthetic_bug()"},
                "oracle": None,
                "evidence_refs": [],
            },
            "quality": {"triage_ready": True, "regression_ready": True},
            "privacy_review": {"status": "approved"},
        },
    )

    assert converter.main(["--triage", str(triage)]) == 0
    candidate = json.loads(
        (triage.parent / "regression-candidate.json").read_text(encoding="utf-8")
    )
    candidate_text = json.dumps(candidate, ensure_ascii=False)
    assert candidate["answer"] == []
    assert "reproduction.oracle.coverage_points" in candidate["promotion_blockers"]
    assert "assessment.expected_behavior.evidence_refs" in candidate["promotion_blockers"]
    assert "PRIVATE ASSESSMENT" not in candidate_text
    assert "PRIVATE ACTUAL" not in candidate_text


def test_shipped_converter_has_no_runtime_import_of_repo_local_eval_tools() -> None:
    source = CONVERTER_SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(alias.name for alias in node.names)
    assert not {"config", "fixtures", "buildprompt", "promote_feedback_fixture"} & imported
    assert ".claude/skills/eval-cs-skill" not in source
