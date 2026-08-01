#!/usr/bin/env python3
"""learning-transfer paired oracle：lesson schema、任务结果与跨模型 verdict。"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any

import yaml
from yaml.nodes import MappingNode
from yaml.resolver import BaseResolver

from _model import MEASURED, SOFT, tagged
from .base import register


_BODY_FIELDS = ("规则：", "适用 / 不适用：", "证据：", "候选归宿：")
_FRONTMATTER_FIELDS = {"status", "scope", "date"}
_LESSON_STATUSES = {"observed", "validated", "retired"}
_CANDIDATE_HOMES = {
    "test",
    "checker",
    "attention",
    "project-doc",
    "adr",
    "codestable-eval",
}
_LESSON_PATH_RE = re.compile(
    r"\.codestable/lessons/"
    r"(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?P<slug>[a-z0-9-]{1,30})\.md"
)
_CONCRETE_EVIDENCE_RE = re.compile(
    r"(?:^|(?<=[\s，,（(]))"
    r"(?=[A-Za-z0-9_./-]*[A-Za-z_])"
    r"(?:\.{0,2}/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+"
    r"|(?<![A-Za-z0-9])(?:[A-Z][A-Z0-9]*-[A-Z0-9]+|#[1-9]\d*)\b"
)
_STRUCTURAL_ORACLES = (
    "a_ok",
    "a_mutation_ok",
    "candidate_unique",
    "lesson_schema_ok",
    "lesson_only_mutation",
    "prompt_equal",
    "isolation_ok",
    "lesson_transition_ok",
    "lesson_expectation_ok",
    "treatment_mutation_ok",
    "control_mutation_ok",
    "treatment_regression_ok",
    "control_regression_ok",
)


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def score_pair(pair: dict[str, Any]) -> dict[str, Any]:
    """把一个完整 paired record 转成不含主观判断的 measured scores。"""
    treatment = float(pair.get("treatment_hidden", 0.0))
    control = float(pair.get("control_hidden", 0.0))
    delta = treatment - control
    scores = {
        name: tagged(1 if pair.get(name) else 0, MEASURED)
        for name in _STRUCTURAL_ORACLES
    }
    scores.update({
        "treatment_hidden": tagged(treatment, MEASURED),
        "control_hidden": tagged(control, MEASURED),
        "paired_delta": tagged(delta, MEASURED),
        "paired_win": tagged(1 if delta > 0 else 0, MEASURED),
        "paired_loss": tagged(1 if delta < 0 else 0, MEASURED),
        "paired_tie": tagged(1 if delta == 0 else 0, MEASURED),
    })
    structural_ok = all(pair.get(name) is True for name in _STRUCTURAL_ORACLES)
    return {
        "scores": scores,
        "evidence": [],
        "status": "passed" if structural_ok else "failed",
    }


@register("learning_transfer", applies_to={"learning-transfer"})
def score_learning_transfer(_fixture, pair, _config=None, _root=None) -> dict[str, Any]:
    """registry adapter；sequence 传入完整 pair，而不是 HarnessResult。"""
    return score_pair(pair)


def _effect_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    treatment = [float(record.get("treatment_hidden", 0.0)) for record in records]
    control = [float(record.get("control_hidden", 0.0)) for record in records]
    deltas = [left - right for left, right in zip(treatment, control)]
    return {
        "pairs": len(records),
        "treatment_rate": round(mean(treatment), 4) if treatment else 0.0,
        "control_rate": round(mean(control), 4) if control else 0.0,
        "paired_delta": round(mean(deltas), 4) if deltas else 0.0,
        "wins": sum(delta > 0 for delta in deltas),
        "losses": sum(delta < 0 for delta in deltas),
        "ties": sum(delta == 0 for delta in deltas),
    }


def _power_assessment(positive: list[dict[str, Any]], guards: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    families = sorted({record.get("family") for record in positive if record.get("family")})
    required_skills = {"cs-feat", "cs-issue", "cs-refactor", "cs-epic"}
    if len(families) < 2:
        reasons.append("需要至少两个 model family")
    for family in families:
        family_positive = [record for record in positive if record.get("family") == family]
        if len(family_positive) < 20:
            reasons.append(f"{family} 正向完成 pair 少于 20")
        for skill in required_skills:
            repeats = {
                record.get("k_index") for record in family_positive
                if record.get("owning_skill") == skill
            }
            if len(repeats) < 5:
                reasons.append(f"{family}/{skill} 完成 repeat 少于 5")
        for guard_class in ("unrelated", "stale"):
            repeats = {
                record.get("k_index") for record in guards
                if record.get("family") == family and record.get("fixture_class") == guard_class
            }
            if len(repeats) < 5:
                reasons.append(f"{family}/{guard_class} guard 完成 repeat 少于 5")
    return {"ok": not reasons, "reasons": reasons}


def aggregate_pairs(
    records: list[dict[str, Any]],
    *,
    operational_errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """按 family 聚合正向迁移，并把 unrelated/stale guard 独立保留。"""
    operational_history = operational_errors or []
    completed = [record for record in records if record.get("state") == "completed"]
    deterministic_blockers = [
        record
        for record in records
        if record.get("state") not in {"completed", "retryable-error"}
    ]
    positive = [record for record in completed if record.get("fixture_class") == "positive"]
    guard_records = [
        record for record in completed
        if record.get("fixture_class") in {"unrelated", "stale"}
    ]
    families = {
        family: _effect_summary([record for record in positive if record.get("family") == family])
        for family in sorted({record.get("family") for record in positive if record.get("family")})
    }
    guards: dict[str, Any] = {}
    for guard_class in ("unrelated", "stale"):
        selected = [record for record in guard_records if record.get("fixture_class") == guard_class]
        guards[guard_class] = {
            "pairs": len(selected),
            "no_regression": all(
                float(record.get("treatment_hidden", 0.0)) >= float(record.get("control_hidden", 0.0))
                and record.get("treatment_regression_ok") is True
                and record.get("control_regression_ok") is True
                for record in selected
            ),
        }
        if guard_class == "stale":
            guards[guard_class]["retired_rate"] = (
                round(mean([1.0 if record.get("stale_retired") else 0.0 for record in selected]), 4)
                if selected else 0.0
            )
    attempt_counts = dict(Counter(str(record.get("state", "incomplete")) for record in records))
    structural_total = len(completed) * len(_STRUCTURAL_ORACLES)
    structural_passed = sum(
        record.get(name) is True
        for record in completed
        for name in _STRUCTURAL_ORACLES
    )
    phase_metrics = [
        phase
        for record in completed
        for phase in record.get("phase_metrics", [])
    ]
    cost_items = [
        phase.get("metrics", {}).get("cost_usd")
        for phase in phase_metrics
        if isinstance(phase.get("metrics", {}).get("cost_usd"), dict)
    ]
    cost_tag = (
        MEASURED
        if len(cost_items) == len(phase_metrics) and all(item.get("tag") == MEASURED for item in cost_items)
        else SOFT
    )
    return {
        "overall": _effect_summary(positive),
        "families": families,
        "guards": guards,
        "power": _power_assessment(positive, guard_records),
        "integrity": {
            "ok": structural_passed == structural_total and not deterministic_blockers,
            "passed": structural_passed,
            "total": structural_total,
            "blockers": len(deterministic_blockers),
        },
        "cost": {
            "invocation_count": len(phase_metrics),
            "cost_usd": tagged(round(sum(float(item.get("value", 0.0)) for item in cost_items), 6), cost_tag),
        },
        "operational_errors": {
            "attempts": len(operational_history),
            "resolved": sum(error.get("resolved") is True for error in operational_history),
            "unresolved": sum(error.get("resolved") is not True for error in operational_history),
        },
        "attempt_counts": attempt_counts,
    }


def transfer_verdict(aggregate: dict[str, Any]) -> dict[str, Any]:
    """按预注册复合门槛给出 learning-transfer 最终判定。"""
    reasons: list[str] = []
    overall = aggregate.get("overall") or {}
    delta = float(overall.get("paired_delta", 0.0))
    if delta < 0.25:
        reasons.append("总体 paired delta 低于 25pp")
    families = aggregate.get("families") or {}
    if len(families) < 2 or any(float(item.get("paired_delta", 0.0)) <= 0 for item in families.values()):
        reasons.append("至少一个 model family 未呈正向迁移")
    if int(overall.get("losses", 0)) > int(overall.get("wins", 0)):
        reasons.append("paired losses 多于 wins")
    guards = aggregate.get("guards") or {}
    for guard_class in ("unrelated", "stale"):
        guard = guards.get(guard_class) or {}
        if not guard.get("pairs") or guard.get("no_regression") is not True:
            reasons.append(f"{guard_class} guard 回退或缺失")
    if float((guards.get("stale") or {}).get("retired_rate", 0.0)) != 1.0:
        reasons.append("stale lesson 未 100% 退役")
    if (aggregate.get("integrity") or {}).get("ok") is not True:
        reasons.append("隔离、schema、mutation 或回归 oracle 未 100% 通过")
    operational = aggregate.get("operational_errors") or {}
    unresolved_operational = int(operational.get("unresolved", 0))
    powered = (aggregate.get("power") or {}).get("ok") is True and unresolved_operational == 0
    if not powered:
        reasons.append("统计功效不足")
    if unresolved_operational:
        reasons.append("存在未解决 operational error")
    accepted = not reasons
    direction = "CONFIRMED" if accepted else ("NULL" if delta < 0 else "REJECTED")
    return {
        "accepted": accepted,
        "verdict": {
            "direction": direction,
            "observed": delta,
            "threshold": 0.25,
            "confidence": "high" if powered else "underpowered",
        },
        "reasons": reasons,
    }


def _iso_date(value: Any) -> str:
    if type(value) is date:
        return value.isoformat()
    if not isinstance(value, str):
        raise ValueError("date must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("date must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ValueError("date must be an ISO date")
    return value


def _evidence_items(value: str) -> list[str]:
    items = [item.strip() for item in re.split(r"[；;]", value)]
    if not 1 <= len(items) <= 3 or any(not item for item in items):
        raise ValueError("evidence must contain 1-3 non-empty items")
    return items


def _evidence_content(value: str) -> str:
    """句末标点不属于 evidence item；追加分项时允许用分隔符替换它。"""
    return value[:-1] if value.endswith(("。", ".")) else value


def _parse_lesson_text(text: str) -> tuple[dict[str, Any], dict[str, str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("unterminated frontmatter") from exc

    frontmatter = "\n".join(lines[1:closing])
    metadata = yaml.load(frontmatter, Loader=_UniqueKeyLoader)
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    keys = set(metadata)
    if keys != _FRONTMATTER_FIELDS:
        missing = sorted(_FRONTMATTER_FIELDS - keys)
        extra = sorted(str(key) for key in keys - _FRONTMATTER_FIELDS)
        raise ValueError(f"frontmatter fields mismatch: missing={missing}, extra={extra}")
    status = metadata["status"]
    if not isinstance(status, str) or status not in _LESSON_STATUSES:
        raise ValueError("invalid status")
    scope = metadata["scope"]
    if not isinstance(scope, str) or not scope.strip() or scope != scope.strip():
        raise ValueError("scope must be a non-empty string")
    metadata["date"] = _iso_date(metadata["date"])

    body_lines = lines[closing + 1:]
    if len(body_lines) != len(_BODY_FIELDS):
        raise ValueError("body must contain exactly four field lines")
    fields: dict[str, str] = {}
    for line in body_lines:
        matches = [prefix for prefix in _BODY_FIELDS if line.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"unexpected body line: {line}")
        prefix = matches[0]
        if prefix in fields:
            raise ValueError(f"duplicate body field: {prefix}")
        value = line[len(prefix):]
        if not value or value != value.strip():
            raise ValueError(f"invalid body value: {prefix}")
        fields[prefix] = value
    if set(fields) != set(_BODY_FIELDS):
        raise ValueError("body fields mismatch")
    if fields["候选归宿："] not in _CANDIDATE_HOMES:
        raise ValueError("invalid candidate home")
    _evidence_items(fields["证据："])
    return metadata, fields


def lesson_status(text: str) -> str | None:
    """从 lesson frontmatter 机械读取 lifecycle status。"""
    try:
        metadata, _ = _parse_lesson_text(text)
    except (ValueError, yaml.YAMLError):
        return None
    status = metadata.get("status")
    return str(status) if status is not None else None


def validate_lesson_transition(before: str, after: str) -> dict[str, Any]:
    """验证 validated/retired 窄迁移不改写规则或 scope。"""
    try:
        before_meta, before_fields = _parse_lesson_text(before)
        after_meta, after_fields = _parse_lesson_text(after)
    except (ValueError, yaml.YAMLError) as exc:
        return {"ok": False, "errors": [str(exc)]}
    errors: list[str] = []
    transition = (before_meta.get("status"), after_meta.get("status"))
    if transition not in {
        ("observed", "validated"),
        ("observed", "retired"),
        ("validated", "retired"),
    }:
        errors.append("status")
    if {k: v for k, v in before_meta.items() if k != "status"} != {
        k: v for k, v in after_meta.items() if k != "status"
    }:
        errors.append("scope/date")
    for prefix in ("规则：", "适用 / 不适用：", "候选归宿："):
        if before_fields.get(prefix) != after_fields.get(prefix):
            errors.append(prefix.removesuffix("："))
    before_evidence = before_fields["证据："]
    after_evidence = after_fields["证据："]
    before_items = _evidence_items(before_evidence)
    after_items = _evidence_items(after_evidence)
    preserved_prefix = next(
        (
            prefix
            for prefix in (before_evidence, _evidence_content(before_evidence))
            if after_evidence.startswith(prefix)
            and after_evidence[len(prefix):len(prefix) + 1] in "；;"
        ),
        None,
    )
    suffix = after_evidence[len(preserved_prefix):] if preserved_prefix is not None else ""
    evidence_ok = (
        len(after_items) == len(before_items) + 1
        and [_evidence_content(item) for item in after_items[:-1]]
        == [_evidence_content(item) for item in before_items]
        and preserved_prefix is not None
        and len(suffix) > 1
        and suffix[0] in "；;"
        and _CONCRETE_EVIDENCE_RE.search(after_items[-1]) is not None
    )
    if not evidence_ok:
        errors.append("证据")
    new_evidence = after_items[-1] if len(after_items) > len(before_items) else ""
    if transition[1] == "retired" and not any(
        marker in new_evidence for marker in ("反证", "替代", "canonical")
    ):
        errors.append("退役原因")
    return {"ok": not errors, "errors": errors}


def _lesson_path_error(repo: Path, path: Path, relative: str) -> str | None:
    match = _LESSON_PATH_RE.fullmatch(relative)
    if match is None:
        return "lesson path must match .codestable/lessons/YYYY-MM-DD-{slug}.md"
    try:
        filename_date = date.fromisoformat(match.group("date"))
    except ValueError:
        return "lesson filename date must be valid"
    if filename_date.isoformat() != match.group("date"):
        return "lesson filename date must be valid"
    try:
        lexical = path.relative_to(repo)
        path.resolve().relative_to(repo.resolve())
    except ValueError:
        return "lesson path escapes repository"
    cursor = repo
    for part in lexical.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return "lesson path must not contain symlinks"
    return None


def validate_observed_lesson(
    repo: Path,
    required_concepts: list[str],
    paths: list[str] | None = None,
) -> dict[str, Any]:
    """机械验证一次 curation 生成的唯一 observed lesson。"""
    repo = repo.resolve()
    if paths is not None:
        candidates = [(str(relative), Path(str(relative))) for relative in paths]
        lesson_paths = [repo / path for _, path in candidates]
    else:
        lesson_paths = sorted((repo / ".codestable/lessons").glob("*.md"))
        candidates = [
            (path.relative_to(repo).as_posix(), path.relative_to(repo))
            for path in lesson_paths
        ]
    errors: list[str] = []
    if len(lesson_paths) != 1:
        return {"ok": False, "path": None, "errors": [f"expected one lesson, got {len(lesson_paths)}"]}
    path = lesson_paths[0]
    relative_text, relative_path = candidates[0]
    if relative_path.is_absolute():
        return {"ok": False, "path": None, "errors": ["lesson path must be relative"]}
    path_error = _lesson_path_error(repo, path, relative_text)
    if path_error:
        return {"ok": False, "path": None, "errors": [path_error]}
    try:
        text = path.read_text(encoding="utf-8")
        metadata, fields = _parse_lesson_text(text)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {"ok": False, "path": None, "errors": [str(exc)]}
    if metadata.get("status") != "observed":
        errors.append("status must be observed")
    filename_date = _LESSON_PATH_RE.fullmatch(relative_text).group("date")
    if metadata["date"] != filename_date:
        errors.append("frontmatter date must match filename date")
    lower = "\n".join(fields.values()).lower()
    for concept in required_concepts:
        if concept.lower() not in lower:
            errors.append(f"missing concept: {concept}")
    return {
        "ok": not errors,
        "path": relative_text,
        "errors": errors,
    }
