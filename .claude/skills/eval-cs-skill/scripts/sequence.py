#!/usr/bin/env python3
"""learning-transfer sequence runner：在同源 repo 上执行 A、curation 与 paired B。"""

from __future__ import annotations

import json
import hashlib
import importlib.util
import inspect
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import metrics
import yaml
from _model import ExecutionTarget, Fixture, HarnessResult, MEASURED, SOFT, tagged
from buildprompt import build_curation_prompt, build_sequence_task_prompt
from config import ExperimentConfig, resolve_skill_path
from e2e_env import (
    build_seed_repo,
    changed_paths,
    copy_repo,
    isolated_subprocess_env,
    paths_match_allowlist,
    repo_control_unchanged,
    repo_control_snapshot,
    repo_manifest,
)
from fixtures import resolve_experiment_asset
from scorers.learning_transfer import (
    aggregate_pairs,
    lesson_status,
    transfer_verdict,
    validate_lesson_transition,
    validate_observed_lesson,
)


_CANDIDATE_MARKER = "晶化候选："
_PHASE_OUTPUT_TOKENS = {"a": 2_000, "curation": 1_000, "b-treatment": 2_000, "b-control": 2_000}
_CHECKPOINT_KIND = "sequence-checkpoint-header"
_CHECKPOINT_SCHEMA_VERSION = 2
_DETERMINISTIC_TIMEOUT_S = 60
_PRIMARY_METRIC = {
    "name": "overall_paired_hidden_pass_delta",
    "threshold": 0.25,
    "aggregation": "overall across both model families and four positive fixtures",
    "family_guard": "each family delta > 0",
}
_PIPELINE_MODULES = (
    "_model.py",
    "buildprompt.py",
    "config.py",
    "e2e_env.py",
    "fixtures.py",
    "metrics.py",
    "probe_targets.py",
    "runner.py",
    "sequence.py",
    "scorers/__init__.py",
    "scorers/base.py",
    "scorers/learning_transfer.py",
)
_EXPERIMENT_INPUTS = (
    "config.json",
    "freeze.json",
    "hypotheses.md",
    "_asset_mutations.py",
    "fixtures",
    "checks",
    "hidden",
    "regression",
    "preflight",
    "hooks",
    "bugs",
    "variants",
)
_PROBE_ORACLES = (
    "cell_write",
    "host_read_blocked",
    "sibling_read_blocked",
    "host_write_blocked",
    "host_config_unchanged",
    "runtime_removed",
)
_PROBE_FIELDS = frozenset({"status", "source_commit", "targets"})
_PROBE_TARGET_FIELDS = frozenset({"id", "family", "harness", "model", *_PROBE_ORACLES})


class RetryableSequenceError(RuntimeError):
    """模型、adapter 或外部进程故障；保留 checkpoint 后可重试。"""

    def __init__(self, message: str, *, invocation_id: str | None = None) -> None:
        super().__init__(message)
        self.invocation_id = invocation_id


def _contained_child(base: Path, name: str) -> Path:
    path = base / name
    resolved = path.resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"运行路径越过 run_root: {name!r}") from exc
    return path


def phase_key(target_id: str, fixture_id: str, k_index: int, phase: str) -> str:
    """一个 sequence phase 的稳定 checkpoint key。"""
    return f"{target_id}|{fixture_id}|{k_index}|{phase}"


