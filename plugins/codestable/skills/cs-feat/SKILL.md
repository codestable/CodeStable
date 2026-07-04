---
name: cs-feat
description: Feature 主入口。触发：新功能/加 X/实现 XX；端到端推进 design、review、goal 包、impl、QA、accept。
argument-hint: "[--stage design|design-review|impl|qa|accept|goal-package] [--mode fastforward] <feature>"
---

# cs-feat

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-feat` 是 feature 的唯一推荐入口。用户只需要持续调用本技能；本技能根据仓库事实恢复当前阶段，并在 design gate 停下来等用户确认。用户确认 design 后，默认生成单 feature goal 包并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。

旧阶段技能长期保留为兼容入口：`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`。它们只传入 `requested_stage` 或 `requested_mode`，不维护独立规则。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage <stage>` 表示阶段意图，用 `--mode <mode>` 表示执行模式，其余文本作为需求描述。

| 参数 | 入口意图 |
|---|---|
| `--stage design` | `requested_stage: design` |
| `--stage design-review` | `requested_stage: design-review` |
| `--stage impl` | `requested_stage: implementation` |
| `--stage qa` | `requested_stage: qa` |
| `--stage accept` | `requested_stage: acceptance` |
| `--stage goal-package` | `requested_stage: goal-package` |
| `--mode fastforward` | `requested_mode: fastforward` |

