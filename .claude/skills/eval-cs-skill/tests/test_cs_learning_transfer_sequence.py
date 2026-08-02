"""learning-transfer sequence 的恢复、隔离与清理契约。"""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


EVAL_SKILL = Path(__file__).resolve().parents[1]
ROOT = EVAL_SKILL.parents[2]
SCRIPTS = EVAL_SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import sequence  # noqa: E402
import e2e_env  # noqa: E402
import runner as runner_mod  # noqa: E402
from _model import ExecutionTarget, Fixture, HarnessResult  # noqa: E402
from config import ExperimentConfig  # noqa: E402


def _fixture() -> Fixture:
    return Fixture.from_dict({
        "id": "lt-checkpoint",
        "answerType": "learning-transfer",
        "task": {"kind": "learning-transfer"},
        "scenario": {
            "class": "positive",
            "seed": "dispatchboard-learning",
            "a": {
                "skill": "cs-feat",
                "request": "complete task A",
                "candidate_source": "output",
            },
            "candidate": {
                "expected_home": "lesson",
                "required_concepts": ["example"],
            },
            "b": {"skill": "cs-feat", "request": "complete task B"},
            "preflight": {},
            "expect": {"lesson_transition": "observed->validated"},
        },
    })


def _config(*, model: str = "mock-model") -> ExperimentConfig:
    return ExperimentConfig(
        name="learning-transfer-checkpoint",
        skill_under_test="cs-feat",
        execution_mode="learning-transfer",
        model_targets=[{
            "id": "fake-target",
            "family": "fake-family",
            "harness": "fake-harness",
            "model": model,
        }],
    )


def _stub_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    def build_seed(_seed: str, destination: Path, _root: Path) -> Path:
        destination.mkdir(parents=True)
        return destination

    def run_pair(**kwargs) -> dict:
        kwargs["phase_callback"]({
            "phase": "a",
            "status": "passed",
            "metrics": {"cost_usd": {"value": 0.01, "tag": "measured"}},
        })
        return {"state": "completed", "phase_metrics": []}

    monkeypatch.setattr(sequence, "build_seed_repo", build_seed)
    monkeypatch.setattr(sequence, "preflight_fixture", lambda *_args: {"ok": True})
    monkeypatch.setattr(sequence, "run_pair", run_pair)


def _structurally_valid_pair() -> dict:
    return {
        "state": "completed",
        "phase_metrics": [],
        "a_ok": True,
        "a_mutation_ok": True,
        "candidate_unique": True,
        "lesson_schema_ok": True,
        "lesson_only_mutation": True,
        "prompt_equal": True,
        "isolation_ok": True,
        "lesson_transition_ok": True,
        "lesson_expectation_ok": True,
        "treatment_mutation_ok": True,
        "control_mutation_ok": True,
        "treatment_regression_ok": True,
        "control_regression_ok": True,
    }


@pytest.mark.parametrize(
    "output,match",
    [
        ("完成。\n晶化候选：example rule", "首个非空输出行"),
        ("晶化候选：unrelated rule", "required concepts"),
    ],
)
def test_output_candidate_requires_first_line_and_frozen_concepts(
    tmp_path, output, match,
) -> None:
    with pytest.raises(ValueError, match=match):
        sequence.extract_candidate(_fixture(), output, tmp_path)


def test_epic_candidate_uses_only_the_new_evidence_delta(tmp_path) -> None:
    fixture = _fixture()
    fixture.raw["scenario"]["a"].update({
        "skill": "cs-epic",
        "candidate_source": "epic-cursor",
    })
    cursor = tmp_path / ".codestable/work/epic-example.md"
    cursor.parent.mkdir(parents=True)
    cursor.write_text(
        "## 临时决策与证据\n\n- 晶化候选：old example rule\n",
        encoding="utf-8",
    )
    before = sequence.snapshot_candidates(fixture, tmp_path)
    cursor.write_text(
        cursor.read_text(encoding="utf-8")
        + "- 晶化候选：new example rule\n",
        encoding="utf-8",
    )

    assert sequence.extract_candidate(
        fixture,
        "Epic 子项不得展示候选",
        tmp_path,
        before=before,
    ) == "new example rule"


def test_adapter_exception_emits_soft_invocation_cost(tmp_path) -> None:
    class RaisingHarness:
        name = "raising"

        def invoke(self, *_args, **_kwargs):
            raise TimeoutError("provider detail must not enter the checkpoint")

    events: list[dict] = []
    with pytest.raises(sequence.RetryableSequenceError, match="TimeoutError"):
        sequence._invoke_phase(
            harness=RaisingHarness(),
            prompt="paid prompt",
            target=ExecutionTarget(
                id="fake-target",
                family="fake-family",
                harness="raising",
                model="mock-model",
            ),
            workdir=tmp_path,
            phase="a",
            emit=events.append,
        )

    assert [event["status"] for event in events] == [
        "invocation-started",
        "retryable-error",
    ]
    assert events[0]["invocation_id"] == events[1]["invocation_id"]
    assert events[1]["error_type"] == "TimeoutError"
    assert events[1]["metrics"]["cost_usd"]["tag"] == "soft"
    assert "provider detail" not in json.dumps(events)


def test_invocation_start_is_durable_before_the_provider_and_reuses_its_id(tmp_path) -> None:
    events: list[dict] = []

    class ObservingHarness:
        name = "observing"

        def invoke(self, _prompt, model, _workdir, timeout_s):
            assert timeout_s == 600
            assert events[0]["status"] == "invocation-started"
            assert events[0]["metrics"]["cost_usd"]["tag"] == "soft"
            return HarnessResult(
                output="completed",
                model=model,
                harness=self.name,
                wall_ms=1,
                usage={"input_tokens": 10, "output_tokens": 5},
            )

    sequence._invoke_phase(
        harness=ObservingHarness(),
        prompt="paid prompt",
        target=ExecutionTarget(
            id="fake-target",
            family="fake-family",
            harness="observing",
            model="mock-model",
        ),
        workdir=tmp_path,
        phase="a",
        emit=events.append,
    )

    assert [event["status"] for event in events] == [
        "invocation-started",
        "invocation-complete",
    ]
    assert events[0]["invocation_id"] == events[1]["invocation_id"]


@pytest.mark.parametrize(
    "terminal,error_type",
    [
        (None, "InterruptedInvocation"),
        ("retryable-error", "TimeoutError"),
    ],
)
def test_invocation_journal_recovers_operational_error_without_generic_error_event(
    tmp_path,
    terminal,
    error_type,
) -> None:
    checkpoint = tmp_path / "results.partial.jsonl"
    base = {
        "target_id": "fake-target",
        "fixture_id": "lt-checkpoint",
        "k_index": 0,
        "phase": "a",
        "invocation_id": "invocation-1",
        "metrics": {"cost_usd": {"value": 0.25, "tag": "soft"}},
    }
    sequence.append_checkpoint(checkpoint, {**base, "status": "invocation-started"})
    if terminal is not None:
        sequence.append_checkpoint(checkpoint, {
            **base,
            "status": terminal,
            "error_type": error_type,
        })
    else:
        with checkpoint.open("a", encoding="utf-8") as handle:
            handle.write('{"phase":"a","status":"invocation-complete"')

    sequence._repair_checkpoint_tail(checkpoint)
    operational = sequence.load_retryable_errors(checkpoint)
    cost = sequence._checkpoint_actual_cost(checkpoint)

    assert len(operational) == 1
    assert operational[0]["error"] == error_type
    assert cost == {
        "invocation_count": 1,
        "cost_usd": {"value": 0.25, "tag": "soft"},
    }


