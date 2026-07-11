# CS Feedback Evidence Pipeline Goal Protocol

## 1. Goal Mode

本 goal 已通过独立 design review 并由用户确认。driver 必须连续执行 implementation → code review → QA → acceptance；普通阶段的用户 checkpoint 改为写报告、state 和证据，只有 handoff 条件命中时停止。

每轮开始先读取：

- `goal-state.yaml`
- `goal-plan.md`
- `cs-feedback-evidence-pipeline-design.md`
- `cs-feedback-evidence-pipeline-checklist.yaml`
- `.codestable/attention.md`

以仓库事实修正 stale state；保留用户已有改动，不做 destructive git 操作。

## 2. Implementation Loop

1. 把 `goal-state.yaml` 更新为 `stage: implementation/status: running`。
2. 按 checklist 顺序执行；行为 step 使用 RED → GREEN → VERIFY，例外写 `TDD exception` 和替代证据。
3. 每个 step 完成立即把 checklist status 改为 `done`，并向 ledger 追加 `{step, status, evidence, commit_scope}`；续跑以 ledger + `git log` 为准，不重复已完成 step。
4. 运行 goal-plan 的 implementation gates，保存 command output、diff summary、隐私负向证据与 DoD 结果。
5. 全部通过后写 `stage: review/status: ready`。

## 3. Code Review Loop

1. 运行 `cs-code-review`，必须启动 Paseo reviewer：`provider=claude`、`model=claude-fable-5`、`thinkingOptionId=high`，使用 provider 的 plan/read-only 等价 mode。
2. review 必须分别给出 spec 合规与代码质量结论，并写 `cs-feedback-evidence-pipeline-review.md`。
3. 有 blocking/important 时写 `stage: review/status: fixing`，回 implementation 做最小修复，再写 `review/ready` 并用同一模型约束重新独立审查。
4. Fable 因额度或 provider 异常无法完成时必须 handoff；用户没有授权任何 reviewer 模型降级。
5. passed 后写 `stage: qa/status: ready`。

## 4. QA Loop

1. 运行 `cs-feat` QA，覆盖 design 的 16 个场景、全部命令、runtime/package baseline 和 cleanliness。
2. QA failed/blocked 时写 `stage: qa/status: fixing`，回 implementation 修复；修完必须重新跑 code review 与 QA。
3. QA passed 后写 `stage: acceptance/status: ready`。

## 5. Acceptance Loop

1. 运行 `cs-feat` acceptance，从代码、tests、runtime copy、文档和报告核验 21 checks。
2. 只更新 checklist checks 为 `passed/failed`，不改写 checks 内容。
3. 所有 checks、review、QA 和 required artifacts 通过后，先写 `stage: complete/status: passed`，再输出 `CS_FEATURE_GOAL_COMPLETE`。

## 6. Handoff

以下任一情况必须先写 `stage: handoff/status: blocked`、`handoff_reason`、`handoff_next`，再输出标记：

- 需要改变 approved design、feature 范围、公开契约或 ADR 方向。
- Fable 5 high 独立 reviewer pending/failed/unavailable。
- 同一失败项三轮修复仍不通过。
- 外部凭证或环境缺失导致核心行为无法判断。
- 用户要求暂停、改方向或终止。

```text
CS_FEATURE_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```

## 7. Literal Goal Command

```text
/goal "执行 CodeStable feature 目录 .codestable/features/2026-07-10-cs-feedback-evidence-pipeline 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md、cs-feedback-evidence-pipeline-design.md、cs-feedback-evidence-pipeline-checklist.yaml；这是已由用户确认 design 后的 goal 模式。按 goal-protocol.md 连续执行 cs-feat implementation、cs-code-review、cs-feat QA、cs-feat acceptance；implementation 的代码行为 step 默认用 TDD micro-loop，必须留下 RED/GREEN/VERIFY evidence，不能 TDD 时写 TDD exception 和替代证据；review blocking 时做 review-fix并重跑 review；QA failed / blocked 时做 qa-fix 并重跑 review 和 QA。所有 review gate 固定使用 Paseo Claude Fable 5、high thinking，不可用时 handoff，不得降级。只有当 CS_FEATURE_GOAL_COMPLETE 出现在 transcript 中，且 review passed、QA passed、acceptance passed、没有 CS_FEATURE_GOAL_HANDOFF，本 goal 才算完成。"
```