def append_checkpoint(path: Path, event: dict) -> None:
    """追加一个 sequence phase 事件，并立即刷新到磁盘。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _repair_checkpoint_tail(path: Path) -> None:
    """保留完整 JSONL 事件；崩溃留下的最后半行可安全丢弃。"""
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if not text or text.endswith("\n"):
        return
    prefix, _, tail = text.rpartition("\n")
    try:
        json.loads(tail)
    except json.JSONDecodeError:
        _atomic_write_text(path, f"{prefix}\n" if prefix else "")
    else:
        _atomic_write_text(path, text + "\n")


def _checkpoint_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"checkpoint 第 {line_number} 行不是有效 JSON") from exc
        if not isinstance(event, dict):
            raise ValueError(f"checkpoint 第 {line_number} 行必须是 JSON object")
        events.append(event)
    return events


def _checkpoint_record(event: dict[str, Any], *, error: str) -> dict[str, Any]:
    return {
        "target_id": event.get("target_id"),
        "fixture_id": event.get("fixture_id"),
        "k_index": event.get("k_index"),
        "state": "retryable-error",
        "error": error,
    }


def _reduce_checkpoint(path: Path) -> dict[str, Any]:
    """Reduce the append-only journal once for resume, cost, and fresh eligibility."""
    _repair_checkpoint_tail(path)
    events = _checkpoint_events(path)
    invocations: dict[str, dict[str, Any]] = {}
    legacy_invocations: list[dict[str, Any]] = []
    generic_retryable: list[dict[str, Any]] = []
    pipeline_errors: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    fixture_invalid: list[dict[str, Any]] = []

    for event_index, event in enumerate(events):
        phase = event.get("phase")
        status = event.get("status")
        invocation_id = event.get("invocation_id")
        if phase in _PHASE_OUTPUT_TOKENS:
            if invocation_id is None:
                if isinstance(event.get("metrics"), dict):
                    legacy_invocations.append({**event, "journal_index": event_index})
            elif not isinstance(invocation_id, str) or not invocation_id:
                raise ValueError("checkpoint invocation_id 必须是非空字符串")
            elif status == "invocation-started":
                if invocation_id in invocations:
                    raise ValueError("checkpoint invocation_id 重复 start")
                if not isinstance(event.get("metrics"), dict):
                    raise ValueError("checkpoint invocation start 缺 fallback metrics")
                invocations[invocation_id] = dict(event)
            elif status in {"invocation-complete", "retryable-error"}:
                started = invocations.get(invocation_id)
                if started is None or started.get("status") != "invocation-started":
                    raise ValueError("checkpoint invocation terminal 缺 durable start")
                identity_fields = ("target_id", "fixture_id", "k_index", "phase")
                if any(event.get(key) != started.get(key) for key in identity_fields):
                    raise ValueError("checkpoint invocation terminal identity 不匹配")
                metrics_value = event.get("metrics")
                if metrics_value is not None and not isinstance(metrics_value, dict):
                    raise ValueError("checkpoint invocation terminal metrics 无效")
                invocations[invocation_id] = {
                    **started,
                    **event,
                    "metrics": {**started["metrics"], **(metrics_value or {})},
                }
            elif invocation_id is not None:
                raise ValueError(f"checkpoint invocation status 无效: {status!r}")

        if phase == "score" and isinstance(event.get("pair"), dict):
            completed_pairs.append(event["pair"])
        elif phase == "error" and event.get("state") == "retryable-error":
            generic_retryable.append(event)
        elif phase == "error" and event.get("state") == "pipeline-error":
            pipeline_errors.append({
                key: event.get(key)
                for key in ("target_id", "fixture_id", "k_index", "state", "error")
            })
        elif phase == "fixture-invalid" and isinstance(event.get("preflight"), dict):
            fixture_invalid.append({
                "fixture_id": event.get("fixture_id"),
                "state": "fixture-invalid",
                "preflight": event["preflight"],
            })

    operational_errors: list[dict[str, Any]] = []
    represented_ids: set[str] = set()
    for invocation_id, event in invocations.items():
        status = event.get("status")
        if status == "invocation-started":
            represented_ids.add(invocation_id)
            operational_errors.append(_checkpoint_record(event, error="InterruptedInvocation"))
        elif status == "retryable-error":
            represented_ids.add(invocation_id)
            operational_errors.append(_checkpoint_record(
                event,
                error=str(event.get("error_type") or "HarnessResultError"),
            ))
    for event in generic_retryable:
        invocation_id = event.get("invocation_id")
        if isinstance(invocation_id, str) and invocation_id in represented_ids:
            continue
        operational_errors.append(_checkpoint_record(
            event,
            error=str(event.get("error") or "RetryableSequenceError"),
        ))

    return {
        "events": events,
        "invocations": [*invocations.values(), *legacy_invocations],
        "operational_errors": operational_errors,
        "pipeline_errors": pipeline_errors,
        "completed_pairs": completed_pairs,
        "fixture_invalid": fixture_invalid,
        "fresh_eligible": all(event.get("phase") == "header" for event in events),
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _file_hash(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"checkpoint 输入不存在或不是普通文件: {path}")
    return _sha256_bytes(path.read_bytes())


def _seed_input_hash(root: Path, seed: str) -> str:
    seed_dir = root / "experiments" / "seeds" / seed
    builder = seed_dir / "build-seed.py"
    if builder.is_file() and not builder.is_symlink():
        return _canonical_hash(_input_tree_hashes(seed_dir, (".",)))
    try:
        source = inspect.getsource(build_seed_repo)
    except (OSError, TypeError):
        code = getattr(build_seed_repo, "__code__", None)
        source = repr((
            getattr(build_seed_repo, "__module__", None),
            getattr(build_seed_repo, "__qualname__", None),
            getattr(code, "co_code", b"").hex(),
            getattr(code, "co_consts", ()),
        ))
    return _canonical_hash({"seed": seed, "injected_builder": source})


def _input_tree_hashes(root: Path, entries: tuple[str, ...]) -> dict[str, str]:
    """Hash exact input bytes while excluding generated result directories."""
    hashes: dict[str, str] = {}
    for entry in entries:
        path = root / entry
        if path.is_symlink():
            raise ValueError(f"checkpoint 输入不得为 symlink: {path}")
        if path.is_file():
            hashes[path.relative_to(root).as_posix()] = _file_hash(path)
            continue
        if not path.is_dir():
            continue
        for child in sorted(path.rglob("*")):
            if child.is_symlink():
                raise ValueError(f"checkpoint 输入不得为 symlink: {child}")
            if child.is_file():
                hashes[child.relative_to(root).as_posix()] = _file_hash(child)
    return hashes


def _pipeline_hashes() -> dict[str, str]:
    scripts = Path(__file__).resolve().parent
    paths = [scripts / relative for relative in _PIPELINE_MODULES]
    paths.extend(sorted((scripts / "harness").glob("*.py")))
    return {
        path.relative_to(scripts).as_posix(): _file_hash(path)
        for path in paths
    }


def _fixture_asset_references(fixtures: list[Fixture]) -> set[str]:
    references: set[str] = set()
    for fixture in fixtures:
        scenario = (fixture.raw or {}).get("scenario") or {}
        a_spec = scenario.get("a") or {}
        b_spec = scenario.get("b") or {}
        preflight = scenario.get("preflight") or {}
        between = scenario.get("between_tasks") or {}
        references.update(str(path) for path in a_spec.get("checks", []) if path)
        references.update(str(path) for path in b_spec.get("hidden_tests", []) if path)
        references.update(str(path) for path in b_spec.get("regression_tests", []) if path)
        references.update(
            str(preflight[key]) for key in ("naive_hook", "golden_hook") if preflight.get(key)
        )
        if between.get("hook"):
            references.add(str(between["hook"]))
    return references


def _experiment_asset_hashes(experiment_dir: Path, fixtures: list[Fixture]) -> dict[str, str]:
    hashes = _input_tree_hashes(experiment_dir, _EXPERIMENT_INPUTS)
    for relative in sorted(_fixture_asset_references(fixtures)):
        path = experiment_dir / relative
        if path.is_symlink():
            raise ValueError(f"checkpoint 输入不得为 symlink: {path}")
        hashes.setdefault(relative, _file_hash(path) if path.is_file() else "missing")
    return hashes


def _root_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"冻结输入不在仓库内: {path}") from exc


def _current_freeze_inputs(
    experiment_dir: Path,
    fixtures: list[Fixture],
) -> dict[str, str]:
    inputs = _experiment_asset_hashes(experiment_dir, fixtures)
    inputs.pop("freeze.json", None)
    return inputs


def _current_freeze_external_inputs(
    root: Path,
    fixtures: list[Fixture],
) -> dict[str, str]:
    external: dict[str, str] = {}
    scripts = Path(__file__).resolve().parent
    for relative, digest in _pipeline_hashes().items():
        external[_root_relative(scripts / relative, root)] = digest
    skill_names = {
        "cs-keep",
        *(
            str((scenario.get(phase) or {}).get("skill"))
            for fixture in fixtures
            for scenario in [(fixture.raw or {}).get("scenario") or {}]
            for phase in ("a", "b")
            if (scenario.get(phase) or {}).get("skill")
        ),
    }
    for skill in sorted(skill_names):
        path = resolve_skill_path(root, skill)
        external[_root_relative(path, root)] = _file_hash(path)
    seeds = {
        str(((fixture.raw or {}).get("scenario") or {}).get("seed"))
        for fixture in fixtures
    }
    for seed in sorted(seeds):
        seed_dir = root / "experiments" / "seeds" / seed
        for relative, digest in _input_tree_hashes(seed_dir, (".",)).items():
            external[_root_relative(seed_dir / relative, root)] = digest
    return dict(sorted(external.items()))


def _git_blob_hash(root: Path, revision: str, relative: str) -> str | None:
    result = _isolated_repo_git(root, "show", f"{revision}:{relative}")
    return _sha256_bytes(result.stdout) if result.returncode == 0 else None


def _isolated_repo_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Run provenance Git commands without host config, hooks, trace or credential environment."""
    with tempfile.TemporaryDirectory(prefix="cs-eval-freeze-git-", dir=root.parent) as tmp:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            env=isolated_subprocess_env(Path(tmp)),
            capture_output=True,
            check=False,
            timeout=20,
        )


def _freeze_run_mode(required: dict[str, Any], actual: dict[str, Any]) -> str:
    if actual == required:
        return "final"
    required_k = int(required.get("k", 0))
    actual_k = int(actual.get("k", 0))
    if not 0 < actual_k < required_k:
        raise ValueError("freeze.json required_scale 与本次执行矩阵不一致")
    expected = dict(required)
    expected["k"] = actual_k
    for field in ("pairs", "agent_invocations", "hook_runs"):
        total = int(required.get(field, -1))
        if required_k <= 0 or total < 0 or total % required_k:
            raise ValueError("freeze.json required_scale 不能等比例校准")
        expected[field] = total // required_k * actual_k
    if actual != expected:
        raise ValueError("校准必须保留完整 fixtures 与 model families，只缩小 k")
    return "calibration"


