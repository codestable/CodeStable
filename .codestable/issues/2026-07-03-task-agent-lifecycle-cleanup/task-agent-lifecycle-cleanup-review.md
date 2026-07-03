---
doc_type: issue-review
issue: 2026-07-03-task-agent-lifecycle-cleanup
status: passed
reviewer: subagent
task_agent_id: 829be4f3-4860-4891-9509-5cb6a82539ff
task_agent_closed: true
tags: [codestable, task-agent, lifecycle]
---

# Task Agent Lifecycle Cleanup Review

## Scope

独立只读 review 覆盖当前未提交 diff，重点检查 GitHub Issue #37：

- Task agent final result 被主流程消费并落盘后是否显式关闭。
- 是否只在 `agent thread limit reached` / capacity exhausted 等容量失败时清理旧 agent。
- 是否按最老已完成且结果已消费 / 不再需要的 agent 回收，并只重试一次。
- 是否保护 still-running、pending、permission-needed 和结果尚未消费的 agent。
- 直接入口文档和测试是否同步。

## Result

独立 reviewer 结论：无 Blocking、无 Important、无 Nit，审查通过。

## Evidence

- reviewer agent: `829be4f3-4860-4891-9509-5cb6a82539ff`
- reviewer type: Paseo subagent, Claude Opus, plan mode
- close / archive result: `archive_agent` success

## Summary

reviewer 确认：

- `execution-conventions.md` 明确了先消费并落盘结果，再调用 `close_agent` 或等价关闭动作。
- 文档明确不要预先批量清理旧 agent。
- 容量恢复只在 create/spawn 容量失败后触发，清理范围限定为最老已完成且结果已消费 / 不再需要的旧 Task agent，并只重试一次。
- `cs-goal`、`cs-code-review`、`cs-feat`、`cs-epic` 相关入口同步一致。
- 新增测试覆盖了关键语义。
- 修改后的 Markdown 文件均未超过 300 行。
