---
name: cs-goal
description: Goal 自主达成。触发：明确终点/验收/预算、持续迭代到完成，或 grill me 后开工。
---

# cs-goal

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-goal` 处理有界 goal：owner 给出起点和期望终态，CodeStable 先做轻量
interview / grill，动手前写起点报告，然后自主实现、验证、迭代；完成前必须请求
Task agent 做功能验收，并写 iteration 报告。报告正文遵守
`.codestable/attention.md` 中的项目报告语言；没有语言策略时，使用 owner 当前对话语言。

这是 goal 包装器，不替代 feature / issue / refactor 规则。goal 跨 capability
boundary、暴露 bug root cause，或需要行为不变的 refactor governance 时，要在 goal
iteration 中创建或引用对应 feature / issue / refactor 产物。

产物模板、`state.yaml` schema、报告标题和恢复规则见 `reference.md`。

---

## 启动

行动前：

1. 读取 `.codestable/attention.md`。
2. 如果存在，读取 `.codestable/reference/system-overview.md`。
3. 读取本技能的 `reference.md`。
4. 如果存在，读取 `.codestable/reference/goal-conventions.md`。
5. 如果存在，读取 `.codestable/reference/approval-conventions.md`。
6. 代码编辑、commit、finish 或 merge 前，如果存在，读取
   `.codestable/reference/worktree-conventions.md`；Task agent review / 验收前读取
   `.codestable/reference/agent-conventions.md`。
7. 检查 `.codestable/goals/` 中是否已有匹配的 active goal。
8. 当 goal 指向已有领域时，搜索 `.codestable/compound/` 和相关 feature / issue /
   refactor 文档。

如果缺少 `.codestable/`，路由到 `cs-onboard`。

---

## 使用场景

owner 表达有界目标时使用 `cs-goal`：

- "starting from this broken state, make the tests pass";
- "reach this acceptance result";
- "run autonomously and self-iterate";
- "keep trying until complete or blocked";
- "grill me first, then implement";
- "I care about the outcome, not the technical choices".

不要用于：

- 没有实现目标的纯 design、roadmap 或讨论请求。
- owner 还不知道终态的开放式 brainstorm。
- 不要求 AI 推进到完成的状态检查或 audit。

---

## 状态模型

沿用 Codex 简单 goal 状态：

```text
active | complete | blocked
```

`state.yaml` 是机器 source of truth，Markdown 面向人。恢复优先级：

1. `.codestable/goals/YYYY-MM-DD-{slug}/state.yaml`
2. latest iteration frontmatter
3. Markdown body text

只要 `state.yaml` 有明确值，就不要从报告正文推断当前机器状态。

---

## 阶段 1：Grill 对齐

创建新 goal 前总是先 grill。把 interview / grill 视为正式 goal 起点，不是一次性聊天。
保持简短，聚焦 owner 层面的信息。

最多问 3-5 个聚焦问题。每轮一个问题，配 2-4 个有实质差异的选项。除非答案会改变 goal
边界，否则不要问实现细节。

如果 grill 答案需要 owner 批准范围、路线、预算、风险或停止策略，且选项需要解释，先写
`.codestable/goals/YYYY-MM-DD-{slug}/approval-report.md`。简单澄清问题可以留在
chat；决策 checkpoint 必须有报告。

只收集：

- objective。
- starting point。
- acceptance / done signal。
- non-goals。
- 已给出的 budget 或 stopping preference。
- 本 goal 特有的 strict owner-stop conditions。

如果 owner 已给足信息，先总结再继续。任何代码编辑或自主实现尝试前，阶段 2 必须创建或
刷新起点报告。

---

## 阶段 2：创建或恢复 Goal

goal 生命周期目录：

```text
.codestable/goals/YYYY-MM-DD-{slug}/
├── state.yaml
├── goal.md
├── functional-acceptance.md
└── iterations/
```

目录名使用 goal 创建日期，保持和 feature / issue / refactor 目录风格一致。
`state.yaml` 的 `goal` 字段保留裸业务 slug。

`functional-acceptance.md` 只在终端验收 gate 创建，不在 goal 开始时创建空文件。

`goal.md` 是从 interview / grill 生成的持久起点报告，必须在实现前存在。内容包括
objective、starting point、acceptance criteria、non-goals、owner decisions、
unresolved assumptions 和 next action。保持简洁，只在 goal 边界或状态变化时更新。

默认使用无后缀 canonical 报告路径。如果 `.codestable/attention.md` 明确要求额外语言副本，
再添加 `goal.{lang}.md`、`functional-acceptance.{lang}.md`、
`iterations/{nnn}.{lang}.md` 这类后缀副本；默认不要求这些变体。

如果已有匹配的 active goal，要恢复它而不是创建重复目录，即使日期前缀不是今天。先读
`state.yaml`，再读匹配 `goal*.md` 的起点报告，然后读最新的
`iterations/{nnn}*.md`。如果缺起点报告，代码编辑前先根据 state 和 interview 证据重建。

---

## 阶段 3：自主迭代

一次 iteration 是一次连贯的实现 / 验证尝试，不是一条命令。

当 `state: active` 时循环：

1. 从 `state.yaml` 选择最小有用的下一次尝试。
2. 按既有 CodeStable 约束实现；适用时包括 worktree、review、spec-governance 和
   commit 规则。
3. 用 fresh 命令或证据验证。
4. 修改 `state.yaml.current_iteration` 前，根据 `state.yaml.current_iteration` 和已有
   `iterations/{nnn}*.md` 文件推导下一个三位数 iteration 编号；不要覆盖旧报告。
5. 为已完成尝试更新 `state.yaml`，留下 `current_iteration: {n}`。
6. 写该次完成 iteration 的 canonical 报告：`iterations/{nnn}.md`。只有
   `.codestable/attention.md` 要求时才添加语言后缀副本。
7. 除非触发 owner-stop 条件，否则自主继续。

不要每条命令后都写报告；报告是 iteration 摘要。不要仅凭普通测试证据把 goal 标成完成；
必须先运行终端功能验收 gate。

## 终端功能验收

把 `state.yaml.status` 改为 `complete` 前：

1. 用 fresh evidence 跑正常验证。
2. 按 `.codestable/reference/agent-conventions.md` 的 Task agent 选择规则启动
   Task agent，对记录的 owner acceptance criteria 和实际产品 / 产物行为做功能验收。
3. 把结果写入 `functional-acceptance.md`，包括 reviewer、scope、acceptance checks、
   functional evidence、verdict、residual risks 和 follow-up。
4. 结果被写入并引用后，按 Task agent 生命周期关闭该验收 agent；关闭失败只记录 warning。
5. 在 final iteration 中引用功能验收报告。

功能验收是面向产品的证据。它可以包括黑盒使用、产物检查、UI / API workflow 检查、
fixture 输出复核，或其他和 owner 相关的证明。单测、lint 和 build 是有用证据，但单独
不足以完成 goal。

如果 Task agent 无法启动或未获授权，先按 Task agent 生命周期处理容量失败重试；仍失败时写
`approval-report.md` 并 owner-stop。不要自验收 goal 为 complete。

## 严格 Owner Stop

只有以下情况才停下来问 owner：

- acceptance criteria 冲突，或已不足以判断完成。
- objective、start point 或 terminal condition 存在重大歧义。
- 继续会改变记录 goal 之外的长期 spec、public contract 或 capability boundary。
- 同一个 blocker 连续三次 iteration 重复出现。
- budget 已用尽或接近用尽。
- 下一步需要明确的人类风险接受、secrets、破坏性操作、外部购买、merge / deployment 批准。

普通技术选择、测试失败、实现备选和局部 refactor 由 AI 负责，除非跨过以上 stop 条件。

---

## Complete 与 Blocked 规则

只有 acceptance signal 已满足、Task agent 功能验收报告记录 passing verdict，且证据已写入
final iteration 时，才能标记 `complete`。

只有同一个 blocker 至少连续三次 iteration 重复，或 owner-stop 规则说明 AI 无法安全继续时，
才能标记 `blocked`。记录 `blocker_signature`、`blocker_count`、证据和需要的 owner
决策。问 owner 决策前，先在 goal 目录写 `approval-report.md`，除非最新 iteration 报告已经
包含完整决策上下文、选项、推荐、权衡、证据、后果和下一步。

如果 budget 在验收前结束，带审批上下文停下，不要假装完成。

---

## Exit

goal run 以下列状态之一退出：

- `complete`：acceptance evidence、Task agent 功能验收和 final iteration 均已写入。
- `blocked`：blocker 证据和 owner 问题已记录。
- `active`：iteration 报告和 next action 已记录，但当前回合或 budget 不足以继续。

最终回复要短；goal 完成时指向 `goal.md`、最新 iteration 报告和
`functional-acceptance.md`。

---

## Guardrails

- 不让 owner 选择日常技术细节。
- 不让报告正文覆盖 `state.yaml`。
- 不为同一 objective 创建重复 active goal。
- 有实质工作后不跳过 iteration 报告。
- 不仅凭测试标记完成，也不伪造 Task agent 验收。
- strict owner-stop 触发后不继续迭代。
- 每个 Markdown 产物必须少于 300 行；过长就拆分。
