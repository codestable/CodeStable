# cs-goal 参考

`cs-goal` 触发后，用本文件查看模板和恢复规则。

## 报告语言

写报告前读取 `.codestable/attention.md`。如果其中有报告语言策略，按策略执行；没有时使用
owner 当前对话语言。不要在本技能中硬编码必须双语。

默认使用无后缀 canonical 报告路径。只有 `.codestable/attention.md` 明确要求多语言副本时，
才添加语言后缀副本。

## Directory

```text
.codestable/goals/YYYY-MM-DD-{slug}/
├── state.yaml
├── goal.md
├── functional-acceptance.md
└── iterations/
    └── 001.md
```

`{slug}` 是简短英文 kebab-case，日期是 goal 创建日期。带日期的目录名是文件系统 unit；
`state.yaml` 的 `goal` 字段保留裸 slug。已有匹配 active goal 时复用，不创建重复目录。

`functional-acceptance.md` 只在终端验收 gate 创建，不在 goal 开始时创建空文件。

如果 attention 明确要求语言变体，使用 `goal.{lang}.md`、
`functional-acceptance.{lang}.md` 和 `iterations/{nnn}.{lang}.md` 这类后缀副本。
`state.yaml` 仍是机器 source of truth。

## state.yaml Schema

```yaml
schema_version: 1
goal: "{slug}"
status: active # active | complete | blocked
objective: "{owner-level outcome}"
start_point: "{known starting condition}"
acceptance:
  - "{observable done signal}"
non_goals:
  - "{explicitly out of scope}"
budget:
  kind: none # none | time | iterations | token | owner-defined
  limit: null
current_iteration: 0
next_action: "{smallest useful next attempt}"
blocker_signature: null
blocker_count: 0
owner_stop: null
updated_at: "YYYY-MM-DD"
```

恢复优先级：

1. `state.yaml`
2. latest iteration frontmatter
3. Markdown body

## 起点报告

`goal.md` 是由 interview / grill 生成的持久起点报告，必须在实现开始前存在，并包含：

- objective;
- starting point;
- acceptance criteria;
- non-goals;
- owner decisions;
- unresolved assumptions;
- next action.

这些报告只是面向人的上下文。`state.yaml` 仍是机器 source of truth，避免后续 agent 从
报告正文推断状态。

## 下一个 Iteration 编号

`state.yaml.current_iteration` 表示最后一个已完成 iteration，不表示下一次进行中的尝试。

修改 `current_iteration` 前，按以下方式计算下一个 `{nnn}`：

```text
max(state.yaml.current_iteration, highest existing iterations/{nnn}*.md) + 1
```

用三位数格式写入 `iterations/{nnn}.md`，然后让 `state.yaml.current_iteration` 等于该
已完成编号。不要覆盖已有 iteration 文件。只有 attention 要求时才添加语言后缀副本。

## goal.md Template

标题使用项目报告语言，但保留这些章节语义：

```markdown
---
doc_type: goal
goal: {slug}
status: active
---

# {Goal Name}

## Objective

## Starting Point

## Acceptance Criteria

## Non-Goals

## Decisions And Assumptions

## Current State

## Next Action
```

## Iteration Frontmatter

```yaml
---
doc_type: goal-iteration
goal: "{slug}"
iteration: 1
status_after: active # active | complete | blocked
next_action: "{same meaning as state.yaml}"
blocker_signature: null
updated_at: "YYYY-MM-DD"
---
```

## Iteration 标题

标题使用项目报告语言，但保留这些章节语义：

```markdown
# Iteration 001

## Current Understanding

## Implementation Approach

## Changes This Iteration

## Verification Evidence

## Problems Encountered

## Next Attempt

## State Update
```

## Iteration 规则

- 只在 iteration 结束时写报告。
- 即使 iteration 失败，也要包含 fresh verification evidence。
- 如果没有改动，明确说明并解释学到了什么。
- 保留历史失败尝试，不要把它们改写成成功。
- 和 iteration 报告同步更新 `state.yaml`，让恢复时看到的人读状态、已完成 iteration 和
  next action 一致。

## 功能验收报告

在 `status: complete` 前，按 `.codestable/reference/execution-conventions.md` 的
Task agent 选择规则启动 Task agent，做面向产品的功能验收。结果写入
`functional-acceptance.md`。

报告必须包含：

- reviewer 和 Task agent role。
- Task agent id / run id、关闭结果或关闭失败 warning。
- 已检查的 acceptance criteria。
- 测试之外的 functional evidence。
- verdict：pass、fail 或 inconclusive。
- residual risks 和 follow-up。
- 引用本次验收的 final iteration。

测试、lint 和 build 是验证证据，但完成必须有 Task agent 功能验收。Task agent 结果消费后
按生命周期关闭；若启动失败，先处理容量恢复重试，仍失败或未授权时写 `approval-report.md`
并 owner-stop，不要把 goal 标为 complete。

## Owner Stop 记录

停止时更新 `state.yaml`：

```yaml
status: blocked
blocker_signature: "{stable short phrase}"
blocker_count: 3
owner_stop: "{question or approval needed}"
next_action: "Wait for owner decision on {topic}."
```

最新 iteration 报告必须说明：

- 需要什么决策。
- 为什么 AI 不能安全继续。
- 选项或期望回答形态。
- owner 回答后会发生什么。

## 与其他流程的关系

适用规则时，`cs-goal` 可以创建或引用 feature、issue、refactor、roadmap 或 decision
产物。goal state 仍是自主迭代的包装层；子产物仍是各自 workflow 的 source of truth。