def test_checkpoint_tail_repair_preserves_original_if_atomic_replace_fails(
    monkeypatch,
    tmp_path,
) -> None:
    checkpoint = tmp_path / "results.partial.jsonl"
    original = b'{"phase":"header"}\n{"phase":"truncated"'
    checkpoint.write_bytes(original)

    def fail_replace(_source, _destination):
        raise OSError("replace interrupted")

    monkeypatch.setattr(sequence.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace interrupted"):
        sequence._repair_checkpoint_tail(checkpoint)

    assert checkpoint.read_bytes() == original
    assert not list(tmp_path.glob(f".{checkpoint.name}.*.tmp"))


def test_invocation_terminal_cannot_reuse_an_id_across_cells(tmp_path) -> None:
    checkpoint = tmp_path / "results.partial.jsonl"
    start = {
        "target_id": "fake-target",
        "fixture_id": "lt-checkpoint",
        "k_index": 0,
        "phase": "a",
        "status": "invocation-started",
        "invocation_id": "invocation-1",
        "metrics": {"cost_usd": {"value": 0.25, "tag": "soft"}},
    }
    sequence.append_checkpoint(checkpoint, start)
    sequence.append_checkpoint(checkpoint, {
        **start,
        "fixture_id": "different-fixture",
        "status": "invocation-complete",
    })

    with pytest.raises(ValueError, match="identity 不匹配"):
        sequence._reduce_checkpoint(checkpoint)


def test_checkpoint_rejects_resume_when_execution_target_changes(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "fixtures": [_fixture()],
        "k": 1,
        "experiment_dir": tmp_path / "experiment",
        "root": ROOT,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }

    sequence.run_sequence(config=_config(), **kwargs)
    assert not (tmp_path / "runs/fake-target__lt-checkpoint__0").exists()

    with pytest.raises(ValueError, match="checkpoint.*不匹配"):
        sequence.run_sequence(config=_config(model="different-model"), **kwargs)

    events = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    assert events[0]["kind"] == "sequence-checkpoint-header"
    assert set(events[0]["inputs"]) == {
        "config",
        "fixtures",
        "skill_snapshots",
        "pipeline",
        "experiment_assets",
        "seeds",
        "targets",
        "k",
        "run_identity",
    }
    assert events[0]["inputs"]["pipeline"]["sequence.py"] == hashlib.sha256(
        Path(sequence.__file__).read_bytes()
    ).hexdigest()
    assert {
        "_model.py",
        "buildprompt.py",
        "config.py",
        "e2e_env.py",
        "fixtures.py",
        "metrics.py",
        "runner.py",
        "scorers/__init__.py",
        "scorers/base.py",
        "scorers/learning_transfer.py",
        "harness/adapter_claude.py",
        "harness/adapter_codex.py",
    } <= set(events[0]["inputs"]["pipeline"])
    a_event = next(event for event in events if event.get("phase") == "a")
    assert a_event["phase_key"] == "fake-target|lt-checkpoint|0|a"


def test_freeze_scale_allows_only_proportional_k_calibration() -> None:
    required = {
        "model_families": 2,
        "positive_fixtures": 4,
        "guard_fixtures": 2,
        "k": 5,
        "pairs": 60,
        "agent_invocations": 240,
        "hook_runs": 20,
    }
    calibration = {
        **required,
        "k": 2,
        "pairs": 24,
        "agent_invocations": 96,
        "hook_runs": 8,
    }

    assert sequence._freeze_run_mode(required, required) == "final"
    assert sequence._freeze_run_mode(required, calibration) == "calibration"
    with pytest.raises(ValueError, match="完整 fixtures 与 model families"):
        sequence._freeze_run_mode(
            required,
            {**calibration, "model_families": 1, "pairs": 12, "agent_invocations": 48},
        )


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda manifest: manifest.update({"schema_version": 2}), "schema_version"),
        (lambda manifest: manifest.update({"hash_algorithm": "sha1"}), "hash_algorithm"),
        (
            lambda manifest: manifest["primary_metric"].update({"aggregation": "per family"}),
            "primary_metric",
        ),
        (
            lambda manifest: manifest["primary_metric"].update({"family_guard": "optional"}),
            "primary_metric",
        ),
    ],
)
def test_freeze_metadata_must_match_the_preregistered_contract(mutation, match) -> None:
    manifest = {
        "schema_version": 1,
        "hash_algorithm": "sha256",
        "primary_metric": dict(sequence._PRIMARY_METRIC),
    }
    mutation(manifest)

    with pytest.raises(ValueError, match=match):
        sequence._validate_freeze_metadata(manifest)


def test_actual_cost_includes_invocations_from_failed_half_pair(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)

    def fail_after_a(**kwargs) -> dict:
        kwargs["phase_callback"]({
            "phase": "a",
            "status": "passed",
            "metrics": {"cost_usd": {"value": 0.25, "tag": "measured"}},
        })
        raise RuntimeError("transient harness failure")

    monkeypatch.setattr(sequence, "run_pair", fail_after_a)
    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=tmp_path / "results.partial.jsonl",
        harness_resolver=lambda _name: object(),
    )

    assert payload["aggregate"]["cost"] == {
        "invocation_count": 1,
        "cost_usd": {"value": 0.25, "tag": "measured"},
    }


def test_successful_invocation_is_checkpointed_before_deterministic_oracle_failure(
    monkeypatch,
    tmp_path,
) -> None:
    _stub_sequence(monkeypatch)

    class PaidHarness:
        name = "paid-harness"

        def invoke(self, _prompt, model, _workdir, timeout_s):
            assert timeout_s == 600
            return HarnessResult(
                output="completed",
                model=model,
                harness=self.name,
                wall_ms=1,
                usage={"input_tokens": 10, "output_tokens": 5},
            )

    harness = PaidHarness()

    def fail_after_paid_invocation(**kwargs) -> dict:
        sequence._invoke_phase(
            harness=harness,
            prompt="paid prompt",
            target=ExecutionTarget(
                id="fake-target",
                family="fake-family",
                harness=harness.name,
                model="mock-model",
            ),
            workdir=tmp_path,
            phase="a",
            emit=kwargs["phase_callback"],
        )
        raise ValueError("deterministic oracle failed")

    monkeypatch.setattr(sequence, "run_pair", fail_after_paid_invocation)
    checkpoint = tmp_path / "results.partial.jsonl"
    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=checkpoint,
        harness_resolver=lambda _name: harness,
    )

    assert payload["errors"][0]["state"] == "pipeline-error"
    assert payload["aggregate"]["cost"]["invocation_count"] == 1
    events = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    invocation = next(
        event
        for event in events
        if event.get("phase") == "a" and event.get("status") == "invocation-complete"
    )
    assert invocation["status"] == "invocation-complete"


def test_checkpoint_rejects_resume_when_experiment_asset_changes(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)
    experiment = tmp_path / "experiment"
    check = experiment / "checks/a.py"
    check.parent.mkdir(parents=True)
    check.write_text("def test_a(): assert True\n", encoding="utf-8")
    fixture = _fixture()
    fixture.raw["scenario"]["a"]["checks"] = ["checks/a.py"]
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [fixture],
        "k": 1,
        "experiment_dir": experiment,
        "root": ROOT,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }

    sequence.run_sequence(**kwargs)
    check.write_text("def test_a(): assert False\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checkpoint.*不匹配"):
        sequence.run_sequence(**kwargs)


