---
name: cs-docs
description: Docs 主入口。触发：写/更新开发者指南、用户指南、API 参考；不包含 docs-neat 收尾整理。
argument-hint: "[--mode tutorial|api] <topic>"
---

# cs-docs

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-docs` 是对外文档写作的唯一推荐入口，只覆盖开发者/用户指南和 API 参考。阶段收尾、知识库卫生、agent 入口同步仍走独立的 `cs-docs-neat`。

旧技能 `cs-doc-tutorial`、`cs-doc-api` 长期保留为兼容入口，只传入 `requested_mode`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--mode tutorial|api` 表示文档模式，其余文本作为文档主题。旧裸 token（如 `api`）只作为历史提示词兼容识别；新文档和新调用一律用 `--mode`。

无参数默认行为：没有 mode / topic 时，先扫既有文档和公开表面，按状态机找 pending / draft / outdated 文档；若没有可恢复文档目标，再根据用户原话判断目标读者，不清楚就问用户选择。

用户没有明确文档类型时先判断目标读者和使用场景；仍不清楚就问用户选择。

---

## 模式边界

| 模式 | 产物 | 适用 |
|---|---|---|
| tutorial | 开发者指南 / 用户指南 | 教读者怎么完成一个任务 |
| api | API / 组件 / 命令参考 | 给读者查公开表面、参数、返回值、示例 |

`cs-docs` 不做全局同步、不整理 `.codestable/`、不毕业 agent memory。发现这些需求时提示 `cs-docs-neat`。

---

## 状态机

启动后先扫既有文档和公开表面：`docs/`、`README*`、用户点名路径、相关源码导出/API/命令。按仓库事实恢复：

| 仓库事实 | 下一步 |
|---|---|
| 用户要任务教程/使用指南，且没有对应 guide | 读取 `references/tutorial/protocol.md` 新建 |
| 已有 guide，但相关代码/spec 已变或 status 为 `outdated` | 读取 `references/tutorial/protocol.md` 更新 |
| 用户要 API/组件/命令参考，且无 manifest 或条目缺失 | 读取 `references/api/protocol.md` 初始化或补条目 |
| API manifest / 条目存在且有 `pending`、`draft` 或 `outdated` | 读取 `references/api/protocol.md` 生成或增量更新 |
| 目标文档已 `current` 且用户只要小改 | 做聚焦编辑，保持事实可追溯 |
| 诉求是全局同步、README/agent 入口/记忆整理 | 转 `cs-docs-neat` |

用户说“继续写文档”时，也按文件和 frontmatter / manifest 状态判断，不靠聊天历史。

---

## Reference 加载

- tutorial：`references/tutorial/protocol.md`
- api：`references/api/protocol.md`，必要时 `references/api/reference.md`

先读代码和既有文档，再按对应模式生成或更新文档。不要凭记忆写 API。

---

## 人工 checkpoint

必须停下等用户明确确认的点：

1. 新建文档前：目标读者、文档类型（tutorial / api）和落点路径。
2. 覆盖或重写已有 `current` 文档前：确认旧内容确实过期，不是并行有效版本。
3. 文档表述会改变 user-facing 契约或公开理解时：让用户确认口径后再落盘。

---

## 退出条件

- 文档目标读者、入口路径和状态已明确。
- 新增/更新文档的 `status` 或 manifest 状态已落到 `draft` / `current` / `outdated` / `pending` / `skipped` 中的合法值。
- 新增/更新的文档能从源码或现有项目事实追溯。
- 需要同步 README、agent 入口或记忆时，明确提示后续运行 `cs-docs-neat`。
