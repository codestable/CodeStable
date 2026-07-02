---
name: cs-feat
description: Feature 主入口。触发：新功能/加 X/实现 XX；端到端推进 design、review、impl、QA、accept。
argument-hint: "[--stage design|design-review|impl|qa|accept] [--mode fastforward] <feature>"
---

# cs-feat

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-feat` 是 feature 的唯一推荐入口。用户只需要持续调用本技能；本技能根据仓库事实恢复当前阶段，并在必要 checkpoint 停下来等用户确认。

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
| design-review passed 但 design 未 approved | 停下让用户整体 review；确认后标 `approved` |
| design approved 且代码未完成 | 读取 `references/implementation/protocol.md` |
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
2. implementation 完成后的 code review 结果处理。
3. QA failed / blocked 后的修复方向。
4. acceptance 最终结论与长期文档回写风险。

本技能是连续编排入口，不是无确认自动到底。

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
