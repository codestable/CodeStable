#!/usr/bin/env python3
"""ExperimentConfig：实验声明。build_prompt 不可序列化，故 config.json 只存声明字段，
runner 按 task.kind 装配 build_prompt。variant 解析为 SKILL.md 快照文本（隔离宿主）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _model import ExecutionTarget, is_safe_slug


@dataclass
class ExperimentConfig:
    name: str
    skill_under_test: str                       # 如 cs-code-review
    variants: list[str] = field(default_factory=lambda: ["baseline"])
    model_list: list[str] = field(default_factory=list)   # ≥2（BAIME 硬约束，dry-run/正式运行时校验）
    k: int = 5
    harnesses: list[str] = field(default_factory=lambda: ["mock"])
    scorers: list[str] = field(default_factory=lambda: ["planted_defect"])
    fixture_classes: list[str] = field(default_factory=lambda: ["planted-defect"])
    budget_usd: float = 50.0
    judge_model: str | None = None              # llm_judge 用，需独立于被测 model
    inject_context: bool = False                # True=prompt 里补齐 onboard 上下文，公平测「主路径」而非 bare-input
    execution_mode: str = "one-shot"
    model_targets: list[ExecutionTarget | dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not is_safe_slug(self.name):
            raise ValueError("experiment name 必须是小写连字符 slug（最多 64 字符）")
        self.model_targets = [
            target if isinstance(target, ExecutionTarget) else ExecutionTarget.from_dict(target)
            for target in self.model_targets
        ]
        ids = [target.id for target in self.model_targets]
        if len(ids) != len(set(ids)):
            raise ValueError("model target id 必须唯一")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        for key in ("name", "skill_under_test"):
            if key not in data:
                raise ValueError(f"config.json 缺字段 {key}")
        known = {
            "name", "skill_under_test", "variants", "model_list", "k", "harnesses",
            "scorers", "fixture_classes", "budget_usd", "judge_model", "inject_context",
            "execution_mode", "model_targets",
        }
        return cls(
            name=data["name"],
            skill_under_test=data["skill_under_test"],
            variants=list(data.get("variants", ["baseline"])),
            model_list=list(data.get("model_list", [])),
            k=int(data.get("k", 5)),
            harnesses=list(data.get("harnesses", ["mock"])),
            scorers=list(data.get("scorers", ["planted_defect"])),
            fixture_classes=list(data.get("fixture_classes", ["planted-defect"])),
            budget_usd=float(data.get("budget_usd", 50.0)),
            judge_model=data.get("judge_model"),
            inject_context=bool(data.get("inject_context", False)),
            execution_mode=str(data.get("execution_mode", "one-shot")),
            model_targets=list(data.get("model_targets", [])),
            raw={k: v for k, v in data.items() if k not in known},
        )


def load_config(experiment_dir: Path) -> ExperimentConfig:
    cfg_path = experiment_dir / "config.json"
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    return ExperimentConfig.from_dict(data)


def judge_issues(config: "ExperimentConfig") -> list[str]:
    """judge oracle 独立性校验：judge_model 必须独立于被测 model_list（混杂控制）。
    覆盖所有依赖 judge_model 的 scorer（llm_judge / recall_judge）。"""
    issues: list[str] = []
    used = {"llm_judge", "recall_judge"} & set(config.scorers)
    if not used:
        return issues
    label = "/".join(sorted(used))
    jm = (config.judge_model or "").strip()
    if not jm:
        issues.append(f"{label} 已启用但未设 judge_model：离线走 token/mock 回退(soft)；真实运行前须设独立 judge_model")
    elif jm in set(config.model_list):
        issues.append(f"judge_model={jm} 在 model_list 中（同源偏差）：oracle 须独立于被测 model")
    return issues


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for path in (current, *current.parents):
        if (path / ".git").exists() or (path / ".codestable").exists():
            return path
    return Path.cwd()


def resolve_skill_path(root: Path, skill: str) -> Path:
    """在两个 skill 根里找被测 skill 的 SKILL.md：shipped 插件 + 项目级 dev skill。"""
    if not is_safe_slug(skill):
        raise ValueError(f"skill 名称不是安全 slug: {skill!r}")
    roots = [root / "plugins" / "codestable" / "skills", root / ".claude" / "skills"]
    for sr in roots:
        p = sr / skill / "SKILL.md"
        if p.exists():
            return p
    return roots[0] / skill / "SKILL.md"  # fallback（报错更清晰）


def select_execution_targets(
    config: ExperimentConfig,
    harness: str | None = None,
    model: str | None = None,
) -> list[ExecutionTarget]:
    """按 CLI 限定筛选显式 model target，不重新组合 harness/model。"""
    return [
        target for target in config.model_targets
        if (not harness or target.harness == harness)
        and (not model or target.model == model)
    ]


def resolve_variant_text(config: ExperimentConfig, variant: str, root: Path,
                         exp_dir: Path | None = None) -> str:
    """把 variant 名解析成 SKILL.md 快照文本。

    - "baseline" → 被测 skill 的 SKILL.md（快照读取，注入 prompt，不让 harness 读宿主已装版本）。
      支持 shipped 插件（plugins/codestable/skills/）与项目级 dev skill（.claude/skills/，如 eval-cs-skill 自指）。
    - 其它 → optimize 产生的候选；优先 `<exp_dir>/variants/<variant>.md`，再退回 `<repo>/experiments/<name>/variants/<variant>.md`。
    """
    baseline = resolve_skill_path(root, config.skill_under_test)
    if variant == "baseline":
        path = baseline
    else:
        candidates = []
        if exp_dir is not None:
            candidates.append(exp_dir / "variants" / f"{variant}.md")
        candidates.append(root / "experiments" / config.name / "variants" / f"{variant}.md")
        path = next((c for c in candidates if c.exists()), baseline)
    return path.read_text(encoding="utf-8")
