#!/usr/bin/env python3
"""recall_judge scorer：judge 模型做**语义**召回判定（措辞无关）。

补 planted_defect（token 重叠）的短板：对纯符号 / 中文散文 answer（如「>= 改成 >」「删掉早返回守卫」），
token 匹配会误判漏检，而模型其实识别到了。recall_judge 让独立 judge 逐条判「输出是否识别到该缺陷」。
judge 分数标 [soft]（模型判定，非机械 oracle）；judge 不可用时退回 token 结果并标注。
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from _model import SOFT, tagged
from scorers.base import register
from scorers.planted_defect import _recalled  # token fallback


def _judge_prompt(answers: list[str], output: str) -> str:
    items = "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers))
    return "\n".join([
        "下面是某代码审查/分析/设计输出。请判断它是否**识别/覆盖**了每一条给定要点（语义匹配，措辞可完全不同，命中即算）。",
        "\n## 要点", items,
        "\n## 待判输出", output[:6000],
        f'\n只输出一个 JSON 数组，长度 {len(answers)}，元素为 true/false，对应每条要点是否被识别。例：[true,false,...]',
    ])


def _parse(text: str, n: int) -> list[bool] | None:
    m = re.search(r"\[[^\]]*\]", text, re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(0))
        if isinstance(arr, list) and len(arr) == n:
            return [bool(x) for x in arr]
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
    return None


@register("recall_judge", applies_to={"findings-recall"})
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    answers = list(fixture.answer or [])
    output = result.output or ""
    if not answers:
        return {"scores": {"recall_judge": tagged(0.0, SOFT, evidence="no answers")}, "evidence": [], "status": "passed"}

    judge_model = (config.judge_model if config else None)
    judge_harness = (config.raw.get("judge_harness") if config else None) or "api"
    verdicts: list[bool] | None = None
    src = "judge"
    if judge_model and "mock" not in judge_model.lower():   # 仅在显式配了真实 judge_model 时走 judge
        import harness as harness_pkg
        try:
            with tempfile.TemporaryDirectory(prefix="cs-recall-") as tmp:
                hr = harness_pkg.get_harness(judge_harness).invoke(_judge_prompt(answers, output), judge_model, Path(tmp), 120)
            verdicts = _parse(hr.output, len(answers))
        except Exception as exc:  # noqa: BLE001 - judge 失败退回 token
            src = f"judge-error({exc})→token"
    else:
        src = "token(no-judge_model)"
    if verdicts is None:
        low = output.lower()
        verdicts = [_recalled(a, low) for a in answers]
        if src == "judge":
            src = "judge-parse-fail→token"

    matched = [a for a, v in zip(answers, verdicts) if v]
    missed = [a for a, v in zip(answers, verdicts) if not v]
    recall = len(matched) / len(answers)
    return {
        "scores": {"recall_judge": tagged(round(recall, 4), SOFT, evidence=f"{len(matched)}/{len(answers)} via {src} ({judge_model})")},
        "evidence": [{"matched": matched, "missed": missed, "judge_model": judge_model, "source": src}],
        "status": "passed" if not missed else "failed",
    }
