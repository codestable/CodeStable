---
name: cs-epic
description: Epic 主入口。触发：大需求/系统级能力/执行整个 epic；规划、review、feature design、goal 包。
argument-hint: "[--stage planning|review|goal-package] <epic>"
---

# cs-epic

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-epic` 是大需求端到端入口。用户文档统一叫 epic；为兼容历史产物，第一版内部目录、frontmatter 和工具仍使用 `roadmap`。

旧技能 `cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal` 长期保留为兼容入口，只传入 `requested_stage`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage planning|review|goal-package` 表示阶段意图，其余文本作为大需求描述。旧裸 token（如 `review`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

入口意图不覆盖仓库事实。已有 roadmap review 未通过时先修规划；已有 feature design 未确认时不生成 goal 包。

---

## 文件放哪儿

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── {slug}-roadmap-review.md
├── goal-plan.md
├── goal-state.yaml
├── goal-protocol*.md
├── goal-audit.md
└── goal-features/
```

普通子 feature 仍放 `.codestable/features/YYYY-MM-DD-{feature-slug}/`。

---

## 状态机

| 仓库事实 | 下一步 |
|---|---|
| 大需求未拆解 | 读取 `references/planning/protocol.md` |
| roadmap draft 无 passed review | 读取 `references/review/protocol.md` |
| roadmap review blocking / blocked | 回 planning 修订后重跑 review |
| roadmap review passed 但用户未确认 | 停下让用户确认 epic 规划 |
| roadmap 已确认，子 feature design 未完成 | 逐项进入 `cs-feat` design/design-review |
| 子 feature design-review passed 但未整体确认 | 停下让用户确认所有 design |
| 所有 design approved，goal 包未生成 | 读取 `references/goal/protocol.md` |
| goal 包已生成 | 输出可粘贴 `/goal` 指令并停止 |

`cs-epic` 不自动执行 slash command。`/goal` 只能由用户触发。

---

## Reference 加载

- planning：`references/planning/protocol.md`，必要时 `references/planning/reference.md`、`references/planning/support/codebase-design.md`
- review：`references/review/protocol.md`
- goal-package：`references/goal/protocol.md`，并复制 `references/goal/support/protocol*.md` 和 `references/goal/support/goal-command-template.md`
- child feature：通过 `cs-feat` 主入口推进，不直接调用旧阶段技能

---

## 人工 checkpoint

1. roadmap/epic planning review passed 后，用户确认规划。
2. 所有子 feature design-review passed 后，用户统一确认 design。
3. goal 包生成后，只输出 `/goal` 指令，不自动执行。

---

## 退出条件

- 规划、审查、子 feature design 和 goal 包状态能从仓库事实恢复。
- 历史 `roadmap` 命名只作为内部兼容说明出现；用户主路径称为 epic。
- 需要同步文档或记忆时提示 `cs-docs-neat`。
