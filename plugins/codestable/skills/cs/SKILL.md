---
name: cs
description: CodeStable 路由入口。触发：用户只说 cs/该用哪个 skill/介绍体系，或诉求未收敛。
argument-hint: "[request]"
---

# cs

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs` 是轻量分诊入口，只把开放式诉求路由到推荐主入口。它不写 spec、不改 `.codestable/` 产物、不替下游流程执行阶段。

旧阶段技能长期保留为兼容入口，但 `cs` 的主路径不再路由到它们。

---

## 收到调用先做的扫描

回应前每次都做：

1. 看仓库有没有 `.codestable/`。
2. 已接入：读 `.codestable/attention.md`；若有 `.codestable/reference/system-overview.md` 也读；扫描进行中的 `features/`、`issues/`、`roadmap/`、`refactors/`。
3. 未接入：提示先走 `cs-onboard`。
4. 看本次调用参数（$ARGUMENTS）：非空且不是字面 `$ARGUMENTS` 时，作为用户诉求匹配路由表。
5. 参数为空再看用户原话：开放式还是带具体诉求；带诉求匹配路由表，没诉求给体系速读。

---

## 体系速读

CodeStable 编排的是软件生命周期，不是 agent 团队。主要实体都落在 `.codestable/`：

```text
.codestable/
├── requirements/    需求 + 领域模型
├── roadmap/         epic 的内部规划/goal 存储模型
├── goals/           目标实体
├── features/        feature 生命周期产物
├── issues/          issue 生命周期产物
├── refactors/       refactor 生命周期产物
├── audits/          审计发现
└── compound/        知识沉淀
```

生命周期主流程入口：

- `cs-feat`：feature 端到端，内部推进 design、design-review、impl、code review、QA、accept。
- `cs-issue`：issue 端到端，内部推进 report、analyze、fix、code review。
- `cs-refactor`：行为等价重构，内部选择标准模式或 fastforward mode。
- `cs-epic`：大需求端到端，用户叫 epic，内部暂用 roadmap 存储模型。
- `cs-docs`：对外文档写作，覆盖 tutorial / API reference。
- `cs-docs-neat`：阶段收尾、文档同步、agent 入口和记忆整理。
- `cs-code-review`：横切实现审查 gate。

接入、goal、brainstorm、审计、需求、领域和知识沉淀等入口也可由 `cs` 路由；完整集合见下方场景路由表。

---

## 场景路由表

匹配用户诉求后输出 route brief：

```text
Route: {目标主入口}
Context: {L0-L4}
Reason: {为什么这条路由合适}
Not routing to: {排除的相邻流程，如有歧义}
Escalation: {什么情况会抬升 context level}
Next: {用户该触发什么，或本入口会决定什么}
```

| 用户说什么 / 想做什么 | 路由到 |
|---|---|
| 仓库还没有 `.codestable/` | `cs-onboard` |
| 限定起点和终点 / 自主迭代直到完成 / goal | `cs-goal` |
| 想法模糊 / 先聊聊 / 不知道是不是新功能 | `cs-brainstorm` |
| 新功能 / 加个 X / 实现 XX / feature 中间问下一步 | `cs-feat` |
| BUG / 异常 / 报错 / 文档错了 / issue 中间问下一步 | `cs-issue` |
| 代码优化 / 重构 / 拆分 / 性能，且行为不变 | `cs-refactor` |
| 审查系统 / 扫描 bug / 审计代码 / 哪里可以优化 | `cs-audit` |
| 补 / 更新需求文档 | `cs-req` |
| 拍板技术决策 / 加领域术语 / 分 context | `cs-domain` |
| 大需求拆解 / 一个系统 / epic / roadmap / 执行整个 roadmap | `cs-epic` |
| 合并前审一下 / code review / 准备 PR / merge | `cs-code-review` |
| 值得记下来 / 踩坑 / 技巧 / 决策 / 调研 | `cs-keep` |
| 一两行项目注意事项 / 命令陷阱 / 记到 attention.md | `cs-note` |
| 开发者指南 / 用户指南 / API 参考 | `cs-docs` |
| 阶段收尾 / 整理文档 / 同步 README、CLAUDE.md、AGENTS.md 或记忆 | `cs-docs-neat` |

判不出来时问用户选项，不硬猜。

---

## Route Level Quick Reference

| Route | Default context | Escalate when |
|---|---|---|
| `cs-onboard` | L2/L4 | 旧文档需要 inventory、迁移或 trusted/stale 分类 |
| `cs-goal` | L1/L2 | 缺验收/起点状态需 grill；完成需 Task agent 功能验收 |
| `cs-brainstorm` | L1→L2 | owner 接受某方向或要下一步可执行项 |
| `cs-epic` | L2/L3 | 牵涉 spec、capability boundary、requirement delta 或 goal 包 |
| `cs-feat` | L1/L3 | 阶段不明、design 触达长期 spec、实现偏离已确认设计 |
| `cs-issue` | L1/L3 | 复现/影响需 owner 确认，或修复暴露错误 spec/公开行为变化 |
| `cs-refactor` | L1/L2 | 跨模块、有风险或行为边界不确定 |
| `cs-code-review` | L1/L3 | review 发现 Critical/Important 或触达公开契约 |
| `cs-docs` | L1/L2 | 文档改变 user-facing 契约或公开理解 |
| `cs-docs-neat` | L1/L4 | 文档/记忆冲突、source-of-truth 不清、入口规则漂移 |
| `cs-keep` / `cs-note` | L1/L3 | 会影响 future agent 输入或长期约束 |

L2/L3 需要 owner 审批、选择、授权或接受风险时，下游流程按 `.codestable/reference/approval-conventions.md` 写对应 approval 报告；`cs` 自身通常只路由。

---

## 兼容入口说明

以下旧技能名仍可直接使用，但只转入主入口：

- Feature：`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`
- Issue：`cs-issue-report`、`cs-issue-analyze`、`cs-issue-fix`
- Refactor：`cs-refactor-ff`
- Docs：`cs-doc-tutorial`、`cs-doc-api`
- Epic：`cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal`

新文档和新提示词应使用主入口。
