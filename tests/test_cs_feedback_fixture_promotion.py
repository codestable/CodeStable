from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROMOTE_SCRIPT = ROOT / ".claude/skills/eval-cs-skill/scripts/promote_feedback_fixture.py"
CONVERTER_SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/feedback_to_fixture.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


promote = load_module(PROMOTE_SCRIPT, "promote_feedback_fixture_contract")
converter = load_module(CONVERTER_SCRIPT, "feedback_to_fixture_contract")
triage_module = sys.modules["feedback_triage"]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_canonical_feedback_pair(path: Path, payload: dict) -> None:
    triage = deepcopy(payload)
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


def compatible_config(**overrides) -> dict:
    config = {
        "name": "feedback-promotion-test",
        "skill_under_test": "cs-code-review",
        "variants": ["baseline"],
        "model_list": ["model-under-test"],
        "k": 1,
        "harnesses": ["api"],
        "scorers": ["recall_judge"],
        "fixture_classes": ["regression"],
        "judge_model": "independent-judge",
    }
    config.update(overrides)
    return config


def findings_candidate(**overrides) -> dict:
    candidate = {
        "id": "reg-cs-code-review-tool-failure",
        "privacy": "local-private",
        "_source": "cs-feedback",
        "_status": "candidate",
        "_profile": "findings-recall",
        "incident_id": "incident-01",
        "target_skill": "cs-code-review",
        "incident_kind": "tool-failure",
        "answerType": "findings-recall",
        "answer": ["unsafe_call must be reported"],
        "task": {
            "kind": "review",
            "spec": "synthetic review contract",
            "diff": "+ unsafe_call()",
        },
        "quality": {"triage_ready": True, "regression_ready": True, "missing_fields": []},
        "privacy_review": {"status": "approved"},
        "promotion_blockers": [],
    }
    candidate.update(overrides)
    return candidate


def run_promotion(tmp_path: Path, candidate: dict, config: dict) -> tuple[int, Path]:
    candidate_path = tmp_path / "feedback/regression-candidate.json"
    experiment = tmp_path / "experiment"
    write_json(candidate_path, candidate)
    write_json(experiment / "config.json", config)
    rc = promote.main(["--candidate", str(candidate_path), "--experiment", str(experiment)])
    target = experiment / "fixtures/regression" / f"{candidate['id']}.json"
    return rc, target


def test_valid_findings_candidate_promotes_only_commit_safe_fixture_fields(tmp_path: Path) -> None:
    rc, target = run_promotion(tmp_path, findings_candidate(), compatible_config())

    assert rc == 0
    fixture = json.loads(target.read_text(encoding="utf-8"))
    assert fixture == {
        "id": "reg-cs-code-review-tool-failure",
        "incident_id": "incident-01",
        "answerType": "findings-recall",
        "answer": ["unsafe_call must be reported"],
        "task": {
            "kind": "review",
            "spec": "synthetic review contract",
            "diff": "+ unsafe_call()",
        },
    }


def test_triage_candidate_to_repo_promotion_uses_only_json_artifact_handoff(tmp_path: Path) -> None:
    triage = tmp_path / "feedback/triage.json"
    write_canonical_feedback_pair(
        triage,
        {
            "schema_version": 2,
            "privacy": "local-private",
            "incident_id": "incident-01",
            "observation_ids": ["obs-02", "obs-03"],
            "trigger_cutoff": "record-0003",
            "target": {"skill": "cs-code-review", "stage_hint": "review"},
            "incident_kind": "tool-failure",
            "assessment": {
                "expected_behavior": {
                    "value": "report the synthetic unsafe call",
                    "source": "user",
                    "evidence_refs": ["obs-03"],
                },
                "actual_behavior": {
                    "value": "the synthetic unsafe call was missed",
                    "source": "transcript",
                    "evidence_refs": ["obs-02"],
                },
            },
            "reproduction": {
                "eval_profile": "findings-recall",
                "task_kind": "review",
                "input": {
                    "spec": "synthetic review contract",
                    "diff": "+ unsafe_call()",
                },
                "oracle": {"coverage_points": ["unsafe_call must be reported"]},
                "evidence_refs": ["obs-02", "obs-03"],
            },
            "quality": {"triage_ready": False, "regression_ready": False},
            "privacy_review": {"status": "approved"},
        },
    )
    assert converter.main(["--triage", str(triage)]) == 0
    candidate = triage.parent / "regression-candidate.json"
    experiment = tmp_path / "experiment"
    write_json(experiment / "config.json", compatible_config())

    assert (
        promote.main(["--candidate", str(candidate), "--experiment", str(experiment)])
        == 0
    )
    promoted = list((experiment / "fixtures/regression").glob("*.json"))
    assert len(promoted) == 1
    fixture_text = promoted[0].read_text(encoding="utf-8")
    assert "unsafe_call must be reported" in fixture_text
    assert "the synthetic unsafe call was missed" not in fixture_text