def test_curation_rejects_git_control_mutation(tmp_path) -> None:
    fixture = _fixture()
    fixture.raw["scenario"]["a"].update({
        "checks": [],
        "allowed_paths": ["post-a.txt"],
    })
    seed = tmp_path / "seed"
    seed.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=seed, check=True)
    (seed / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=seed, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=seed, check=True)

    class CurationGitMutatingHarness:
        name = "curation-git-mutating"

        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, prompt, model, workdir, timeout_s):
            assert timeout_s == 600
            self.calls += 1
            if self.calls == 1:
                (workdir / "post-a.txt").write_text("done\n", encoding="utf-8")
                output = "晶化候选：example rule"
            else:
                lesson = workdir / ".codestable/lessons/2026-08-02-example.md"
                lesson.parent.mkdir(parents=True)
                lesson.write_text(
                    "---\nstatus: observed\nscope: example\ndate: 2026-08-02\n---\n"
                    "规则：example rule。\n"
                    "适用 / 不适用：适用于 example；已有 owner 时停止。\n"
                    "证据：post-a.txt。\n候选归宿：project-doc\n",
                    encoding="utf-8",
                )
                subprocess.run(
                    ["git", "config", "user.name", "changed"],
                    cwd=workdir,
                    check=True,
                )
                output = "recorded"
            return HarnessResult(
                output=output,
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    harness = CurationGitMutatingHarness()
    pair = sequence.run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake-target",
            family="fake-family",
            harness=harness.name,
            model="mock-model",
        ),
        k_index=0,
        seed_repo=seed,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=tmp_path / "run",
        harness=harness,
    )

    assert harness.calls == 2
    assert pair["state"] == "pipeline-failed"
    assert pair["curation_repo_integrity_ok"] is False
    assert pair["lesson_only_mutation"] is False


def test_repo_manifest_only_ignores_root_git_control_directory(tmp_path) -> None:
    root_git = tmp_path / ".git/config"
    nested_git = tmp_path / "module/.git/payload.txt"
    root_git.parent.mkdir(parents=True)
    nested_git.parent.mkdir(parents=True)
    root_git.write_text("ignored\n", encoding="utf-8")
    nested_git.write_text("business data\n", encoding="utf-8")

    manifest = sequence.repo_manifest(tmp_path)

    assert ".git/config" not in manifest
    assert "module/.git/payload.txt" in manifest


def test_repo_control_rejects_a_git_dir_outside_the_cell(tmp_path) -> None:
    repo = tmp_path / "cell"
    external_git = tmp_path / "external-git"
    subprocess.run(
        ["git", "init", "-q", "--separate-git-dir", str(external_git), str(repo)],
        check=True,
    )

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["repository"] is True
    assert snapshot["safe"] is False
    assert sequence.repo_control_unchanged(snapshot, snapshot) is False


def test_pair_baseline_comparison_preserves_preexisting_lessons() -> None:
    existing = ".codestable/lessons/2026-07-01-existing.md"
    injected = ".codestable/lessons/2026-08-02-new.md"
    control = {"app.py": "same", existing: "existing"}
    treatment = {**control, injected: "new"}

    assert sequence._differs_only_by_path(treatment, control, injected) is True


def test_repo_control_snapshot_rejects_external_hooks_without_reading_them(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    external = tmp_path / "external-hooks"
    external.mkdir()
    (external / "secret").write_text("must not be read\n", encoding="utf-8")
    subprocess.run(
        ["git", "config", "core.hooksPath", str(external)],
        cwd=repo,
        check=True,
    )
    original_hash_tree = e2e_env._hash_tree

    def guarded_hash_tree(path: Path):
        assert path.resolve() != external.resolve()
        return original_hash_tree(path)

    monkeypatch.setattr(e2e_env, "_hash_tree", guarded_hash_tree)

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is False
    assert snapshot["hooks"] is None


def test_repo_control_snapshot_rejects_local_config_includes_before_running_git(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    external = tmp_path / "external.gitconfig"
    external.write_text("[alias]\n  leaked = status\n", encoding="utf-8")
    subprocess.run(
        ["git", "config", "include.path", str(external)],
        cwd=repo,
        check=True,
    )

    def unexpected_git(*_args, **_kwargs):
        raise AssertionError("local include 必须在任何 Git 子进程前被拒绝")

    monkeypatch.setattr(e2e_env, "_git_output", unexpected_git)
    monkeypatch.setattr(e2e_env.subprocess, "run", unexpected_git)

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is False
    assert snapshot["local_config"] == hashlib.sha256(
        (repo / ".git/config").read_bytes()
    ).hexdigest()


def test_repo_control_rejects_bom_prefixed_include_before_running_git(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    config = repo / ".git/config"
    config.write_text(
        "\ufeff[include]\n  path = /tmp/outside.gitconfig\n" + config.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    def unexpected_git(*_args, **_kwargs):
        raise AssertionError("BOM include 必须在任何 Git 子进程前被拒绝")

    monkeypatch.setattr(e2e_env, "_git_output", unexpected_git)
    monkeypatch.setattr(e2e_env.subprocess, "run", unexpected_git)

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is False
    assert snapshot["local_config"] == hashlib.sha256(config.read_bytes()).hexdigest()


def test_repo_control_git_commands_ignore_host_config_and_repo_injection(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    external_hooks = tmp_path / "external-hooks"
    external_hooks.mkdir()
    (external_hooks / "host-only").write_text("do not read\n", encoding="utf-8")
    global_config = tmp_path / "global.gitconfig"
    global_config.write_text(
        f"[core]\n  hooksPath = {external_hooks}\n",
        encoding="utf-8",
    )
    external_git = tmp_path / "external-git"
    external_git.mkdir()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(external_hooks))
    monkeypatch.setenv("GIT_DIR", str(external_git))

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is True
    assert "host-only" not in snapshot["hooks"]


def test_repo_control_git_commands_receive_only_minimal_environment(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-cross")
    monkeypatch.setenv("PROJECT_SECRET", "must-not-cross")
    monkeypatch.setenv("GIT_TRACE", "1")
    monkeypatch.setenv("DYLD_INSERT_LIBRARIES", "/tmp/must-not-load.dylib")
    observed: list[dict[str, str]] = []
    real_run = e2e_env.subprocess.run

    def capture_run(*args, **kwargs):
        observed.append(dict(kwargs["env"]))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(e2e_env.subprocess, "run", capture_run)

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is True
    assert observed
    for env in observed:
        for forbidden in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "PROJECT_SECRET",
            "GIT_TRACE",
            "DYLD_INSERT_LIBRARIES",
        ):
            assert forbidden not in env
        assert env["GIT_CONFIG_COUNT"] == "0"
        assert env["GIT_CONFIG_NOSYSTEM"] == "1"
        assert "PYTHONPATH" not in env
        assert Path(env["HOME"]) != Path.home()


def test_freeze_git_commands_receive_only_minimal_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross")
    monkeypatch.setenv("PROJECT_SECRET", "must-not-cross")
    monkeypatch.setenv("GIT_TRACE", "1")
    observed: list[dict[str, str]] = []
    real_run = sequence.subprocess.run

    def capture_run(*args, **kwargs):
        observed.append(dict(kwargs["env"]))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(sequence.subprocess, "run", capture_run)

    digest = sequence._git_blob_hash(ROOT, "HEAD", "AGENTS.md")

    assert digest is not None
    assert observed
    for env in observed:
        assert "OPENAI_API_KEY" not in env
        assert "PROJECT_SECRET" not in env
        assert "GIT_TRACE" not in env
        assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"
        assert "PYTHONPATH" not in env
        assert Path(env["HOME"]) != Path.home()


def test_deterministic_hook_receives_no_host_credentials_or_python_plugins(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / "hook.py"
    (tmp_path / "hook_helper.py").write_text("VALUE = 'loaded'\n", encoding="utf-8")
    script.write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).parent))\n"
        "from hook_helper import VALUE\n"
        "assert VALUE == 'loaded'\n"
        "Path(sys.argv[1], 'hook-env.json').write_text(json.dumps(dict(os.environ)))\n",
        encoding="utf-8",
    )
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PROJECT_SECRET"):
        monkeypatch.setenv(key, "must-not-cross")
    monkeypatch.setenv("PYTHONPATH", "/tmp/host-pythonpath")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--capture=no")

    result = sequence._run_repo_script(script, repo)

    assert result.returncode == 0, result.stderr
    env = json.loads((repo / "hook-env.json").read_text(encoding="utf-8"))
    for forbidden in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "PROJECT_SECRET",
        "PYTEST_ADDOPTS",
    ):
        assert forbidden not in env
    assert env["PYTHONPATH"] == str(repo.resolve())
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert Path(env["HOME"]) != Path.home()
    assert not (tmp_path / "__pycache__").exists()


