#!/usr/bin/env python3
"""eval-cs-skill eval runner：跨 variant×harness×model×k 执行被测 skill，打分，写 results.json。

用法：
  python3 runner.py --experiment experiments/cs-code-review-001 [--harness mock] \
      [--model M] [--scorer planted_defect] [--k 1] [--dry-run] [--confirm] [--out PATH]

隔离：被测 SKILL.md 以快照文本注入 prompt（config.resolve_variant_text），每 cell 独立 tmp workdir。
成本：多模型真实运行前用 --dry-run 估算；超 budget_usd 需 --confirm。
"""

from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True  # 不污染 plugin 包（check-plugin-package 禁 __pycache__）

import json
import tempfile
from pathlib import Path
from statistics import mean
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import harness as harness_pkg          # noqa: E402
import metrics                          # noqa: E402
import scorers as scorers_pkg          # noqa: E402
from _model import EvalResult, MEASURED, SOFT, UNDERPOWERED, render_tagged, tagged, write_json  # noqa: E402
from buildprompt import build_prompt   # noqa: E402
from config import ExperimentConfig, judge_issues, load_config, repo_root, resolve_variant_text  # noqa: E402
from e2e_env import prepare_e2e_workdir  # noqa: E402
from fixtures import load_fixtures      # noqa: E402


def _agg_tag(tags: set[str]) -> str:
    """聚合认知诚实 tag：全 measured 才 measured；含 soft 则 soft；否则 underpowered。"""
    if tags == {MEASURED}:
        return MEASURED
    if SOFT in tags:
        return SOFT
    return UNDERPOWERED


def _cell_key(variant: str, harness: str, model: str, fixture_id: str, k_index: int) -> str:
    """一个执行单元的唯一标识，用于 resume 去重。"""
    return f"{variant}|{harness}|{model}|{fixture_id}|{k_index}"


def _load_checkpoint(path: Path) -> tuple[list[EvalResult], set[str]]:
    """读已完成 cell 的 checkpoint jsonl → (已完成结果, 已完成 cell key 集合)。"""
    done: list[EvalResult] = []
    keys: set[str] = set()
    if not path.exists():
        return done, keys
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        er = EvalResult.from_dict(json.loads(line))
        done.append(er)
        keys.add(_cell_key(er.variant, er.harness, er.model, er.fixture_id, er.k_index))
    return done, keys


