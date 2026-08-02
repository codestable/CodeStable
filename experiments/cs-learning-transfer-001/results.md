# cs-learning-transfer-001 结果

状态：`pipeline-correction-prepared; final-models-not-run`。旧 source 已运行校准；当前候选尚未运行。

## 冻结与运行身份

- Freeze manifest：`freeze.json`（当前候选为 `prepared-awaiting-commit`）
- Frozen commit：`pending`
- Calibration：旧 source 有一次完整负结果、一次中断结果；当前候选 `pending`
- Final run：`pending`（两个 model family，六个 fixture，`k=5`）

## 离线 preflight

| fixture | golden hidden | naive hidden | golden regression | naive regression |
|---|---:|---:|---:|---:|
| `lt-feat-patch` | 1.0 | 0.0 | 1.0 | 1.0 |
| `lt-issue-reference` | 1.0 | 0.0 | 1.0 | 1.0 |
| `lt-refactor-events` | 1.0 | 0.0 | 1.0 | 1.0 |
| `lt-epic-sequence` | 1.0 | 0.0 | 1.0 | 1.0 |
| `lt-unrelated-display` | 1.0 | 0.0 | 1.0 | 1.0 |
| `lt-stale-reference-v2` | 1.0 | 0.0 | 1.0 | 1.0 |

A oracle 另经 seed-red / known-golden-green 校准：seed 为 `0/4`，known golden 为 `4/4`。stale hook
在两侧各执行一次，先把 A 侧 reference lookup 迁移到 `opaque-v2`，同时保持非 lesson manifest 同源且
lesson 字节不变。dry-run 估算 240 次 agent invocation、20 次 deterministic hook，成本
`$3.41 [soft]`，低于 `$50` 预算；该估算不是实际花费。

## Primary 结果

| metric | result | tag |
|---|---:|---|
| overall treatment hidden rate | pending | `[measured]` after run |
| overall control hidden rate | pending | `[measured]` after run |
| overall paired delta | pending | `[measured]` after run |
| Claude paired delta | pending | `[measured]` after run |
| Codex paired delta | pending | `[measured]` after run |
| wins / losses / ties | pending | `[measured]` after run |
| unrelated no-regression | pending | `[measured]` after run |
| stale retired rate | pending | `[measured]` after run |
| structural integrity pass rate | pending | `[measured]` after run |
| operational attempts / resolved / unresolved | pending | `[measured]` after run |
| total cost | pending | harness usage tag after run |

## Verdict

`pending`。必须逐条应用 `hypotheses.md` 的复合门槛；校准、单 family 或 `[underpowered]` 结果不能
写成确认结论。

## Evidence pointers

- 结构化最终结果：`artifacts/analysis/exp-cs-learning-transfer-001-results.json`（运行后生成，gitignored）
- Pair checkpoint：同目录 `.partial.jsonl`（运行中 append-only；中断或含 errors/invalid 的结果保留，
  无 errors/invalid 的完整结果落盘后删除）
- Tracked 摘要：本文件只记录聚合指标、冻结 commit、异常与必要的 hash/diff 指针，不复制完整响应。

## 负结果与异常

- `9fb5d0f` 的 `k=2` calibration 完整结束：Claude 12/12 为 `pipeline-failed`，Codex 12/12 为未解决
  operational error，0 个完成 pair，成本 `$2.003669 [soft]`，verdict 为 `REJECTED / underpowered`。
  最终 JSON SHA-256 为 `afce3136...959e6`，49 行 checkpoint 为 `c72675d0...38ca19`。该 source 后来因
  pipeline/probe 修正被取代，不计入当前候选的接受证据，但负结果原样保留。
- `92b12ba` 的 `k=2` calibration 完整结束：Claude 12/12 为 `pipeline-failed`，Codex 12/12 为未解决
  operational error，0 个完成 pair，成本 `$1.886275 [soft]`，verdict 为 `REJECTED / underpowered`。
  最终 JSON SHA-256 为 `4cae6c21...9820a8`，checkpoint 为 `3bb74da8...d788880`。
- `652949c` 的独立 calibration 被 owner 中断，无最终 JSON、无 verdict。append-only checkpoint 保留
  53 行（1 个 header + 52 个事件）：18 个 durable start、17 个 invocation complete、17 个
  `A oracle failed` 终态；最后一个
  invocation 未完成。Claude 已完成 12 个 A cell；Codex 已完成 5 个。checkpoint SHA-256 为
  `61efb61b...ac052`，不得恢复、删除或用 `--fresh` 覆盖。
- 17 个 A 终态分为：Claude 8 个 checks-only 失败、Claude 4 个 allowlist/lesson mutation 失败、Codex
  5 个 control mutation 失败。旧 checkpoint 没有路径或 check 明细，不能从结果后猜 4 个越界路径。
- 中断结果暴露 runner 丢弃 A check 证据、sequence prompt 缺少非交互上下文并错误推动额外流程产物，
  以及 Git index stat-cache 刷新被误判为 staging 变化。当前候选改为读取 seed 的真实 attention、禁止为
  评测模拟额外流程产物，并持久化后续失败的有界诊断；不改 fixture、hypothesis、primary metric、预算
  或样本。若 4 个 mutation 类在新 source 重现，以新诊断修正，不删除样本或倒推旧路径。
- 两次完整 calibration 的已知软成本合计 `$3.889944`；`652949c` 中断运行的实际成本另保留在 journal，
  因无最终聚合结果不在此伪造总数。