def test_valid_routing_candidate_promotes_with_routing_scorer(tmp_path: Path) -> None:
    candidate = findings_candidate(
        id="reg-cs-feat-wrong-route",
        _profile="routing-decision",
        target_skill="cs-feat",
        incident_kind="wrong-route",
        answerType="routing-decision",
        expect={"result_type": "RoutedTo", "target": "design-review"},
        task={"kind": "routing", "utterance": "continue the approved feature"},
    )
    candidate.pop("answer")
    config = compatible_config(
        skill_under_test="cs-feat",
        scorers=["routing_decision"],
        judge_model=None,
    )

    rc, target = run_promotion(tmp_path, candidate, config)
    assert rc == 0
    fixture = json.loads(target.read_text(encoding="utf-8"))
    assert fixture["answerType"] == "routing-decision"
    assert fixture["expect"]["result_type"] == "RoutedTo"


def test_promotion_without_experiment_config_never_creates_fixture_directory(tmp_path: Path) -> None:
    candidate_path = tmp_path / "feedback/regression-candidate.json"
    experiment = tmp_path / "experiment"
    write_json(candidate_path, findings_candidate())
    experiment.mkdir()

    assert (
        promote.main(
            ["--candidate", str(candidate_path), "--experiment", str(experiment)]
        )
        != 0
    )
    assert not (experiment / "fixtures").exists()


@pytest.mark.parametrize(
    ("candidate_patch", "config_patch"),
    [
        ({}, {"scorers": ["planted_defect"]}),
        ({}, {"judge_model": None}),
        ({}, {"judge_model": "mock-judge"}),
        ({}, {"judge_model": "model-under-test"}),
        ({"target_skill": "cs-audit"}, {}),
        ({"_profile": "routing-decision"}, {}),
        ({"promotion_blockers": ["reproduction.input"]}, {}),
        ({"privacy_review": {"status": "pending"}}, {}),
        ({"id": "../escape"}, {}),
        ({}, {"fixture_classes": ["planted-defect"]}),
    ],
)
def test_findings_promotion_gates_fail_closed_without_writing(
    tmp_path: Path, candidate_patch: dict, config_patch: dict
) -> None:
    candidate = findings_candidate(**deepcopy(candidate_patch))
    config = compatible_config(**deepcopy(config_patch))

    rc, target = run_promotion(tmp_path, candidate, config)
    assert rc != 0
    assert not target.exists()


