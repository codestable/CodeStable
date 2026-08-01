#!/usr/bin/env python3
"""加载与校验 experiments/<name>/fixtures/<class>/*.json。"""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

from _model import Fixture, is_safe_slug


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("~") or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _check_relative_paths(problems: list[str], label: str, values: object) -> None:
    if not isinstance(values, list):
        return
    for value in values:
        if not _safe_relative_path(value):
            problems.append(f"{label} 只允许仓库内相对路径: {value!r}")


def _allowlist_reaches_lessons(values: object) -> bool:
    return isinstance(values, list) and any(
        isinstance(value, str)
        and fnmatchcase(".codestable/lessons/2026-08-02-example.md", value)
        for value in values
    )


def load_fixtures(experiment_dir: Path, classes: list[str]) -> list[Fixture]:
    out: list[Fixture] = []
    seen: set[str] = set()
    for cls in classes:
        cls_dir = experiment_dir / "fixtures" / cls
        if not cls_dir.is_dir():
            continue
        for path in sorted(cls_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            problems = validate_fixture_dict(data)
            if problems:
                raise ValueError(f"fixture {path} 不合规: {'; '.join(problems)}")
            data["_exp_dir"] = str(experiment_dir)  # scorer 需要实验目录定位 hidden_tests
            fixture = Fixture.from_dict(data)
            if fixture.id in seen:
                raise ValueError(f"重复 fixture id: {fixture.id} ({path})")
            seen.add(fixture.id)
            out.append(fixture)
    return out


def resolve_experiment_asset(experiment_dir: Path, relative: str) -> Path:
    """解析 tracked experiment asset，并拒绝逃逸、目录与 symlink。"""
    if not _safe_relative_path(relative):
        raise ValueError(f"实验资产只允许仓库内相对路径: {relative!r}")
    base = experiment_dir.resolve()
    path = (base / relative).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"实验资产越过 experiment_dir: {relative!r}") from exc
    if not path.is_file() or (base / relative).is_symlink():
        raise ValueError(f"实验资产不存在、不是文件或为 symlink: {relative!r}")
    return path


def validate_learning_transfer_coverage(fixtures: list[Fixture]) -> list[str]:
    """验收 campaign 必须覆盖四 task skill 与 unrelated/stale guards。"""
    problems: list[str] = []
    learning = [fixture for fixture in fixtures if fixture.answer_type == "learning-transfer"]
    positive = [fixture for fixture in learning if fixture.raw["scenario"]["class"] == "positive"]
    skills = {(fixture.raw["scenario"].get("a") or {}).get("skill") for fixture in positive}
    expected = {"cs-feat", "cs-issue", "cs-refactor", "cs-epic"}
    if len(positive) != 4 or skills != expected:
        problems.append("四个 positive fixture 必须与四个 task skill 一一对应")
    classes = {fixture.raw["scenario"]["class"] for fixture in learning}
    if not {"unrelated", "stale"} <= classes:
        problems.append("learning-transfer 必须同时包含 unrelated 与 stale guard")
    return problems


