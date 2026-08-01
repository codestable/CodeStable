# cs-learning-transfer-001 结果

状态：`preflight-passed; real-models-not-run`。本文件不包含模型自评或预填的真实运行数值。

## 冻结与运行身份

- Freeze manifest：`freeze.json`（待与冻结输入一起提交）
- Frozen commit：`pending`
- Calibration：`pending`（仅允许 `k=2`，不能作为接受证据）
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
- Pair checkpoint：同目录 `.partial.jsonl`（仅中断恢复；完整结果落盘后删除）
- Tracked 摘要：本文件只记录聚合指标、冻结 commit、异常与必要的 hash/diff 指针，不复制完整响应。

## 负结果与异常

待运行后如实填写。Deterministic failure 必须保留并阻断；operational error 必须分别报告尝试、已解决与
未解决，只有完整 pair 能标为 resolved，成功重试仍计入成本。不得删除失败 fixture、半 pair 或 adapter
error 来改善结果；`--fresh` 只允许 header-only journal，其他运行证据与结果必须换新 `--out`。
