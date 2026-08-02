"""eval-cs-skill eval 层单测：fixtures / scorers / metrics / runner 端到端 / 认知诚实 tag。"""

from __future__ import annotations

import json
import sys
from argparse import Namespace
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
                     state={"designStatus": "Missing", "designReviewStatus": "ReviewMissing"},
                     intent={"requestedStage": "（无）"})
    prompt = build_prompt(fx, "SKILL BODY HERE", False)
    assert "SKILL BODY HERE" in prompt
    assert "designStatus: Missing" in prompt
    assert "designReviewStatus: ReviewMissing" in prompt
    assert "只输出一个 JSON 对象" in prompt
    assert "result_type" in prompt
    assert "DispatchGoalDriver" in prompt
    assert "Awaiting" in prompt
    assert "ReportDriver" not in prompt


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
    for missing_key in ("seed", "issue_report", "hidden_tests"):
        d = _e2e_fixture_dict()
        del d["scenario"][missing_key]
        problems = fx_mod.validate_fixture_dict(d)
        assert any(missing_key in p for p in problems), f"未检测到缺 {missing_key!r}"
    # bug_id 可选（feature 场景无 bug 注入），缺失不报问题
    d = _e2e_fixture_dict()
    del d["scenario"]["bug_id"]
    assert fx_mod.validate_fixture_dict(d) == []


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
    assert "用户请求" in prompt   # feature/issue 通用的中性标题
    # P0 L2 教训：共享模板不得含过程要求（fix-note/跑回归），否则泄题给无 skill 对照组；
    # 过程契约由 skill 文本自身规定（见 cs-issue-e2e-001/results.md 方法学缺陷节）
    assert "fix-note" not in prompt
    assert "pytest" not in prompt


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


# ---- learning-transfer sequence ----

def test_learning_targets_bind_each_model_to_one_harness() -> None:
    from config import ExperimentConfig

    config = ExperimentConfig(
        name="learning-transfer",
        skill_under_test="cs-feat",
        execution_mode="learning-transfer",
        model_targets=[
            {
                "id": "claude-haiku",
                "family": "claude",
                "harness": "claude-headless",
                "model": "claude-haiku-4-5",
            },
            {
                "id": "codex-terra",
                "family": "codex",
                "harness": "codex-cli",
                "model": "gpt-5.6-terra",
            },
        ],
    )

    cells = runner_mod.build_matrix(
        config,
        Namespace(variant=None, harness=None, model=None),
    )

    assert cells == [
        ("baseline", "claude-headless", "claude-haiku-4-5"),
        ("baseline", "codex-cli", "gpt-5.6-terra"),
    ]


@pytest.mark.parametrize(
    "overrides,cli",
    [
        ({"variants": ["candidate"]}, []),
        ({"scorers": ["planted_defect"]}, []),
        ({}, ["--scorer", "planted_defect"]),
    ],
)
def test_learning_transfer_runner_fixes_baseline_and_scorer(
    monkeypatch, tmp_path, overrides, cli,
) -> None:
    from config import ExperimentConfig

    values = {
        "name": "learning-contract",
        "skill_under_test": "cs-feat",
        "execution_mode": "learning-transfer",
        "variants": ["baseline"],
        "scorers": ["learning_transfer"],
        "fixture_classes": ["positive"],
        "model_targets": [{
            "id": "mock-target",
            "family": "mock-family",
            "harness": "mock",
            "model": "mock-model",
        }],
    }
    values.update(overrides)
    monkeypatch.setattr(runner_mod, "load_config", lambda _path: ExperimentConfig(**values))
    monkeypatch.setattr(runner_mod, "load_fixtures", lambda *_args: [])

    assert runner_mod.main([
        "--experiment", str(tmp_path), "--dry-run", *cli,
    ]) == 2


def _learning_fixture_dict() -> dict:
    return {
        "id": "lt-feat-01",
        "answerType": "learning-transfer",
        "task": {"kind": "learning-transfer"},
        "scenario": {
            "class": "positive",
            "seed": "learning-lab",
            "a": {
                "skill": "cs-feat",
                "request": "实现第一条选择路径",
                "candidate_source": "output",
                "checks": ["checks/a.py"],
                "allowed_paths": ["post-a.txt", ".codestable/work/**"],
            },
            "candidate": {
                "expected_home": "lesson",
                "required_concepts": ["empty collection", "sibling behavior"],
            },
            "b": {
                "skill": "cs-feat",
                "request": "实现第二条选择路径",
                "hidden_tests": ["hidden/feat.py"],
                "regression_tests": ["regression/feat.py"],
                "allowed_paths": ["learning_lab/notes.py", ".codestable/work/**"],
            },
            "preflight": {
                "naive_hook": "preflight/feat-naive.py",
                "golden_hook": "preflight/feat-golden.py",
            },
            "expect": {
                "lesson_transition": "observed->validated",
            },
        },
    }


def test_learning_transfer_fixture_validation_accepts_complete_positive_scenario() -> None:
    fixture = _learning_fixture_dict()

    assert fx_mod.validate_fixture_dict(fixture) == []


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (
            lambda fixture: fixture["scenario"]["a"].update(
                {"allowed_paths": [".codestable/**"]}
            ),
            "a.allowed_paths 不得允许 lesson mutation",
        ),
        (
            lambda fixture: fixture["scenario"]["b"].update(
                {"skill": "cs-refactor"}
            ),
            "A/B 必须由同一个 owning skill",
        ),
        (
            lambda fixture: fixture["scenario"]["candidate"].update(
                {"required_concepts": []}
            ),
            "required_concepts 必须是非空 list",
        ),
    ],
)
def test_learning_transfer_fixture_rejects_confounding_contracts(
    mutation, expected,
) -> None:
    fixture = _learning_fixture_dict()
    mutation(fixture)

    assert any(expected in problem for problem in fx_mod.validate_fixture_dict(fixture))


def test_learning_transfer_fixture_rejects_paths_outside_the_experiment_or_repo() -> None:
    fixture = _learning_fixture_dict()
    fixture["scenario"]["b"]["allowed_paths"] = ["../outside.py"]

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("相对路径" in problem for problem in problems)


def test_learning_transfer_fixture_rejects_unsafe_ids_and_seed_paths() -> None:
    fixture = _learning_fixture_dict()
    fixture["id"] = "../../escape"
    fixture["scenario"]["seed"] = "../outside"

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("id" in problem and "slug" in problem for problem in problems)
    assert any("seed" in problem and "slug" in problem for problem in problems)