def test_deterministic_hook_ignores_repo_sitecustomize(monkeypatch, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = repo / "sitecustomize-loaded"
    (repo / "sitecustomize.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('loaded')\n",
        encoding="utf-8",
    )
    script = tmp_path / "hook.py"
    script.write_text("# deterministic no-op\n", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(repo))

    result = sequence._run_repo_script(script, repo)

    assert result.returncode == 0
    assert not marker.exists()


def test_deterministic_pytest_receives_exact_repo_pythonpath_and_no_host_credentials(
    monkeypatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    check = tmp_path / "test_env.py"
    check.write_text(
        "import os\n"
        f"EXPECTED = {str(repo.resolve())!r}\n"
        "def test_environment_is_isolated():\n"
        "    assert os.environ['PYTHONPATH'] == EXPECTED\n"
        "    assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'\n"
        "    assert os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'\n"
        "    assert 'OPENAI_API_KEY' not in os.environ\n"
        "    assert 'PROJECT_SECRET' not in os.environ\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross")
    monkeypatch.setenv("PROJECT_SECRET", "must-not-cross")
    monkeypatch.setenv("PYTHONPATH", "/tmp/host-pythonpath")

    result = sequence._run_check_files(repo, [check])

    assert result["passed"] == 1
    assert result["total"] == 1
    assert set(result["evidence"][0]) == {
        "check_id",
        "check_sha256",
        "passed",
        "returncode",
        "output_sha256",
    }
    assert not (tmp_path / "__pycache__").exists()


def test_seed_builder_receives_minimal_environment(monkeypatch, tmp_path) -> None:
    root = tmp_path / "root"
    builder = root / "experiments/seeds/example/build-seed.py"
    builder.parent.mkdir(parents=True)
    (builder.parent / "seed_helper.py").write_text("VALUE = 'loaded'\n", encoding="utf-8")
    builder.write_text(
        "import argparse, json, os, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).parent))\n"
        "from seed_helper import VALUE\n"
        "assert VALUE == 'loaded'\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--out', required=True)\n"
        "out = Path(parser.parse_args().out)\n"
        "out.mkdir(parents=True)\n"
        "(out / 'seed-env.json').write_text(json.dumps(dict(os.environ)))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross")
    monkeypatch.setenv("PROJECT_SECRET", "must-not-cross")
    destination = tmp_path / "cell/repo"

    e2e_env.build_seed_repo("example", destination, root)

    env = json.loads((destination / "seed-env.json").read_text(encoding="utf-8"))
    assert "OPENAI_API_KEY" not in env
    assert "PROJECT_SECRET" not in env
    assert env["PYTHONPATH"] == str(root.resolve())
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert not (builder.parent / "__pycache__").exists()


def test_bug_injector_receives_minimal_environment(monkeypatch, tmp_path) -> None:
    experiment = tmp_path / "experiment"
    injector = experiment / "bugs/example/inject.py"
    injector.parent.mkdir(parents=True)
    (injector.parent / "inject_helper.py").write_text("VALUE = 'loaded'\n", encoding="utf-8")
    injector.write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).parent))\n"
        "from inject_helper import VALUE\n"
        "assert VALUE == 'loaded'\n"
        "Path(sys.argv[1], 'inject-env.json').write_text(json.dumps(dict(os.environ)))\n",
        encoding="utf-8",
    )

    def fake_build_seed(_seed: str, destination: Path, _root: Path) -> Path:
        destination.mkdir(parents=True)
        return destination

    monkeypatch.setattr(e2e_env, "build_seed_repo", fake_build_seed)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-cross")
    monkeypatch.setenv("PROJECT_SECRET", "must-not-cross")
    fixture = type("FixtureStub", (), {
        "raw": {"scenario": {"seed": "example", "bug_id": "example"}},
    })()

    repo = e2e_env.prepare_e2e_workdir(fixture, str(tmp_path / "cell"), experiment)

    env = json.loads((repo / "inject-env.json").read_text(encoding="utf-8"))
    assert "ANTHROPIC_API_KEY" not in env
    assert "PROJECT_SECRET" not in env
    assert env["PYTHONPATH"] == str(Path.cwd().resolve())
    assert not (injector.parent / "__pycache__").exists()


@pytest.mark.parametrize(
    "relative,content",
    [
        ("config.worktree", "[include]\n  path = /tmp/outside.gitconfig\n"),
        ("commondir", "../../outside-git\n"),
        ("objects/info/alternates", "/tmp/outside-objects\n"),
        ("objects/info/http-alternates", "https://example.invalid/objects\n"),
    ],
)
def test_repo_control_rejects_extended_git_control_before_running_git(
    monkeypatch,
    tmp_path,
    relative,
    content,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    if relative == "config.worktree":
        subprocess.run(
            ["git", "config", "extensions.worktreeConfig", "true"],
            cwd=repo,
            check=True,
        )
    control = repo / ".git" / relative
    control.parent.mkdir(parents=True, exist_ok=True)
    control.write_text(content, encoding="utf-8")

    def unexpected_git(*_args, **_kwargs):
        raise AssertionError("扩展 Git 控制面必须在任何 Git 子进程前被拒绝")

    monkeypatch.setattr(e2e_env, "_git_output", unexpected_git)
    monkeypatch.setattr(e2e_env.subprocess, "run", unexpected_git)

    snapshot = sequence.repo_control_snapshot(repo)

    assert snapshot["safe"] is False
    assert relative in snapshot["unsafe_control_paths"]


def test_truncated_preflight_cache_is_rebuilt_atomically(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)
    run_root = tmp_path / "runs"
    cache = run_root / "preflight/lt-checkpoint.json"
    cache.parent.mkdir(parents=True)
    cache.write_text('{"checkpoint_fingerprint":', encoding="utf-8")

    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=run_root,
        checkpoint_path=tmp_path / "results.partial.jsonl",
        harness_resolver=lambda _name: object(),
    )

    assert len(payload["pairs"]) == 1
    rebuilt = json.loads(cache.read_text(encoding="utf-8"))
    assert rebuilt["result"] == {"ok": True}
    assert not list(cache.parent.glob(f".{cache.name}.*.tmp"))


def test_fixture_invalid_preflight_is_persisted_in_the_checkpoint(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)
    monkeypatch.setattr(
        sequence,
        "preflight_fixture",
        lambda *_args: {"ok": False, "state": "fixture-invalid", "reason": "golden failed"},
    )
    checkpoint = tmp_path / "results.partial.jsonl"

    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=checkpoint,
        harness_resolver=lambda _name: object(),
    )

    assert payload["invalid"][0]["state"] == "fixture-invalid"
    events = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    invalid = next(event for event in events if event.get("phase") == "fixture-invalid")
    assert invalid["fixture_id"] == "lt-checkpoint"
    assert invalid["preflight"]["reason"] == "golden failed"


