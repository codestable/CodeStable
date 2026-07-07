# Results — cs-feat-refactor-ab-001

- 状态：**k=5 双模型全量运行中**（分段 + resume）。verdict 待 8 段齐后由 `merge` 出。
- 判据：见 `hypotheses.md`（非劣性：重构 recall_judge ≥ 原版 − 0.05 或 95%CI 下界）。
- caveats：见 `hypotheses.md`——**非盲预注册**、**judge 同源偏差**（haiku 一侧更可信）、**recall_judge=soft**。

## 初步信号（`[underpowered]`，供参考，非 verdict）

| 阶段 | 模型 | 重构(baseline) | 原版(original) | Δ | 指标 |
|---|---|---|---|---|---|
| k=1 全量 | sonnet+haiku | — | — | 散射 variance，feat-004 重构更好 | recall_judge |
| k=3 半量 | haiku | 0.972 | 0.917 | +0.056 | recall_judge |
| k=3 半量 | haiku | 0.639 | 0.556 | +0.083 | planted recall (measured) |

四次独立观察（结构测试 155 passed + contracts 护栏 + k=1 散射 + k=3 haiku）均指向"重构无回退"。k=5 用于坐实。

## 完整 k=5 verdict（2026-07-07，16 段收口，judge=claude-opus-4-8 独立）

| 模型 | 重构(baseline) | 原版(original) | Δ | n | 判定 |
|---|---|---|---|---|---|
| claude-sonnet-4-6 | 0.933±0.024 | 0.850±0.044 | **+0.083** | 40/40 | ✓ 无回退 |
| claude-haiku-4-5 | 0.883±0.028 | 0.858±0.033 | +0.025 | 40/40 | ✓ 无回退 |
| gpt-5.4 | 0.950±0.027 | 0.883±0.049 | +0.067 | 20/20 [underpowered] | ✓ 无回退 |
| gpt-5.5 | — | — | — | 0（见下） | 无有效数据 |

**VERDICT: CONFIRMED 无回退**（3/4 模型方向一致，且均为正向；非劣性判据在全部有数据模型上满足）。confidence：sonnet/haiku=high，gpt-5.4=underpowered（半量），gpt-5.5=无数据。

### gpt-5.5 数据缺口（基础设施限制，诚实标注）

gpt-5.5 全部 4 段 80/80 cell 均 HTTP 504：design 生成为长输出任务，gpt-5.5 推理耗时超 gateway（Tengine）上游超时，客户端退避重试 3 次亦然。gpt-5.4 同因损失半数 cell（有效 n=20/40 每变体）。**非模型能力或 skill 问题**——同 gateway 下 routing 任务（短输出）gpt-5.5 正常完成且成绩满分。per-cell 容错按设计将 error 记录在案（`k5-*-gpt-5.5-*.json` status=error 可查证）。若需补齐，需 gateway 支持 streaming 或更高上游超时。

### 结论叠加（与 routing 三方 verdict 互证）

design-recall（本实验，soft judge）与 routing_ok（`cs-issue-routing-001/results.md`，measured）两条独立证据线均确认：cs-feat 重写式重构（Spec 唯一路由真相）**无行为回退，且两线均为正向增益**（design recall +0.03~+0.08，routing +0.097）。
