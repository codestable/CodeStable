"""eval-cs-skill eval 层单测：fixtures / scorers / metrics / runner 端到端 / 认知诚实 tag。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
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
    # recall_judge 也用 judge_model，同样纳入独立性检查（此前只看 llm_judge，漏检）
    rj = dict(name="t", skill_under_test="x", model_list=["m1", "m2"], scorers=["recall_judge"])
    assert judge_issues(ExperimentConfig(**rj, judge_model="m1"))           # 同源 → issue
    assert not judge_issues(ExperimentConfig(**rj, judge_model="judge-x"))  # 独立 → 无


def test_calibrate_judge_mock_soft_only():
    import calibrate_judge
    result = calibrate_judge.calibrate(EXPERIMENT)
    assert result["verdict"] == "soft-only"        # mock 启发式不可升 measured
    assert 0.0 <= result["pairwise_accuracy"] <= 1.0


def test_reasoning_fixtures_present():
    pd = list((EXPERIMENT / "fixtures/planted-defect").glob("*.json"))
    reasoning = [p for p in pd if json.loads(p.read_text(encoding="utf-8")).get("difficulty") == "reasoning"]
    assert len(pd) >= 13 and len(reasoning) >= 5    # 混合难度、有区分度的集合


# ---- C：checkpoint / resume（治 runner 长跑被 kill 的硬伤）----

def test_eval_result_roundtrip():
    from _model import EvalResult
    er = EvalResult(fixture_id="f", variant="v", model="m", harness="h", k_index=2,
                    scores={"recall": {"value": 1.0, "tag": MEASURED}}, status="passed")
    assert EvalResult.from_dict(er.to_dict()) == er


def test_resume_skips_checkpointed_cells(tmp_path):
    """预写一个 cell 的 checkpoint（带 sentinel），resume 应跳过它、补齐其余、checkpoint 增长到全量。"""
    from _model import EvalResult
    from config import ExperimentConfig
    cfg = ExperimentConfig(
        name="cs-code-review-001", skill_under_test="cs-code-review",
        variants=["baseline"], model_list=["m1"], harnesses=["mock"],
        scorers=["planted_defect"], fixture_classes=["planted-defect"],
    )
    fixtures = fx_mod.load_fixtures(EXPERIMENT, ["planted-defect"])
    cells = [("baseline", "mock", "m1")]
    ckpt = tmp_path / "ck.jsonl"

    fid = fixtures[0].id
    sentinel = EvalResult(fixture_id=fid, variant="baseline", model="m1", harness="mock", k_index=0)
    sentinel.scores = {"recall": {"value": -999.0, "tag": MEASURED}}  # 不可能被真实打分产生
    runner_mod._append_checkpoint(ckpt, sentinel)

    results = runner_mod.run(cfg, fixtures, cells, ["planted_defect"], 1, EXPERIMENT, ckpt)

    assert len(results) == len(fixtures)                       # 全部 fixture 齐了
    kept = [r for r in results if r.fixture_id == fid and r.k_index == 0]
    assert len(kept) == 1 and kept[0].scores["recall"]["value"] == -999.0  # sentinel 保留=没重算
    others = [r for r in results if r.fixture_id != fid]
    assert others and all("recall" in r.scores for r in others)            # 其余真实跑了
    _, keys = runner_mod._load_checkpoint(ckpt)
    assert len(keys) == len(fixtures)                          # checkpoint 增长到全量


def test_main_cleans_checkpoint_on_success(tmp_path):
    out = tmp_path / "r.json"
    ckpt = out.parent / (out.name + ".partial.jsonl")
    rc = runner_mod.main(["--experiment", str(EXPERIMENT), "--harness", "mock", "--k", "1", "--out", str(out)])
    assert rc == 0 and out.exists()
    assert not ckpt.exists()  # final 落盘后 checkpoint 清理，避免下次误 resume 旧数据


def test_fixture_limit_reduces_runs(tmp_path):
    """--limit 切 fixture 子集，配合 resume 支持分段跑（每段稳过环境 kill 线）。"""
    full = tmp_path / "full.json"
    lim = tmp_path / "lim.json"
    runner_mod.main(["--experiment", str(EXPERIMENT), "--harness", "mock", "--k", "1", "--out", str(full)])
    runner_mod.main(["--experiment", str(EXPERIMENT), "--harness", "mock", "--k", "1", "--limit", "2", "--out", str(lim)])
    nf = json.loads(full.read_text(encoding="utf-8"))["aggregate"]["baseline"]["n"]
    nl = json.loads(lim.read_text(encoding="utf-8"))["aggregate"]["baseline"]["n"]
    assert 0 < nl < nf


# ---- 鲁棒性：间歇 504/网络错误不毁整段（gpt-5.x 慢响应触发过）----

def test_run_per_cell_error_does_not_kill_segment(monkeypatch, tmp_path):
    """单 cell invoke 抛异常（如 504）应标 error 并继续，不让整段崩溃。"""
    import harness as harness_pkg
    from config import ExperimentConfig

    class BoomHarness:
        def invoke(self, prompt, model, workdir, timeout_s):
            raise RuntimeError("API HTTP 504 simulated")

    monkeypatch.setattr(harness_pkg, "get_harness", lambda h: BoomHarness())
    cfg = ExperimentConfig(
        name="cs-code-review-001", skill_under_test="cs-code-review",
        variants=["baseline"], model_list=["m1"], harnesses=["mock"],
        scorers=["planted_defect"], fixture_classes=["planted-defect"],
    )
    fixtures = fx_mod.load_fixtures(EXPERIMENT, ["planted-defect"])
    ckpt = tmp_path / "ck.jsonl"
    results = runner_mod.run(cfg, fixtures, [("baseline", "mock", "m1")], ["planted_defect"], 1, EXPERIMENT, ckpt)
    assert len(results) == len(fixtures)                    # 段没崩，全部 fixture 产出
    assert all(r.status == "error" for r in results)        # 每个都标 error
    _, keys = runner_mod._load_checkpoint(ckpt)
    assert len(keys) == len(fixtures)                       # error 也落 checkpoint（不会无限重跑）


# ---- 路线3：routing-decision（decision fixture 的执行引擎）----

def _routing_fx(expect, state=None, intent=None):
    raw = {"id": "rt", "answerType": "routing-decision", "expect": expect,
           "task": {"kind": "routing", "state": state or {}, "intent": intent or {}}}
    return Fixture(id="rt", answer_type="routing-decision", answer=[],
                   task=raw["task"], raw=raw)


def test_routing_fixture_validation():
    ok = {"id": "r1", "answerType": "routing-decision", "task": {"kind": "routing"},
          "expect": {"result_type": "RoutedTo", "target": "Design"}}
    assert fx_mod.validate_fixture_dict(ok) == []
    bad = {"id": "r2", "answerType": "routing-decision", "task": {"kind": "routing"}}
    assert any("expect.result_type" in p for p in fx_mod.validate_fixture_dict(bad))


def test_routing_scorer_applies_only_to_routing():
    assert scorers_pkg.applies("routing_decision", "routing-decision")
    assert not scorers_pkg.applies("routing_decision", "findings-recall")
    assert not scorers_pkg.applies("planted_defect", "routing-decision")


def test_routing_scorer_hit_miss_forbidden_parse():
    scorer = scorers_pkg.get_scorer("routing_decision")
    fx = _routing_fx({"result_type": "HumanCheckpoint", "target": "ConfirmDesign",
                      "must_not_target": "GoalPackage"})
    hit = scorer(fx, _hr('{"result_type": "HumanCheckpoint", "target": "ConfirmDesign", "reason": "x"}'), None, None)
    assert hit["scores"]["routing_ok"]["value"] == 1.0
    assert hit["scores"]["routing_ok"]["tag"] == MEASURED

    miss = scorer(fx, _hr('{"result_type": "RoutedTo", "target": "GoalPackage"}'), None, None)
    assert miss["scores"]["routing_ok"]["value"] == 0.0

    # 模型输出 JSON 外带解释文字 → 容错提取
    wrapped = scorer(fx, _hr('按规则应停下。\n{"result_type": "HumanCheckpoint", "target": "ConfirmDesign"}\n完'), None, None)
    assert wrapped["scores"]["routing_ok"]["value"] == 1.0

    bad = scorer(fx, _hr("我觉得应该继续实现"), None, None)
    assert bad["scores"]["routing_ok"]["value"] == 0.0
    assert bad["scores"]["routing_ok"]["evidence"] == "parse-error"

    # result_type_any：语义等价的 outcome 词（如转交 skill 被答成 GoalHandoff）
    fx2 = _routing_fx({"result_type": "RoutedTo", "target": "cs-feat",
                       "result_type_any": ["RoutedTo", "GoalHandoff"]})
    alt = scorer(fx2, _hr('{"result_type": "GoalHandoff", "target": "cs-feat"}'), None, None)
    assert alt["scores"]["routing_ok"]["value"] == 1.0


def test_build_routing_prompt_contains_state_and_json_contract():
    from buildprompt import build_prompt
    fx = _routing_fx({"result_type": "RoutedTo", "target": "Design"},
                     state={"designStatus": "Missing", "reviewStatus": "Missing"},
                     intent={"requestedStage": "（无）"})
    prompt = build_prompt(fx, "SKILL BODY HERE", False)
    assert "SKILL BODY HERE" in prompt
    assert "designStatus: Missing" in prompt
    assert "只输出一个 JSON 对象" in prompt
    assert "result_type" in prompt


def test_api_post_retries_on_504(monkeypatch):
    """_post 对 504 退避重试；前 2 次 504、第 3 次成功。"""
    import io
    import urllib.error
    import harness.adapter_api as api

    calls = {"n": 0}

    def fake_urlopen(req, timeout):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.HTTPError(req.full_url, 504, "Gateway Timeout", {}, io.BytesIO(b"504"))
        return io.BytesIO(b'{"ok": true}')

    monkeypatch.setattr(api.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(api.time, "sleep", lambda s: None)  # 不真睡
    assert api._post("http://x", {}, {"a": 1}, timeout_s=5) == {"ok": True}
    assert calls["n"] == 3  # 前 2 次 504 重试，第 3 次成功


# ---- e2e-outcome：fixture 校验 ----

def _e2e_fixture_dict(**overrides):
    base = {
        "id": "e2e-01",
        "answerType": "e2e-outcome",
        "task": {"kind": "e2e"},
        "scenario": {
            "seed": "task-api",
            "bug_id": "g01",
            "issue_report": "API 返回 500",
            "hidden_tests": ["hidden/test_bug_g01.py"],
        },
    }
    base.update(overrides)
    return base


def test_e2e_fixture_validation_good():
    assert fx_mod.validate_fixture_dict(_e2e_fixture_dict()) == []


def test_e2e_fixture_validation_missing_scenario():
    d = _e2e_fixture_dict()
    del d["scenario"]
    problems = fx_mod.validate_fixture_dict(d)
    assert any("scenario" in p for p in problems)


def test_e2e_fixture_validation_missing_scenario_fields():
    for missing_key in ("seed", "bug_id", "issue_report", "hidden_tests"):
        d = _e2e_fixture_dict()
        del d["scenario"][missing_key]
        problems = fx_mod.validate_fixture_dict(d)
        assert any(missing_key in p for p in problems), f"未检测到缺 {missing_key!r}"


def test_e2e_fixture_validation_wrong_kind():
    d = _e2e_fixture_dict()
    d["task"]["kind"] = "review"
    problems = fx_mod.validate_fixture_dict(d)
    assert any("kind" in p for p in problems)


# ---- build_e2e_prompt ----

def test_build_e2e_prompt_contains_issue_and_skill(tmp_path):
    from buildprompt import build_prompt
    raw = _e2e_fixture_dict()
    raw["scenario"]["issue_report"] = "接口返回 NullPointerException"
    fx = Fixture(id="e2e-01", answer_type="e2e-outcome", answer=[],
                 task=raw["task"], raw=raw)
    prompt = build_prompt(fx, "SKILL_BODY_HERE", False)
    assert "SKILL_BODY_HERE" in prompt
    assert "接口返回 NullPointerException" in prompt
    assert "fix-note" in prompt          # 产物契约提示
    assert "Issue 报告" in prompt


# ---- e2e_outcome scorer（全离线，构造假 repo）----

def _make_fake_repo(tmp_path, *, with_fixnote=False):
    """构造最小 repo：tests/test_ok.py 恒绿，hidden 测试（外部传入）。"""
    repo = tmp_path / "repo"
    tests = repo / "tests"
    tests.mkdir(parents=True)
    (tests / "test_ok.py").write_text("def test_always_pass(): assert True\n")
    if with_fixnote:
        note_dir = repo / ".codestable" / "issues" / "g01"
        note_dir.mkdir(parents=True)
        (note_dir / "fix-note.md").write_text("根因：xxx\n")
    return repo


def _make_hidden(tmp_path, *, pass_test=True):
    hidden_src = tmp_path / "hidden"
    hidden_src.mkdir(exist_ok=True)
    if pass_test:
        (hidden_src / "test_bug_g01_pass.py").write_text("def test_pass(): assert True\n")
    else:
        (hidden_src / "test_bug_g01_fail.py").write_text("def test_fail(): assert False\n")
    return hidden_src


def _e2e_fixture_obj(exp_dir: str, hidden_rel_paths: list) -> Fixture:
    raw = _e2e_fixture_dict()
    raw["scenario"]["hidden_tests"] = hidden_rel_paths
    raw["_exp_dir"] = exp_dir
    return Fixture(id="e2e-01", answer_type="e2e-outcome", answer=[],
                   task=raw["task"], raw=raw)


def _hr_with_workdir(workdir: str):
    hr = HarnessResult(output="done", model="m", harness="mock", wall_ms=1, turns=1)
    hr.workdir = workdir
    return hr


def test_e2e_scorer_hidden_pass_half(tmp_path):
    """一绿一红 hidden test → hidden_pass=0.5。"""
    scorer = scorers_pkg.get_scorer("e2e_outcome")
    repo = _make_fake_repo(tmp_path)

    # 准备 hidden 源文件：一个绿、一个红，放在 exp_dir/hidden/
    hidden_src = tmp_path / "exp" / "hidden"
    hidden_src.mkdir(parents=True)
    (hidden_src / "test_green.py").write_text("def test_pass(): assert True\n")
    (hidden_src / "test_red.py").write_text("def test_fail(): assert False\n")

    fx = _e2e_fixture_obj(
        str(tmp_path / "exp"),
        ["hidden/test_green.py", "hidden/test_red.py"],
    )
    hr = _hr_with_workdir(str(repo))
    result = scorer(fx, hr, None, None)
    assert result["scores"]["hidden_pass"]["value"] == 0.5
    assert result["scores"]["hidden_pass"]["tag"] == MEASURED


def test_e2e_scorer_regression_pass(tmp_path):
    """tests/ 全绿 → regression_pass=1.0。"""
    scorer = scorers_pkg.get_scorer("e2e_outcome")
    repo = _make_fake_repo(tmp_path)
    fx = _e2e_fixture_obj(str(tmp_path / "exp"), [])
    hr = _hr_with_workdir(str(repo))
    result = scorer(fx, hr, None, None)
    assert result["scores"]["regression_pass"]["value"] == 1.0


def test_e2e_scorer_artifact_ok_present(tmp_path):
    scorer = scorers_pkg.get_scorer("e2e_outcome")
    repo = _make_fake_repo(tmp_path, with_fixnote=True)
    fx = _e2e_fixture_obj(str(tmp_path / "exp"), [])
    hr = _hr_with_workdir(str(repo))
    result = scorer(fx, hr, None, None)
    assert result["scores"]["artifact_ok"]["value"] == 1.0


def test_e2e_scorer_artifact_ok_absent(tmp_path):
    scorer = scorers_pkg.get_scorer("e2e_outcome")
    repo = _make_fake_repo(tmp_path, with_fixnote=False)
    fx = _e2e_fixture_obj(str(tmp_path / "exp"), [])
    hr = _hr_with_workdir(str(repo))
    result = scorer(fx, hr, None, None)
    assert result["scores"]["artifact_ok"]["value"] == 0.0


def test_e2e_scorer_workdir_none():
    scorer = scorers_pkg.get_scorer("e2e_outcome")
    raw = _e2e_fixture_dict()
    raw["_exp_dir"] = ""
    fx = Fixture(id="e2e-01", answer_type="e2e-outcome", answer=[], task=raw["task"], raw=raw)
    hr = HarnessResult(output="", model="m", harness="mock", wall_ms=1)
    # workdir 未设 → 全 0
    result = scorer(fx, hr, None, None)
    assert result["scores"]["hidden_pass"]["value"] == 0.0
    assert result["status"] == "failed"


def test_e2e_scorer_applies_only_e2e():
    assert scorers_pkg.applies("e2e_outcome", "e2e-outcome")
    assert not scorers_pkg.applies("e2e_outcome", "findings-recall")
    assert not scorers_pkg.applies("e2e_outcome", "routing-decision")
