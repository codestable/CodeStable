#!/usr/bin/env python3
"""llm_judge scorer：两轴打分（compliance 照做没 / quality 质量）。

若 v1 项目保留 `.codestable/reference/code-dimensions.md`，可将其作为 repo-local rubric；
文件不存在时使用内置 rubric，不依赖 shipped skill 或集中式 onboard runtime。
judge 模型须独立于被测模型（避免同源偏差）。judge 分数默认 [soft]，
经 sanity 集校准（calibration.md）后方可在结论中升为 [measured]。
mock/离线：用确定性启发式，不发 LLM 调用。
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from _model import SOFT, tagged
from scorers.base import register

_BUILTIN_RUBRIC = "健壮性/结构/性能/可读性 四核心维 + 可测试性/安全性 场景维；档位越高要求越严。"


def _load_rubric(root: Path | None) -> str:
    if root:
        path = root / ".codestable" / "reference" / "code-dimensions.md"
        if path.is_file():
            return path.read_text(encoding="utf-8")[:4000]
    return _BUILTIN_RUBRIC


def _judge_prompt(fixture, output: str, rubric: str) -> str:
    task = fixture.task or {}
    return "\n".join([
        "你是独立评审 oracle。依据下述维度 rubric，对「某 skill 对一个任务产出的结果」打两轴分（0~1）：",
        "- compliance：是否遵循该 skill 的输出契约、是否只做被要求的事（照做没）。",
        "- quality：结论/发现的质量（准确、具体、可执行、无臆造）。",
        "\n## rubric（节选）", rubric,
        "\n## 任务", json.dumps(task, ensure_ascii=False)[:2000],
        "\n## 待评结果", output[:4000],
        '\n只输出 JSON：{"compliance": <0-1>, "quality": <0-1>, "rationale": "<一句话>"}',
    ])


def _heuristic(output: str) -> dict[str, float]:
    """离线确定性伪判分：结构完整度 + 发现具体度。仅用于打通管线，非真实质量。"""
    low = output.lower()
    has_findings = "findings" in low or "发现" in low
    finding_lines = [ln for ln in output.splitlines() if ln.strip().startswith("-")]
    has_locus = sum(1 for ln in finding_lines if re.search(r"\[[^\]]+\]", ln))
    compliance = 1.0 if has_findings else 0.4
    quality = min(1.0, 0.3 + 0.1 * has_locus) if finding_lines else 0.2
    return {"compliance": round(compliance, 3), "quality": round(quality, 3)}


def _parse(text: str) -> dict[str, float] | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return {"compliance": float(data["compliance"]), "quality": float(data["quality"])}
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


@register("llm_judge")  # applies_to 空=适用所有 answerType（judge 评任何输出）
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    judge_model = (config.judge_model if config else None) or "mock"
    rubric = _load_rubric(root)

    if "mock" in judge_model.lower():
        axes = _heuristic(result.output or "")
        rationale = "offline-heuristic"
    else:
        import harness as harness_pkg  # 延迟导入，避免离线路径依赖真实 harness
        judge_harness = (config.raw.get("judge_harness") if config else None) or "claude-headless"
        prompt = _judge_prompt(fixture, result.output or "", rubric)
        try:
            with tempfile.TemporaryDirectory(prefix="cs-judge-") as tmp:
                hr = harness_pkg.get_harness(judge_harness).invoke(prompt, judge_model, Path(tmp), 300)
            axes = _parse(hr.output) or _heuristic(result.output or "")
            rationale = "judge-model" if _parse(hr.output) else "judge-parse-failed→heuristic"
        except Exception as exc:  # noqa: BLE001 - judge 失败退化为启发式，不崩实验
            axes = _heuristic(result.output or "")
            rationale = f"judge-error→heuristic: {exc}"

    return {
        "scores": {
            "judge_compliance": tagged(axes["compliance"], SOFT, evidence=rationale),
            "judge_quality": tagged(axes["quality"], SOFT, evidence=rationale),
        },
        "evidence": [{"judge_model": judge_model, "axes": axes, "rationale": rationale}],
        "status": "passed" if axes["compliance"] >= 0.5 else "failed",
    }