def test_learning_transfer_fixture_requires_regression_oracles() -> None:
    fixture = _learning_fixture_dict()
    del fixture["scenario"]["b"]["regression_tests"]

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("regression_tests" in problem for problem in problems)


def test_learning_transfer_fixture_requires_a_mutation_allowlist() -> None:
    fixture = _learning_fixture_dict()
    del fixture["scenario"]["a"]["allowed_paths"]

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("a.allowed_paths" in problem for problem in problems)


def test_learning_transfer_fixture_requires_explicit_lesson_transition() -> None:
    fixture = _learning_fixture_dict()
    del fixture["scenario"]["expect"]

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("lesson_transition" in problem for problem in problems)


def test_learning_transfer_stale_fixture_requires_hook_allowlist() -> None:
    fixture = _learning_fixture_dict()
    fixture["scenario"]["class"] = "stale"
    fixture["scenario"]["expect"]["lesson_transition"] = "observed->retired"
    fixture["scenario"]["between_tasks"] = {"hook": "hooks/stale.py"}

    problems = fx_mod.validate_fixture_dict(fixture)

    assert any("between_tasks.allowed_paths" in problem for problem in problems)


def test_claude_harness_disables_session_persistence(monkeypatch, tmp_path) -> None:
    import subprocess
    import harness.adapter_claude as adapter_claude

    observed: dict[str, list[str]] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"result": "done", "num_turns": 1}),
            stderr="",
        )

    monkeypatch.setattr(
        adapter_claude.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"claude", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_claude.subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross-provider")

    adapter_claude.ClaudeHarness().invoke("task", "claude-haiku-4-5", tmp_path, 30)

    assert observed["command"][0] == "/usr/bin/sandbox-exec"
    profile_index = observed["command"].index("-p")
    profile = observed["command"][profile_index + 1]
    assert "(allow default)" in profile
    assert "(deny file-read*" in profile
    assert "(deny file-write*" in profile
    assert str(tmp_path.resolve()) in profile
    assert "--no-session-persistence" in observed["command"]
    assert "--safe-mode" in observed["command"]
    permission_index = observed["command"].index("--permission-mode")
    assert observed["command"][permission_index + 1] == "bypassPermissions"
    assert "OPENAI_API_KEY" not in observed["env"]


def test_codex_harness_runs_ephemerally(monkeypatch, tmp_path) -> None:
    import subprocess
    import harness.adapter_codex as adapter_codex

    observed: dict[str, list[str]] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(
        adapter_codex.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"codex", "sandbox-exec"} else None,
    )
    monkeypatch.setattr(adapter_codex.subprocess, "run", fake_run)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-cross-provider")

    adapter_codex.CodexHarness().invoke("task", "gpt-5.6-terra", tmp_path, 30)

    assert observed["command"][0] == "/usr/bin/sandbox-exec"
    profile = observed["command"][observed["command"].index("-p") + 1]
    assert "(deny file-read*" in profile
    assert "(deny file-write*" in profile
    assert str(tmp_path.resolve()) in profile
    assert "--ephemeral" in observed["command"]
    assert "--json" in observed["command"]
    assert "--ignore-user-config" in observed["command"]
    assert "--ignore-rules" in observed["command"]
    sandbox_index = observed["command"].index("--sandbox")
    assert observed["command"][sandbox_index + 1] == "danger-full-access"
    assert "ANTHROPIC_API_KEY" not in observed["env"]


def test_codex_harness_parses_jsonl_usage_as_measured_tokens() -> None:
    import harness.adapter_codex as adapter_codex

    output, usage = adapter_codex._parse("\n".join([
        json.dumps({"type": "thread.started", "thread_id": "session-secret"}),
        json.dumps({
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "done"},
        }),
        json.dumps({
            "type": "turn.completed",
            "usage": {"input_tokens": 120, "cached_input_tokens": 20, "output_tokens": 30},
        }),
    ]))

    assert output == "done"
    assert usage == {
        "input_tokens": 120,
        "output_tokens": 30,
        "source": "codex-json",
    }
    captured = metrics_mod.capture(HarnessResult(
        output=output,
        model="gpt-5.6-terra",
        harness="codex-cli",
        wall_ms=1,
        usage=usage,
    ), prompt="task")
    assert captured["input_tokens"]["tag"] == MEASURED
    assert captured["output_tokens"]["tag"] == MEASURED
    assert captured["cost_usd"]["tag"] == SOFT


def test_learning_transfer_b_prompt_does_not_leak_the_candidate() -> None:
    from buildprompt import build_sequence_task_prompt

    fixture = Fixture.from_dict(_learning_fixture_dict())

    prompt = build_sequence_task_prompt(fixture, "B SKILL SNAPSHOT", phase="b")

    assert "B SKILL SNAPSHOT" in prompt
    assert "实现第二条选择路径" in prompt
    assert "empty collection" not in prompt
    assert "sibling behavior" not in prompt
    assert "晶化候选" not in prompt
    assert "treatment" not in prompt
    assert "control" not in prompt


def test_learning_transfer_extracts_one_candidate_from_ordinary_task_output(tmp_path) -> None:
    from sequence import extract_candidate

    fixture = Fixture.from_dict(_learning_fixture_dict())
    output = (
        "晶化候选：修改选择接口前先核对同域 empty collection 与 sibling behavior。\n"
        "完成实现和验证。\n证据：tests。"
    )

    candidate = extract_candidate(fixture, output, tmp_path)

    assert candidate == "修改选择接口前先核对同域 empty collection 与 sibling behavior。"


def test_learning_transfer_extracts_epic_candidate_from_existing_cursor(tmp_path) -> None:
    from sequence import extract_candidate

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["a"]["skill"] = "cs-epic"
    fixture_dict["scenario"]["a"]["candidate_source"] = "epic-cursor"
    fixture_dict["scenario"]["candidate"]["required_concepts"] = ["rollback", "fixture"]
    cursor = tmp_path / ".codestable/work/epic-learning.md"
    cursor.parent.mkdir(parents=True)
    cursor.write_text(
        "## 临时决策与证据\n- 晶化候选：迁移子项开工前先核对 rollback fixture。\n",
        encoding="utf-8",
    )

    candidate = extract_candidate(Fixture.from_dict(fixture_dict), "不得展示候选", tmp_path)

    assert candidate == "迁移子项开工前先核对 rollback fixture。"


