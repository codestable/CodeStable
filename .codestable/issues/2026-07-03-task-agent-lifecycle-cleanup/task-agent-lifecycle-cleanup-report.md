---
doc_type: issue-report
issue: 2026-07-03-task-agent-lifecycle-cleanup
status: confirmed
severity: P1
summary: CodeStable flows do not explicitly close completed Task agents.
tags: [codestable, task-agent, lifecycle]
---

# Task Agent Lifecycle Cleanup Issue Report

## 1. 问题现象

CodeStable 多个流程会启动独立 Task agent 做 review、QA、audit 或功能验收，但流程规则没有要求主 agent 在消费最终结果后显式关闭该 Task agent。

结果是旧 Task agent 业务上已经完成，平台层面仍占用线程名额。长会话连续执行 goal / acceptance / review 后，会出现 `agent thread limit reached`，新 Task agent 无法创建。

## 2. 复现步骤

1. 在长会话里连续执行多个依赖 Task agent 的 CodeStable 流程，例如 goal 终端验收、feature acceptance auditor 或独立 review。
2. 等待这些 Task agent 返回最终结果。
3. 后续再次创建 Task agent。
4. 观察到：旧 Task agent 仍挂在当前会话中，占用并发名额，新的 create/spawn 报 `agent thread limit reached`。

复现频率：长会话中稳定累积，达到平台线程上限后必现。

## 3. 期望 vs 实际

**期望行为**：Task agent 结果被主流程消费并落盘后，主 agent 显式关闭该 agent；只有创建新 agent 遇到容量失败时，才清理最老的已完成旧 agent 并重试一次。

**实际行为**：流程只规定何时启动 Task agent 和启动失败如何 blocked / owner-stop，没有规定消费后关闭，也没有规定容量失败后的旧 agent 回收重试。

## 4. 环境信息

- 涉及模块 / 功能：CodeStable skills 的 Task agent review / QA / audit / acceptance / goal driver 流程。
- 相关文件 / 函数：`plugins/codestable/skills/cs-onboard/references/execution-conventions.md` 及直接引用 Task agent 的流程文档。
- 运行环境：Codex / Claude / Paseo 等支持子 agent 的宿主平台。
- 其他上下文：手动关闭旧 agent 后立即可创建新 agent，说明问题是资源未回收，不是任务仍在运行。

## 5. 严重程度

**P1** — 长会话核心 workflow 会被平台线程上限卡死，导致 review / QA / acceptance 无法继续，但可通过手动关闭旧 agent 临时恢复。

## 备注

GitHub issue: https://github.com/liuzhengdongfortest/CodeStable/issues/37
