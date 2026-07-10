---
doc_type: feature-goal-protocol
feature: 2026-07-10-cs-router-direct-dispatch
status: complete
created: 2026-07-10
---

# cs-router-direct-dispatch Goal Protocol

## 终态优先

先读 `goal-state.yaml`。`stage: complete` 且 `status: passed` 是终态；review、QA、acceptance 与 checklist 仓库事实一致时，输出 `CS_FEATURE_GOAL_COMPLETE`，不得重新派发 driver 或重复实现。

若 state 与产物不一致，以仓库事实修正 state，再从最早未完成阶段恢复。

## 执行 Loop

1. 读取 design、checklist、goal-plan、goal-state。
2. implementation 按 checklist 顺序执行；行为改动使用 TDD micro-loop，留下 RED/GREEN/VERIFY，例外写 `TDD exception`。
3. 运行 implementation gates 与 checklist CMD-001..005，保存真实基线和失败归因。
4. 进入 `cs-code-review`；blocking 只做 review-fix，之后重跑 review。
5. review passed 后进入 `cs-feat` QA；failed/blocked 只做 qa-fix，并重跑 review 与 QA。
6. QA passed 后进入 acceptance，逐条更新 checklist checks 与必要长期文档。
7. acceptance passed 且无 handoff 时，先写 `stage: complete` / `status: passed`，再输出完成标记。

Goal 模式接管普通阶段的等待点，但不绕过 design、review、QA、acceptance 或 TDD gate；只有 handoff 条件才停。每个 stage 变化立即写 `goal-state.yaml`，step 进度写 ledger，恢复时不重复已完成 step。

## Handoff

命中以下任一项，先写 `stage: handoff` / `status: blocked` / `handoff_reason` / `handoff_next`：

- 需要改变 approved design、公开契约或 feature 范围。
- 独立 reviewer pending/failed/blocked 且无用户降级。
- 同一失败项三轮仍不通过。
- 外部凭证/环境缺失导致核心行为无法判断。
- 用户要求暂停、改方向或终止。

然后输出：

```text
CS_FEATURE_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```

## 当前完成证据

- checklist：4 steps done，19 checks passed。
- review：round 2 `passed`，`reviewer: subagent+ocr`。
- QA：`passed`，Opus runner 16/16 场景符合。
- acceptance：`passed`，final audit targeted 92 / full 215 / runtime ok / diff check ok。

```text
CS_FEATURE_GOAL_COMPLETE
```