def test_learning_transfer_curation_prompt_carries_exact_authorized_candidate() -> None:
    from buildprompt import build_curation_prompt

    fixture = Fixture.from_dict(_learning_fixture_dict())

    prompt = build_curation_prompt(
        fixture,
        "CS-KEEP SNAPSHOT",
        "修改选择接口前先核对同域空集合语义。",
        "A checks passed: 2/2",
    )

    assert "CS-KEEP SNAPSHOT" in prompt
    assert "修改选择接口前先核对同域空集合语义。" in prompt
    assert "A checks passed: 2/2" in prompt
    assert "显式授权" in prompt
    assert "记录" in prompt
    assert "lesson 类归宿" in prompt
    assert "不得修改业务代码" in prompt


def test_learning_transfer_repo_copy_has_identical_content_manifest(tmp_path) -> None:
    from e2e_env import copy_repo, repo_manifest

    source = tmp_path / "source"
    (source / "learning_lab").mkdir(parents=True)
    (source / "learning_lab/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git/index").write_text("volatile", encoding="utf-8")

    treatment = copy_repo(source, tmp_path / "treatment")
    control = copy_repo(source, tmp_path / "control")

    assert repo_manifest(treatment) == repo_manifest(control)
    assert repo_manifest(treatment) == {
        "learning_lab/module.py": repo_manifest(source)["learning_lab/module.py"]
    }


def test_learning_transfer_curation_allows_only_lesson_mutation(tmp_path) -> None:
    from e2e_env import changed_paths, paths_match_allowlist, repo_manifest

    repo = tmp_path / "repo"
    (repo / "learning_lab").mkdir(parents=True)
    (repo / "learning_lab/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    before = repo_manifest(repo)
    lesson = repo / ".codestable/lessons/2026-08-02-selection.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text("---\nstatus: observed\n---\n规则：x\n", encoding="utf-8")

    lesson_changes = changed_paths(before, repo_manifest(repo))

    assert paths_match_allowlist(lesson_changes, [".codestable/lessons/**"])

    (repo / "learning_lab/module.py").write_text("VALUE = 2\n", encoding="utf-8")
    code_changes = changed_paths(before, repo_manifest(repo))

    assert not paths_match_allowlist(code_changes, [".codestable/lessons/**"])


def test_learning_transfer_lesson_oracle_requires_observed_schema(tmp_path) -> None:
    from scorers.learning_transfer import validate_observed_lesson

    lesson = tmp_path / ".codestable/lessons/2026-08-02-selection.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text(
        """---
status: observed
scope: selection interfaces
date: 2026-08-02
---
规则：修改选择接口前先核对同域 empty collection 语义。
适用 / 不适用：适用于 sibling behavior；有项目文档 owner 时停止。
证据：tests/test_selection.py。
候选归宿：project-doc
""",
        encoding="utf-8",
    )

    result = validate_observed_lesson(
        tmp_path,
        required_concepts=["empty collection", "sibling behavior"],
    )

    assert result["ok"] is True
    assert result["path"] == ".codestable/lessons/2026-08-02-selection.md"


def test_learning_transfer_hidden_checks_are_measured_per_file(tmp_path) -> None:
    from sequence import _run_check_files

    repo = tmp_path / "repo"
    repo.mkdir()
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    (hidden / "test_green.py").write_text("def test_green(): assert True\n", encoding="utf-8")
    (hidden / "test_red.py").write_text("def test_red(): assert False\n", encoding="utf-8")

    result = _run_check_files(repo, [hidden / "test_green.py", hidden / "test_red.py"])

    assert result["passed"] == 1
    assert result["total"] == 2
    assert result["rate"] == 0.5


def test_learning_transfer_checkpoint_key_includes_phase() -> None:
    from sequence import phase_key

    a_key = phase_key("claude-haiku", "lt-feat-01", 2, "a")
    b_key = phase_key("claude-haiku", "lt-feat-01", 2, "b-treatment")

    assert a_key == "claude-haiku|lt-feat-01|2|a"
    assert b_key == "claude-haiku|lt-feat-01|2|b-treatment"
    assert a_key != b_key


def test_learning_transfer_checkpoint_excludes_half_pairs(tmp_path) -> None:
    from sequence import append_checkpoint, load_completed_pairs

    checkpoint = tmp_path / "sequence.partial.jsonl"
    base = {"target_id": "claude-haiku", "fixture_id": "lt-feat-01", "k_index": 0}
    for phase in ("a", "curation", "b-treatment", "b-control"):
        append_checkpoint(checkpoint, {**base, "phase": phase, "status": "passed"})

    assert load_completed_pairs(checkpoint) == []

    pair = {**base, "phase": "score", "status": "passed", "pair": {"treatment_ok": 1, "control_ok": 0}}
    append_checkpoint(checkpoint, pair)

    assert load_completed_pairs(checkpoint) == [pair["pair"]]


def test_learning_transfer_alternates_paired_branch_order() -> None:
    from sequence import branch_order

    assert branch_order(0) == ("treatment", "control")
    assert branch_order(1) == ("control", "treatment")
    assert branch_order(2) == ("treatment", "control")


def test_learning_transfer_dry_run_counts_all_pair_invocations() -> None:
    from config import ExperimentConfig
    from sequence import dry_run_sequence

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["between_tasks"] = {
        "hook": "hooks/stale.py",
        "allowed_paths": ["facts/version.txt"],
    }
    config = ExperimentConfig(
        name="learning-transfer",
        skill_under_test="cs-feat",
        execution_mode="learning-transfer",
        model_targets=[{
            "id": "claude-haiku",
            "family": "claude",
            "harness": "claude-headless",
            "model": "claude-haiku-4-5",
        }],
    )

    estimate = dry_run_sequence(
        config,
        [Fixture.from_dict(fixture_dict)],
        k=3,
        root=ROOT,
    )

    assert estimate["invocation_count"] == 12
    assert estimate["phase_invocations"] == {
        "a": 3,
        "curation": 3,
        "b-treatment": 3,
        "b-control": 3,
    }
    assert estimate["hook_runs"] == 6
    assert estimate["est_total_usd"] > 0


