"""M2 autoresearch 护栏：收敛数学 + V_meta 分量 + provenance + 认知诚实机械校验。"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

EVAL_SKILL = Path(__file__).resolve().parents[1]
ROOT = EVAL_SKILL.parents[2]
SCRIPTS = EVAL_SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import optimize as opt              # noqa: E402
from _model import MEASURED, SOFT, tagged  # noqa: E402
from config import ExperimentConfig  # noqa: E402

EXPERIMENT = ROOT / "experiments/cs-code-review-001"
_TAG_RE = re.compile(r"\[(measured|soft|underpowered)")


# ---- 收敛数学 ----

def test_convergence_modes():
    assert opt.convergence(0.9, 0.9) == (True, "standard")
    assert opt.convergence(0.60, 0.85) == (True, "meta-focused")
    assert opt.convergence(0.9, 0.5) == (False, "not-converged")
    assert opt.convergence(0.5, 0.5) == (False, "not-converged")


# ---- V_instance tag 诚实 ----

def test_v_instance_tag_follows_constituents():
    measured = {"recall": tagged(0.8, MEASURED)}
    assert opt.v_instance(measured, {"recall": 1.0})["tag"] == MEASURED
    mixed = {"recall": tagged(0.8, MEASURED), "judge_quality": tagged(0.5, SOFT)}
    assert opt.v_instance(mixed, {"recall": 0.5, "judge_quality": 0.5})["tag"] == SOFT


# ---- V_meta 四分量 ----

def _synth_config(**kw):
    base = dict(name="t", skill_under_test="cs-code-review", variants=["baseline"],
                model_list=["m1", "m2"], k=5, harnesses=["mock"],
                scorers=["planted_defect"], fixture_classes=["planted-defect"])
    base.update(kw)
    return ExperimentConfig(**base)


def test_v_meta_statistical_power(tmp_path):
    (tmp_path / "fixtures/planted-defect").mkdir(parents=True)
    for i in range(8):
        (tmp_path / f"fixtures/planted-defect/p{i}.json").write_text("{}", encoding="utf-8")
    # k>=5 且 n>=8 → statistical_power pass
    _, comp = opt.v_meta_experiment(tmp_path, _synth_config(k=5), 5, [])
    assert comp["statistical_power"] is True
    # k<5 → fail
    _, comp2 = opt.v_meta_experiment(tmp_path, _synth_config(k=1), 1, [])
    assert comp2["statistical_power"] is False


def test_v_meta_confound_control():
    # 用 judge 但 judge_model 在被测 model_list → fail
    cfg_bad = _synth_config(scorers=["planted_defect", "llm_judge"], judge_model="m1")
    assert opt._confound_ok(cfg_bad) is False
    # judge_model 独立 → pass
    cfg_ok = _synth_config(scorers=["planted_defect", "llm_judge"], judge_model="judge-x")
    assert opt._confound_ok(cfg_ok) is True
    # 不用 judge → pass（无同源偏差）
    assert opt._confound_ok(_synth_config(scorers=["planted_defect"])) is True


def test_v_meta_oracle_calibration(tmp_path):
    (tmp_path / "fixtures/planted-defect").mkdir(parents=True)
    _, comp = opt.v_meta_experiment(tmp_path, _synth_config(), 5, [])
    assert comp["oracle_calibration"] is False
    (tmp_path / "calibration.md").write_text("x", encoding="utf-8")
    _, comp2 = opt.v_meta_experiment(tmp_path, _synth_config(), 5, [])
    assert comp2["oracle_calibration"] is True


# ---- provenance ----

def test_preregistration_uncommitted_fails(tmp_path):
    # tmp 里的 hypotheses.md 不在 git → 未冻结 → False
    (tmp_path / "hypotheses.md").write_text("H-x: r >= 0.8", encoding="utf-8")
    assert opt._preregistered(tmp_path) is False
    # 无 hypotheses.md → False
    assert opt._preregistered(tmp_path / "nope") is False


# ---- 认知诚实机械护栏（对生成的 iteration 产物）----

def _run_optimize_in_tmp(tmp_path):
    dst = tmp_path / "exp"
    shutil.copytree(EXPERIMENT, dst, ignore=shutil.ignore_patterns("artifacts", "iteration-*.md", "results.md"))
    opt.main(["--experiment", str(dst), "--max-iterations", "2"])
    return dst


_ASSIGN_RE = re.compile(r"V_(instance|meta_experiment)\s*=")     # 只查「赋值行」，不查 section 标题
_BARE_RE = re.compile(r"V_(instance|meta_experiment)\s*=\s*[0-9.]+\s*$")  # 数值结尾、无 tag


def test_iterations_all_numbers_tagged(tmp_path):
    dst = _run_optimize_in_tmp(tmp_path)
    iters = sorted(dst.glob("iteration-*.md"))
    assert iters, "应生成 iteration 文件"
    for path in iters:
        for line in path.read_text(encoding="utf-8").splitlines():
            if _ASSIGN_RE.search(line):
                assert _TAG_RE.search(line), f"{path.name} 赋值行缺 tag: {line}"


def test_no_bare_v_instance_decimal(tmp_path):
    dst = _run_optimize_in_tmp(tmp_path)
    for path in dst.glob("iteration-*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            assert not _BARE_RE.search(line), f"{path.name} 裸数值（缺 tag）: {line}"