def _validate_freeze_metadata(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise ValueError("freeze.json schema_version 必须为 1")
    if manifest.get("hash_algorithm") != "sha256":
        raise ValueError("freeze.json hash_algorithm 必须为 sha256")
    if manifest.get("primary_metric") != _PRIMARY_METRIC:
        raise ValueError("freeze.json primary_metric 与预注册契约不一致")


def _validate_probe_attestation(
    manifest: dict[str, Any],
    targets: list[ExecutionTarget],
    source_commit: str,
) -> None:
    probe = manifest.get("model_target_probe")
    if not isinstance(probe, dict) or probe.get("status") != "passed":
        raise ValueError("freeze.json model_target_probe 必须先通过")
    if set(probe) != _PROBE_FIELDS:
        raise ValueError("model_target_probe 字段必须严格匹配 attestation schema")
    if probe.get("source_commit") != source_commit:
        raise ValueError("model_target_probe source_commit 不匹配")
    records = probe.get("targets")
    if not isinstance(records, list):
        raise ValueError("model_target_probe targets 必须是 list")
    expected = {
        (target.id, target.family, target.harness, target.model)
        for target in targets
    }
    actual: set[tuple[str, str, str, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("model_target_probe target 必须是 object")
        if set(record) != _PROBE_TARGET_FIELDS:
            raise ValueError("model_target_probe target 字段必须严格匹配 attestation schema")
        identity = tuple(record.get(key) for key in ("id", "family", "harness", "model"))
        if len(identity) != 4 or not all(isinstance(value, str) and value for value in identity):
            raise ValueError("model_target_probe target identity 无效")
        actual.add(identity)
        if any(record.get(oracle) is not True for oracle in _PROBE_ORACLES):
            raise ValueError("model_target_probe filesystem oracle 未全部通过")
    if len(actual) != len(records) or actual != expected:
        raise ValueError("model_target_probe targets 与 config 不一致")


def validate_freeze_manifest(
    *,
    experiment_dir: Path,
    root: Path,
    config: ExperimentConfig,
    fixtures: list[Fixture],
    k: int,
    targets: list[ExecutionTarget],
) -> dict[str, Any]:
    """真实模型前验证冻结声明、当前字节与已提交 provenance 三方一致。"""
    manifest_path = experiment_dir / "freeze.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("真实 learning-transfer 运行缺少普通文件 freeze.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("freeze.json 不是有效 JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("freeze.json 必须是 JSON object")
    if manifest.get("state") != "frozen":
        raise ValueError("freeze.json state 必须为 frozen；prepared/pending 禁止真实模型")
    _validate_freeze_metadata(manifest)
    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("freeze.json source_commit 必须是完整 40 位 commit SHA")
    _validate_probe_attestation(manifest, targets, source_commit)
    if (manifest.get("offline_preflight") or {}).get("status") != "passed":
        raise ValueError("freeze.json offline_preflight 必须先通过")

    current_inputs = _current_freeze_inputs(experiment_dir, fixtures)
    current_external = _current_freeze_external_inputs(root, fixtures)
    if any(digest == "missing" for digest in current_inputs.values()):
        raise ValueError("freeze.json 引用的实验资产存在缺失")
    if manifest.get("inputs") != current_inputs:
        raise ValueError("freeze.json inputs 与当前实验输入字节不一致")
    if manifest.get("external_inputs") != current_external:
        raise ValueError("freeze.json external_inputs 与当前 pipeline/skill/seed 字节不一致")
    if float(manifest.get("budget_usd", -1)) != float(config.budget_usd):
        raise ValueError("freeze.json budget_usd 与 config 不一致")

    positive = sum(
        ((fixture.raw or {}).get("scenario") or {}).get("class") == "positive"
        for fixture in fixtures
    )
    guards = sum(
        ((fixture.raw or {}).get("scenario") or {}).get("class") in {"unrelated", "stale"}
        for fixture in fixtures
    )
    pairs = len(targets) * len(fixtures) * k
    hook_runs = len(targets) * k * 2 * sum(
        bool((((fixture.raw or {}).get("scenario") or {}).get("between_tasks") or {}).get("hook"))
        for fixture in fixtures
    )
    actual_scale = {
        "model_families": len({target.family for target in targets}),
        "positive_fixtures": positive,
        "guard_fixtures": guards,
        "k": k,
        "pairs": pairs,
        "agent_invocations": pairs * len(_PHASE_OUTPUT_TOKENS),
        "hook_runs": hook_runs,
    }
    run_mode = _freeze_run_mode(manifest.get("required_scale") or {}, actual_scale)
    manifest_relative = _root_relative(manifest_path, root)
    if _git_blob_hash(root, "HEAD", manifest_relative) != _file_hash(manifest_path):
        raise ValueError("freeze.json 的 frozen 版本必须先提交到 HEAD")
    ancestry = _isolated_repo_git(root, "merge-base", "--is-ancestor", source_commit, "HEAD")
    if ancestry.returncode != 0:
        raise ValueError("freeze.json source_commit 不是当前 HEAD 的祖先")
    experiment_relative = Path(_root_relative(experiment_dir, root))
    committed_inputs = {
        relative: _git_blob_hash(root, source_commit, (experiment_relative / relative).as_posix())
        for relative in current_inputs
    }
    committed_external = {
        relative: _git_blob_hash(root, source_commit, relative)
        for relative in current_external
    }
    if committed_inputs != current_inputs or committed_external != current_external:
        raise ValueError("freeze.json source_commit 未包含声明的精确输入字节")
    return {
        "ok": True,
        "source_commit": source_commit,
        "run_mode": run_mode,
        "inputs": len(current_inputs),
        "external_inputs": len(current_external),
    }


def _checkpoint_header(
    *,
    config: ExperimentConfig,
    fixtures: list[Fixture],
    k: int,
    experiment_dir: Path,
    root: Path,
    run_root: Path,
    checkpoint_path: Path,
    targets: list[ExecutionTarget],
) -> dict[str, Any]:
    skill_names = sorted({
        "cs-keep",
        *(
            str((scenario.get(phase) or {}).get("skill"))
            for fixture in fixtures
            for scenario in [(fixture.raw or {}).get("scenario") or {}]
            for phase in ("a", "b")
            if (scenario.get(phase) or {}).get("skill")
        ),
    })
    seeds = sorted({
        str(((fixture.raw or {}).get("scenario") or {}).get("seed"))
        for fixture in fixtures
    })
    inputs = {
        "config": _canonical_hash(asdict(config)),
        "fixtures": {
            fixture.id: _canonical_hash(fixture.raw)
            for fixture in sorted(fixtures, key=lambda item: item.id)
        },
        "skill_snapshots": {
            skill: _file_hash(resolve_skill_path(root, skill))
            for skill in skill_names
        },
        "pipeline": _pipeline_hashes(),
        "experiment_assets": _experiment_asset_hashes(experiment_dir, fixtures),
        "seeds": {
            seed: _seed_input_hash(root, seed)
            for seed in seeds
        },
        "targets": _canonical_hash([asdict(target) for target in targets]),
        "k": k,
        "run_identity": _canonical_hash({
            "experiment_dir": str(experiment_dir.resolve()),
            "run_root": str(run_root.resolve()),
            "checkpoint": str(checkpoint_path.resolve()),
        }),
    }
    return {
        "kind": _CHECKPOINT_KIND,
        "phase": "header",
        "schema_version": _CHECKPOINT_SCHEMA_VERSION,
        "fingerprint": _canonical_hash(inputs),
        "inputs": inputs,
    }


def _ensure_checkpoint_header(path: Path, expected: dict[str, Any]) -> None:
    _repair_checkpoint_tail(path)
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        append_checkpoint(path, expected)
        return
    first = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    try:
        actual = json.loads(first)
    except json.JSONDecodeError as exc:
        raise ValueError("checkpoint header 不匹配：首行不是有效 JSON") from exc
    if actual != expected:
        raise ValueError(
            "checkpoint header 不匹配：config、fixture、skill、pipeline、experiment asset、seed、target、k "
            "或 run identity 已变化；请使用新的 checkpoint 或 --fresh"
        )


def load_completed_pairs(path: Path) -> list[dict]:
    """只恢复已经写入 score phase 的完整 pair。"""
    return list(_reduce_checkpoint(path)["completed_pairs"])


def load_retryable_errors(path: Path) -> list[dict[str, Any]]:
    """恢复历史 operational/half-pair 错误，避免重试成功后幸存者筛选。"""
    return list(_reduce_checkpoint(path)["operational_errors"])


def load_pipeline_errors(path: Path) -> list[dict[str, Any]]:
    """恢复不可重试的 pipeline 异常；同一冻结输入下不得再次执行。"""
    return list(_reduce_checkpoint(path)["pipeline_errors"])


def _checkpoint_actual_cost(path: Path) -> dict[str, Any]:
    invocation_events = _reduce_checkpoint(path)["invocations"]
    cost_items = [
        event.get("metrics", {}).get("cost_usd")
        for event in invocation_events
        if isinstance(event.get("metrics", {}).get("cost_usd"), dict)
    ]
    cost_tag = (
        MEASURED
        if len(cost_items) == len(invocation_events)
        and all(item.get("tag") == MEASURED for item in cost_items)
        else SOFT
    )
    return {
        "invocation_count": len(invocation_events),
        "cost_usd": tagged(
            round(sum(float(item.get("value", 0.0)) for item in cost_items), 6),
            cost_tag,
        ),
    }


def checkpoint_has_irreversible_evidence(path: Path) -> bool:
    """Only a missing/header-only journal may be erased with --fresh."""
    return _reduce_checkpoint(path)["fresh_eligible"] is not True


def branch_order(k_index: int) -> tuple[str, str]:
    """交替 paired 分支顺序，避免固定先后带来的系统偏差。"""
    if k_index % 2 == 0:
        return "treatment", "control"
    return "control", "treatment"


def _lesson_manifest(manifest: dict[str, str]) -> dict[str, str]:
    return {path: digest for path, digest in manifest.items() if path.startswith(".codestable/lessons/")}


def _without_lessons(manifest: dict[str, str]) -> dict[str, str]:
    return {path: digest for path, digest in manifest.items() if not path.startswith(".codestable/lessons/")}


def _differs_only_by_path(
    treatment: dict[str, str],
    control: dict[str, str],
    treatment_only_path: str,
) -> bool:
    """比较 pair 时只移除新注入 lesson，保留双方原有项目 lessons。"""
    reduced = dict(treatment)
    reduced.pop(treatment_only_path, None)
    return reduced == control


def materialize_paired_repos(
    post_a: Path,
    curation_repo: Path,
    lesson_path: str,
    treatment_path: Path,
    control_path: Path,
) -> tuple[Path, Path]:
    """从同一 post-A 基线重建 pair，只把已验证 lesson 注入 treatment。"""
    lesson = Path(lesson_path)
    if lesson.is_absolute() or ".." in lesson.parts or not lesson_path.startswith(".codestable/lessons/"):
        raise ValueError(f"非法 lesson path: {lesson_path!r}")
    treatment = copy_repo(post_a, treatment_path)
    control = copy_repo(post_a, control_path)
    source = curation_repo / lesson
    destination = treatment / lesson
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"curation lesson 不存在或为 symlink: {lesson_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return treatment, control


def apply_between_tasks_hook(
    hook: Path,
    treatment: Path,
    control: Path,
    allowed_paths: list[str],
) -> dict[str, Any]:
    """在 paired 两侧运行同一 deterministic hook，并验证 lesson 外结果同源。"""
    before_manifests = {"treatment": repo_manifest(treatment), "control": repo_manifest(control)}
    before_controls = {
        "treatment": repo_control_snapshot(treatment),
        "control": repo_control_snapshot(control),
    }
    before_lessons = {name: _lesson_manifest(manifest) for name, manifest in before_manifests.items()}
    results = [_run_repo_script(hook, repo) for repo in (treatment, control)]
    treatment_manifest = repo_manifest(treatment)
    control_manifest = repo_manifest(control)
    control_unchanged = (
        repo_control_unchanged(before_controls["treatment"], repo_control_snapshot(treatment))
        and repo_control_unchanged(before_controls["control"], repo_control_snapshot(control))
    )
    lesson_unchanged = (
        _lesson_manifest(treatment_manifest) == before_lessons["treatment"]
        and _lesson_manifest(control_manifest) == before_lessons["control"]
    )
    allowed = (
        paths_match_allowlist(changed_paths(before_manifests["treatment"], treatment_manifest), allowed_paths)
        and paths_match_allowlist(changed_paths(before_manifests["control"], control_manifest), allowed_paths)
    )
    return {
        "ok": (
            all(result.returncode == 0 for result in results)
            and lesson_unchanged
            and control_unchanged
            and allowed
            and _without_lessons(treatment_manifest) == _without_lessons(control_manifest)
        ),
        "runs": len(results),
        "timed_out": sum(result.returncode == 124 for result in results),
        "returncodes": [result.returncode for result in results],
    }


def _run_repo_script(script: Path, repo: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-I", "-B", str(script), str(repo)]
    try:
        with tempfile.TemporaryDirectory(prefix="cs-eval-script-", dir=repo.parent) as tmp:
            return subprocess.run(
                command,
                cwd=repo,
                env=isolated_subprocess_env(Path(tmp), pythonpath=repo),
                capture_output=True,
                text=True,
                check=False,
                timeout=_DETERMINISTIC_TIMEOUT_S,
            )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=command,
            returncode=124,
            stdout="",
            stderr=f"deterministic subprocess timeout after {_DETERMINISTIC_TIMEOUT_S}s",
        )


def _run_check_files(repo: Path, paths: list[Path]) -> dict[str, Any]:
    """执行 A/B deterministic pytest，并把 timeout 记为机械失败。"""
    passed = 0
    timed_out = 0
    evidence: list[dict[str, Any]] = []
    pytest_spec = importlib.util.find_spec("pytest")
    if pytest_spec is None or pytest_spec.origin is None:
        raise RuntimeError("deterministic checks 需要 pytest")
    pytest_site = Path(pytest_spec.origin).resolve().parent.parent
    bootstrap = (
        "import sys; "
        "sys.path[:0] = sys.argv[1:3]; "
        "import pytest; "
        "raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider', sys.argv[3]]))"
    )
    with tempfile.TemporaryDirectory(prefix="cs-eval-checks-", dir=repo.parent) as tmp:
        env = isolated_subprocess_env(Path(tmp), pythonpath=repo)
        for path in paths:
            command = [
                sys.executable,
                "-I",
                "-B",
                "-c",
                bootstrap,
                str(repo.resolve()),
                str(pytest_site),
                str(path),
            ]
            try:
                result = subprocess.run(
                    command,
                    cwd=repo,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=_DETERMINISTIC_TIMEOUT_S,
                )
                raw_output = result.stdout + result.stderr
                ok = result.returncode == 0
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                timed_out += 1
                raw_output = f"deterministic pytest timeout after {_DETERMINISTIC_TIMEOUT_S}s"
                ok = False
                returncode = 124
            passed += int(ok)
            evidence.append({
                "check_sha256": _file_hash(path),
                "passed": ok,
                "returncode": returncode,
                "output_sha256": _sha256_bytes(raw_output.encode("utf-8", errors="replace")),
            })
    total = len(paths)
    return {
        "passed": passed,
        "total": total,
        "rate": round(passed / total, 4) if total else 0.0,
        "timed_out": timed_out,
        "evidence": evidence,
    }
def _markdown_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"缺少 frontmatter: {path}")
    try:
        _, raw, body = text.split("---\n", 2)
        metadata = yaml.safe_load(raw) or {}
    except (ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"frontmatter 无效: {path}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"frontmatter 必须是 mapping: {path}")
    return metadata, body


def _repo_relative_pointer(repo: Path, owner: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"缺少文档指针: {owner}")
    path = (owner.parent / value).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ValueError(f"文档指针越过 seed repo: {value!r}") from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"文档指针不存在或为 symlink: {value!r}")
    return path


def validate_epic_seed(repo: Path) -> dict[str, Any]:
    """验证 Epic fixture 走真实 active 恢复路径，而不是隐式豁免 owner gate。"""
    errors: list[str] = []
    cursors = sorted((repo / ".codestable/work").glob("epic-*.md"))
    if len(cursors) != 1:
        return {"ok": False, "errors": [f"需要恰好一个 Epic 游标，实际 {len(cursors)}"]}
    cursor = cursors[0]
    try:
        cursor_meta, cursor_body = _markdown_frontmatter(cursor)
        epic = _repo_relative_pointer(repo, cursor, cursor_meta.get("epic"))
        epic_meta, epic_body = _markdown_frontmatter(epic)
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [str(exc)]}

    if epic_meta.get("status") != "active":
        errors.append("永久 Epic status 必须为 active")
    if cursor_meta.get("phase") != "executing":
        errors.append("Epic 游标 phase 必须为 executing")
    approved = str(cursor_meta.get("approved_revision") or "")
    if approved != _file_hash(epic):
        errors.append("approved_revision 与永久 Epic SHA-256 不匹配")
    try:
        work_pointer = _repo_relative_pointer(repo, epic, epic_meta.get("work"))
        if work_pointer != cursor.resolve():
            errors.append("永久 Epic work 指针未指向当前游标")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))

    progression = cursor_meta.get("item_progression")
    commit = cursor_meta.get("milestone_commit")
    publish = cursor_meta.get("remote_publish")
    if progression not in {"continuous", "per-item"}:
        errors.append("item_progression 非法")
    if commit not in {"authorized", "manual"}:
        errors.append("milestone_commit 非法")
    if publish not in {"each-milestone", "final", "manual"}:
        errors.append("remote_publish 非法")
    if commit == "manual" and (progression != "per-item" or publish != "manual"):
        errors.append("manual milestone 策略组合非法")
    if publish == "each-milestone" and commit != "authorized":
        errors.append("each-milestone publish 必须搭配 authorized commit")

    item_section = epic_body.split("## 子项契约", 1)
    item_text = item_section[1].split("\n## ", 1)[0] if len(item_section) == 2 else ""
    item_ids = re.findall(r"^-\s+`([^`]+)`\s*[：:]", item_text, flags=re.MULTILINE)
    if len(item_ids) < 2 or len(item_ids) != len(set(item_ids)):
        errors.append("永久 Epic 必须含至少两个唯一的已批准子项")

    progress_section = cursor_body.split("## 子项进度", 1)
    progress_text = progress_section[1].split("\n## ", 1)[0] if len(progress_section) == 2 else ""
    progress_entries = re.findall(
        r"^-\s+\[([ xX])\]\s+`?([^`\s]+)`?\s*$",
        progress_text,
        flags=re.MULTILINE,
    )
    progress = {item_id: marker.lower() == "x" for marker, item_id in progress_entries}
    if set(progress) != set(item_ids):
        errors.append("游标子项进度必须与已批准子项一一对应")
    current = str(cursor_meta.get("current_item") or "")
    if current not in item_ids:
        errors.append("current_item 不属于已批准子项")
    elif progress.get(current) is not False:
        errors.append("current_item 必须是尚未完成的子项")
    if "## 临时决策与证据" not in cursor_body:
        errors.append("Epic 游标必须含临时决策与证据区")
    return {"ok": not errors, "errors": errors}