def test_checkpoint_recovers_truncated_tail_and_preserves_retry_history(
    monkeypatch,
    tmp_path,
) -> None:
    _stub_sequence(monkeypatch)
    attempts = 0

    def flaky_pair(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            kwargs["phase_callback"]({
                "phase": "a",
                "status": "retryable-error",
                "metrics": {"cost_usd": {"value": 0.2, "tag": "soft"}},
            })
            raise sequence.RetryableSequenceError("temporary")
        return _structurally_valid_pair()

    monkeypatch.setattr(sequence, "run_pair", flaky_pair)
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [_fixture()],
        "k": 1,
        "experiment_dir": tmp_path / "experiment",
        "root": ROOT,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }
    first = sequence.run_sequence(**kwargs)
    assert len(first["errors"]) == 1
    with checkpoint.open("a", encoding="utf-8") as handle:
        handle.write('{"phase":"truncated"')

    second = sequence.run_sequence(**kwargs)

    assert attempts == 2
    assert len(second["pairs"]) == 1
    assert second["errors"] == []
    assert second["aggregate"]["integrity"]["ok"] is True
    assert second["aggregate"]["operational_errors"] == {
        "attempts": 1,
        "resolved": 1,
        "unresolved": 0,
    }
    assert second["operational_errors"][0]["resolved"] is True
    assert checkpoint.read_text(encoding="utf-8").endswith("\n")


def test_checkpoint_rejects_resume_when_custom_asset_or_seed_sibling_changes(
    monkeypatch,
    tmp_path,
) -> None:
    _stub_sequence(monkeypatch)
    root = tmp_path / "root"
    for skill in ("cs-feat", "cs-keep"):
        path = root / f"plugins/codestable/skills/{skill}/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"# {skill}\n", encoding="utf-8")
    seed = root / "experiments/seeds/dispatchboard-learning"
    seed.mkdir(parents=True)
    (seed / "build-seed.py").write_text("# builder\n", encoding="utf-8")
    sibling = seed / "template.txt"
    sibling.write_text("v1\n", encoding="utf-8")
    experiment = tmp_path / "experiment"
    custom = experiment / "custom/oracle.py"
    custom.parent.mkdir(parents=True)
    custom.write_text("# v1\n", encoding="utf-8")
    fixture = _fixture()
    fixture.raw["scenario"]["a"]["checks"] = ["custom/oracle.py"]
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [fixture],
        "k": 1,
        "experiment_dir": experiment,
        "root": root,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }
    sequence.run_sequence(**kwargs)

    custom.write_text("# v2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint.*不匹配"):
        sequence.run_sequence(**kwargs)

    custom.write_text("# v1\n", encoding="utf-8")
    sibling.write_text("v2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint.*不匹配"):
        sequence.run_sequence(**kwargs)


def test_real_campaign_rejects_prepared_freeze_before_reading_models(tmp_path) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    (experiment / "freeze.json").write_text(
        json.dumps({"state": "prepared-awaiting-commit", "source_commit": "pending"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="state 必须为 frozen"):
        sequence.validate_freeze_manifest(
            experiment_dir=experiment,
            root=tmp_path,
            config=_config(),
            fixtures=[_fixture()],
            k=1,
            targets=_config().model_targets,
        )


def _passed_probe_attestation(targets, source_commit: str) -> dict:
    return {
        "status": "passed",
        "source_commit": source_commit,
        "targets": [
            {
                "id": target.id,
                "family": target.family,
                "harness": target.harness,
                "model": target.model,
                "cell_write": True,
                "host_read_blocked": True,
                "sibling_read_blocked": True,
                "host_write_blocked": True,
                "host_config_unchanged": True,
                "runtime_removed": True,
            }
            for target in targets
        ],
    }


def test_probe_attestation_requires_exact_targets_source_and_all_oracles() -> None:
    targets = _config().model_targets
    source_commit = "a" * 40
    manifest = {
        "model_target_probe": _passed_probe_attestation(targets, source_commit),
    }

    sequence._validate_probe_attestation(manifest, targets, source_commit)

    wrong_source = json.loads(json.dumps(manifest))
    wrong_source["model_target_probe"]["source_commit"] = "b" * 40
    with pytest.raises(ValueError, match="source_commit"):
        sequence._validate_probe_attestation(wrong_source, targets, source_commit)

    missing = json.loads(json.dumps(manifest))
    missing["model_target_probe"]["targets"] = []
    with pytest.raises(ValueError, match="targets 与 config"):
        sequence._validate_probe_attestation(missing, targets, source_commit)

    failed = json.loads(json.dumps(manifest))
    failed["model_target_probe"]["targets"][0]["sibling_read_blocked"] = False
    with pytest.raises(ValueError, match="oracle"):
        sequence._validate_probe_attestation(failed, targets, source_commit)

    duplicate = json.loads(json.dumps(manifest))
    duplicate["model_target_probe"]["targets"].append(
        duplicate["model_target_probe"]["targets"][0]
    )
    with pytest.raises(ValueError, match="targets 与 config"):
        sequence._validate_probe_attestation(duplicate, targets, source_commit)


@pytest.mark.parametrize(
    ("scope", "field"),
    [
        ("probe", "prompt"),
        ("target", "output"),
        ("target", "path"),
        ("target", "secret"),
        ("target", "session_id"),
        ("target", "extra_oracle"),
    ],
)
def test_probe_attestation_rejects_unregistered_fields(scope: str, field: str) -> None:
    targets = _config().model_targets
    source_commit = "a" * 40
    manifest = {
        "model_target_probe": _passed_probe_attestation(targets, source_commit),
    }
    if scope == "probe":
        manifest["model_target_probe"][field] = "must-not-persist"
    else:
        manifest["model_target_probe"]["targets"][0][field] = "must-not-persist"

    with pytest.raises(ValueError, match="字段"):
        sequence._validate_probe_attestation(manifest, targets, source_commit)


def test_different_result_paths_have_independent_sequence_run_roots(tmp_path) -> None:
    first = runner_mod._sequence_run_root(tmp_path / "calibration.json")
    second = runner_mod._sequence_run_root(tmp_path / "final.json")

    assert first != second
    assert first.parent == second.parent == tmp_path / "runs"


def test_same_result_path_uses_a_nonblocking_process_lock(tmp_path) -> None:
    out_path = tmp_path / "calibration.json"

    with runner_mod._sequence_output_lock(out_path):
        with pytest.raises(runner_mod.SequenceOutputBusyError, match="同一 --out"):
            with runner_mod._sequence_output_lock(out_path):
                pass

    with runner_mod._sequence_output_lock(out_path):
        pass


def test_fresh_runner_clears_checkpoint_preflight_and_cell_state(
    monkeypatch,
    tmp_path,
) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    out_path = tmp_path / "calibration.json"
    checkpoint = out_path.parent / f"{out_path.name}.partial.jsonl"
    run_root = runner_mod._sequence_run_root(out_path)
    stale = run_root / "preflight/stale.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")
    checkpoint.write_text('{"phase":"header"}\n', encoding="utf-8")
    config = _config()
    config.variants = ["baseline"]
    config.scorers = ["learning_transfer"]
    targets = config.model_targets

    monkeypatch.setattr(runner_mod, "load_config", lambda _path: config)
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [_fixture()])
    monkeypatch.setattr(runner_mod, "select_execution_targets", lambda *_args: targets)
    monkeypatch.setattr(runner_mod, "repo_root", lambda: ROOT)
    monkeypatch.setattr(sequence, "dry_run_sequence", lambda *_args: {
        "est_total_usd": 0.1,
        "budget_usd": 50.0,
        "invocation_count": 4,
        "hook_runs": 0,
    })
    monkeypatch.setattr(sequence, "validate_freeze_manifest", lambda **_kwargs: {"ok": True})

    def run_sequence(**kwargs):
        assert kwargs["run_root"] == run_root
        assert not stale.exists()
        assert not checkpoint.exists()
        return {"pairs": [], "errors": [], "invalid": []}

    monkeypatch.setattr(sequence, "run_sequence", run_sequence)

    exit_code = runner_mod.main([
        "--experiment", str(experiment),
        "--fresh",
        "--out", str(out_path),
    ])

    assert exit_code == 0
    assert not run_root.exists()


