"""M4 自指 + 自治：eval-cs-skill 评自己（无递归）+ 实验队列 run-next 幂等。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
sys.path.insert(0, str(SCRIPTS))

import runner as runner_mod          # noqa: E402
import enqueue_experiment as eq      # noqa: E402


# ---- 自指 ----

def test_selfref_experiment_runs(tmp_path):
    exp = ROOT / "experiments/eval-cs-skill-001"
    out = tmp_path / "r.json"
    rc = runner_mod.main(["--experiment", str(exp), "--harness", "mock", "--k", "1", "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["skill_under_test"] == "eval-cs-skill"          # 指向自己
    # 同一 harness/scorer 产出 measured 召回；无递归（跑完即返回）
    assert data["aggregate"]["baseline"]["scores"]["recall"]["tag"] == "measured"


def test_selfref_does_not_invoke_cs_skill_tools(tmp_path):
    # 自指靠「把 eval-cs-skill/SKILL.md 当被测文本注入」，不调用其工具 → 不会递归起 runner。
    # 机械证据：被测文本来自快照读取，prompt 里含 SKILL.md 标记而非工具执行结果。
    from config import ExperimentConfig, resolve_variant_text
    cfg = ExperimentConfig(name="eval-cs-skill-001", skill_under_test="eval-cs-skill")
    text = resolve_variant_text(cfg, "baseline", ROOT)
    assert "eval-cs-skill" in text and "runner.py" in text  # 是 SKILL.md 文本，不是执行产物


# ---- 自治队列 ----

def test_queue_enqueue_and_run_next(tmp_path, monkeypatch):
    q = tmp_path / ".queue.jsonl"
    monkeypatch.setattr(eq, "_queue_path", lambda: q)
    calls = []

    def fake_run(argv):
        calls.append(argv)
        return 0

    monkeypatch.setattr(eq.runner, "main", fake_run)
    exp = str(tmp_path / "exp")
    eq.enqueue(exp, "eval")
    eq.enqueue(exp, "eval")

    assert eq.run_next() == 0
    assert [item["status"] for item in eq._load()] == ["done", "queued"]
    assert calls == [["--experiment", exp]]

    assert eq.run_next() == 0
    assert [item["status"] for item in eq._load()] == ["done", "done"]
    assert calls == [["--experiment", exp], ["--experiment", exp]]

    assert eq.run_next() == 0
    assert len(calls) == 2