def test_learning_transfer_run_pair_uses_only_lesson_as_treatment(tmp_path) -> None:
    from _model import ExecutionTarget
    from sequence import run_pair

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["a"]["checks"] = ["checks/a.py"]
    fixture_dict["scenario"]["b"]["hidden_tests"] = ["hidden/b.py"]
    fixture_dict["scenario"]["b"]["allowed_paths"] = ["learning_lab/result.txt"]
    fixture_dict["scenario"]["between_tasks"] = {
        "hook": "hooks/between.py",
        "allowed_paths": ["facts/version.txt"],
    }
    fixture = Fixture.from_dict(fixture_dict)
    experiment = tmp_path / "experiment"
    (experiment / "checks").mkdir(parents=True)
    (experiment / "hidden").mkdir()
    (experiment / "regression").mkdir()
    (experiment / "hooks").mkdir()
    (experiment / "checks/a.py").write_text(
        "from pathlib import Path\n\ndef test_a(): assert Path('post-a.txt').exists()\n",
        encoding="utf-8",
    )
    (experiment / "hidden/b.py").write_text(
        "from pathlib import Path\n\ndef test_b():\n"
        "    assert Path('learning_lab/result.txt').read_text() == 'correct\\n'\n"
        "    assert Path('facts/version.txt').read_text() == 'v2\\n'\n",
        encoding="utf-8",
    )
    (experiment / "hooks/between.py").write_text(
        "from pathlib import Path\nimport sys\n"
        "repo = Path(sys.argv[1])\n(repo / 'facts').mkdir(exist_ok=True)\n"
        "(repo / 'facts/version.txt').write_text('v2\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (experiment / "regression/feat.py").write_text(
        "from pathlib import Path\n\ndef test_existing(): assert Path('post-a.txt').exists()\n",
        encoding="utf-8",
    )
    seed = tmp_path / "seed"
    (seed / "learning_lab").mkdir(parents=True)
    (seed / "learning_lab/__init__.py").write_text("", encoding="utf-8")

    class FakeLearningHarness:
        name = "fake-learning"

        def __init__(self) -> None:
            self.calls: list[tuple[str, Path]] = []

        def invoke(self, prompt, model, workdir, timeout_s):
            self.calls.append((prompt, workdir))
            if "实现第一条选择路径" in prompt:
                (workdir / "post-a.txt").write_text("passed\n", encoding="utf-8")
                output = "晶化候选：修改选择接口前先核对同域 empty collection 与 sibling behavior。"
            elif "请记录为 observed lesson" in prompt:
                lesson = workdir / ".codestable/lessons/2026-08-02-selection.md"
                lesson.parent.mkdir(parents=True)
                lesson.write_text(
                    "---\nstatus: observed\nscope: selection\ndate: 2026-08-02\n---\n"
                    "规则：核对 empty collection。\n"
                    "适用 / 不适用：适用于 sibling behavior。\n"
                    "证据：post-a.txt。\n候选归宿：project-doc\n",
                    encoding="utf-8",
                )
                output = "recorded"
            else:
                lesson = workdir / ".codestable/lessons/2026-08-02-selection.md"
                learned = lesson.exists()
                if learned:
                    text = lesson.read_text(encoding="utf-8")
                    lesson.write_text(
                        text.replace("status: observed", "status: validated").replace(
                            "证据：post-a.txt。",
                            "证据：post-a.txt；learning_lab/result.txt。",
                        ),
                        encoding="utf-8",
                    )
                (workdir / "learning_lab/result.txt").write_text(
                    "correct\n" if learned else "wrong\n",
                    encoding="utf-8",
                )
                output = "done"
            return HarnessResult(
                output=output,
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    harness = FakeLearningHarness()
    phase_events: list[dict] = []
    pair = run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake",
            family="fake",
            harness=harness.name,
            model="mock-model",
        ),
        k_index=0,
        seed_repo=seed,
        experiment_dir=experiment,
        root=ROOT,
        run_root=tmp_path / "run",
        harness=harness,
        phase_callback=phase_events.append,
    )

    assert len(harness.calls) == 4
    assert pair["a_ok"] is True
    assert pair["a_mutation_ok"] is True
    assert pair["candidate_unique"] is True
    assert pair["lesson_schema_ok"] is True
    assert pair["lesson_only_mutation"] is True
    assert pair["prompt_equal"] is True
    assert pair["hook_ok"] is True
    assert pair["lesson_transition_ok"] is True
    assert pair["lesson_expectation_ok"] is True
    assert pair["lesson_status"] == "validated"
    assert pair["stale_retired"] is None
    assert pair["treatment_regression_ok"] is True
    assert pair["control_regression_ok"] is True
    assert pair["treatment_ok"] is True
    assert pair["control_ok"] is False
    assert harness.calls[2][0] == harness.calls[3][0]
    assert [item["phase"] for item in pair["phase_metrics"]] == [
        "a",
        "curation",
        "b-treatment",
        "b-control",
    ]
    assert all("wall_ms" in item["metrics"] for item in pair["phase_metrics"])
    assert [
        event["phase"]
        for event in phase_events
        if event.get("status") != "invocation-started"
    ] == [
        "a",
        "curation",
        "hook",
        "b-treatment",
        "b-control",
    ]
    for phase in ("a", "curation", "b-treatment", "b-control"):
        invocation_events = [event for event in phase_events if event["phase"] == phase]
        assert [event["status"] for event in invocation_events] == [
            "invocation-started",
            "invocation-complete",
        ]
        assert invocation_events[0]["invocation_id"] == invocation_events[1]["invocation_id"]
    assert all("output" not in event and "candidate" not in event for event in phase_events)


