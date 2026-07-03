---
doc_type: issue-analysis
issue: 2026-07-03-task-agent-lifecycle-cleanup
status: confirmed
root_cause_type: missing-guard
related: [task-agent-lifecycle-cleanup-report.md]
tags: [codestable, task-agent, lifecycle]
---

# Task Agent Lifecycle Cleanup 根因分析

## 1. 问题定位

| 关键位置 | 说明 |
|---|---|
| `plugins/codestable/skills/cs-onboard/references/execution-conventions.md` | 共享 Task agent 选择规则只规定选择顺序、降级条件和 prompt 边界，没有规定结果消费后的关闭动作和容量失败恢复。 |
| `plugins/codestable/skills/cs-goal/SKILL.md` | 终端功能验收要求启动 Task agent，但没有说明功能验收结果落盘后关闭该 agent。 |
| `plugins/codestable/skills/cs-code-review/references/independent-review/protocol.md` | 环节 A 独立 reviewer 是 gate 必需，但合并 reviewer findings 后没有关闭动作。 |
| `plugins/codestable/skills/cs-feat/references/qa/protocol.md` | 独立 QA runner 可选，但 runner 输出消费后的生命周期没有定义。 |
| `plugins/codestable/skills/cs-feat/references/acceptance/protocol.md` | acceptance auditor 可选，但 auditor findings 消费后的生命周期没有定义。 |

## 2. 失败路径还原

**正常路径**：主 agent 启动 Task agent → Task agent 返回结果 → 主 agent 核验 findings / evidence → 写入 review / QA / acceptance / functional-acceptance 报告 → 关闭已完成 Task agent → 后续还能创建新 Task agent。

**失败路径**：主 agent 启动 Task agent → Task agent 返回结果 → 主 agent 写报告但不关闭 agent → 多轮流程积累已完成旧 agent → 新 create/spawn 触发 `agent thread limit reached` → 流程误判为平台不可用并 blocked。

**分叉点**：`execution-conventions.md` 的 Task agent 共享规则缺少生命周期收尾和容量失败恢复。

## 3. 根因

**根因类型**：missing-guard

**根因描述**：CodeStable 把 Task agent 当作审查/验收能力来编排，但没有把它当作需要显式释放的平台资源。流程文档只覆盖“什么时候启动”和“启动失败如何降级”，缺少“结果消费后关闭”和“容量失败时先回收已完成旧 agent 再重试”的标准动作。

**是否有多个根因**：否。直接根因是共享生命周期规则缺失；各入口文档只是继承了这个缺口。

## 4. 影响面

- **影响范围**：所有会启动 Task agent 的流程，包括 review、QA、acceptance auditor、goal 终端功能验收和 goal driver。
- **潜在受害模块**：`cs-goal`、`cs-feat`、`cs-epic`、`cs-code-review` 以及遵循 `execution-conventions` 的后续流程。
- **数据完整性风险**：无直接代码数据损坏，但会造成 workflow 状态误判和 blocked 产物。
- **严重程度复核**：维持 P1。它会阻断核心 workflow 的长会话执行，但手动关闭旧 agent 可恢复。

## 5. 修复方案

### 方案 A：只在共享约定补生命周期规则

- **做什么**：在 `execution-conventions.md` 增加 Task agent 生命周期规则：消费后关闭；容量失败时清理最老已完成旧 agent 并重试一次。
- **优点**：规则集中，后续流程自动继承。
- **缺点 / 风险**：直接入口文档仍可能被 agent 只读局部 reference 时漏掉。
- **影响面**：只动共享文档和测试。

### 方案 B：共享约定为权威，关键入口补短句引用

- **做什么**：在共享约定写完整生命周期；在 `cs-goal`、`cs-code-review`、feature QA/acceptance、epic review/gates 等直接消费 Task agent 结果的文档补短句。
- **优点**：规则统一，同时降低局部流程漏读风险。
- **缺点 / 风险**：需要控制 Markdown 行数。
- **影响面**：改动多个 skill 文档，但都是规则同步，不改变具体流程产物 schema。

### 推荐方案

**推荐方案 B**，理由：Issue 影响的是所有 Task agent 流程，生命周期规则应集中在 `execution-conventions.md`，但关键入口也需要显式提醒“结果消费后关闭”，避免 agent 只按局部 protocol 执行时漏掉资源回收。
