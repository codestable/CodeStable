"""M4 自举：新 skill 零核心改动接入 + buildprompt 分派 + cs-feedback→fixture 闭环。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
FEEDBACK_SCRIPTS = ROOT / "plugins/codestable/skills/cs-feedback/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(FEEDBACK_SCRIPTS))

import buildprompt              # noqa: E402
import fixtures as fx_mod       # noqa: E402
import runner as runner_mod     # noqa: E402
import feedback_to_fixture as f2f  # noqa: E402
from _model import Fixture      # noqa: E402


# ---- 零核心改动接入新 skill ----

def test_cs_issue_fix_experiment_runs(tmp_path):
    exp = ROOT / "experiments/cs-issue-fix-001"
    out = tmp_path / "r.json"
    assert runner_mod.main(["--experiment", str(exp), "--harness", "mock", "--k", "1", "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["skill_under_test"] == "cs-issue"
    assert "recall" in data["aggregate"]["baseline"]["scores"]


def test_cs_audit_experiment_runs(tmp_path):
    exp = ROOT / "experiments/cs-audit-001"
    out = tmp_path / "r.json"
    assert runner_mod.main(["--experiment", str(exp), "--harness", "mock", "--k", "1", "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["skill_under_test"] == "cs-audit"


def test_new_experiments_touch_only_data():
    # 自举证据：这些 skill 接入只需 experiments/ 数据（review 型，复用现有 builder），无代码改动
    # review 型 + design 型(cs-epic 复用现有 design builder) 均纯数据接入
    for name in ("cs-issue-fix-001", "cs-audit-001", "cs-refactor-001", "cs-epic-001"):
        d = ROOT / "experiments" / name
        assert (d / "config.json").is_file()
        assert list(d.glob("fixtures/**/*.json"))
        # 实验目录内不得夹带 python 代码（接入=纯数据）
        assert not list(d.glob("**/*.py"))


def test_cs_refactor_experiment_runs(tmp_path):
    exp = ROOT / "experiments/cs-refactor-001"
    out = tmp_path / "r.json"
    assert runner_mod.main(["--experiment", str(exp), "--harness", "mock", "--k", "1", "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["skill_under_test"] == "cs-refactor"
    assert data["aggregate"]["baseline"]["scores"]["recall"]["tag"] == "measured"


def test_cs_feat_design_experiment_runs(tmp_path):
    # cs-feat design 是生成型，需 build_design_prompt（一个 builder）；离线 mock 无信号但 pipeline 能跑
    exp = ROOT / "experiments/cs-feat-001"
    out = tmp_path / "r.json"
    assert runner_mod.main(["--experiment", str(exp), "--harness", "mock", "--k", "1", "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["skill_under_test"] == "cs-feat"


def test_cs_epic_and_docs_run(tmp_path):
    for name, skill in (("cs-epic-001", "cs-epic"), ("cs-docs-001", "cs-docs")):
        out = tmp_path / f"{name}.json"
        assert runner_mod.main(["--experiment", str(ROOT / "experiments" / name),
                                "--harness", "mock", "--k", "1", "--out", str(out)]) == 0
        assert json.loads(out.read_text(encoding="utf-8"))["skill_under_test"] == skill


def test_new_experiments_reach_power():
    for name in ("cs-refactor-001", "cs-feat-001", "cs-epic-001", "cs-docs-001"):
        n = len(list((ROOT / "experiments" / name / "fixtures/planted-defect").glob("*.json")))
        assert n >= 8, f"{name} 应达 n>=8"


# ---- buildprompt 按 kind 分派 ----

def test_buildprompt_dispatch():
    text = "SKILL BODY"
    review = buildprompt.build_prompt(Fixture(id="r", answer_type="findings-recall", task={"kind": "review", "diff": "x"}), text)
    fix = buildprompt.build_prompt(Fixture(id="f", answer_type="findings-recall", task={"kind": "fix", "diff": "x"}), text)
    audit = buildprompt.build_prompt(Fixture(id="a", answer_type="findings-recall", task={"kind": "audit", "diff": "x"}), text)
    design = buildprompt.build_prompt(Fixture(id="d", answer_type="findings-recall", task={"kind": "design", "spec": "加导出"}), text)
    docs = buildprompt.build_prompt(Fixture(id="w", answer_type="findings-recall", task={"kind": "docs", "spec": "写 reference"}), text)
    assert "待审查改动" in review
    assert "待修复问题" in fix
    assert "待审计代码" in audit
    assert "产出一份 design" in design
    assert "文档任务" in docs
    assert "SKILL BODY" in review  # 被测 skill 快照注入


# ---- cs-feedback → local candidate ----

def test_feedback_to_fixture_candidate_only(tmp_path):
    exp = tmp_path / "experiments/cs-code-review-007"
    exp.mkdir(parents=True)
    rc = f2f.main(["--experiment", str(exp), "--failure", "agent 漏报了 SQL 注入", "--kind", "review"])
    assert rc != 0
    assert not (exp / "fixtures/regression").exists()

    evidence = tmp_path / "feedback/public-issue-context.json"
    evidence.parent.mkdir()
    evidence.write_text(
        json.dumps({"privacy": "public-preview", "events": [{"sanitized_excerpt": "agent 漏报 SQL 注入"}]}),
        encoding="utf-8",
    )
    assert f2f.main(["--evidence", str(evidence)]) == 0
    data = json.loads((evidence.parent / "regression-candidate.json").read_text(encoding="utf-8"))
    assert data["_source"] == "cs-feedback"
    assert data["_status"] == "candidate"
    assert data["quality"]["regression_ready"] is False
    assert fx_mod.validate_fixture_dict(data) == []
