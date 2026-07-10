---
name: cs
description: CodeStable 路由入口。触发：用户显式调用 cs、询问该用哪个 skill、请求介绍体系，或诉求未收敛；明确行动请求路由后在当前 run 继续。
argument-hint: "[request]"
contracts:
  - grep: "HumanCheckpoint ClarifyRoute"
  - grep: "当前 run 继续"
  - grep: "Dispatch: continuing-current-run | recommendation-only"
  - grep: "原始诉求原样传递"
  - not-grep: "L0-L4"
---

# cs

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

这里 preflight 只记录缺失状态，不在入口模式判定前自动转交：仅 Execute 进入 onboard 串行前置 gate，Advise / Explain 保持只读。

`cs` 是窄路由入口：先判断用户要执行、咨询、了解体系还是补充信息，再选择一个推荐主 skill。它不写下游产物、不模拟目标 workflow，也不绕过目标 skill 的 checkpoint。

旧阶段技能继续作为兼容入口存在，但 `cs` 只选择主入口。

## 入口意图与最小恢复

本次调用参数：$ARGUMENTS

参数非空且不是字面 `$ARGUMENTS` 时，把它作为本轮诉求；否则使用用户原话。无参数默认行为：用户原话也没有具体诉求时进入 Explain，输出体系速读。

入口模式先于路由目标。完成首次 preflight 后，同一会话复用 attention / runtime 结论：

- 明确的新行动或咨询不扫描全部活动目录；目标 skill 自己恢复所需仓库事实。
- 只有“继续”“下一步”“接着做”这类续作请求，才浅扫 `features/issues/roadmap/goals/refactors/audits/brainstorms/feedback`。
- 续作只有一个活动单元时按其类型选主入口；多个候选时返回 `HumanCheckpoint ClarifyRoute`，只问一个聚焦问题。
- `.codestable/attention.md` 缺失不授权 `cs` 创建文件；Execute 按“onboard 串行前置 gate”处理，Advise / Explain 不自动接入仓库。

## Spec

```haskell
data IntakeMode = Execute | Advise | Explain | Ambiguous

data RouterOutcome
  = RoutedTo SkillName
  | Completed Recommendation
  | Completed Overview
  | HumanCheckpoint ClarifyRoute
  | NeedsHuman TargetUnavailable

route :: Request -> RouterOutcome
route request = classifyIntake request >>= selectTarget >>= dispatch

Execute   -> RoutedTo target
Advise    -> Completed Recommendation
Explain   -> Completed Overview
Ambiguous -> HumanCheckpoint ClarifyRoute
```

模式判定：

| 信号 | IntakeMode | 行为 |
|---|---|---|
| “修复 / 实现 / 更新 / 扫描 / 继续”等明确行动 | Execute | 选唯一主入口并同轮转交 |
| “该用哪个 skill / 应该走什么流程 / 你建议怎么做” | Advise | 只推荐，不启动 workflow |
| 只说 `cs`、请求介绍 CodeStable、没有具体诉求 | Explain | 输出体系速读 |
| 有行动意图，但信息不足以区分相邻流程 | Ambiguous | 只问一个能区分路线的问题 |

不要只按问句形式判断。比如“能帮我修这个报错吗”仍是 Execute；“这种报错该走哪个 skill”是 Advise；“帮我改一下”无法区分 bug / feature / refactor，是 Ambiguous。

## 路由优先级

专用 workflow 优先于 `cs-goal`：诉求已经明确属于 feature / issue / refactor / docs / epic 等生命周期时，即使用户说“持续做到完成”，仍进入专用入口。只有用户给出独立终点、验收或预算，且没有更具体 workflow 时才选 `cs-goal`。

相邻路线按以下语义区分：

