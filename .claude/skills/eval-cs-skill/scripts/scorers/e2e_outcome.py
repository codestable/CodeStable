#!/usr/bin/env python3
"""e2e_outcome scorer：hidden test 通过率 + 回归 + 产物契约，全机械 [measured]。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from _model import MEASURED, tagged
from scorers.base import register


def _run_pytest(cwd: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        capture_output=True, text=True, cwd=str(cwd),
    )
    output = (result.stdout + result.stderr)[-2000:]
    return result.returncode, output


def _count_files_passing(cwd: Path, test_files: list[Path]) -> tuple[int, int, str]:
    """逐文件跑 pytest，返回 (通过数, 总数, 合并输出尾)。"""
    passed = 0
    outputs: list[str] = []
    for f in test_files:
        rc, out = _run_pytest(cwd, str(f), "-q")
        if rc == 0:
            passed += 1
        outputs.append(f"# {f.name}: {'PASS' if rc == 0 else 'FAIL'}\n{out[-400:]}")
    return passed, len(test_files), "\n".join(outputs)[-2000:]


@register("e2e_outcome", applies_to={"e2e-outcome"})
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    workdir = getattr(result, "workdir", None)
    if not workdir:
        return {
            "scores": {
                "hidden_pass": tagged(0.0, MEASURED, evidence="workdir=None"),
                "regression_pass": tagged(0.0, MEASURED, evidence="workdir=None"),
                "artifact_ok": tagged(0.0, MEASURED, evidence="workdir=None"),
                "e2e_ok": tagged(0.0, MEASURED, evidence="workdir=None"),
            },
            "evidence": [{"error": "result.workdir 为 None，无法打分"}],
            "status": "failed",
        }

    repo = Path(workdir)
    if not repo.is_dir():
        return {
            "scores": {
                "hidden_pass": tagged(0.0, MEASURED, evidence="repo missing"),
                "regression_pass": tagged(0.0, MEASURED, evidence="repo missing"),
                "artifact_ok": tagged(0.0, MEASURED, evidence="repo missing"),
                "e2e_ok": tagged(0.0, MEASURED, evidence="repo missing"),
            },
            "evidence": [{"error": f"repo 目录不存在: {repo}"}],
            "status": "failed",
        }

    scenario = (fixture.raw or {}).get("scenario") or {}
    hidden_rel_paths: list[str] = scenario.get("hidden_tests") or []
    exp_dir_str = (fixture.raw or {}).get("_exp_dir", "")
    exp_dir = Path(exp_dir_str) if exp_dir_str else None

    evidence_parts: list[Any] = []

    # --- a) hidden_pass ---
    hidden_dir = repo / "_hidden_tests"
    hidden_dir.mkdir(exist_ok=True)
    hidden_test_files: list[Path] = []
    for rel in hidden_rel_paths:
        src = (exp_dir / rel) if exp_dir else None
        if src and src.exists():
            dst = hidden_dir / src.name
            shutil.copy2(str(src), str(dst))
            hidden_test_files.append(dst)
    if hidden_test_files:
        h_pass, h_total, h_out = _count_files_passing(repo, hidden_test_files)
        hidden_pass_val = round(h_pass / h_total, 4)
        evidence_parts.append({"hidden_pytest": h_out})
    else:
        h_pass, h_total = 0, 0
        hidden_pass_val = 0.0
        evidence_parts.append({"hidden_pytest": "no hidden test files found"})

    # --- b) regression_pass ---
    tests_dir = repo / "tests"
    if tests_dir.is_dir():
        reg_rc, reg_out = _run_pytest(repo, "tests", "-q")
        regression_pass_val = 1.0 if reg_rc == 0 else 0.0
        evidence_parts.append({"regression_pytest": reg_out})
    else:
        regression_pass_val = 1.0  # 无 tests/ 视为无回归（不惩罚）
        evidence_parts.append({"regression_pytest": "no tests/ directory"})

    # --- c) artifact_ok ---
    issues_root = repo / ".codestable" / "issues"
    fix_note_found = False
    if issues_root.is_dir():
        for fix_note in issues_root.rglob("*fix-note*"):
            if fix_note.is_file():
                fix_note_found = True
                break
    artifact_ok_val = 1.0 if fix_note_found else 0.0
    evidence_parts.append({"artifact_ok": fix_note_found})

    # --- 合成 ---
    e2e_ok_val = round(
        hidden_pass_val * 0.6 + regression_pass_val * 0.3 + artifact_ok_val * 0.1, 4
    )
    status = "passed" if (h_pass == h_total and h_total > 0 and regression_pass_val == 1.0) else "failed"

    return {
        "scores": {
            "hidden_pass": tagged(hidden_pass_val, MEASURED, evidence=f"{h_pass}/{h_total} hidden tests"),
            "regression_pass": tagged(regression_pass_val, MEASURED),
            "artifact_ok": tagged(artifact_ok_val, MEASURED),
            "e2e_ok": tagged(e2e_ok_val, MEASURED, evidence="0.6*hidden+0.3*reg+0.1*artifact"),
        },
        "evidence": evidence_parts,
        "status": status,
    }