def test_learning_transfer_a_without_unique_candidate_is_terminal_pipeline_failure(tmp_path) -> None:
    from _model import ExecutionTarget
    from sequence import run_pair

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["a"]["checks"] = []
    fixture = Fixture.from_dict(fixture_dict)
    seed = tmp_path / "seed"
    seed.mkdir()

    class MissingCandidateHarness:
        name = "missing-candidate"

        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, prompt, model, workdir, timeout_s):
            self.calls += 1
            return HarnessResult(
                output="任务完成，但没有形成候选。",
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    harness = MissingCandidateHarness()
    pair = run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake", family="fake", harness=harness.name, model="mock-model",
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
    assert pair["a_ok"] is True
    assert pair["candidate_unique"] is False


def test_learning_transfer_invalid_curation_stops_before_b(tmp_path) -> None:
    from _model import ExecutionTarget
    from sequence import run_pair

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["a"]["checks"] = []
    fixture = Fixture.from_dict(fixture_dict)
    seed = tmp_path / "seed"
    seed.mkdir()

    class InvalidCurationHarness:
        name = "invalid-curation"

        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, prompt, model, workdir, timeout_s):
            self.calls += 1
            if self.calls == 1:
                output = "晶化候选：核对 empty collection 与 sibling behavior。"
            else:
                lesson = workdir / ".codestable/lessons/bad.md"
                lesson.parent.mkdir(parents=True)
                lesson.write_text("无 schema\n", encoding="utf-8")
                output = "recorded"
            return HarnessResult(
                output=output,
                model=model,
                harness=self.name,
                wall_ms=1,
            )

    harness = InvalidCurationHarness()
    pair = run_pair(
        fixture=fixture,
        target=ExecutionTarget(
            id="fake", family="fake", harness=harness.name, model="mock-model",
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
    assert pair["candidate_unique"] is True
    assert pair["lesson_schema_ok"] is False


def test_learning_transfer_lesson_transition_allows_status_and_evidence_only() -> None:
    from scorers.learning_transfer import validate_lesson_transition

    before = """---
status: observed
scope: selection
date: 2026-08-02
---
规则：先核对空集合语义。
适用 / 不适用：选择接口；已有文档 owner 时停止。
证据：tests/test_first.py。
候选归宿：project-doc
"""
    validated = before.replace("status: observed", "status: validated").replace(
        "证据：tests/test_first.py。",
        "证据：tests/test_first.py；tests/test_second.py。",
    )
    rewritten = validated.replace("规则：先核对空集合语义。", "规则：所有接口都返回空集合。")

    assert validate_lesson_transition(before, validated)["ok"] is True
    result = validate_lesson_transition(before, rewritten)
    assert result["ok"] is False
    assert "规则" in result["errors"]


def test_learning_transfer_lesson_transition_allows_narrow_retirement() -> None:
    from scorers.learning_transfer import validate_lesson_transition

    before = """---
status: validated
scope: selection
date: 2026-08-02
---
规则：先核对空集合语义。
适用 / 不适用：选择接口；已有文档 owner 时停止。
证据：tests/test_first.py。
候选归宿：project-doc
"""
    retired = before.replace("status: validated", "status: retired").replace(
        "证据：tests/test_first.py。",
        "证据：tests/test_first.py；hooks/stale.py 反证，替代为 docs/selection.md。",
    )

    result = validate_lesson_transition(before, retired)

    assert result["ok"] is True


def test_learning_transfer_between_hook_keeps_both_branches_in_sync(tmp_path) -> None:
    from e2e_env import copy_repo
    from sequence import apply_between_tasks_hook

    source = tmp_path / "source"
    (source / "facts").mkdir(parents=True)
    (source / "facts/version.txt").write_text("v1\n", encoding="utf-8")
    treatment = copy_repo(source, tmp_path / "treatment")
    control = copy_repo(source, tmp_path / "control")
    lesson = treatment / ".codestable/lessons/2026-08-02-selection.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text("---\nstatus: observed\n---\n规则：v1。\n", encoding="utf-8")
    hook = tmp_path / "stale.py"
    hook.write_text(
        "from pathlib import Path\nimport sys\n"
        "repo = Path(sys.argv[1])\n"
        "(repo / 'facts/version.txt').write_text('v2\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = apply_between_tasks_hook(hook, treatment, control, ["facts/version.txt"])

    assert result["ok"] is True
    assert result["runs"] == 2
    assert lesson.read_text(encoding="utf-8") == "---\nstatus: observed\n---\n规则：v1。\n"
    assert (treatment / "facts/version.txt").read_text(encoding="utf-8") == "v2\n"
    assert (control / "facts/version.txt").read_text(encoding="utf-8") == "v2\n"


def test_learning_transfer_scores_a_positive_pair_with_measured_oracles() -> None:
    from scorers.learning_transfer import score_pair

    result = score_pair({
        "fixture_class": "positive",
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
        "treatment_hidden": 1.0,
        "control_hidden": 0.0,
    })

    assert result["status"] == "passed"
    assert result["scores"]["paired_delta"] == {"value": 1.0, "tag": MEASURED}
    assert result["scores"]["paired_win"]["value"] == 1
    assert result["scores"]["paired_loss"]["value"] == 0
    assert result["scores"]["paired_tie"]["value"] == 0
    assert all(score["tag"] == MEASURED for score in result["scores"].values())


def test_learning_transfer_aggregate_sums_phase_cost_instead_of_averaging() -> None:
    from scorers.learning_transfer import aggregate_pairs

    records = []
    for k_index in range(2):
        pair = _completed_learning_pair(
            family="claude",
            fixture_id="feat",
            owning_skill="cs-feat",
            k_index=k_index,
        )
        pair["phase_metrics"] = [
            {"phase": phase, "metrics": {"cost_usd": {"value": 0.125, "tag": MEASURED}}}
            for phase in ("a", "curation", "b-treatment", "b-control")
        ]
        records.append(pair)

    aggregate = aggregate_pairs(records)

    assert aggregate["cost"] == {
        "invocation_count": 8,
        "cost_usd": {"value": 1.0, "tag": MEASURED},
    }


def _completed_learning_pair(
    *,
    family: str,
    fixture_id: str,
    owning_skill: str,
    k_index: int,
    fixture_class: str = "positive",
    treatment: float = 1.0,
    control: float = 0.0,
) -> dict:
    pair = {
        "state": "completed",
        "family": family,
        "fixture_id": fixture_id,
        "owning_skill": owning_skill,
        "k_index": k_index,
        "fixture_class": fixture_class,
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
        "treatment_hidden": treatment,
        "control_hidden": control,
    }
    if fixture_class == "stale":
        pair["stale_retired"] = True
    return pair


def test_learning_transfer_aggregate_keeps_family_effects_and_guards_separate() -> None:
    from scorers.learning_transfer import aggregate_pairs

    records = [
        _completed_learning_pair(
            family="claude", fixture_id="feat", owning_skill="cs-feat", k_index=0,
        ),
        _completed_learning_pair(
            family="codex", fixture_id="feat", owning_skill="cs-feat", k_index=0,
            treatment=0.5,
        ),
        _completed_learning_pair(
            family="claude", fixture_id="unrelated", owning_skill="cs-feat", k_index=0,
            fixture_class="unrelated", treatment=1.0, control=1.0,
        ),
    ]

    aggregate = aggregate_pairs(records)

    assert aggregate["overall"]["paired_delta"] == 0.75
    assert aggregate["families"]["claude"]["paired_delta"] == 1.0
    assert aggregate["families"]["codex"]["paired_delta"] == 0.5
    assert aggregate["overall"]["wins"] == 2
    assert aggregate["guards"]["unrelated"]["pairs"] == 1
    assert aggregate["power"]["ok"] is False


def _powered_learning_records(treatment: float = 1.0, control: float = 0.0) -> list[dict]:
    records = []
    skills = ("cs-feat", "cs-issue", "cs-refactor", "cs-epic")
    for family in ("claude", "codex"):
        for skill in skills:
            for k_index in range(5):
                records.append(_completed_learning_pair(
                    family=family,
                    fixture_id=skill,
                    owning_skill=skill,
                    k_index=k_index,
                    treatment=treatment,
                    control=control,
                ))
        for guard_class in ("unrelated", "stale"):
            for k_index in range(5):
                records.append(_completed_learning_pair(
                    family=family,
                    fixture_id=guard_class,
                    owning_skill="cs-feat",
                    k_index=k_index,
                    fixture_class=guard_class,
                    treatment=1.0,
                    control=1.0,
                ))
    return records


def test_learning_transfer_power_requires_two_families_four_skills_and_k5() -> None:
    from scorers.learning_transfer import aggregate_pairs

    records = _powered_learning_records()

    assert aggregate_pairs(records)["power"]["ok"] is True

    missing_repeat = [
        record for record in records
        if not (
            record["family"] == "codex"
            and record["owning_skill"] == "cs-epic"
            and record["fixture_class"] == "positive"
            and record["k_index"] == 4
        )
    ]
    assert aggregate_pairs(missing_repeat)["power"]["ok"] is False


def test_learning_transfer_verdict_confirms_at_the_25pp_boundary() -> None:
    from scorers.learning_transfer import aggregate_pairs, transfer_verdict

    aggregate = aggregate_pairs(_powered_learning_records(treatment=0.75, control=0.5))

    result = transfer_verdict(aggregate)

    assert result["accepted"] is True
    assert result["verdict"] == {
        "direction": "CONFIRMED",
        "observed": 0.25,
        "threshold": 0.25,
        "confidence": "high",
    }
    assert result["reasons"] == []


def test_resolved_operational_error_is_reported_without_poisoning_acceptance() -> None:
    from scorers.learning_transfer import aggregate_pairs, transfer_verdict

    aggregate = aggregate_pairs(
        _powered_learning_records(treatment=0.75, control=0.5),
        operational_errors=[{
            "target_id": "claude",
            "fixture_id": "cs-feat",
            "k_index": 0,
            "state": "retryable-error",
            "error": "RetryableSequenceError",
            "resolved": True,
        }],
    )

    assert aggregate["integrity"]["ok"] is True
    assert aggregate["operational_errors"] == {
        "attempts": 1,
        "resolved": 1,
        "unresolved": 0,
    }
    assert transfer_verdict(aggregate)["accepted"] is True


def test_unresolved_operational_error_is_underpowered_not_structural_corruption() -> None:
    from scorers.learning_transfer import aggregate_pairs, transfer_verdict

    records = _powered_learning_records(treatment=0.75, control=0.5)
    missing = records.pop()
    operational = {
        "target_id": missing["family"],
        "fixture_id": missing["fixture_id"],
        "k_index": missing["k_index"],
        "state": "retryable-error",
        "error": "RetryableSequenceError",
        "resolved": False,
    }
    aggregate = aggregate_pairs(
        [*records, {key: value for key, value in operational.items() if key != "resolved"}],
        operational_errors=[operational],
    )
    result = transfer_verdict(aggregate)

    assert aggregate["integrity"]["ok"] is True
    assert aggregate["operational_errors"]["unresolved"] == 1
    assert result["accepted"] is False
    assert result["verdict"]["confidence"] == "underpowered"
    assert "存在未解决 operational error" in result["reasons"]


@pytest.mark.parametrize("state", ["pipeline-failed", "pipeline-error", "fixture-invalid"])
def test_deterministic_failure_states_block_structural_integrity(state: str) -> None:
    from scorers.learning_transfer import aggregate_pairs

    aggregate = aggregate_pairs([
        *_powered_learning_records(),
        {"state": state},
    ])

    assert aggregate["integrity"]["ok"] is False
    assert aggregate["integrity"]["blockers"] == 1


def test_missing_structural_oracle_fails_closed() -> None:
    from scorers.learning_transfer import aggregate_pairs

    records = _powered_learning_records()
    records[0].pop("prompt_equal")

    assert aggregate_pairs(records)["integrity"]["ok"] is False


def test_learning_transfer_verdict_rejects_underpowered_family_and_guard_failures() -> None:
    from scorers.learning_transfer import aggregate_pairs, transfer_verdict

    powered = _powered_learning_records(treatment=0.75, control=0.5)
    underpowered = powered[:-1]
    underpowered_result = transfer_verdict(aggregate_pairs(underpowered))
    assert underpowered_result["accepted"] is False
    assert underpowered_result["verdict"]["confidence"] == "underpowered"
    assert "统计功效不足" in underpowered_result["reasons"]

    flat_family = [dict(record) for record in powered]
    for record in flat_family:
        if record["family"] == "codex" and record["fixture_class"] == "positive":
            record["treatment_hidden"] = record["control_hidden"]
    family_result = transfer_verdict(aggregate_pairs(flat_family))
    assert family_result["accepted"] is False
    assert "至少一个 model family 未呈正向迁移" in family_result["reasons"]

    guard_regression = [dict(record) for record in powered]
    guard = next(record for record in guard_regression if record["fixture_class"] == "unrelated")
    guard["treatment_hidden"] = 0.0
    guard["control_hidden"] = 1.0
    guard_result = transfer_verdict(aggregate_pairs(guard_regression))
    assert guard_result["accepted"] is False
    assert "unrelated guard 回退或缺失" in guard_result["reasons"]


def test_learning_transfer_scorer_is_registered_only_for_sequence_fixtures() -> None:
    assert "learning_transfer" in scorers_pkg.available()
    assert scorers_pkg.applies("learning_transfer", "learning-transfer")
    assert not scorers_pkg.applies("learning_transfer", "e2e-outcome")


def test_learning_transfer_runner_delegates_dry_run_to_sequence(tmp_path) -> None:
    experiment = tmp_path / "learning-transfer"
    fixtures_dir = experiment / "fixtures/learning-transfer"
    fixtures_dir.mkdir(parents=True)
    (experiment / "config.json").write_text(json.dumps({
        "name": "learning-transfer",
        "skill_under_test": "cs-feat",
        "execution_mode": "learning-transfer",
        "model_targets": [{
            "id": "claude-haiku",
            "family": "claude",
            "harness": "claude-headless",
            "model": "claude-haiku-4-5",
        }],
        "fixture_classes": ["learning-transfer"],
        "scorers": ["learning_transfer"],
        "k": 1,
        "budget_usd": 10,
    }), encoding="utf-8")
    (fixtures_dir / "feat.json").write_text(
        json.dumps(_learning_fixture_dict(), ensure_ascii=False),
        encoding="utf-8",
    )
    out = tmp_path / "estimate.json"

    rc = runner_mod.main([
        "--experiment", str(experiment),
        "--dry-run",
        "--out", str(out),
    ])

    assert rc == 0
    estimate = json.loads(out.read_text(encoding="utf-8"))
    assert estimate["invocation_count"] == 4
    assert estimate["phase_invocations"] == {
        "a": 1,
        "curation": 1,
        "b-treatment": 1,
        "b-control": 1,
    }


def test_learning_transfer_runner_filters_explicit_execution_targets(tmp_path) -> None:
    experiment = tmp_path / "learning-transfer"
    fixtures_dir = experiment / "fixtures/learning-transfer"
    fixtures_dir.mkdir(parents=True)
    (experiment / "config.json").write_text(json.dumps({
        "name": "learning-transfer",
        "skill_under_test": "cs-feat",
        "execution_mode": "learning-transfer",
        "model_targets": [
            {
                "id": "claude-haiku",
                "family": "claude",
                "harness": "claude-headless",
                "model": "claude-haiku-4-5",
            },
            {
                "id": "codex-terra",
                "family": "codex",
                "harness": "codex-cli",
                "model": "gpt-5.6-terra",
            },
        ],
        "fixture_classes": ["learning-transfer"],
        "scorers": ["learning_transfer"],
        "k": 1,
        "budget_usd": 10,
    }), encoding="utf-8")
    (fixtures_dir / "feat.json").write_text(
        json.dumps(_learning_fixture_dict(), ensure_ascii=False),
        encoding="utf-8",
    )
    out = tmp_path / "estimate.json"

    rc = runner_mod.main([
        "--experiment", str(experiment),
        "--harness", "codex-cli",
        "--model", "gpt-5.6-terra",
        "--dry-run",
        "--out", str(out),
    ])

    assert rc == 0
    estimate = json.loads(out.read_text(encoding="utf-8"))
    assert estimate["targets"] == 1
    assert estimate["per_target"] == [
        {"target_id": "codex-terra", "est_usd": estimate["per_target"][0]["est_usd"]},
    ]
    assert estimate["invocation_count"] == 4


def test_learning_transfer_runner_rejects_empty_execution_target_filter(tmp_path, capsys) -> None:
    experiment = tmp_path / "learning-transfer"
    fixtures_dir = experiment / "fixtures/learning-transfer"
    fixtures_dir.mkdir(parents=True)
    (experiment / "config.json").write_text(json.dumps({
        "name": "learning-transfer",
        "skill_under_test": "cs-feat",
        "execution_mode": "learning-transfer",
        "model_targets": [{
            "id": "claude-haiku",
            "family": "claude",
            "harness": "claude-headless",
            "model": "claude-haiku-4-5",
        }],
        "fixture_classes": ["learning-transfer"],
        "scorers": ["learning_transfer"],
    }), encoding="utf-8")
    (fixtures_dir / "feat.json").write_text(
        json.dumps(_learning_fixture_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

    rc = runner_mod.main([
        "--experiment", str(experiment),
        "--harness", "codex-cli",
        "--dry-run",
    ])

    assert rc == 2
    assert "没有匹配的 model target" in capsys.readouterr().err


def test_learning_transfer_builds_each_seed_repo_from_its_builder(tmp_path) -> None:
    from e2e_env import build_seed_repo

    root = tmp_path / "project"
    seed_dir = root / "experiments/seeds/learning-lab"
    seed_dir.mkdir(parents=True)
    (seed_dir / "build-seed.py").write_text(
        "from pathlib import Path\nimport argparse\n"
        "p=argparse.ArgumentParser(); p.add_argument('--out', required=True); a=p.parse_args()\n"
        "out=Path(a.out); out.mkdir(parents=True); (out/'seed.txt').write_text('fresh\\n')\n",
        encoding="utf-8",
    )

    repo = build_seed_repo("learning-lab", tmp_path / "cell/repo", root)

    assert repo == tmp_path / "cell/repo"
    assert (repo / "seed.txt").read_text(encoding="utf-8") == "fresh\n"


def test_learning_transfer_repo_manifest_rejects_symlinks(tmp_path) -> None:
    from e2e_env import repo_manifest

    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "escape").symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        repo_manifest(repo)


def test_learning_transfer_rebuilds_treatment_from_post_a_git_state(tmp_path) -> None:
    import subprocess
    from e2e_env import copy_repo, repo_manifest
    from sequence import materialize_paired_repos

    post_a = tmp_path / "post-a"
    post_a.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=post_a, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=post_a, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=post_a, check=True)
    (post_a / "code.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "code.py"], cwd=post_a, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=post_a, check=True)

    curation = copy_repo(post_a, tmp_path / "curation")
    lesson = curation / ".codestable/lessons/2026-08-02-example.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text("lesson\n", encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "changed-by-curation"], cwd=curation, check=True)
    subprocess.run(["git", "add", lesson.relative_to(curation).as_posix()], cwd=curation, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "must-not-propagate"], cwd=curation, check=True)

    treatment, control = materialize_paired_repos(
        post_a,
        curation,
        lesson.relative_to(curation).as_posix(),
        tmp_path / "treatment",
        tmp_path / "control",
    )

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=post_a, check=True, capture_output=True, text=True,
    ).stdout.strip()
    for repo in (treatment, control):
        assert subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True,
        ).stdout.strip() == head
        assert subprocess.run(
            ["git", "config", "user.name"], cwd=repo, check=True, capture_output=True, text=True,
        ).stdout.strip() == "eval"
    assert (treatment / lesson.relative_to(curation)).read_text(encoding="utf-8") == "lesson\n"
    assert not (control / lesson.relative_to(curation)).exists()
    treatment_without_lesson = repo_manifest(treatment)
    treatment_without_lesson.pop(lesson.relative_to(curation).as_posix())
    assert treatment_without_lesson == repo_manifest(control)


def test_learning_transfer_sequence_resumes_only_complete_pairs(monkeypatch, tmp_path) -> None:
    import sequence
    from config import ExperimentConfig

    config = ExperimentConfig(
        name="learning-transfer",
        skill_under_test="cs-feat",
        execution_mode="learning-transfer",
        model_targets=[{
            "id": "fake",
            "family": "fake-family",
            "harness": "fake-harness",
            "model": "mock-model",
        }],
    )
    fixture = Fixture.from_dict(_learning_fixture_dict())
    calls: list[int] = []

    def fake_build_seed(_seed, destination, _root):
        destination.mkdir(parents=True)
        return destination

    def fake_run_pair(**kwargs):
        calls.append(kwargs["k_index"])
        kwargs["phase_callback"]({"phase": "a", "status": "passed"})
        pair = _completed_learning_pair(
            family="fake-family",
            fixture_id=fixture.id,
            owning_skill="cs-feat",
            k_index=kwargs["k_index"],
        )
        if kwargs["k_index"] == 1:
            pair["state"] = "pipeline-failed"
        return pair

    monkeypatch.setattr(sequence, "build_seed_repo", fake_build_seed)
    monkeypatch.setattr(sequence, "run_pair", fake_run_pair)
    monkeypatch.setattr(sequence, "preflight_fixture", lambda *_args: {"ok": True})
    checkpoint = tmp_path / "results.partial.jsonl"
    run_root = tmp_path / "runs"

    first = sequence.run_sequence(
        config=config,
        fixtures=[fixture],
        k=2,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=run_root,
        checkpoint_path=checkpoint,
        harness_resolver=lambda _name: object(),
    )
    second = sequence.run_sequence(
        config=config,
        fixtures=[fixture],
        k=2,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=run_root,
        checkpoint_path=checkpoint,
        harness_resolver=lambda _name: object(),
    )

    assert calls == [0, 1]
    assert len(first["pairs"]) == 2
    assert len(second["pairs"]) == 2
    assert [pair["state"] for pair in first["pairs"]] == ["completed", "pipeline-failed"]
    assert first["preflight"][fixture.id]["ok"] is True
    assert len(sequence.load_completed_pairs(checkpoint)) == 2
    events = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    assert [event["phase"] for event in events].count("a") == 2
    assert [event["phase"] for event in events].count("score") == 2


def test_learning_transfer_runner_executes_sequence_and_writes_results(monkeypatch, tmp_path) -> None:
    import sequence

    experiment = tmp_path / "learning-transfer"
    fixtures_dir = experiment / "fixtures/learning-transfer"
    fixtures_dir.mkdir(parents=True)
    (experiment / "config.json").write_text(json.dumps({
        "name": "learning-transfer",
        "skill_under_test": "cs-feat",
        "execution_mode": "learning-transfer",
        "model_targets": [{
            "id": "fake",
            "family": "fake-family",
            "harness": "mock",
            "model": "mock-model",
        }],
        "fixture_classes": ["learning-transfer"],
        "scorers": ["learning_transfer"],
        "k": 1,
        "budget_usd": 10,
    }), encoding="utf-8")
    (fixtures_dir / "feat.json").write_text(
        json.dumps(_learning_fixture_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

    def fake_build_seed(_seed, destination, _root):
        destination.mkdir(parents=True)
        return destination

    def fake_run_pair(**kwargs):
        return _completed_learning_pair(
            family="fake-family",
            fixture_id="lt-feat-01",
            owning_skill="cs-feat",
            k_index=kwargs["k_index"],
        )

    monkeypatch.setattr(sequence, "build_seed_repo", fake_build_seed)
    monkeypatch.setattr(sequence, "run_pair", fake_run_pair)
    monkeypatch.setattr(sequence, "preflight_fixture", lambda *_args: {"ok": True})
    out = tmp_path / "results.json"

    rc = runner_mod.main([
        "--experiment", str(experiment),
        "--out", str(out),
    ])

    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["execution_mode"] == "learning-transfer"
    assert len(payload["pairs"]) == 1
    assert not Path(str(out) + ".partial.jsonl").exists()


def test_learning_transfer_preflight_requires_golden_green_and_naive_target_red(tmp_path) -> None:
    from sequence import preflight_fixture

    fixture_dict = _learning_fixture_dict()
    fixture_dict["scenario"]["b"]["hidden_tests"] = ["hidden/feat.py"]
    fixture_dict["scenario"]["b"]["regression_tests"] = ["regression/feat.py"]
    fixture = Fixture.from_dict(fixture_dict)
    experiment = tmp_path / "experiment"
    for dirname in ("hidden", "regression", "preflight"):
        (experiment / dirname).mkdir(parents=True)
    (experiment / "hidden/feat.py").write_text(
        "from pathlib import Path\n\ndef test_target(): assert Path('behavior.txt').read_text() == 'golden\\n'\n",
        encoding="utf-8",
    )
    (experiment / "regression/feat.py").write_text(
        "from pathlib import Path\n\ndef test_existing(): assert Path('existing.txt').read_text() == 'stable\\n'\n",
        encoding="utf-8",
    )
    for name, value in (("feat-naive.py", "naive"), ("feat-golden.py", "golden")):
        (experiment / "preflight" / name).write_text(
            "from pathlib import Path\nimport sys\nrepo=Path(sys.argv[1])\n"
            f"(repo/'behavior.txt').write_text('{value}\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "existing.txt").write_text("stable\n", encoding="utf-8")

    result = preflight_fixture(
        fixture,
        seed,
        experiment,
        tmp_path / "preflight-runs",
    )

    assert result["ok"] is True
    assert result["golden_hidden"] == 1.0
    assert result["naive_hidden"] == 0.0
    assert result["golden_regression"] == 1.0
    assert result["naive_regression"] == 1.0


def test_learning_transfer_invalid_fixture_skips_models_and_blocks_verdict(monkeypatch, tmp_path) -> None:
    import sequence
    from config import ExperimentConfig

    config = ExperimentConfig(
        name="learning-transfer",
        skill_under_test="cs-feat",
        execution_mode="learning-transfer",
        model_targets=[{
            "id": "fake",
            "family": "fake-family",
            "harness": "fake-harness",
            "model": "mock-model",
        }],
    )
    fixture = Fixture.from_dict(_learning_fixture_dict())

    def fake_build_seed(_seed, destination, _root):
        destination.mkdir(parents=True)
        return destination

    monkeypatch.setattr(sequence, "build_seed_repo", fake_build_seed)
    monkeypatch.setattr(sequence, "preflight_fixture", lambda *_args: {
        "ok": False,
        "golden_hidden": 0.0,
    })
    monkeypatch.setattr(
        sequence,
        "run_pair",
        lambda **_kwargs: pytest.fail("invalid fixture 不得调用模型"),
    )

    payload = sequence.run_sequence(
        config=config,
        fixtures=[fixture],
        k=1,
        experiment_dir=tmp_path,
        root=ROOT,
        run_root=tmp_path / "runs",
        checkpoint_path=tmp_path / "partial.jsonl",
        harness_resolver=lambda _name: object(),
    )

    assert payload["pairs"] == []
    assert payload["invalid"][0]["state"] == "fixture-invalid"
    assert payload["verdict"]["accepted"] is False
