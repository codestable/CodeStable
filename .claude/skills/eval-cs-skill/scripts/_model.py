#!/usr/bin/env python3
"""eval-cs-skill eval 核心数据模型与认知诚实标注。

self-contained：eval-cs-skill 不 import 其他 skill 的 lib（CLAUDE.md skill 独立性）。
数值一律带 tag：measured（oracle/机械可验）/ soft（自评/估算）/ underpowered（k<5 或 n<8）。
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # 不污染 plugin 包

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

MEASURED = "measured"
SOFT = "soft"
UNDERPOWERED = "underpowered"
_TAGS = {MEASURED, SOFT, UNDERPOWERED}


def tagged(value: Any, tag: str, evidence: str | None = None) -> dict[str, Any]:
    """把一个数值包成带认知诚实 tag 的结构。"""
    if tag not in _TAGS:
        raise ValueError(f"unknown tag {tag!r}; must be one of {sorted(_TAGS)}")
    out: dict[str, Any] = {"value": value, "tag": tag}
    if evidence:
        out["evidence"] = evidence
    return out


def render_tagged(t: Any) -> str:
    """渲染成 markdown 里的 `X [measured]` 形式，供 results.md / iteration-N.md 使用。"""
    if isinstance(t, dict) and "tag" in t and "value" in t:
        suffix = f" [{t['tag']}]"
        if t.get("evidence"):
            suffix = f" [{t['tag']}: {t['evidence']}]"
        return f"{t['value']}{suffix}"
    return str(t)


@dataclass
class Fixture:
    """一个评测样本。BAIME id/answer/answerType 的超集。"""

    id: str
    answer_type: str            # findings-recall | dod-gate | dimensions-judge
    answer: list[str] = field(default_factory=list)
    task: dict[str, Any] = field(default_factory=dict)
    checklist_path: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Fixture":
        missing = [k for k in ("id", "answerType") if k not in data]
        if missing:
            raise ValueError(f"fixture 缺字段 {missing}: {data.get('id', '<no-id>')}")
        return cls(
            id=str(data["id"]),
            answer_type=str(data["answerType"]),
            answer=list(data.get("answer", [])),
            task=dict(data.get("task", {})),
            checklist_path=data.get("checklist_path"),
            raw=data,
        )


@dataclass
class HarnessResult:
    """一次 harness/model 调用的原始产物 + 可回收指标。"""

    output: str
    model: str
    harness: str
    wall_ms: int
    turns: int | None = None
    usage: dict[str, Any] | None = None          # {input_tokens, output_tokens, cost_usd} 若 harness 回传
    transcript_path: str | None = None
    error: str | None = None
    workdir: str | None = None


@dataclass
class EvalResult:
    """单个 (fixture, variant, model, harness, k_index) 的评测结果。对齐 gate_result 形状。"""

    fixture_id: str
    variant: str
    model: str
    harness: str
    k_index: int
    scores: dict[str, Any] = field(default_factory=dict)   # {name: tagged(...)}
    metrics: dict[str, Any] = field(default_factory=dict)  # {name: tagged(...)}
    status: str = "passed"                                  # passed | failed | error
    evidence: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalResult":
        """从 checkpoint jsonl 反序列化，供 runner resume round-trip。"""
        return cls(
            fixture_id=str(data["fixture_id"]),
            variant=str(data["variant"]),
            model=str(data["model"]),
            harness=str(data["harness"]),
            k_index=int(data["k_index"]),
            scores=dict(data.get("scores", {})),
            metrics=dict(data.get("metrics", {})),
            status=str(data.get("status", "passed")),
            evidence=list(data.get("evidence", [])),
        )


@dataclass
class Verdict:
    """BAIME hypothesis verdict。"""

    id: str
    direction: str              # CONFIRMED | NULL | REJECTED
    observed: float
    threshold: float
    confidence: str             # high | medium | underpowered


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