def _append_checkpoint(path: Path, er: EvalResult) -> None:
    """单个 cell 完成即 append 落盘 + flush，保证被 kill 也不丢已完成结果。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(er.to_dict(), ensure_ascii=False) + "\n")
        f.flush()


def _models_for(config: ExperimentConfig, override: str | None, harness: str) -> list[str]:
    if override:
        return [override]
    if config.model_list:
        return config.model_list
    return ["mock-model"] if harness == "mock" else ["default"]


def build_matrix(config: ExperimentConfig, args) -> list[tuple[str, str, str]]:
    variants = [args.variant] if args.variant else config.variants
    harnesses = [args.harness] if args.harness else config.harnesses
    cells = []
    for variant in variants:
        for h in harnesses:
            for model in _models_for(config, args.model, h):
                cells.append((variant, h, model))
    return cells


def dry_run(config: ExperimentConfig, fixtures, cells, k: int, exp_dir: Path | None = None) -> dict[str, Any]:
    total = 0.0
    per_cell = []
    for variant, h, model in cells:
        text = resolve_variant_text(config, variant, repo_root(), exp_dir)
        cell_cost = 0.0
        for fx in fixtures:
            prompt = build_prompt(fx, text, config.inject_context)
            cell_cost += metrics.estimate_cost(prompt, model) * k
        per_cell.append({"variant": variant, "harness": h, "model": model, "est_usd": round(cell_cost, 4)})
        total += cell_cost
    return {"est_total_usd": round(total, 2), "per_cell": per_cell, "budget_usd": config.budget_usd,
            "fixtures": len(fixtures), "cells": len(cells), "k": k}


def run(config: ExperimentConfig, fixtures, cells, scorer_names, k: int, exp_dir: Path | None = None,
        checkpoint_path: Path | None = None) -> list[EvalResult]:
    done, done_keys = _load_checkpoint(checkpoint_path) if checkpoint_path else ([], set())
    results: list[EvalResult] = list(done)
    root = repo_root()
    for variant, h, model in cells:
        text = resolve_variant_text(config, variant, root, exp_dir)
        harness = harness_pkg.get_harness(h)
        for fx in fixtures:
            prompt = build_prompt(fx, text, config.inject_context)
            for ki in range(k):
                if _cell_key(variant, h, model, fx.id, ki) in done_keys:
                    continue  # resume：跳过已 checkpoint 的 cell
                er = EvalResult(fixture_id=fx.id, variant=variant, model=model, harness=h, k_index=ki)
                try:
                    with tempfile.TemporaryDirectory(prefix="cs-eval-") as tmp:
                        # e2e fixture：在 invoke 前准备真实 seed 仓库，并把 workdir 指向它
                        invoke_workdir = Path(tmp)
                        if fx.answer_type == "e2e-outcome":
                            repo = prepare_e2e_workdir(fx, tmp, exp_dir or Path("."))
                            invoke_workdir = repo
                        hr = harness.invoke(prompt, model, invoke_workdir, timeout_s=600)
                        hr.workdir = str(invoke_workdir)
                        er.metrics = metrics.capture(hr, prompt)
                        if hr.error:
                            er.status = "error"
                            er.evidence.append({"error": hr.error})
                            results.append(er)
                            if checkpoint_path:
                                _append_checkpoint(checkpoint_path, er)
                            continue
                        # 打分：只跑与 fixture.answer_type 匹配的 scorer
                        statuses = []
                        for sname in scorer_names:
                            if not scorers_pkg.applies(sname, fx.answer_type):
                                continue
                            sc = scorers_pkg.get_scorer(sname)(fx, hr, config, root)
                            er.scores.update(sc.get("scores", {}))
                            er.evidence.extend(sc.get("evidence", []))
                            statuses.append(sc.get("status", "passed"))
                        er.status = "failed" if "failed" in statuses else "passed"
                except Exception as exc:  # 单 cell 失败（504/网络等）不毁整段
                    er.status = "error"
                    er.evidence.append({"error": f"{type(exc).__name__}: {str(exc)[:200]}"})
                results.append(er)
                if checkpoint_path:
                    _append_checkpoint(checkpoint_path, er)
    return results


def aggregate(config: ExperimentConfig, results: list[EvalResult]) -> dict[str, Any]:
    agg: dict[str, Any] = {}
    for variant in {r.variant for r in results}:
        rs = [r for r in results if r.variant == variant]
        score_names = {name for r in rs for name in r.scores}
        scores = {}
        for name in score_names:
            vals = [r.scores[name]["value"] for r in rs if name in r.scores]
            tags = {r.scores[name]["tag"] for r in rs if name in r.scores}
            if vals:
                scores[name] = tagged(round(mean(vals), 4), _agg_tag(tags), evidence=f"mean over n={len(vals)}")
        metric_names = {name for r in rs for name in r.metrics}
        metrics = {}
        for name in metric_names:
            vals = [r.metrics[name]["value"] for r in rs if name in r.metrics and isinstance(r.metrics[name]["value"], (int, float))]
            tags = {r.metrics[name]["tag"] for r in rs if name in r.metrics}
            if vals:
                metrics[name] = tagged(round(mean(vals), 2), _agg_tag(tags), evidence=f"mean n={len(vals)}")
        agg[variant] = {"scores": scores, "metrics": metrics, "n": len(rs)}
    return agg


def write_results_md(exp_dir: Path, config: ExperimentConfig, agg: dict, cells: list, k: int, json_path: Path) -> None:
    """人读摘要 + evidence_pointer。收敛模式由 optimize 阶段补写。"""
    try:
        pointer = json_path.relative_to(exp_dir)
    except ValueError:
        pointer = json_path
    lines = [
        f"# Results — {config.name}", "",
        f"- skill_under_test: `{config.skill_under_test}`",
        f"- cells: {len(cells)}（variant×harness×model）× k={k}",
        f"- evidence_pointer: `{pointer}`",
        "- generated_by: eval-cs-skill/scripts/runner.py", "",
        "## Aggregate（每个数值带认知诚实 tag）", "",
        "| variant | 指标 | 值 |", "|---|---|---|",
    ]
    for variant, a in sorted(agg.items()):
        for name, t in sorted(a.get("scores", {}).items()):
            lines.append(f"| {variant} | {name} | {render_tagged(t)} |")
        for name, t in sorted(a.get("metrics", {}).items()):
            lines.append(f"| {variant} | {name} | {render_tagged(t)} |")
    lines += ["", "## 收敛模式", "", "（optimize 阶段填：V_instance∧V_meta 是否达标、留/杀了哪些变体）", ""]
    (exp_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="eval-cs-skill eval runner")
    p.add_argument("--experiment", required=True)
    p.add_argument("--harness")
    p.add_argument("--model")
    p.add_argument("--variant")
    p.add_argument("--scorer", action="append", help="可多次；默认取 config.scorers")
    p.add_argument("--k", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--confirm", action="store_true", help="确认超预算仍执行")
    p.add_argument("--out")
    p.add_argument("--fresh", action="store_true", help="忽略并删除已有 checkpoint，从头跑")
    p.add_argument("--offset", type=int, default=0, help="跳过前 M 个 fixture（分段用）")
    p.add_argument("--limit", type=int, help="只跑 offset 起 N 个 fixture（分段用，每段配独立 --out）")
    args = p.parse_args(argv)

    exp_dir = Path(args.experiment).resolve()
    config = load_config(exp_dir)
    k = args.k if args.k is not None else config.k
    scorer_names = args.scorer or config.scorers
    fixtures = load_fixtures(exp_dir, config.fixture_classes)
    if args.offset or args.limit:
        fixtures = fixtures[args.offset: (args.offset + args.limit) if args.limit else None]
    if not fixtures:
        print(f"[eval-cs-skill] 无 fixtures：{exp_dir}/fixtures/{config.fixture_classes}", file=sys.stderr)
        return 2
    cells = build_matrix(config, args)

    for issue in judge_issues(config):
        print(f"[eval-cs-skill][judge] {issue}", file=sys.stderr)

    est = dry_run(config, fixtures, cells, k, exp_dir)
    print(f"[eval-cs-skill] 预估成本 ${est['est_total_usd']} / 预算 ${est['budget_usd']} "
          f"(cells={est['cells']} × fixtures={est['fixtures']} × k={k})")
    if args.dry_run:
        if args.out:
            write_json(Path(args.out), est)
        return 0
    if est["est_total_usd"] > config.budget_usd and not args.confirm:
        print(f"[eval-cs-skill] 阻断：预估 ${est['est_total_usd']} 超预算 ${config.budget_usd}；加 --confirm 放行。", file=sys.stderr)
        return 3

    out_path = Path(args.out) if args.out else exp_dir / "artifacts" / "analysis" / f"exp-{config.name}-results.json"
    checkpoint_path = out_path.parent / (out_path.name + ".partial.jsonl")
    if args.fresh:
        checkpoint_path.unlink(missing_ok=True)
    _, resumed_keys = _load_checkpoint(checkpoint_path)
    if resumed_keys:
        print(f"[eval-cs-skill] resume：跳过 {len(resumed_keys)} 个已完成 cell（checkpoint={checkpoint_path.name}）")
    results = run(config, fixtures, cells, scorer_names, k, exp_dir, checkpoint_path)
    agg = aggregate(config, results)
    payload = {
        "experiment": config.name,
        "skill_under_test": config.skill_under_test,
        "generated_by": "eval-cs-skill/scripts/runner.py",
        "k": k, "scorers": scorer_names,
        "cells": [f"{v}|{h}|{m}" for v, h, m in cells],
        "aggregate": agg,
        "runs": [r.to_dict() for r in results],
    }
    write_json(out_path, payload)
    checkpoint_path.unlink(missing_ok=True)  # final 已落盘，清理中间 checkpoint
    if not args.out:  # 默认路径运行才写 results.md 到实验目录（测试传 --out 不 clobber）
        write_results_md(exp_dir, config, agg, cells, k, out_path)

    print(f"[eval-cs-skill] 完成 {len(results)} runs → {out_path}")
    for variant, a in agg.items():
        rec = a["scores"].get("recall")
        if rec:
            print(f"  {variant}: recall = {render_tagged(rec)} (n={a['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
