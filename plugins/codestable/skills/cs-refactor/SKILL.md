---
name: cs-refactor
description: Refactor 主入口。触发：优化/重构/拆分/性能/代码太长，且不改变行为、不新增需求。
argument-hint: "[--stage scan|design|apply] [--mode standard|fastforward] <target>"
---

# cs-refactor

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-refactor` 是重构的唯一推荐入口。它统一判定标准模式和 fastforward 模式，核心底线是行为等价：一旦会改变外部可观察行为，就转 `cs-feat` 或 `cs-issue`。

`cs-refactor-ff` 长期保留为兼容入口，只传入 `requested_mode: fastforward`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage <stage>` 表示阶段意图，用 `--mode <mode>` 表示执行模式，其余文本作为重构目标。

| 参数 | 入口意图 |
|---|---|
| `--stage scan` | `requested_stage: scan` |
| `--stage design` | `requested_stage: design` |
| `--stage apply` | `requested_stage: apply` |
| `--mode standard` | `requested_mode: standard` |
| `--mode fastforward` | `requested_mode: fastforward` |

旧裸 token（如 `ff`、`scan`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage` / `--mode`。

无参数默认行为：没有 flag / 目标描述时，先按 `.codestable/refactors/`、scan/design/checklist/apply-notes 和当前 git diff 恢复；若没有可恢复重构且用户原话也没有目标，先问用户要优化哪个范围。

入口意图只是偏好。仓库事实优先：已有 scan/design/checklist/apply-notes 时按真实状态续跑。

---

## 文件放哪儿

```text
.codestable/refactors/{YYYY-MM-DD}-{slug}/
├── {slug}-scan.md
├── {slug}-refactor-design.md
├── {slug}-checklist.yaml
└── {slug}-apply-notes.md
```

fastforward 默认不建目录；用户要求留记录时才写 `{slug}-refactor-note.md`。

---

## 模式选择

启动后先确认用户诉求是否真是行为不变的重构，再检查范围和测试自证能力。

标准模式读取 `references/standard/protocol.md`，流程是：

```text
scan → 用户勾选 → design → 用户确认 → apply → cs-code-review
```

fastforward 模式读取 `references/fastforward/protocol.md`。必须同时满足：

1. 行为真的不变，没有“顺便支持 X / 改成 Y”。
2. 范围小：单函数/单组件/少量动点，不跨模块。
3. 有测试、类型检查或等价证据能自证。

任何一条不满足，回标准模式；不能因为用户说“快点”就跳过安全边界。

---

## Reference 加载

- standard：`references/standard/protocol.md`
- fastforward：`references/fastforward/protocol.md`
- 方法库：`references/library/methods.md`、`references/library/methods-l4.md`、`references/library/methods-architecture.md`
- scan 格式与拒绝路由：`references/library/scan-checklist-format.md`、`references/library/refusal-routing.md`
- code review：公开横切技能 `cs-code-review`

按阶段加载，scan 时才全量加载方法库。

---

## 人工 checkpoint

- scan 产物必须由用户勾选，AI 不替用户勾选。
- design 必须用户整体 review 后才进入 apply。
- apply 中 HUMAN 验证项必须停下等用户明确继续。
- 完成后进入 `cs-code-review`；Critical/Important 未清零不提交。

---

## 退出条件

- 标准模式：scan 已勾选、design approved、apply-notes 记录每步验证、必要测试通过、code review 通过。
- fastforward：已说明方法、范围、验证证据；如变复杂已停下切回标准模式。
- 不夹带 feature 或 issue 改动。