def test_fresh_runner_refuses_to_erase_paid_invocation_history(
    monkeypatch,
    tmp_path,
) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    out_path = tmp_path / "calibration.json"
    checkpoint = out_path.parent / f"{out_path.name}.partial.jsonl"
    checkpoint.write_text(
        json.dumps({
            "phase": "a",
            "status": "retryable-error",
            "metrics": {"cost_usd": {"value": 0.1, "tag": "soft"}},
        }) + '\n{"phase":"truncated"',
        encoding="utf-8",
    )
    config = _config()
    config.variants = ["baseline"]
    config.scorers = ["learning_transfer"]
    monkeypatch.setattr(runner_mod, "load_config", lambda _path: config)
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [_fixture()])
    monkeypatch.setattr(
        runner_mod,
        "select_execution_targets",
        lambda *_args: config.model_targets,
    )
    monkeypatch.setattr(runner_mod, "repo_root", lambda: ROOT)
    monkeypatch.setattr(sequence, "dry_run_sequence", lambda *_args: {
        "est_total_usd": 0.1,
        "budget_usd": 50.0,
        "invocation_count": 4,
        "hook_runs": 0,
    })
    monkeypatch.setattr(sequence, "validate_freeze_manifest", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(
        sequence,
        "run_sequence",
        lambda **_kwargs: pytest.fail("paid history must block before sequence execution"),
    )

    exit_code = runner_mod.main([
        "--experiment", str(experiment),
        "--fresh",
        "--out", str(out_path),
    ])

    assert exit_code == 2
    assert checkpoint.exists()


@pytest.mark.parametrize("fresh", [False, True])
def test_runner_refuses_to_overwrite_terminal_sequence_output(
    monkeypatch,
    tmp_path,
    fresh,
) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    out_path = tmp_path / "final.json"
    original = '{"aggregate":{"cost":{"invocation_count":240}}}\n'
    out_path.write_text(original, encoding="utf-8")
    config = _config()
    config.variants = ["baseline"]
    config.scorers = ["learning_transfer"]
    monkeypatch.setattr(runner_mod, "load_config", lambda _path: config)
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [_fixture()])
    monkeypatch.setattr(
        runner_mod,
        "select_execution_targets",
        lambda *_args: config.model_targets,
    )
    monkeypatch.setattr(runner_mod, "repo_root", lambda: ROOT)
    monkeypatch.setattr(sequence, "dry_run_sequence", lambda *_args: {
        "est_total_usd": 0.1,
        "budget_usd": 50.0,
        "invocation_count": 4,
        "hook_runs": 0,
    })
    monkeypatch.setattr(sequence, "validate_freeze_manifest", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(
        sequence,
        "run_sequence",
        lambda **_kwargs: pytest.fail("terminal output must block before sequence execution"),
    )
    args = ["--experiment", str(experiment), "--out", str(out_path)]
    if fresh:
        args.append("--fresh")

    exit_code = runner_mod.main(args)

    assert exit_code == 2
    assert out_path.read_text(encoding="utf-8") == original


def test_learning_transfer_dry_run_refuses_to_overwrite_existing_output(
    monkeypatch,
    tmp_path,
) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    out_path = tmp_path / "final.json"
    original = '{"aggregate":{"cost":{"invocation_count":240}}}\n'
    out_path.write_text(original, encoding="utf-8")
    config = _config()
    config.variants = ["baseline"]
    config.scorers = ["learning_transfer"]
    monkeypatch.setattr(runner_mod, "load_config", lambda _path: config)
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [_fixture()])
    monkeypatch.setattr(
        runner_mod,
        "select_execution_targets",
        lambda *_args: config.model_targets,
    )
    monkeypatch.setattr(sequence, "dry_run_sequence", lambda *_args: {
        "est_total_usd": 0.1,
        "budget_usd": 50.0,
        "invocation_count": 4,
        "hook_runs": 0,
    })

    exit_code = runner_mod.main([
        "--experiment", str(experiment),
        "--dry-run",
        "--out", str(out_path),
    ])

    assert exit_code == 2
    assert out_path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "event",
    [
        {"phase": "error", "state": "pipeline-error", "status": "pipeline-error"},
        {"phase": "score", "status": "pipeline-failed", "pair": {"state": "pipeline-failed"}},
        {
            "phase": "fixture-invalid",
            "status": "fixture-invalid",
            "preflight": {"ok": False, "state": "fixture-invalid"},
        },
    ],
)
def test_fresh_runner_refuses_to_erase_irreversible_sequence_evidence(
    monkeypatch,
    tmp_path,
    event,
) -> None:
    experiment = tmp_path / "experiment"
    experiment.mkdir()
    out_path = tmp_path / "calibration.json"
    checkpoint = runner_mod._sequence_checkpoint_path(out_path)
    checkpoint.write_text(json.dumps(event) + "\n", encoding="utf-8")
    config = _config()
    config.variants = ["baseline"]
    config.scorers = ["learning_transfer"]
    monkeypatch.setattr(runner_mod, "load_config", lambda _path: config)
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [_fixture()])
    monkeypatch.setattr(
        runner_mod,
        "select_execution_targets",
        lambda *_args: config.model_targets,
    )
    monkeypatch.setattr(runner_mod, "repo_root", lambda: ROOT)
    monkeypatch.setattr(sequence, "dry_run_sequence", lambda *_args: {
        "est_total_usd": 0.1,
        "budget_usd": 50.0,
        "invocation_count": 4,
        "hook_runs": 0,
    })
    monkeypatch.setattr(sequence, "validate_freeze_manifest", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(
        sequence,
        "run_sequence",
        lambda **_kwargs: pytest.fail("irreversible evidence must block --fresh"),
    )

    exit_code = runner_mod.main([
        "--experiment", str(experiment),
        "--fresh",
        "--out", str(out_path),
    ])

    assert exit_code == 2
    assert checkpoint.exists()


def test_a_failure_diagnostics_bound_paths_and_name_git_control_changes(tmp_path) -> None:
    fixture = _fixture()
    fixture.raw["scenario"]["a"]["allowed_paths"] = ["post-a.txt"]
    seed = tmp_path / "seed"
    seed.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=seed, check=True)
    (seed / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=seed, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=seed, check=True)

    class GitMutatingHarness:
        name = "git-mutating"

        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, _prompt, model, workdir, timeout_s):
            assert timeout_s == 600
            self.calls += 1
            (workdir / "post-a.txt").write_text("done\n", encoding="utf-8")
            for index in range(21):
                (workdir / f"unexpected-{index:02}.txt").write_text("unexpected\n", encoding="utf-8")
            subprocess.run(["git", "config", "user.name", "changed"], cwd=workdir, check=True)
            return HarnessResult(
                output="晶化候选：example rule",
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    harness = GitMutatingHarness()
    pair = sequence.run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake-target",
            family="fake-family",
            harness=harness.name,
            model="mock-model",
        ),
        k_index=0,
        seed_repo=seed,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=tmp_path / "run",
        harness=harness,
    )

    assert harness.calls == 1
    assert pair["state"] == "pipeline-failed"
    assert pair["a_mutation_ok"] is False
    assert pair["a_repo_integrity_ok"] is False
    mutation = pair["a_diagnostics"]["mutation"]
    assert mutation["changed_path_count"] == 22
    assert mutation["unexpected_path_count"] == 21
    assert mutation["unexpected_paths"] == [
        f"unexpected-{index:02}.txt" for index in range(20)
    ]
    assert mutation["unexpected_paths_truncated"] is True
    assert mutation["repo_control_changes"] == ["local_config"]


