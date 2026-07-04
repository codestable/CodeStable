---
name: cs-epic
description: Epic 主入口。触发：大需求/系统级能力/执行整个 epic；规划、review、feature design、goal 包。
argument-hint: "[--stage planning|review|goal-package] <epic>"
---

# cs-epic

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-epic` 是大需求端到端入口。用户文档统一叫 epic；为兼容历史产物，第一版内部目录、frontmatter 和工具仍使用 `roadmap`。用户确认 roadmap 和所有子 feature design 后，默认生成 goal 包并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。

旧技能 `cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal` 长期保留为兼容入口，只传入 `requested_stage`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage planning|review|goal-package` 表示阶段意图，其余文本作为大需求描述。旧裸 token（如 `review`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

无参数默认行为：没有 stage / epic 描述时，扫描 `.codestable/roadmap/`、子 feature design 和 goal 包状态，用状态机恢复；若没有可恢复 epic 且用户原话也没有大需求目标，先问用户要规划哪个 epic。

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
| roadmap 已确认，子 feature design 未完成 | 逐项进入 `cs-feat` design/design-review，并带内部上下文 `epic_child_batch: true`；design 保持 `draft`，不逐个让用户确认 |
| 仍有子 feature 未完成 design-review | 继续下一个子 feature，不停用户 |
| 所有子 feature design-review passed 但未整体确认 | 停下让用户统一确认所有 design，确认后逐份标 `approved` |
| 所有 design approved，goal 包未生成 | 读取 `references/goal/protocol.md` |
| goal 包已生成 | 按 Goal driver 派发；派发失败则输出可粘贴 `/goal` 指令并停止 |

`cs-epic` 不在主线程直接执行长程 goal；只能通过可见 Task agent goal driver 派发。没有可见 driver 或派发失败时，回退为用户手动粘贴 `/goal`。

---

### Child design batch loop

roadmap 已确认后，子 feature design 阶段是一个连续 batch loop，不是单次子任务：

- 每轮开始、每个 child design-review 后、以及准备 final answer 前，先运行
  `python3 .codestable/tools/codestable-workflow-next.py epic --roadmap .codestable/roadmap/{slug} --json`。
- 依赖 CodeStable preflight 已确认的 `workflow-next` runtime capability。
- hook 输出 `must_continue: true` 或 `final_answer_allowed: false` 时，必须按 `next_action` 继续；不得结束本轮。
- 每轮先扫描 `{slug}-items.yaml`，找出下一个 `planned` / `in-progress` 且缺 design、checklist 或 `passed` design-review 的 item。
- 完成某一个 child 的 design + design-review `passed` 只是内部进度；不得 final answer、不得要求用户确认该 child、不得进入实现。
- 只有 items.yaml 里所有未 dropped child 都已有 design + checklist + `passed` design-review，才允许触发“所有 design 统一确认”的人工 checkpoint。
- 若下一条 child 可继续推进，本轮必须继续调用 `cs-feat`，而不是用“下一步继续处理下一个 child”作为结束汇报。

---

## Reference 加载

- planning：`references/planning/protocol.md`，必要时 `references/planning/reference.md`、`references/planning/support/codebase-design.md`
- review：`references/review/protocol.md`
- goal-package：`references/goal/protocol.md`，并复制 `references/goal/support/protocol*.md` 和 `references/goal/support/goal-command-template.md`
- goal driver：`.codestable/reference/execution-conventions.md` 的 Goal driver 派发规则
- child feature：通过 `cs-feat` 主入口推进，不直接调用旧阶段技能；调用时带内部上下文 `epic_child_batch: true`，让单 feature 人工 checkpoint 推迟到 `cs-epic` 的批量确认

---

## 人工 checkpoint

1. roadmap/epic planning review passed 后，用户确认规划。
2. 所有子 feature design-review passed 后，用户统一确认 design。
3. goal driver 不可见、派发失败或返回 `CS_ROADMAP_GOAL_HANDOFF` 时，把 `/goal` 指令或 handoff 原因交给用户。

不要在第一个或任一单独子 feature design-review passed 后停下来要求用户确认执行；那是
`cs-feat` 普通单 feature 行为，在 `cs-epic` 子流程里必须延后到所有子 feature 都完成
design-review 后统一处理。

---

## 退出条件

- child design batch loop 只在全部 child design-review passed、遇到 blocking / pending / 授权问题、或用户明确要求停止时才可结束。
- 若 `codestable-workflow-next.py` 返回 `final_answer_allowed: false`，当前 run 不能退出。
- 规划、审查、子 feature design 和 goal 包状态能从仓库事实恢复。
- 历史 `roadmap` 命名只作为内部兼容说明出现；用户主路径称为 epic。
- 需要同步文档或记忆时提示 `cs-docs-neat`。