| 用户目标 | 路由目标 |
|---|---|
| 仓库接入、迁移、补 CodeStable 骨架 | `cs-onboard` |
| 明确终点 / 验收 / 预算的自主达成，且无专用 workflow | `cs-goal` |
| 想法模糊、先聊、方向摇摆 | `cs-brainstorm` |
| 新功能、功能改造 | `cs-feat` |
| bug、报错、既有行为异常 | `cs-issue` |
| 已知优化目标、行为等价的重构 / 拆分 / 性能改进 | `cs-refactor` |
| 主动扫描未知问题、系统审计、寻找可优化处 | `cs-audit` |
| 起草或更新 capability / requirement | `cs-req` |
| canonical 决策、ADR、术语或 context 边界 | `cs-domain` |
| 可复用经验、踩坑、调研结论 | `cs-keep` |
| 一两行每次都要知道的 attention 规则 | `cs-note` |
| 多 feature 系统能力、epic、roadmap | `cs-epic` |
| 本轮 diff / 合并前的 code review | `cs-code-review` |
| CodeStable skill 跑偏、规则不清、工具失败 | `cs-feedback` |
| 开发者 / 用户指南、API 参考 | `cs-docs` |
| 阶段收尾、全局文档与记忆卫生 | `cs-docs-neat` |

一个请求同一时刻只转交一个主入口。若用户同时给出两个独立诉求，返回 `HumanCheckpoint ClarifyRoute` 询问先后顺序，不并行加载两个目标。

## 转交协议

route brief 只用于 Execute / Advise：

```text
Route: {目标主入口}
Reason: {一句话判别依据}
Dispatch: continuing-current-run | recommendation-only
```

- Execute：输出 `continuing-current-run` 后，按已安装 skill 名称加载目标协议，原始诉求原样传递，并在当前 run 继续；route brief 不是最终答复。
- Advise：输出 `recommendation-only` 后结束，不加载目标协议、不写产物。
- Explain：直接输出体系速读，不伪造 route brief。
- Ambiguous：直接返回 `HumanCheckpoint ClarifyRoute`，不伪造 route brief；用户回答后同轮继续判定与转交，不要求重新调用命令。
- 目标 skill 无法加载时返回 `NeedsHuman TargetUnavailable`，报告目标与失败原因，不在 `cs` 内模拟目标流程。

`cs-onboard` 是串行前置 gate：未接入仓库收到 Execute 时，先判明原目标，再同轮加载 `cs-onboard`。onboard 自身的确认与写入 checkpoint 完整生效；完成后保留原始诉求和原目标，串行加载原目标 skill。若会话停在 checkpoint，本轮不越过它；后续轮次恢复时继续携带原始诉求和原目标，缺失时先向用户确认而不硬猜。

转交只加载协议，不扩大授权：目标 skill 的写入、外部通信、Task agent 和人工 checkpoint 规则继续生效。已完成的 preflight 结论可幂等复用，但目标 skill 仍按自己的协议恢复业务事实。

## Explain 输出

体系速读保持简短，并只介绍推荐主入口：

- 生命周期：`cs-feat` 覆盖 design、design-review、goal 包、impl、code review、QA、accept，并可由可见 driver 长程执行；另有 `cs-issue`、`cs-refactor`、`cs-epic`。
- 横切能力：`cs-code-review`、`cs-audit`、`cs-docs`、`cs-docs-neat`、`cs-feedback`。
- 需求与知识：`cs-req`、`cs-domain`、`cs-keep`、`cs-note`。
- 启动与探索：`cs-onboard`、`cs-brainstorm`、`cs-goal`。

主要产物位于 `.codestable/requirements/`、`roadmap/`、`goals/`、`features/`、`issues/`、`refactors/`、`audits/`、`brainstorms/`、`feedback/` 与 `compound/`。

## 兼容入口

以下旧技能名仍可直接使用，但只转入主入口；新文档和新提示词不得推荐它们：

- Feature：`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`
- Issue：`cs-issue-report`、`cs-issue-analyze`、`cs-issue-fix`
- Refactor：`cs-refactor-ff`
- Docs：`cs-doc-tutorial`、`cs-doc-api`
- Epic：`cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal`