def test_epic_preflight_rejects_seed_with_mismatched_approved_revision(tmp_path) -> None:
    fixture = _fixture()
    scenario = fixture.raw["scenario"]
    scenario["a"]["skill"] = "cs-epic"
    scenario["b"]["skill"] = "cs-epic"
    scenario["b"].update({
        "hidden_tests": ["hidden/result.py"],
        "regression_tests": ["regression/base.py"],
    })
    scenario["preflight"] = {
        "naive_hook": "preflight/naive.py",
        "golden_hook": "preflight/golden.py",
    }

    experiment = tmp_path / "experiment"
    for directory in ("hidden", "regression", "preflight"):
        (experiment / directory).mkdir(parents=True)
    (experiment / "preflight/naive.py").write_text("# no-op\n", encoding="utf-8")
    (experiment / "preflight/golden.py").write_text(
        "from pathlib import Path\nimport sys\n"
        "(Path(sys.argv[1]) / 'result.txt').write_text('ok\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (experiment / "hidden/result.py").write_text(
        "from pathlib import Path\ndef test_result(): assert Path('result.txt').exists()\n",
        encoding="utf-8",
    )
    (experiment / "regression/base.py").write_text(
        "def test_base(): assert True\n",
        encoding="utf-8",
    )

    seed = tmp_path / "seed"
    epic = seed / ".codestable/epics/example.md"
    cursor = seed / ".codestable/work/epic-example.md"
    epic.parent.mkdir(parents=True)
    cursor.parent.mkdir(parents=True)
    epic.write_text(
        "---\nstatus: active\nwork: ../work/epic-example.md\n---\n"
        "# Example\n\n## 子项契约\n\n- `ITEM-A`：first\n- `ITEM-B`：second\n",
        encoding="utf-8",
    )
    cursor.write_text(
        "---\nepic: ../epics/example.md\nphase: executing\n"
        "approved_revision: deadbeef\ncurrent_item: ITEM-A\n"
        "item_progression: continuous\nmilestone_commit: authorized\n"
        "remote_publish: final\n---\n\n## 子项进度\n\n- [ ] ITEM-A\n- [ ] ITEM-B\n",
        encoding="utf-8",
    )

    result = sequence.preflight_fixture(
        fixture,
        seed,
        experiment,
        tmp_path / "preflight-run",
    )

    assert result["ok"] is False
    assert result["state"] == "fixture-invalid"
    assert "approved_revision" in result["reason"]


def test_operational_exception_is_checkpointed_as_retryable_error(monkeypatch, tmp_path) -> None:
    _stub_sequence(monkeypatch)

    def fail_operationally(**_kwargs) -> dict:
        raise sequence.RetryableSequenceError("model transport timed out")

    monkeypatch.setattr(sequence, "run_pair", fail_operationally)
    checkpoint = tmp_path / "results.partial.jsonl"
    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=checkpoint,
        harness_resolver=lambda _name: object(),
    )

    assert payload["errors"][0]["state"] == "retryable-error"
    assert payload["operational_errors"][0]["resolved"] is False
    events = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    error_event = next(event for event in events if event.get("phase") == "error")
    assert error_event["status"] == "retryable-error"
    assert error_event["phase_key"] == "fake-target|lt-checkpoint|0|error"
    assert not (tmp_path / "runs/fake-target__lt-checkpoint__0").exists()


def test_non_retryable_pipeline_exception_is_checkpointed_and_not_retried(
    monkeypatch,
    tmp_path,
) -> None:
    _stub_sequence(monkeypatch)
    attempts = 0

    def fail_deterministically(**_kwargs) -> dict:
        nonlocal attempts
        attempts += 1
        raise ValueError("pipeline contract broken")

    monkeypatch.setattr(sequence, "run_pair", fail_deterministically)
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [_fixture()],
        "k": 1,
        "experiment_dir": tmp_path / "experiment",
        "root": ROOT,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }

    first = sequence.run_sequence(**kwargs)
    second = sequence.run_sequence(**kwargs)

    assert attempts == 1
    assert first["errors"][0]["state"] == "pipeline-error"
    assert second["errors"] == first["errors"]
    assert second["operational_errors"] == []
    assert second["aggregate"]["integrity"]["ok"] is False


def test_retryable_error_followed_by_pipeline_error_remains_unresolved(
    monkeypatch,
    tmp_path,
) -> None:
    _stub_sequence(monkeypatch)
    attempts = 0

    def fail_in_two_different_ways(**_kwargs) -> dict:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise sequence.RetryableSequenceError("transport timed out")
        raise ValueError("deterministic pipeline failure")

    monkeypatch.setattr(sequence, "run_pair", fail_in_two_different_ways)
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [_fixture()],
        "k": 1,
        "experiment_dir": tmp_path / "experiment",
        "root": ROOT,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }

    sequence.run_sequence(**kwargs)
    second = sequence.run_sequence(**kwargs)

    assert attempts == 2
    assert second["operational_errors"][0]["resolved"] is False
    assert second["aggregate"]["operational_errors"] == {
        "attempts": 1,
        "resolved": 0,
        "unresolved": 1,
    }


def test_preflight_hook_timeout_is_fast_fixture_invalid(monkeypatch, tmp_path) -> None:
    fixture = _fixture()
    scenario = fixture.raw["scenario"]
    scenario["b"].update({
        "hidden_tests": ["hidden/result.py"],
        "regression_tests": ["regression/base.py"],
    })
    scenario["preflight"] = {
        "naive_hook": "preflight/naive.py",
        "golden_hook": "preflight/golden.py",
    }
    experiment = tmp_path / "experiment"
    for directory in ("hidden", "regression", "preflight"):
        (experiment / directory).mkdir(parents=True)
    (experiment / "preflight/naive.py").write_text(
        "import time\ntime.sleep(1)\n",
        encoding="utf-8",
    )
    (experiment / "preflight/golden.py").write_text(
        "from pathlib import Path\nimport sys\n"
        "(Path(sys.argv[1]) / 'result.txt').write_text('ok\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (experiment / "hidden/result.py").write_text(
        "from pathlib import Path\ndef test_result(): assert Path('result.txt').exists()\n",
        encoding="utf-8",
    )
    (experiment / "regression/base.py").write_text(
        "def test_base(): assert True\n",
        encoding="utf-8",
    )
    seed = tmp_path / "seed"
    seed.mkdir()
    monkeypatch.setattr(sequence, "_DETERMINISTIC_TIMEOUT_S", 0.05, raising=False)

    started = time.monotonic()
    result = sequence.preflight_fixture(
        fixture,
        seed,
        experiment,
        tmp_path / "preflight-run",
    )

    assert time.monotonic() - started < 0.5
    assert result["ok"] is False
    assert result["state"] == "fixture-invalid"
    assert "timeout" in result["reason"]


