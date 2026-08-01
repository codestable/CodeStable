#!/usr/bin/env python3
"""指标采集与成本估算，统一认知诚实 tag。

- wall_ms / turns：harness 直接可得 → [measured]。
- tokens / cost：harness 回传 usage（如 claude --output-format json）→ [measured]；
  否则 chars/4 估算 + pricing → [soft]。
每个数值都带 tag，禁止裸数。
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from typing import Any

from _model import HarnessResult, MEASURED, SOFT, tagged

# USD / 1M token（估算用；真实成本以 harness usage 为准）
PRICING: dict[str, tuple[float, float]] = {
    "opus": (15.0, 75.0),
    "sonnet": (3.0, 15.0),
    "haiku": (0.8, 4.0),
    "gpt": (2.5, 10.0),
    "fable": (5.0, 25.0),
    "mock": (0.0, 0.0),
}
_DEFAULT_PRICE = (3.0, 15.0)


def price_for(model: str) -> tuple[float, float]:
    low = (model or "").lower()
    for key, val in PRICING.items():
        if key in low:
            return val
    return _DEFAULT_PRICE


def estimate_cost(prompt: str, model: str, out_tokens: int = 500) -> float:
    pin, pout = price_for(model)
    tin = len(prompt) / 4
    return (tin * pin + out_tokens * pout) / 1_000_000


def capture(result: HarnessResult, prompt: str | None = None) -> dict[str, Any]:
    """从一次 harness 调用回收指标，全部带 tag。"""
    metrics: dict[str, Any] = {"wall_ms": tagged(result.wall_ms, MEASURED)}
    if result.turns is not None:
        metrics["turns"] = tagged(result.turns, MEASURED)

    usage = result.usage or {}
    real = usage.get("source") in {"claude-json", "codex-json"}
    tag = MEASURED if real else SOFT

    tin = usage.get("input_tokens")
    tout = usage.get("output_tokens")
    if tin is None and prompt is not None:
        tin = int(len(prompt) / 4)
    if tin is not None:
        metrics["input_tokens"] = tagged(tin, tag if usage.get("input_tokens") is not None else SOFT)
    if tout is not None:
        metrics["output_tokens"] = tagged(tout, tag)

    cost = usage.get("cost_usd")
    if cost is None and prompt is not None:
        cost = round(estimate_cost(prompt, result.model, out_tokens=int(tout or 500)), 6)
        metrics["cost_usd"] = tagged(cost, SOFT)
    elif cost is not None:
        metrics["cost_usd"] = tagged(cost, tag)
    return metrics
