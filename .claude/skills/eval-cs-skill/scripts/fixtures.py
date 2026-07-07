#!/usr/bin/env python3
"""加载与校验 experiments/<name>/fixtures/<class>/*.json。"""

from __future__ import annotations

import json
from pathlib import Path

from _model import Fixture


def load_fixtures(experiment_dir: Path, classes: list[str]) -> list[Fixture]:
    out: list[Fixture] = []
    seen: set[str] = set()
    for cls in classes:
        cls_dir = experiment_dir / "fixtures" / cls
        if not cls_dir.is_dir():
            continue
        for path in sorted(cls_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_exp_dir"] = str(experiment_dir)  # scorer 需要实验目录定位 hidden_tests
            fixture = Fixture.from_dict(data)
            if fixture.id in seen:
                raise ValueError(f"重复 fixture id: {fixture.id} ({path})")
            seen.add(fixture.id)
            out.append(fixture)
    return out


def validate_fixture_dict(data: dict) -> list[str]:
    """返回问题列表，空=合规。供 tests 复用。"""
    problems: list[str] = []
    if "id" not in data:
        problems.append("缺 id")
    at = data.get("answerType")
    if at not in {"findings-recall", "dod-gate", "dimensions-judge", "routing-decision", "e2e-outcome"}:
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
            for key in ("seed", "bug_id", "issue_report", "hidden_tests"):
                if key not in scenario:
                    problems.append(f"e2e-outcome scenario 缺 {key!r}")
            if "hidden_tests" in scenario and not isinstance(scenario["hidden_tests"], list):
                problems.append("e2e-outcome scenario.hidden_tests 必须是 list")
        task = data.get("task") or {}
        if task.get("kind") != "e2e":
            problems.append("e2e-outcome task.kind 应为 'e2e'")
    if "task" not in data:
        problems.append("缺 task")
    return problems