def preflight_fixture(
    fixture: Fixture,
    seed_repo: Path,
    experiment_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    """机械证明 fixture 的 golden 可解且 naive 只在目标不变量上失败。"""
    scenario = (fixture.raw or {}).get("scenario") or {}
    b_spec = scenario.get("b") or {}
    preflight = scenario.get("preflight") or {}
    if "cs-epic" in {
        (scenario.get("a") or {}).get("skill"),
        (scenario.get("b") or {}).get("skill"),
    }:
        epic_result = validate_epic_seed(seed_repo)
        if not epic_result["ok"]:
            return {
                "ok": False,
                "state": "fixture-invalid",
                "reason": "; ".join(epic_result["errors"]),
                "epic": epic_result,
            }
    run_root.mkdir(parents=True, exist_ok=True)
    repos = {
        "naive": copy_repo(seed_repo, run_root / "naive"),
        "golden": copy_repo(seed_repo, run_root / "golden"),
    }
    script_results = {
        name: _run_repo_script(
            resolve_experiment_asset(experiment_dir, preflight[f"{name}_hook"]), repo,
        )
        for name, repo in repos.items()
    }
    timed_out = [name for name, result in script_results.items() if result.returncode == 124]
    failed_hooks = [name for name, result in script_results.items() if result.returncode != 0]
    if failed_hooks:
        reason = (
            f"preflight hook timeout: {', '.join(timed_out)}"
            if timed_out
            else f"preflight hook failed: {', '.join(failed_hooks)}"
        )
        return {
            "ok": False,
            "state": "fixture-invalid",
            "reason": reason,
            "hook_returncodes": {
                name: result.returncode for name, result in script_results.items()
            },
        }
    hidden_paths = [
        resolve_experiment_asset(experiment_dir, path) for path in b_spec.get("hidden_tests", [])
    ]
    regression_paths = [
        resolve_experiment_asset(experiment_dir, path) for path in b_spec.get("regression_tests", [])
    ]
    checks = {
        name: {
            "hidden": _run_check_files(repo, hidden_paths),
            "regression": _run_check_files(repo, regression_paths),
        }
        for name, repo in repos.items()
    }
    golden_hidden = checks["golden"]["hidden"]["rate"]
    naive_hidden = checks["naive"]["hidden"]["rate"]
    golden_regression = checks["golden"]["regression"]["rate"]
    naive_regression = checks["naive"]["regression"]["rate"]
    ok = (
        golden_hidden == 1.0
        and naive_hidden < 1.0
        and golden_regression == 1.0
        and naive_regression == 1.0
    )
    return {
        "ok": ok,
        "state": "runnable" if ok else "fixture-invalid",
        "reason": None if ok else "golden/naive deterministic oracle contract failed",
        "golden_hidden": golden_hidden,
        "naive_hidden": naive_hidden,
        "golden_regression": golden_regression,
        "naive_regression": naive_regression,
    }


def dry_run_sequence(
    config: ExperimentConfig,
    fixtures: list[Fixture],
    k: int,
    root: Path,
    targets: list[ExecutionTarget] | None = None,
) -> dict[str, Any]:
    """估算完整 paired sequence，显式累加 A、curation 与两侧 B。"""
    selected_targets = config.model_targets if targets is None else targets
    if not selected_targets:
        raise ValueError("learning-transfer 需要显式 model_targets")
    phase_invocations = {phase: 0 for phase in _PHASE_OUTPUT_TOKENS}
    per_target: list[dict[str, Any]] = []
    total = 0.0
    hook_runs = 0
    for target in selected_targets:
        target_cost = 0.0
        keep_text = resolve_skill_path(root, "cs-keep").read_text(encoding="utf-8")
        for fixture in fixtures:
            scenario = (fixture.raw or {}).get("scenario") or {}
            a_text = resolve_skill_path(root, (scenario.get("a") or {}).get("skill", "")).read_text(encoding="utf-8")
            b_text = resolve_skill_path(root, (scenario.get("b") or {}).get("skill", "")).read_text(encoding="utf-8")
            concepts = (scenario.get("candidate") or {}).get("required_concepts") or ["fixture candidate"]
            prompts = {
                "a": build_sequence_task_prompt(fixture, a_text, "a"),
                "curation": build_curation_prompt(fixture, keep_text, "; ".join(concepts), "A checks passed"),
                "b-treatment": build_sequence_task_prompt(fixture, b_text, "b"),
                "b-control": build_sequence_task_prompt(fixture, b_text, "b"),
            }
            for phase, prompt in prompts.items():
                phase_invocations[phase] += k
                target_cost += metrics.estimate_cost(
                    prompt,
                    target.model,
                    out_tokens=_PHASE_OUTPUT_TOKENS[phase],
                ) * k
            if (scenario.get("between_tasks") or {}).get("hook"):
                hook_runs += 2 * k
        total += target_cost
        per_target.append({"target_id": target.id, "est_usd": round(target_cost, 4)})
    return {
        "est_total_usd": round(total, 2),
        "budget_usd": config.budget_usd,
        "invocation_count": sum(phase_invocations.values()),
        "phase_invocations": phase_invocations,
        "hook_runs": hook_runs,
        "per_target": per_target,
        "fixtures": len(fixtures),
        "targets": len(selected_targets),
        "k": k,
    }


def _all_checks_passed(result: dict[str, Any]) -> bool:
    return result["passed"] == result["total"]


def _pipeline_failure(
    *,
    target: ExecutionTarget,
    fixture: Fixture,
    k_index: int,
    a_ok: bool,
    a_mutation_ok: bool,
    a_repo_integrity_ok: bool,
    candidate_unique: bool,
    reason: str,
    phase_metrics: list[dict[str, Any]],
    lesson_schema_ok: bool = False,
    lesson_only_mutation: bool = False,
    curation_repo_integrity_ok: bool | None = None,
) -> dict[str, Any]:
    scenario = (fixture.raw or {}).get("scenario") or {}
    return {
        "state": "pipeline-failed",
        "target_id": target.id,
        "family": target.family,
        "fixture_id": fixture.id,
        "fixture_class": scenario.get("class"),
        "k_index": k_index,
        "a_ok": a_ok,
        "a_mutation_ok": a_mutation_ok,
        "a_repo_integrity_ok": a_repo_integrity_ok,
        "candidate_unique": candidate_unique,
        "lesson_schema_ok": lesson_schema_ok,
        "lesson_only_mutation": lesson_only_mutation,
        "curation_repo_integrity_ok": curation_repo_integrity_ok,
        "prompt_equal": False,
        "isolation_ok": False,
        "lesson_transition_ok": False,
        "lesson_expectation_ok": False,
        "treatment_mutation_ok": False,
        "control_mutation_ok": False,
        "treatment_regression_ok": False,
        "control_regression_ok": False,
        "treatment_hidden": 0.0,
        "control_hidden": 0.0,
        "phase_metrics": phase_metrics,
        "failure_reason": reason,
    }


def _invoke_phase(
    *,
    harness: Any,
    prompt: str,
    target: ExecutionTarget,
    workdir: Path,
    phase: str,
    emit: Callable[[dict[str, Any]], None],
) -> tuple[HarnessResult, dict[str, Any]]:
    """Write-ahead one provider attempt, then append its terminal metrics."""
    invocation_id = secrets.token_hex(16)
    started = time.monotonic()
    fallback = HarnessResult(
        output="",
        model=target.model,
        harness=str(getattr(harness, "name", target.harness)),
        wall_ms=0,
        usage={"output_tokens": _PHASE_OUTPUT_TOKENS[phase]},
        error="InvocationIncomplete",
    )
    fallback_metrics = metrics.capture(fallback, prompt)
    emit({
        "phase": phase,
        "status": "invocation-started",
        "invocation_id": invocation_id,
        "metrics": fallback_metrics,
    })
    try:
        result = harness.invoke(prompt, target.model, workdir, timeout_s=600)
        phase_metrics = metrics.capture(result, prompt)
    except Exception as exc:
        synthetic = HarnessResult(
            output="",
            model=target.model,
            harness=str(getattr(harness, "name", target.harness)),
            wall_ms=int((time.monotonic() - started) * 1000),
            usage={"output_tokens": _PHASE_OUTPUT_TOKENS[phase]},
            error=type(exc).__name__,
        )
        phase_metrics = metrics.capture(synthetic, prompt)
        emit({
            "phase": phase,
            "status": "retryable-error",
            "invocation_id": invocation_id,
            "metrics": phase_metrics,
            "error_type": type(exc).__name__,
        })
        raise RetryableSequenceError(
            f"{phase} adapter invocation failed: {type(exc).__name__}",
            invocation_id=invocation_id,
        ) from exc
    if result.error:
        emit({
            "phase": phase,
            "status": "retryable-error",
            "invocation_id": invocation_id,
            "metrics": phase_metrics,
            "error_type": "HarnessResultError",
        })
        raise RetryableSequenceError(
            f"{phase} harness returned an error",
            invocation_id=invocation_id,
        )
    emit({
        "phase": phase,
        "status": "invocation-complete",
        "invocation_id": invocation_id,
        "metrics": phase_metrics,
    })
    return result, phase_metrics


def run_pair(
    *,
    fixture: Fixture,
    target: ExecutionTarget,
    k_index: int,
    seed_repo: Path,
    experiment_dir: Path,
    root: Path,
    run_root: Path,
    harness: Any,
    phase_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """执行一个完整 paired cell，仅返回可聚合的结构化 oracle。"""
    scenario = (fixture.raw or {}).get("scenario") or {}
    a_spec = scenario.get("a") or {}
    b_spec = scenario.get("b") or {}
    candidate_spec = scenario.get("candidate") or {}
    run_root.mkdir(parents=True, exist_ok=True)
    emit = phase_callback or (lambda _event: None)

    a_repo = copy_repo(seed_repo, run_root / "post-a")
    before_a = repo_manifest(a_repo)
    before_a_control = repo_control_snapshot(a_repo)
    if before_a_control.get("safe") is not True:
        return _pipeline_failure(
            target=target,
            fixture=fixture,
            k_index=k_index,
            a_ok=False,
            a_mutation_ok=False,
            a_repo_integrity_ok=False,
            candidate_unique=False,
            reason="seed Git control plane escapes the cell",
            phase_metrics=[],
        )
    candidate_before = snapshot_candidates(fixture, a_repo)
    a_text = resolve_skill_path(root, a_spec["skill"]).read_text(encoding="utf-8")
    a_prompt = build_sequence_task_prompt(fixture, a_text, "a")
    a_result, a_metrics = _invoke_phase(
        harness=harness,
        prompt=a_prompt,
        target=target,
        workdir=a_repo,
        phase="a",
        emit=emit,
    )
    a_checks = _run_check_files(
        a_repo,
        [resolve_experiment_asset(experiment_dir, path) for path in a_spec.get("checks", [])],
    )
    a_changes = changed_paths(before_a, repo_manifest(a_repo))
    a_repo_integrity_ok = repo_control_unchanged(
        before_a_control,
        repo_control_snapshot(a_repo),
    )
    a_mutation_ok = (
        paths_match_allowlist(a_changes, list(a_spec.get("allowed_paths", [])))
        and a_repo_integrity_ok
        and not any(path.startswith(".codestable/lessons/") for path in a_changes)
    )
    a_ok = not a_result.error and _all_checks_passed(a_checks) and a_mutation_ok
    if not a_ok:
        return _pipeline_failure(
            target=target,
            fixture=fixture,
            k_index=k_index,
            a_ok=False,
            a_mutation_ok=a_mutation_ok,
            a_repo_integrity_ok=a_repo_integrity_ok,
            candidate_unique=False,
            reason="A oracle failed",
            phase_metrics=[{"phase": "a", "metrics": a_metrics}],
        )
    try:
        candidate = extract_candidate(
            fixture,
            a_result.output,
            a_repo,
            before=candidate_before,
        )
    except ValueError as exc:
        return _pipeline_failure(
            target=target,
            fixture=fixture,
            k_index=k_index,
            a_ok=True,
            a_mutation_ok=a_mutation_ok,
            a_repo_integrity_ok=a_repo_integrity_ok,
            candidate_unique=False,
            reason=str(exc),
            phase_metrics=[{"phase": "a", "metrics": a_metrics}],
        )

    curation_repo = copy_repo(a_repo, run_root / "curation")
    before_curation = repo_manifest(curation_repo)
    before_curation_control = repo_control_snapshot(curation_repo)
    keep_text = resolve_skill_path(root, "cs-keep").read_text(encoding="utf-8")
    curation_prompt = build_curation_prompt(
        fixture,
        keep_text,
        candidate,
        (
            f"A checks passed: {a_checks['passed']}/{a_checks['total']}; "
            f"changed paths: {', '.join(sorted(a_changes))}"
        ),
    )
    curation_result, curation_metrics = _invoke_phase(
        harness=harness,
        prompt=curation_prompt,
        target=target,
        workdir=curation_repo,
        phase="curation",
        emit=emit,
    )
    after_curation = repo_manifest(curation_repo)
    curation_changes = changed_paths(before_curation, after_curation)
    curation_repo_integrity_ok = repo_control_unchanged(
        before_curation_control,
        repo_control_snapshot(curation_repo),
    )
    lesson_only_mutation = (
        not curation_result.error
        and bool(curation_changes)
        and paths_match_allowlist(curation_changes, [".codestable/lessons/**"])
        and curation_repo_integrity_ok
    )
    lesson_paths = sorted(path for path in curation_changes if path.startswith(".codestable/lessons/"))
    lesson_oracle = validate_observed_lesson(
        curation_repo,
        list(candidate_spec.get("required_concepts", [])),
        lesson_paths,
    )
    if not lesson_only_mutation or not lesson_oracle["ok"]:
        return _pipeline_failure(
            target=target,
            fixture=fixture,
            k_index=k_index,
            a_ok=True,
            a_mutation_ok=a_mutation_ok,
            a_repo_integrity_ok=a_repo_integrity_ok,
            candidate_unique=True,
            lesson_schema_ok=lesson_oracle["ok"],
            lesson_only_mutation=lesson_only_mutation,
            curation_repo_integrity_ok=curation_repo_integrity_ok,
            reason="curation mutation/schema failed",
            phase_metrics=[
                {"phase": "a", "metrics": a_metrics},
                {"phase": "curation", "metrics": curation_metrics},
            ],
        )

    treatment, control = materialize_paired_repos(
        a_repo,
        curation_repo,
        lesson_paths[0],
        run_root / "treatment",
        run_root / "control",
    )
    treatment_manifest = repo_manifest(treatment)
    control_manifest = repo_manifest(control)
    post_a_equal = _differs_only_by_path(
        treatment_manifest,
        control_manifest,
        lesson_paths[0],
    )

    hook_result = {"ok": True, "runs": 0}
    hook_path = (scenario.get("between_tasks") or {}).get("hook")
    if hook_path:
        hook_result = apply_between_tasks_hook(
            resolve_experiment_asset(experiment_dir, hook_path),
            treatment,
            control,
            list((scenario.get("between_tasks") or {}).get("allowed_paths", [])),
        )
        emit({"phase": "hook", "status": "passed" if hook_result["ok"] else "failed", "runs": 2})
        if not hook_result["ok"]:
            return _pipeline_failure(
                target=target,
                fixture=fixture,
                k_index=k_index,
                a_ok=True,
                a_mutation_ok=a_mutation_ok,
                a_repo_integrity_ok=a_repo_integrity_ok,
                candidate_unique=True,
                lesson_schema_ok=lesson_oracle["ok"],
                lesson_only_mutation=lesson_only_mutation,
                reason="between_tasks hook failed",
                phase_metrics=[
                    {"phase": "a", "metrics": a_metrics},
                    {"phase": "curation", "metrics": curation_metrics},
                ],
            )

    b_text = resolve_skill_path(root, b_spec["skill"]).read_text(encoding="utf-8")
    b_prompt = build_sequence_task_prompt(fixture, b_text, "b")
    prompt_hash = hashlib.sha256(b_prompt.encode("utf-8")).hexdigest()
    before_b = {
        "treatment": repo_manifest(treatment),
        "control": repo_manifest(control),
    }
    before_b_control = {
        "treatment": repo_control_snapshot(treatment),
        "control": repo_control_snapshot(control),
    }
    before_lesson_text = {
        path: (treatment / path).read_text(encoding="utf-8")
        for path in lesson_paths
    }
    repos = {"treatment": treatment, "control": control}
    branch_results: dict[str, Any] = {}
    branch_metrics: dict[str, dict[str, Any]] = {}
    for branch in branch_order(k_index):
        branch_results[branch], branch_metrics[branch] = _invoke_phase(
            harness=harness,
            prompt=b_prompt,
            target=target,
            workdir=repos[branch],
            phase=f"b-{branch}",
            emit=emit,
        )
    hidden_paths = [
        resolve_experiment_asset(experiment_dir, path) for path in b_spec.get("hidden_tests", [])
    ]
    regression_paths = [
        resolve_experiment_asset(experiment_dir, path) for path in b_spec.get("regression_tests", [])
    ]
    branch_checks: dict[str, dict[str, Any]] = {}
    branch_regressions: dict[str, dict[str, Any]] = {}
    branch_mutation_ok: dict[str, bool] = {}
    branch_repo_integrity_ok: dict[str, bool] = {}
    lesson_transition_ok = True
    for branch, repo in repos.items():
        branch_checks[branch] = _run_check_files(repo, hidden_paths)
        branch_regressions[branch] = _run_check_files(repo, regression_paths)
        allowed = list(b_spec.get("allowed_paths", []))
        if branch == "treatment":
            allowed.extend(lesson_paths)
        changes = changed_paths(before_b[branch], repo_manifest(repo))
        changed_lessons = [path for path in changes if path.startswith(".codestable/lessons/")]
        branch_repo_integrity_ok[branch] = repo_control_unchanged(
            before_b_control[branch],
            repo_control_snapshot(repo),
        )
        branch_mutation_ok[branch] = (
            paths_match_allowlist(changes, allowed)
            and branch_repo_integrity_ok[branch]
            and (branch == "treatment" or not changed_lessons)
            and (branch != "treatment" or set(changed_lessons) <= set(lesson_paths))
        )
        if branch == "treatment":
            changed_lessons = [path for path in lesson_paths if path in changes]
            if changed_lessons:
                lesson_transition_ok = len(changed_lessons) == 1 and validate_lesson_transition(
                    before_lesson_text[changed_lessons[0]],
                    (repo / changed_lessons[0]).read_text(encoding="utf-8"),
                )["ok"]
                branch_mutation_ok[branch] = branch_mutation_ok[branch] and lesson_transition_ok

    def branch_ok(branch: str) -> bool:
        return (
            not branch_results[branch].error
            and hook_result["ok"]
            and branch_mutation_ok[branch]
            and _all_checks_passed(branch_checks[branch])
            and _all_checks_passed(branch_regressions[branch])
        )

    final_lesson_text = (treatment / lesson_paths[0]).read_text(encoding="utf-8")
    final_lesson_status = lesson_status(final_lesson_text)
    lesson_unchanged = final_lesson_text == before_lesson_text[lesson_paths[0]]
    expected_transition = (scenario.get("expect") or {}).get("lesson_transition")
    lesson_expectation_ok = {
        "observed->validated": final_lesson_status == "validated" and lesson_transition_ok,
        "unchanged-observed": final_lesson_status == "observed" and lesson_unchanged,
        "observed->retired": final_lesson_status == "retired" and lesson_transition_ok,
    }.get(expected_transition, False)

    return {
        "target_id": target.id,
        "family": target.family,
        "fixture_id": fixture.id,
        "fixture_class": scenario.get("class"),
        "k_index": k_index,
        "a_ok": a_ok,
        "a_mutation_ok": a_mutation_ok,
        "a_repo_integrity_ok": a_repo_integrity_ok,
        "candidate_unique": True,
        "post_a_equal": post_a_equal,
        "lesson_schema_ok": lesson_oracle["ok"],
        "lesson_only_mutation": lesson_only_mutation,
        "curation_repo_integrity_ok": curation_repo_integrity_ok,
        "prompt_equal": True,
        "prompt_hash": prompt_hash,
        "hook_ok": hook_result["ok"],
        "isolation_ok": post_a_equal and hook_result["ok"],
        "lesson_transition_ok": lesson_transition_ok,
        "lesson_expectation_ok": lesson_expectation_ok,
        "lesson_unchanged": lesson_unchanged,
        "lesson_status": final_lesson_status,
        "stale_retired": final_lesson_status == "retired" if scenario.get("class") == "stale" else None,
        "treatment_ok": branch_ok("treatment"),
        "control_ok": branch_ok("control"),
        "treatment_hidden": branch_checks["treatment"]["rate"],
        "control_hidden": branch_checks["control"]["rate"],
        "treatment_mutation_ok": branch_mutation_ok["treatment"],
        "control_mutation_ok": branch_mutation_ok["control"],
        "treatment_repo_integrity_ok": branch_repo_integrity_ok["treatment"],
        "control_repo_integrity_ok": branch_repo_integrity_ok["control"],
        "treatment_regression_ok": _all_checks_passed(branch_regressions["treatment"]),
        "control_regression_ok": _all_checks_passed(branch_regressions["control"]),
        "phase_metrics": [
            {"phase": "a", "metrics": a_metrics},
            {"phase": "curation", "metrics": curation_metrics},
            {"phase": "b-treatment", "metrics": branch_metrics["treatment"]},
            {"phase": "b-control", "metrics": branch_metrics["control"]},
        ],
    }


def _pair_identity(pair: dict[str, Any]) -> tuple[str, str, int]:
    return str(pair["target_id"]), str(pair["fixture_id"]), int(pair["k_index"])


def _read_preflight_cache(path: Path, fingerprint: str) -> dict[str, Any] | None:
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(cached, dict):
        return None
    result = cached.get("result")
    if cached.get("checkpoint_fingerprint") != fingerprint or not isinstance(result, dict):
        return None
    return result


def _write_preflight_cache(path: Path, fingerprint: str, result: dict[str, Any]) -> None:
    payload = json.dumps(
        {"checkpoint_fingerprint": fingerprint, "result": result},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    _atomic_write_text(path, payload)


def run_sequence(
    *,
    config: ExperimentConfig,
    fixtures: list[Fixture],
    k: int,
    experiment_dir: Path,
    root: Path,
    run_root: Path,
    checkpoint_path: Path,
    targets: list[ExecutionTarget] | None = None,
    harness_resolver=None,
) -> dict[str, Any]:
    """运行完整 learning-transfer matrix，并从 score checkpoint 幂等恢复。"""
    if harness_resolver is None:
        import harness as harness_pkg
        harness_resolver = harness_pkg.get_harness
    selected_targets = config.model_targets if targets is None else targets
    if not selected_targets:
        raise ValueError("learning-transfer 需要显式 model_targets")
    header = _checkpoint_header(
        config=config,
        fixtures=fixtures,
        k=k,
        experiment_dir=experiment_dir,
        root=root,
        run_root=run_root,
        checkpoint_path=checkpoint_path,
        targets=selected_targets,
    )
    _ensure_checkpoint_header(checkpoint_path, header)
    restored_journal = _reduce_checkpoint(checkpoint_path)
    restored_invalid = {
        str(record["fixture_id"]): record
        for record in restored_journal["fixture_invalid"]
        if record.get("fixture_id") is not None
    }
    run_root.mkdir(parents=True, exist_ok=True)
    preflight_dir = run_root / "preflight"
    preflight_dir.mkdir(exist_ok=True)
    preflight_results: dict[str, dict[str, Any]] = {}
    invalid: list[dict[str, Any]] = []
    runnable: list[Fixture] = []
    for fixture in fixtures:
        result_path = _contained_child(preflight_dir, f"{fixture.id}.json")
        restored = restored_invalid.get(fixture.id)
        preflight_result: dict[str, Any] | None = (
            dict(restored["preflight"]) if restored is not None else None
        )
        if preflight_result is None and result_path.exists():
            preflight_result = _read_preflight_cache(result_path, header["fingerprint"])
        if preflight_result is None:
            scenario = (fixture.raw or {}).get("scenario") or {}
            try:
                with tempfile.TemporaryDirectory(prefix=f"{fixture.id}-", dir=preflight_dir) as tmp:
                    tmp_path = Path(tmp)
                    seed_repo = build_seed_repo(str(scenario["seed"]), tmp_path / "seed", root)
                    preflight_result = preflight_fixture(
                        fixture,
                        seed_repo,
                        experiment_dir,
                        tmp_path / "runs",
                    )
            except Exception as exc:
                preflight_result = {
                    "ok": False,
                    "state": "fixture-invalid",
                    "reason": f"{type(exc).__name__}: {str(exc)[:300]}",
                }
            if preflight_result.get("ok") is not True:
                append_checkpoint(checkpoint_path, {
                    "fixture_id": fixture.id,
                    "phase": "fixture-invalid",
                    "phase_key": f"fixture|{fixture.id}|preflight",
                    "status": "fixture-invalid",
                    "preflight": preflight_result,
                })
            _write_preflight_cache(result_path, header["fingerprint"], preflight_result)
        preflight_results[fixture.id] = preflight_result
        if preflight_result.get("ok") is True:
            runnable.append(fixture)
        else:
            invalid.append({
                "fixture_id": fixture.id,
                "state": "fixture-invalid",
                "preflight": preflight_result,
            })
    completed = load_completed_pairs(checkpoint_path)
    completed_keys = {_pair_identity(pair) for pair in completed}
    pairs = list(completed)
    operational_history = load_retryable_errors(checkpoint_path)
    pipeline_errors = load_pipeline_errors(checkpoint_path)
    terminal_keys = {_pair_identity(error) for error in pipeline_errors}
    for target in selected_targets:
        harness = harness_resolver(target.harness)
        for fixture in runnable:
            scenario = (fixture.raw or {}).get("scenario") or {}
            for k_index in range(k):
                identity = (target.id, fixture.id, k_index)
                if identity in completed_keys or identity in terminal_keys:
                    continue
                cell_root = _contained_child(run_root, f"{target.id}__{fixture.id}__{k_index}")
                if cell_root.exists():
                    shutil.rmtree(cell_root)
                def checkpoint_phase(event: dict[str, Any]) -> None:
                    append_checkpoint(checkpoint_path, {
                        "target_id": target.id,
                        "fixture_id": fixture.id,
                        "k_index": k_index,
                        **event,
                        "phase_key": phase_key(
                            target.id,
                            fixture.id,
                            k_index,
                            str(event.get("phase", "unknown")),
                        ),
                    })
                try:
                    seed_repo = build_seed_repo(str(scenario["seed"]), cell_root / "seed", root)
                    pair = run_pair(
                        fixture=fixture,
                        target=target,
                        k_index=k_index,
                        seed_repo=seed_repo,
                        experiment_dir=experiment_dir,
                        root=root,
                        run_root=cell_root / "pair",
                        harness=harness,
                        phase_callback=checkpoint_phase,
                    )
                except RetryableSequenceError as exc:
                    error = {
                        "target_id": target.id,
                        "fixture_id": fixture.id,
                        "k_index": k_index,
                        "state": "retryable-error",
                        "error": type(exc).__name__,
                    }
                    if exc.invocation_id is not None:
                        error["invocation_id"] = exc.invocation_id
                    operational_history.append(error)
                    append_checkpoint(checkpoint_path, {
                        **error,
                        "phase": "error",
                        "phase_key": phase_key(target.id, fixture.id, k_index, "error"),
                        "status": "retryable-error",
                    })
                    continue
                except Exception as exc:
                    error = {
                        "target_id": target.id,
                        "fixture_id": fixture.id,
                        "k_index": k_index,
                        "state": "pipeline-error",
                        "error": type(exc).__name__,
                    }
                    pipeline_errors.append(error)
                    terminal_keys.add(identity)
                    append_checkpoint(checkpoint_path, {
                        **error,
                        "phase": "error",
                        "phase_key": phase_key(target.id, fixture.id, k_index, "error"),
                        "status": "pipeline-error",
                    })
                    continue
                finally:
                    if cell_root.exists():
                        shutil.rmtree(cell_root)
                pair.setdefault("state", "completed")
                pair.update({
                    "target_id": target.id,
                    "family": target.family,
                    "model": target.model,
                    "harness": target.harness,
                    "fixture_id": fixture.id,
                    "fixture_class": scenario.get("class"),
                    "owning_skill": (scenario.get("a") or {}).get("skill"),
                    "k_index": k_index,
                })
                append_checkpoint(checkpoint_path, {
                    "target_id": target.id,
                    "fixture_id": fixture.id,
                    "k_index": k_index,
                    "phase": "score",
                    "phase_key": phase_key(target.id, fixture.id, k_index, "score"),
                    "status": pair["state"],
                    "pair": pair,
                })
                pairs.append(pair)
    completed_outcomes = {_pair_identity(pair) for pair in pairs}
    operational_errors = [
        {**error, "resolved": _pair_identity(error) in completed_outcomes}
        for error in operational_history
    ]
    unresolved_operational = [
        {key: value for key, value in error.items() if key != "resolved"}
        for error in operational_errors
        if error["resolved"] is False
    ]
    errors = [*pipeline_errors, *unresolved_operational]
    records = [*pairs, *errors, *invalid]
    aggregate = aggregate_pairs(records, operational_errors=operational_errors)
    aggregate["cost"] = _checkpoint_actual_cost(checkpoint_path)
    return {
        "experiment": config.name,
        "execution_mode": "learning-transfer",
        "k": k,
        "pairs": pairs,
        "errors": errors,
        "operational_errors": operational_errors,
        "invalid": invalid,
        "preflight": preflight_results,
        "aggregate": aggregate,
        "verdict": transfer_verdict(aggregate),
    }


def _candidate_lines(text: str) -> list[str]:
    matches: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        if line.startswith(_CANDIDATE_MARKER):
            candidate = line[len(_CANDIDATE_MARKER):].strip()
            if candidate:
                matches.append(candidate)
    return matches


def _epic_candidate_lines(repo: Path) -> list[str]:
    cursors = sorted((repo / ".codestable/work").glob("epic-*.md"))
    if len(cursors) != 1:
        raise ValueError(f"Epic 候选需要恰好一个游标，实际 {len(cursors)} 个")
    text = cursors[0].read_text(encoding="utf-8")
    sections = text.split("## 临时决策与证据", 1)
    if len(sections) != 2:
        raise ValueError("Epic 游标缺少临时决策与证据区")
    evidence = sections[1].split("\n## ", 1)[0]
    return _candidate_lines(evidence)


def snapshot_candidates(fixture: Fixture, repo: Path) -> Counter[str]:
    """A 前快照持久通道，避免把旧 Epic 候选归因给本轮。"""
    scenario = (fixture.raw or {}).get("scenario") or {}
    source = (scenario.get("a") or {}).get("candidate_source")
    if source == "output":
        return Counter()
    if source == "epic-cursor":
        return Counter(_epic_candidate_lines(repo))
    raise ValueError(f"尚不支持的 candidate_source: {source!r}")


def extract_candidate(
    fixture: Fixture,
    output: str,
    repo: Path,
    *,
    before: Counter[str] | None = None,
) -> str:
    """按 fixture 声明提取本轮新增、位置正确且概念完整的唯一候选。"""
    scenario = (fixture.raw or {}).get("scenario") or {}
    source = (scenario.get("a") or {}).get("candidate_source")
    if source == "output":
        matches = _candidate_lines(output)
        nonempty = [line.strip() for line in output.splitlines() if line.strip()]
        first = nonempty[0] if nonempty else ""
        if not first.startswith(_CANDIDATE_MARKER):
            raise ValueError("普通任务候选必须位于首个非空输出行")
    elif source == "epic-cursor":
        baseline = before or Counter()
        current = Counter(_epic_candidate_lines(repo))
        matches = list((current - baseline).elements())
        if any(baseline[match] for match in matches):
            raise ValueError("Epic 候选不得重复既有规则")
    else:
        raise ValueError(f"尚不支持的 candidate_source: {source!r}")
    if len(matches) != 1:
        raise ValueError(f"本轮新增候选必须恰好一条，实际 {len(matches)} 条")
    candidate = matches[0]
    missing = [
        concept for concept in (scenario.get("candidate") or {}).get("required_concepts", [])
        if str(concept).lower() not in candidate.lower()
    ]
    if missing:
        raise ValueError(f"候选缺少 required concepts: {missing}")
    return candidate