def test_a_check_timeout_is_fast_pipeline_failure(monkeypatch, tmp_path) -> None:
    fixture = _fixture()
    fixture.raw["scenario"]["a"]["checks"] = ["checks/hang.py"]
    experiment = tmp_path / "experiment"
    (experiment / "checks").mkdir(parents=True)
    (experiment / "checks/hang.py").write_text(
        "import time\ndef test_hang(): time.sleep(1)\n",
        encoding="utf-8",
    )
    seed = tmp_path / "seed"
    seed.mkdir()

    class CandidateHarness:
        name = "candidate"

        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, _prompt, model, _workdir, timeout_s):
            assert timeout_s == 600
            self.calls += 1
            return HarnessResult(
                output="晶化候选：example rule",
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    monkeypatch.setattr(sequence, "_DETERMINISTIC_TIMEOUT_S", 0.05)
    harness = CandidateHarness()
    started = time.monotonic()
    pair = sequence.run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake-target",
            family="fake-family",
            harness=harness.name,
            model="mock-model",
        ),
        k_index=0,
        seed_repo=seed,
        experiment_dir=experiment,
        root=ROOT,
        run_root=tmp_path / "run",
        harness=harness,
    )

    assert time.monotonic() - started < 0.5
    assert harness.calls == 1
    assert pair["state"] == "pipeline-failed"
    assert pair["failure_reason"] == "A oracle failed"
    diagnostics = pair["a_diagnostics"]
    assert diagnostics["checks"]["timed_out"] == 1
    assert diagnostics["checks"]["evidence"][0]["check_id"] == "hang.py"
    assert diagnostics["checks"]["evidence"][0]["returncode"] == 124
    assert len(diagnostics["checks"]["evidence"][0]["output_sha256"]) == 64
    assert diagnostics["mutation"] == {
        "changed_path_count": 0,
        "unexpected_path_count": 0,
        "unexpected_paths": [],
        "unexpected_paths_truncated": False,
        "repo_control_changes": [],
    }


def test_between_tasks_hook_timeout_is_fast_and_symmetric(monkeypatch, tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    treatment = tmp_path / "treatment"
    control = tmp_path / "control"
    sequence.copy_repo(source, treatment)
    sequence.copy_repo(source, control)
    hook = tmp_path / "hang.py"
    hook.write_text("import time\ntime.sleep(1)\n", encoding="utf-8")
    monkeypatch.setattr(sequence, "_DETERMINISTIC_TIMEOUT_S", 0.05)

    started = time.monotonic()
    result = sequence.apply_between_tasks_hook(hook, treatment, control, [])

    assert time.monotonic() - started < 0.5
    assert result["ok"] is False
    assert result["runs"] == 2
    assert result["timed_out"] == 2


def test_harness_result_error_is_retryable_not_pipeline_failure(monkeypatch, tmp_path) -> None:
    def build_seed(_seed: str, destination: Path, _root: Path) -> Path:
        destination.mkdir(parents=True)
        return destination

    class ErrorHarness:
        name = "error-harness"

        def invoke(self, _prompt, model, _workdir, timeout_s):
            assert timeout_s == 600
            return HarnessResult(
                output="",
                model=model,
                harness=self.name,
                wall_ms=1,
                error="transport unavailable",
            )

    monkeypatch.setattr(sequence, "build_seed_repo", build_seed)
    monkeypatch.setattr(sequence, "preflight_fixture", lambda *_args: {"ok": True})
    payload = sequence.run_sequence(
        config=_config(),
        fixtures=[_fixture()],
        k=1,
        experiment_dir=tmp_path / "experiment",
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=tmp_path / "results.partial.jsonl",
        harness_resolver=lambda _name: ErrorHarness(),
    )

    assert payload["pairs"] == []
    assert payload["errors"][0]["state"] == "retryable-error"
    assert payload["errors"][0]["error"] == "RetryableSequenceError"


def test_b_rejects_index_mutation_while_control_business_diff_stays_valid(tmp_path) -> None:
    fixture = _fixture()
    scenario = fixture.raw["scenario"]
    scenario["a"]["allowed_paths"] = ["post-a.txt"]
    scenario["b"]["allowed_paths"] = ["result.txt"]
    scenario["expect"]["lesson_transition"] = "unchanged-observed"
    seed = tmp_path / "seed"
    seed.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=seed, check=True)
    (seed / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=seed, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=seed, check=True)

    class IndexMutatingHarness:
        name = "index-mutating"

        def invoke(self, prompt, model, workdir, timeout_s):
            assert timeout_s == 600
            if "complete task A" in prompt:
                (workdir / "post-a.txt").write_text("done\n", encoding="utf-8")
                output = "晶化候选：example rule"
            elif "请记录为 observed lesson" in prompt:
                lesson = workdir / ".codestable/lessons/2026-08-02-example.md"
                lesson.parent.mkdir(parents=True)
                lesson.write_text(
                    "---\nstatus: observed\nscope: example\ndate: 2026-08-02\n---\n"
                    "规则：example rule。\n适用 / 不适用：example scope。\n"
                    "证据：post-a.txt。\n候选归宿：project-doc\n",
                    encoding="utf-8",
                )
                output = "recorded"
            else:
                (workdir / "result.txt").write_text("done\n", encoding="utf-8")
                if (workdir / ".codestable/lessons/2026-08-02-example.md").exists():
                    subprocess.run(["git", "add", "result.txt"], cwd=workdir, check=True)
                output = "done"
            return HarnessResult(
                output=output,
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    pair = sequence.run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake-target",
            family="fake-family",
            harness=IndexMutatingHarness.name,
            model="mock-model",
        ),
        k_index=0,
        seed_repo=seed,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=tmp_path / "run",
        harness=IndexMutatingHarness(),
    )

    assert pair["treatment_repo_integrity_ok"] is False
    assert pair["treatment_mutation_ok"] is False
    assert pair["control_repo_integrity_ok"] is True
    assert pair["control_mutation_ok"] is True


def test_repo_control_allows_semantically_unchanged_index_stat_refresh(tmp_path) -> None:
    repo = tmp_path / "index-refresh"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    before = sequence.repo_control_snapshot(repo)
    raw_index_before = (repo / ".git/index").read_bytes()

    stat = tracked.stat()
    os.utime(tracked, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
    subprocess.run(["git", "update-index", "--refresh"], cwd=repo, check=True)

    assert (repo / ".git/index").read_bytes() != raw_index_before
    assert sequence.repo_control_unchanged(before, sequence.repo_control_snapshot(repo)) is True


@pytest.mark.parametrize("mutation", ["head", "index", "config", "hooks"])
def test_repo_control_snapshot_detects_every_protected_git_surface(tmp_path, mutation) -> None:
    repo = tmp_path / mutation
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    before = sequence.repo_control_snapshot(repo)

    if mutation == "head":
        (repo / "second.txt").write_text("second\n", encoding="utf-8")
        subprocess.run(["git", "add", "second.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)
    elif mutation == "index":
        tracked.write_text("staged\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    elif mutation == "config":
        subprocess.run(["git", "config", "user.name", "changed"], cwd=repo, check=True)
    else:
        hooks = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        hook_dir = Path(hooks) if Path(hooks).is_absolute() else repo / hooks
        (hook_dir / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    assert sequence.repo_control_snapshot(repo) != before


@pytest.mark.parametrize("changed_input", ["skill", "seed"])
def test_checkpoint_rejects_resume_when_frozen_file_changes(
    monkeypatch,
    tmp_path,
    changed_input,
) -> None:
    _stub_sequence(monkeypatch)
    root = tmp_path / "root"
    for skill in ("cs-feat", "cs-keep"):
        skill_path = root / f"plugins/codestable/skills/{skill}/SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(f"# {skill}\n", encoding="utf-8")
    seed_builder = root / "experiments/seeds/dispatchboard-learning/build-seed.py"
    seed_builder.parent.mkdir(parents=True)
    seed_builder.write_text("# frozen seed\n", encoding="utf-8")
    checkpoint = tmp_path / "results.partial.jsonl"
    kwargs = {
        "config": _config(),
        "fixtures": [_fixture()],
        "k": 1,
        "experiment_dir": tmp_path / "experiment",
        "root": root,
        "run_root": tmp_path / "runs",
        "checkpoint_path": checkpoint,
        "harness_resolver": lambda _name: object(),
    }
    sequence.run_sequence(**kwargs)

    changed = (
        root / "plugins/codestable/skills/cs-feat/SKILL.md"
        if changed_input == "skill"
        else seed_builder
    )
    changed.write_text(changed.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checkpoint.*不匹配"):
        sequence.run_sequence(**kwargs)
