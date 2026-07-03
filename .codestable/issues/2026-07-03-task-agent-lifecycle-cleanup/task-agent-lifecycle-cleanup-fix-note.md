---
doc_type: issue-fix-note
issue: 2026-07-03-task-agent-lifecycle-cleanup
status: confirmed
tags: [codestable, task-agent, lifecycle]
---

# Task Agent Lifecycle Cleanup Fix Note

## 根因

CodeStable 的共享 Task agent 规则没有覆盖资源生命周期：结果消费后不要求关闭，容量失败时也没有“清理已完成旧 agent 后重试”的恢复路径。

## 改动

- 在 `execution-conventions.md` 新增 `Task agent 生命周期`：
  - 本轮 Task agent final result 被消费并落盘后，调用 `close_agent` 或宿主等价关闭动作。
  - close 失败不改变已核验 verdict，但要记录 warning、agent 标识和人工清理提示。
  - 不关闭 still-running、pending、permission-needed 或结果尚未消费的 agent。
  - 不预先批量清理旧 agent；只有 create/spawn 出现 `agent thread limit reached` / capacity exhausted 时，才按最老优先关闭已完成且结果已消费或不再需要的旧 agent，并重试一次。
- 同步直接 Task agent 入口：
  - `cs-goal` 功能验收 agent。
  - `cs-code-review` 环节 A reviewer。
  - `cs-feat` design-review reviewer、QA runner、acceptance auditor。
  - `cs-epic` roadmap reviewer、goal QA runner、acceptance auditor。
- 新增测试覆盖生命周期关键语义。

## 验证

- `pytest -q` → `146 passed in 41.60s`
- `python tools/check-plugin-package.py --root . --json` → `{"ok": true, "findings": []}`
- `git diff --check` → pass
- Markdown 行数上限检查 → pass，无超过 300 行的 skill / issue Markdown。

## 遗留风险

- 不同宿主关闭工具命名可能不同，文档使用 `close_agent` 或等价关闭动作表达。具体执行仍由宿主工具能力决定。