def validate_fixture_dict(data: dict) -> list[str]:
    """返回问题列表，空=合规。供 tests 复用。"""
    problems: list[str] = []
    if "id" not in data:
        problems.append("缺 id")
    elif not is_safe_slug(data["id"]):
        problems.append("id 必须是小写连字符 slug（最多 64 字符）")
    at = data.get("answerType")
    if at not in {
        "findings-recall", "dod-gate", "dimensions-judge", "routing-decision", "e2e-outcome",
        "learning-transfer",
    }:
        problems.append(f"answerType 非法: {at!r}")
    if at == "findings-recall" and not data.get("answer"):
        problems.append("findings-recall 必须有非空 answer")
    if at == "dod-gate" and not data.get("checklist_path"):
        problems.append("dod-gate 必须有 checklist_path")
    if at == "routing-decision":
        expect = data.get("expect")
        if not isinstance(expect, dict) or "result_type" not in expect:
            problems.append("routing-decision 必须有 expect.result_type（机械比对的 oracle）")
    if at == "e2e-outcome":
        scenario = data.get("scenario")
        if not isinstance(scenario, dict):
            problems.append("e2e-outcome 必须有 scenario dict")
        else:
            # bug_id 可选：bug 修复场景用它定位 inject；feature 场景无 bug 注入
            for key in ("seed", "issue_report", "hidden_tests"):
                if key not in scenario:
                    problems.append(f"e2e-outcome scenario 缺 {key!r}")
            if "hidden_tests" in scenario and not isinstance(scenario["hidden_tests"], list):
                problems.append("e2e-outcome scenario.hidden_tests 必须是 list")
        task = data.get("task") or {}
        if task.get("kind") != "e2e":
            problems.append("e2e-outcome task.kind 应为 'e2e'")
    if at == "learning-transfer":
        scenario = data.get("scenario")
        if not isinstance(scenario, dict):
            problems.append("learning-transfer 必须有 scenario dict")
        else:
            if scenario.get("class") not in {"positive", "unrelated", "stale"}:
                problems.append("learning-transfer scenario.class 非法")
            if not scenario.get("seed"):
                problems.append("learning-transfer scenario 缺 'seed'")
            elif not is_safe_slug(scenario["seed"]):
                problems.append("learning-transfer seed 必须是小写连字符 slug")
            for phase in ("a", "candidate", "b", "preflight"):
                if not isinstance(scenario.get(phase), dict):
                    problems.append(f"learning-transfer scenario 缺 {phase!r} dict")
            a = scenario.get("a") or {}
            if a.get("skill") not in {"cs-feat", "cs-issue", "cs-refactor", "cs-epic"}:
                problems.append("learning-transfer a.skill 非法")
            if not a.get("request"):
                problems.append("learning-transfer a.request 不能为空")
            if a.get("candidate_source") not in {"output", "epic-cursor"}:
                problems.append("learning-transfer a.candidate_source 非法")
            if (a.get("skill") == "cs-epic") != (a.get("candidate_source") == "epic-cursor"):
                problems.append("cs-epic 必须从 Epic 游标取候选，其他 task skill 必须从输出取候选")
            if not isinstance(a.get("checks"), list):
                problems.append("learning-transfer a.checks 必须是 list")
            _check_relative_paths(problems, "learning-transfer a.checks", a.get("checks"))
            if not isinstance(a.get("allowed_paths"), list) or not a.get("allowed_paths"):
                problems.append("learning-transfer a.allowed_paths 必须是非空 list")
            _check_relative_paths(problems, "learning-transfer a.allowed_paths", a.get("allowed_paths"))
            if _allowlist_reaches_lessons(a.get("allowed_paths")):
                problems.append("learning-transfer a.allowed_paths 不得允许 lesson mutation")
            candidate = scenario.get("candidate") or {}
            if candidate.get("expected_home") != "lesson":
                problems.append("learning-transfer candidate.expected_home 必须是 lesson")
            concepts = candidate.get("required_concepts")
            if not isinstance(concepts, list) or not concepts:
                problems.append("learning-transfer candidate.required_concepts 必须是非空 list")
            elif (
                any(not isinstance(concept, str) or not concept.strip() for concept in concepts)
                or len({concept.strip().lower() for concept in concepts}) != len(concepts)
            ):
                problems.append("learning-transfer candidate.required_concepts 必须是唯一的非空字符串")
            b = scenario.get("b") or {}
            if b.get("skill") not in {"cs-feat", "cs-issue", "cs-refactor", "cs-epic"}:
                problems.append("learning-transfer b.skill 非法")
            if b.get("skill") != a.get("skill"):
                problems.append("learning-transfer A/B 必须由同一个 owning skill 执行")
            if not b.get("request"):
                problems.append("learning-transfer b.request 不能为空")
            if not isinstance(b.get("hidden_tests"), list) or not b.get("hidden_tests"):
                problems.append("learning-transfer b.hidden_tests 必须是非空 list")
            if not isinstance(b.get("regression_tests"), list) or not b.get("regression_tests"):
                problems.append("learning-transfer b.regression_tests 必须是非空 list")
            if not isinstance(b.get("allowed_paths"), list):
                problems.append("learning-transfer b.allowed_paths 必须是 list")
            _check_relative_paths(problems, "learning-transfer b.hidden_tests", b.get("hidden_tests"))
            _check_relative_paths(problems, "learning-transfer b.regression_tests", b.get("regression_tests"))
            _check_relative_paths(problems, "learning-transfer b.allowed_paths", b.get("allowed_paths"))
            if _allowlist_reaches_lessons(b.get("allowed_paths")):
                problems.append("learning-transfer b.allowed_paths 不得允许额外 lesson mutation")
            preflight = scenario.get("preflight") or {}
            for hook in ("naive_hook", "golden_hook"):
                if not preflight.get(hook):
                    problems.append(f"learning-transfer preflight 缺 {hook!r}")
                elif not _safe_relative_path(preflight[hook]):
                    problems.append(f"learning-transfer preflight.{hook} 只允许实验内相对路径")
            between = scenario.get("between_tasks")
            if isinstance(between, dict) and between.get("hook") and not _safe_relative_path(between["hook"]):
                problems.append("learning-transfer between_tasks.hook 只允许实验内相对路径")
            if scenario.get("class") == "stale" and not (
                isinstance(between, dict) and between.get("hook")
            ):
                problems.append("learning-transfer stale fixture 必须有 between_tasks.hook")
            if isinstance(between, dict) and between.get("hook"):
                if not isinstance(between.get("allowed_paths"), list) or not between.get("allowed_paths"):
                    problems.append("learning-transfer between_tasks.allowed_paths 必须是非空 list")
                _check_relative_paths(
                    problems,
                    "learning-transfer between_tasks.allowed_paths",
                    between.get("allowed_paths"),
                )
            expect = scenario.get("expect") or {}
            transition = expect.get("lesson_transition")
            expected_by_class = {
                "positive": "observed->validated",
                "unrelated": "unchanged-observed",
                "stale": "observed->retired",
            }
            if transition != expected_by_class.get(scenario.get("class")):
                problems.append("learning-transfer expect.lesson_transition 与 scenario.class 不一致")
        task = data.get("task") or {}
        if task.get("kind") != "learning-transfer":
            problems.append("learning-transfer task.kind 应为 'learning-transfer'")
    if "task" not in data:
        problems.append("缺 task")
    return problems
