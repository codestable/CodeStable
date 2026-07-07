"""cs-skill-lab eval 层单测：fixtures / scorers / metrics / runner 端到端 / 认知诚实 tag。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/cs-skill-lab/scripts"
sys.path.insert(0, str(SCRIPTS))

import fixtures as fx_mod            # noqa: E402
import metrics as metrics_mod       # noqa: E402
import runner as runner_mod         # noqa: E402
import scorers as scorers_pkg       # noqa: E402
from _model import Fixture, HarnessResult, MEASURED, SOFT  # noqa: E402

EXPERIMENT = ROOT / "experiments/cs-code-review-001"


# ---- fixtures 校验 ----

def test_fixture_validation_good():
    data = {"id": "x", "answerType": "findings-recall", "answer": ["a"], "task": {"kind": "review"}}
    assert fx_mod.validate_fixture_dict(data) == []


def test_fixture_validation_bad():
    problems = fx_mod.validate_fixture_dict({"id": "x", "answerType": "bogus"})
    assert any("answerType" in p for p in problems)
    assert any("task" in p for p in problems)


def test_real_fixtures_all_valid():
    for path in EXPERIMENT.glob("fixtures/**/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert fx_mod.validate_fixture_dict(data) == [], f"{path} 不合规"


def test_at_least_8_planted_defects():
    n = len(list((EXPERIMENT / "fixtures/planted-defect").glob("*.json")))
    assert n >= 8, "统计功效要求每类 n>=8"


# ---- planted_defect scorer ----

def _fx(answer, kind="review", answer_type="findings-recall", **task):
    return Fixture(id="t", answer_type=answer_type, answer=answer, task={"kind": kind, **task})


def _hr(output):
    return HarnessResult(output=output, model="m", harness="mock", wall_ms=1, turns=1)


def test_planted_defect_recall_hit_and_miss():
    scorer = scorers_pkg.get_scorer("planted_defect")
    hit = scorer(_fx(["SQL injection via SELECT query"]), _hr("- SQL injection in SELECT query"), None, None)
    assert hit["scores"]["recall"]["value"] == 1.0
    assert hit["scores"]["recall"]["tag"] == MEASURED
    miss = scorer(_fx(["race condition in scheduler"]), _hr("looks fine"), None, None)
    assert miss["scores"]["recall"]["value"] == 0.0


def test_scorer_applicability():
    assert scorers_pkg.applies("planted_defect", "findings-recall")
    assert not scorers_pkg.applies("planted_defect", "dod-gate")
    assert scorers_pkg.applies("llm_judge", "dod-gate")  # 空适用集=适用所有


# ---- llm_judge（离线 heuristic，soft）----

def test_llm_judge_offline_soft():
    scorer = scorers_pkg.get_scorer("llm_judge")
    out = scorer(_fx(["x"]), _hr("## Findings\n- [f.py:1] bug"), None, ROOT)
    assert out["scores"]["judge_compliance"]["tag"] == SOFT
    assert out["scores"]["judge_quality"]["tag"] == SOFT
    assert 0.0 <= out["scores"]["judge_quality"]["value"] <= 1.0


def test_recall_judge_token_fallback_offline():
    # 无 judge_model → recall_judge 直接走 token 回退，确定性、不发 api；tag 恒 soft
    scorer = scorers_pkg.get_scorer("recall_judge")
    hit = scorer(_fx(["SQL injection via SELECT query"]), _hr("- SQL injection in SELECT query"), None, None)
    assert hit["scores"]["recall_judge"]["value"] == 1.0
    assert hit["scores"]["recall_judge"]["tag"] == SOFT
    assert "token" in hit["evidence"][0]["source"]
    miss = scorer(_fx(["race condition in scheduler"]), _hr("looks fine"), None, None)
    assert miss["scores"]["recall_judge"]["value"] == 0.0


# ---- dod_gate（合成 checklist）----

def test_dod_gate_pass_and_fail(tmp_path):
    scorer = scorers_pkg.get_scorer("dod_gate")
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"commands": [{"id": "C1", "command": "true", "core": True}]}), encoding="utf-8")
    fx = Fixture(id="g", answer_type="dod-gate", checklist_path=str(ok), task={"kind": "review"})
    assert scorer(fx, _hr(""), None, tmp_path)["scores"]["dod_pass"]["value"] == 1.0

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"commands": [{"id": "C1", "command": "false", "core": True}]}), encoding="utf-8")
    fx2 = Fixture(id="g2", answer_type="dod-gate", checklist_path=str(bad), task={"kind": "review"})
    assert scorer(fx2, _hr(""), None, tmp_path)["scores"]["dod_pass"]["value"] == 0.0


# ---- metrics tag ----

def test_metrics_tags_mock():
    hr = HarnessResult(output="x", model="mock-model", harness="mock", wall_ms=5, turns=1,
                       usage={"input_tokens": 10, "output_tokens": 3, "cost_usd": 0.0, "source": "mock-estimate"})
    m = metrics_mod.capture(hr, prompt="hello world")
    assert m["wall_ms"]["tag"] == MEASURED
    assert m["turns"]["tag"] == MEASURED
    assert m["input_tokens"]["tag"] == SOFT   # mock-estimate 非真实 usage


# ---- runner 端到端（mock，离线）----

def test_runner_end_to_end(tmp_path):
    out = tmp_path / "results.json"
    rc = runner_mod.main(["--experiment", str(EXPERIMENT), "--harness", "mock", "--k", "1", "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    agg = data["aggregate"]["baseline"]
    assert agg["scores"]["recall"]["tag"] == MEASURED
    # recall_judge 是 soft（离线走 token 回退），聚合后绝不能被标成 measured（认知诚实）
    assert agg["scores"]["recall_judge"]["tag"] == SOFT
    assert agg["n"] >= 10


def test_dry_run_budget_block():
    # 人造超预算：给一个 budget=0 的临时 config 不便，改用真实 config 的 dry-run 应在预算内
    rc = runner_mod.main(["--experiment", str(EXPERIMENT), "--harness", "mock", "--dry-run"])
    assert rc == 0


# ---- Phase 2：多 harness × 多 model 矩阵（自举底座）----

def test_all_adapters_registered():
    import harness as harness_pkg
    names = set(harness_pkg.available())
    # 离线 + 4 类执行目标适配器都应注册（import 时不依赖外部 CLI）
    assert {"mock", "mock-weak", "claude-headless", "codex-cli", "paseo", "api"} <= names


def test_matrix_cross_harness_and_model():
    import argparse
    from statistics import mean as _mean
    from config import ExperimentConfig
    cfg = ExperimentConfig(
        name="cs-code-review-001", skill_under_test="cs-code-review",
        variants=["baseline"], model_list=["m1", "m2"],
        harnesses=["mock", "mock-weak"], scorers=["planted_defect"],
        fixture_classes=["planted-defect"],
    )
    fixtures = fx_mod.load_fixtures(EXPERIMENT, ["planted-defect"])
    args = argparse.Namespace(variant=None, harness=None, model=None)
    cells = runner_mod.build_matrix(cfg, args)
    assert len(cells) == 4  # 1 variant × 2 harness × 2 model
    results = runner_mod.run(cfg, fixtures, cells, ["planted_defect"], 1)

    by_harness: dict[str, list[float]] = {}
    for r in results:
        by_harness.setdefault(r.harness, []).append(r.scores["recall"]["value"])
    # 跨 harness 差异真实可测：强 harness 召回 > 弱 harness
    assert _mean(by_harness["mock"]) > _mean(by_harness["mock-weak"])
    # 两个 model 都被执行
    assert {r.model for r in results} == {"m1", "m2"}


# ---- Phase 3：成本护栏阻断 ----

def _tmp_experiment(tmp_path, budget, model):
    exp = tmp_path / "exp-budget"
    (exp / "fixtures/planted-defect").mkdir(parents=True)
    (exp / "config.json").write_text(json.dumps({
        "name": "exp-budget", "skill_under_test": "cs-code-review",
        "variants": ["baseline"], "model_list": [model], "k": 1,
        "harnesses": ["mock"], "scorers": ["planted_defect"],
        "fixture_classes": ["planted-defect"], "budget_usd": budget,
    }), encoding="utf-8")
    (exp / "fixtures/planted-defect/pd-x.json").write_text(json.dumps({
        "id": "pd-x", "answerType": "findings-recall", "answer": ["eval injection"],
        "task": {"kind": "review", "diff": "+eval(payload)"},
    }), encoding="utf-8")
    return exp


def test_budget_blocks_without_confirm(tmp_path):
    exp = _tmp_experiment(tmp_path, budget=0.0, model="claude-opus")  # opus 计价>0，预算0
    assert runner_mod.main(["--experiment", str(exp), "--out", str(tmp_path / "r.json")]) == 3
    # --confirm 放行（mock harness 离线执行）
    assert runner_mod.main(["--experiment", str(exp), "--confirm", "--out", str(tmp_path / "r.json")]) == 0


# ---- judge oracle 独立性 + 校准 ----

def test_judge_independence_issues():
    from config import ExperimentConfig, judge_issues
    base = dict(name="t", skill_under_test="cs-code-review", model_list=["m1", "m2"], scorers=["planted_defect", "llm_judge"])
    assert judge_issues(ExperimentConfig(**base, judge_model="m1"))          # 同源 → 有 issue
    assert not judge_issues(ExperimentConfig(**base, judge_model="judge-x"))  # 独立 → 无
    assert judge_issues(ExperimentConfig(**base, judge_model=None))           # 未设 → 有 issue
    # 不用 judge → 无所谓
    assert not judge_issues(ExperimentConfig(name="t", skill_under_test="x", scorers=["planted_defect"]))


def test_calibrate_judge_mock_soft_only():
    import calibrate_judge
    result = calibrate_judge.calibrate(EXPERIMENT)
    assert result["verdict"] == "soft-only"        # mock 启发式不可升 measured
    assert 0.0 <= result["pairwise_accuracy"] <= 1.0


def test_reasoning_fixtures_present():
    pd = list((EXPERIMENT / "fixtures/planted-defect").glob("*.json"))
    reasoning = [p for p in pd if json.loads(p.read_text(encoding="utf-8")).get("difficulty") == "reasoning"]
    assert len(pd) >= 13 and len(reasoning) >= 5    # 混合难度、有区分度的集合
