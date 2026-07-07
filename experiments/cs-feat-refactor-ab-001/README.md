# cs-feat-refactor-ab-001 — 真实 api 评估

验证 cs-feat prompt-as-code 重构（`## Spec` + `## Workflow` + frontmatter `contracts`）未使 design 生成行为回退。

## ⚠️ 与 mock 自测 config 的区分（重要）

experiments/ 下**大多数 config 是 mock**（`harnesses:["mock"]` / `model_list:["mock-model"]`）——那是**管线自测 fixture**，让 pytest 离线、确定、免费地验证 runner/scorer/metrics 逻辑（见 `tests/test_cs_skill_eval.py::test_runner_end_to_end`）。**它们不产生真实评估结论。**

**本实验相反，是真实 api 评估**：`harnesses:["api"]` + 真实模型 + 真实 judge。

判别一次 run 是真是假，看 `wall_ms`：真实 api 是几千~几万毫秒（观测到 26908ms），**mock 恒 = 1**。

## 怎么跑（真实 api）

credentials **不入库**（放本地 env，如 `/tmp/cs-eval-env.sh`，含 gateway key）。

```bash
source /tmp/cs-eval-env.sh        # 提供 gateway credentials（不入库）
R=.claude/skills/eval-cs-skill/scripts/runner.py
python3 $R --experiment experiments/cs-feat-refactor-ab-001 --dry-run   # 成本预估（超 budget_usd 阻断）
python3 $R --experiment experiments/cs-feat-refactor-ab-001 --out artifacts/full.json
```

### 分段跑（长跑抗环境 kill）

真实 api 每 call 数十秒，全量 k=5 长跑易被环境回收。用 `--limit/--offset` 切 fixture + resume（每 cell 落盘；`--out` 相同则自动续；每段配独立 `--out`）：

```bash
# 按 variant×model×fixture-half 分 8 段，每段独立 out；被 kill 重跑即段级续
for V in baseline original; do for M in claude-sonnet-4-6 claude-haiku-4-5; do for O in 0 4; do
  out=artifacts/k5-$V-$M-$O.json          # artifacts/ 已 gitignore
  [ -f "$out" ] && continue
  python3 $R --experiment experiments/cs-feat-refactor-ab-001 \
    --variant $V --model $M --offset $O --limit 4 --k 5 --out "$out"
done; done; done
```

## 文件

| 文件 | 说明 |
|---|---|
| `config.json` | 真实评估配置（api + 双模型 + judge=sonnet） |
| `hypotheses.md` | 假设 + 判据 + **诚实 caveats**（非盲注册 / judge 同源偏差 / soft） |
| `fixtures/` | 8 个 design 生成样本（与 cs-feat-001 同源，冻结复现） |
| `variants/original.md` | 重构前 cs-feat 快照（A/B 对照；`baseline` 变体读 live 重构版） |
| `results.md` | verdict（人读摘要） |
| `artifacts/` | 结果生成物（**gitignore**，可复现） |