@pytest.mark.parametrize(
    "unsafe_value",
    [
        "/home/alice/private-spec.md",
        "/repo",
        "API_TOKEN=topsecret123",
        "https://github.com/acme/private",
        "token=secret123456",
        '{"token":"secret123456"}',
        "password=p@ssw0rd!123",
        'password: "correct horse battery staple"',
        'export password="s3cr3tv@lue"',
        'token = "abc def ghi jkl"',
        "password=abc<def>ghi",
        "password=`s3cr3tv@l!`",
        "password：hunter22!",
        "token＝abc<def>ghi",
        'password="s3cr3tv@lue',
        "token='unterminated secret value",
        r"password=secret\ pass",
        "password：`abc<def>ghi`",
        "password=abc'def'ghi",
        'password=abc"def"ghi',
        "password=abc`def`ghi",
        "password=abc\\\ndef",
        "password=$'abcd'",
        "password=$(printf secretvalue)",
        'password="abcd\nsecretvalue"',
        "password='ab\r\ncdefgh'",
        "password=$'a\nbcdefgh'",
        "password=$(\nprintf secretvalue\n)",
        "password=${TOKEN:-\nsecretvalue\n}",
        "Authorization: Basic dXNlcjpwYXNz",
        "Bearer standalone123",
        "Proxy-Authorization=Basic cHJveHk6cGFzcw==",
        "Authorization: token ghp_short12",
        "curl -u deploy:password123 endpoint",
        "TODO replace this placeholder",
        "unknown",
        "   ",
    ],
)
def test_commit_safe_scan_rejects_each_private_or_placeholder_field(
    tmp_path: Path, unsafe_value: str
) -> None:
    candidate = findings_candidate()
    candidate["task"] = {**candidate["task"], "spec": unsafe_value}

    rc, target = run_promotion(tmp_path, candidate, compatible_config())
    assert rc != 0
    assert not target.exists()


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("password=hunter22", "safe", "secret"),
        ("API_TOKEN", "safe", "environment-name"),
        ("marker", "local-private", "private-marker"),
    ],
)
def test_commit_safe_scan_checks_dict_keys_and_private_markers(
    key: str, value: str, reason: str
) -> None:
    problems = promote._commit_safe_issues({"task": {key: value}})
    assert any(reason in problem for problem in problems)


def test_promotion_rejects_task_keys_outside_profile_schema_without_writing(
    tmp_path: Path,
) -> None:
    candidate = findings_candidate()
    candidate["task"] = {**candidate["task"], "unexpected": "safe"}

    rc, target = run_promotion(tmp_path, candidate, compatible_config())
    assert rc != 0
    assert not target.exists()


def test_promotion_rejects_invalid_candidate_value_types_without_writing(
    tmp_path: Path,
) -> None:
    routing = findings_candidate(
        id="reg-cs-feat-wrong-route",
        _profile="routing-decision",
        target_skill="cs-feat",
        incident_kind="wrong-route",
        answerType="routing-decision",
        expect={"result_type": "RoutedTo", "target": "design-review"},
        task={"kind": "routing", "state": {"stage": "review"}},
    )
    routing.pop("answer")
    routing_config = compatible_config(
        skill_under_test="cs-feat",
        scorers=["routing_decision"],
        judge_model=None,
    )
    cases = (
        (
            {**routing, "expect": {"result_type": {"nested": "safe"}}},
            routing_config,
        ),
        ({**routing, "task": {"kind": "routing", "state": ["review"]}}, routing_config),
        (
            findings_candidate(
                task={"kind": "review", "spec": ["not", "text"], "diff": "+ safe"}
            ),
            compatible_config(),
        ),
        (
            findings_candidate(
                quality={
                    "triage_ready": "true",
                    "regression_ready": True,
                    "missing_fields": [],
                }
            ),
            compatible_config(),
        ),
        (findings_candidate(incident_id=["incident-01"]), compatible_config()),
    )
    for index, (candidate, config) in enumerate(cases):
        rc, target = run_promotion(tmp_path / str(index), candidate, config)
        assert rc == 2
        assert not target.exists()


@pytest.mark.parametrize("kind", ["design", "docs"])
def test_design_and_docs_candidates_require_non_mock_harness(tmp_path: Path, kind: str) -> None:
    target_skill = "cs-feat" if kind == "design" else "cs-docs"
    candidate = findings_candidate(
        id=f"reg-{target_skill}-unclear-rule",
        target_skill=target_skill,
        incident_kind="unclear-rule",
        task={
            "kind": kind,
            "spec": "synthetic requirement",
            "diff": "+ synthetic material" if kind == "docs" else "",
        },
    )
    config = compatible_config(skill_under_test=target_skill, harnesses=["mock"])

    rc, target = run_promotion(tmp_path, candidate, config)
    assert rc != 0
    assert not target.exists()
