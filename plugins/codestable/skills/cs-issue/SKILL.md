---
name: cs-issue
description: Issue 主入口。触发：修 bug/有问题/修复 XX；端到端推进 report、analyze、fix、review。
argument-hint: "[--stage report|analyze|fix] <issue>"
---

# cs-issue

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-issue` 是问题修复的唯一推荐入口。它负责把问题从记录、根因分析、定点修复、验证、fix-note 和 code review 衔接到闭环。

旧阶段技能 `cs-issue-report`、`cs-issue-analyze`、`cs-issue-fix` 长期保留为兼容入口，只传入 `requested_stage`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage report|analyze|fix` 表示阶段意图，其余文本作为问题描述。旧裸 token（如 `fix`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

无参数默认行为：没有 flag / 问题描述时，不猜阶段；扫描 `.codestable/issues/`、目标产物和当前 git diff，用状态机恢复下一步。若没有可恢复 issue 且用户原话也没有问题目标，先问用户要处理哪个 issue。

入口意图不覆盖仓库事实。若 report 已存在但用户从 report 兼容入口进来，继续 analyze；若代码已改但无 fix-note，进入 fix 验证/记录。

---

## 文件放哪儿

```text
.codestable/issues/{YYYY-MM-DD}-{slug}/
├── {slug}-report.md
├── {slug}-analysis.md
└── {slug}-fix-note.md
```

日期取发现/提报问题当天。`fix-note.md` 是必出产物，即使走快速通道也要写。

---

## 状态机

启动后扫描 `.codestable/issues/`、读取目标 issue 产物、检查当前 git diff：

| 仓库事实 | 下一步 |
|---|---|
| 没有 issue 文件 | 读取 `references/report/protocol.md` |
| report 存在，根因不明且无 analysis | 读取 `references/analyze/protocol.md` |
| report 存在，且读代码后确认根因明确、改动小、无跨模块影响 | 用户确认后直接进入 fix，仍写 fix-note |
| analysis 存在，代码未改 | 读取 `references/fix/protocol.md` |
| 代码已改但无 fix-note | 读取 `references/fix/protocol.md` 的验证/记录部分 |
| fix-note 已写但无 review | 进入公开横切 gate `cs-code-review` |
| review 有 blocking | 回 fix 窄修复，修完重跑 review |
| review passed | 汇报完成，并提示 docs/neat 候选 |

用户描述的是新增能力而不是坏掉的既有行为时，路由到 `cs-feat`。

---

## Reference 加载

- report：`references/report/protocol.md`
- analyze：`references/analyze/protocol.md`
- fix：`references/fix/protocol.md`，必要时 `references/fix/reference.md`
- code review：公开横切技能 `cs-code-review`

按阶段加载，不一次性读完。

---

## 快速通道

快速通道是 `cs-issue` 内部模式，不是单独技能。必须同时满足：

1. 读代码后能指出明确根因。
2. 修复很小，通常 1-2 处。
3. 无跨模块影响风险。

不满足就走标准 report → analyze → fix。进入标准路径后默认不再二次改判，避免阶段之间口径漂移。

---

## 人工 checkpoint

- report 阶段确认问题描述、复现、期望/实际、环境、严重度。
- analyze 阶段确认推荐修复方案和风险。
- fix 阶段验证结果和 review blocking 处理。

---

## 退出条件

- `{slug}-fix-note.md` 已写明根因、改动、验证和遗留风险。
- 必要 code review 已通过或阻塞项已清楚交回。
- 修复暴露新 feature 需求时，不在 issue 内偷做，另开 `cs-feat`。