旧裸 token（如 `qa`、`ff`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage` / `--mode`。

无参数默认行为：没有 flag / 需求描述时，不猜阶段；扫描 `.codestable/features/`、目标产物和当前 git diff，用状态机恢复下一步。若没有可恢复 feature 且用户原话也没有新功能目标，先问用户要处理哪个 feature。

入口意图只是偏好。仓库事实优先：如果已有产物显示当前应先 review、修 QA 或验收，就按事实推进并向用户说明。

---

## 文件放哪儿

```text
.codestable/features/{YYYY-MM-DD}-{slug}/
├── {slug}-brainstorm.md
├── {slug}-intent.md
├── {slug}-design.md
├── {slug}-design-review.md
├── {slug}-checklist.yaml
├── goal-plan.md             # 单 feature 长程执行包
├── goal-state.yaml
├── goal-protocol.md
├── {slug}-review.md
├── {slug}-qa.md
├── {slug}-acceptance.md
└── {slug}-ff-note.md        # 仅 fastforward 模式
```

目录命名取首次创建当天，slug 小写字母 / 数字 / 连字符。标准流程使用 design/checklist/review/QA/acceptance；fastforward 模式只写 `{slug}-ff-note.md`。feature 过程里发现的 bug 另开 issue，不在 feature 里偷修。

---

## 状态机

启动后先扫描 `.codestable/features/`、读取目标 feature 的现有产物、检查当前 git diff，再按下表恢复：

| 仓库事实 | 下一步 |
|---|---|
| 想法模糊，边界/成功标准/不做什么不清 | 转 `cs-brainstorm` 分诊 |
| 用户要求快速模式且范围小 | 读取 `references/fastforward/protocol.md` |
| 无 design，或已有 intent/brainstorm 要进设计 | 读取 `references/design/protocol.md` |
| design 为 draft 且无 passed design-review | 读取 `references/design-review/protocol.md` |
| design-review changes-requested / blocked | 回 design 修订，再重跑 design-review |
| design-review passed 但 design 未 approved | 普通单 feature 停下让用户整体 review；若调用上下文是 `epic_child_batch: true`，不在这里停，回到 `cs-epic` 继续下一个子 feature，等待所有 design 统一确认 |
| design approved 且 goal 包未生成 | 读取 `references/goal/protocol.md` |
| goal 包已生成且代码未完成 | 按 Goal driver 派发；派发失败则输出可粘贴 `/goal` 指令 |
| 用户明确请求单阶段实现，或 goal driver handoff 后需要人工续跑 | 读取 `references/implementation/protocol.md` |
| 代码完成但无 `{slug}-review.md` | 进入公开横切 gate `cs-code-review` |
| review 有 unresolved blocking | 回 implementation 的 review-fix |
| review passed 但无 `{slug}-qa.md` | 读取 `references/qa/protocol.md` |
| QA failed / blocked | 回 implementation 的 qa-fix，修完重跑 review 和 QA |
| QA passed 但无 acceptance | 读取 `references/acceptance/protocol.md` |
| acceptance passed | 汇报完成状态和后续 docs / neat 候选 |

用户说“下一步”时，也按仓库事实而不是聊天历史判断。

---

## Reference 加载

只在进入对应阶段时加载厚规则：

- design：`references/design/protocol.md`，必要时 `references/design/reference.md`、`references/design/support/intent-template.md`、`references/design/support/codebase-design.md`
- design-review：`references/design-review/protocol.md`
- goal-package：`references/goal/protocol.md`
- implementation：`references/implementation/protocol.md`，必要时 `references/implementation/support/reference.md`、`references/implementation/support/tdd.md`
- code review：公开横切技能 `cs-code-review`
- QA：`references/qa/protocol.md`
- acceptance：`references/acceptance/protocol.md`，必要时 `references/acceptance/reference.md`
- fastforward：`references/fastforward/protocol.md`

不要把所有 reference 一次性读完；按阶段渐进加载。

---

## 人工 checkpoint

必须停下等用户明确确认的点：

1. design-review passed 后的 design 整体确认。
2. goal driver 不可见、派发失败或返回 `CS_FEATURE_GOAL_HANDOFF` 时，把 `/goal` 指令或 handoff 原因交给用户。
3. 长程执行中需要改变 approved design、feature 范围或公开契约时，停下让用户确认。

implementation / code review / QA / acceptance 的普通阻塞优先由 goal driver 按协议循环修复；不要在每个阶段默认打断用户。

---

## Epic 子 Feature 批量设计上下文

当 `cs-epic` 为 roadmap items 批量生成子 feature design 时，会以内部上下文
`epic_child_batch: true` 调用本入口的 design / design-review 阶段。该上下文不是用户公开
参数，不写入 `argument-hint`。

在 `epic_child_batch: true` 下：

- design-review `passed` 后，design 继续保持 `status: draft`。
- 不执行单 feature 的人工整体 review checkpoint，不把 design 改成 `approved`。
- 只把 design、checklist、design-review 和 items.yaml 回写落盘，然后返回 `cs-epic`；不得用 final answer 要用户确认单个 child。
- 退出前必须运行 `python3 .codestable/tools/codestable-workflow-next.py feature --feature .codestable/features/YYYY-MM-DD-{slug} --epic-child-batch --json`；若输出 `final_answer_allowed: false`，按 `next_action` 交回 `cs-epic` 继续批量流程。
- 依赖 CodeStable preflight 已确认的 `workflow-next` runtime capability。
- `cs-epic` 负责继续处理剩余子 feature；全部 design-review 都 passed 后，才一次性交给
  用户统一确认。

若用户单独调用 `cs-feat` 或没有该内部上下文，仍按普通单 feature checkpoint 停下等用户确认。

---

## Fastforward

`requested_mode: fastforward` 只表示用户想走快速模式。进入前仍要确认范围小、需求清楚、无跨系统术语/契约风险。若不满足，解释原因并回标准 design 流程。

fastforward 产物固定为 `.codestable/features/{YYYY-MM-DD}-{slug}/{slug}-ff-note.md`，不生成标准 design/checklist/QA/acceptance 套件。

`cs-feat-ff` 是兼容入口，不再单独维护快速模式规则。

---

## 退出条件

- 当前阶段产物已落盘，状态可由仓库事实恢复。
- 阻塞项、用户 checkpoint 或下一阶段已明确说明。
- 标准流程最终需要 design approved、review passed、QA passed、acceptance passed。
- 需要外部文档时提示 `cs-docs`；需要阶段收尾/记忆同步时提示 `cs-docs-neat`。

---

## 相关入口

- `cs-code-review`：实现后的横切只读审查 gate。
- `cs-docs`：对外教程 / API 参考文档。
- `cs-docs-neat`：阶段收尾和知识库同步。
- `cs-epic`：大需求拆分与 goal 执行包。
