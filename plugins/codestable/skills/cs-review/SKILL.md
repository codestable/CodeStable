---
name: cs-review
description: 只读审查叶子执行器。默认审当前 diff，也审 design 方案，或按用户要求做 repo 级审计。单轮返回结果，不创建子 agent。曾名 cs-code-review。
argument-hint: "[--range <git-range>] [scope 或 audit 目标]"
---

# cs-review

审查一段变更（默认）或一块代码（审计模式），产出分级发现。本 skill 是叶子执行器，
只完成一轮审查并返回结果。

## 调用边界

- 用户直接调用时，当前 agent 就是 reviewer，不再派生 reviewer。
- 来源流程派发前冻结一个明确的审查目标（diff review 优先 staged diff，也可用明确的 `--range` 或 patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把审查目标标识写入 task packet；reviewer 返回前不得移动该目标或对应工作树。目标变化则本轮失效；调用方重新冻结完整目标后，按 reviewer lineage 规则决定 follow-up 或更换 reviewer。
- 来源流程负责在每个独立审查阶段首轮进入本 skill 前完成 reviewer 创建方式与 agent/model 选择并创建 fresh reviewer；首轮 task packet 传入单一审查目的、改动意图、审查目标、不审内容、期望返回格式，以及最终创建方式、agent/model 与回退原因。design review、change review、contract review 与 Epic final acceptance 使用不同阶段；仅因本阶段 findings 修复而复审时，调用方把新的冻结目标和修复摘要作为 follow-up 交给同一 reviewer 的同一 session。
- follow-up 复审必须检查完整当前候选与本轮修复增量，逐项报告 `resolved` / `unresolved` / `new findings`，不得只核对旧 finding。独立性由调用方建立；reviewer 只需独立于实现者，不要求对自身上一轮审查失忆，本 skill 也不通过再次委派来补建独立视角。

## 模式

- **diff review**（默认）：审当前工作区 diff 或 `--range` 指定范围，对照本次改动的意图（对话共识、work 文档或 design）。
- **design review**：审 cs-feat / cs-epic 提交的方案要点或拆解方案，检查需求覆盖、契约影响、风险与取舍是否成立。
- **audit**：用户要求主动扫描时，按用户给的范围（全仓 / 目录 / 维度如安全、性能）做只读审计。范围大时先和用户对齐扫哪里、找什么。

## 硬门槛

- **只读**：本 skill 不修代码、不写业务文件；修复由来源流程负责。
- **叶子执行器**：禁止创建、委派或唤醒任何子 agent；不得再次调用 `cs-review` 或 `cs-code-review`，也不把审查转交给其他流程。
- 每次调用必须返回一份终态审查结果；上下文不足时返回 `NeedsContext`、缺失项和已检查范围，不得以 `idle`、`Awaiting` 或无结果结束。
- 每个发现附 `文件:行号`（design 审查附对应小节）、问题说明和理由；不确定的标注为疑问而不是断言。
- blocking 未解决不得给出“通过”结论；本 skill 不修复、不自行发起复审，但可承接来源流程发给同一 session 的 follow-up。

## 审查标准

目标不是完美代码，而是确认改动没有降低代码健康、且朝声明的意图前进。**先对照意图与既有约束，再挑结构**：这批改动想解决什么、是否越界、是否漏验证；然后看归属与命名、深度（是否纯穿透层）、接缝是否为想象中的扩展、边界处理。只提会改变正确性或失败代价的点，不机械过检查表；能被 lint / formatter 自动处理的问题不手工阻塞。整体结论三档：**可合 / 有条件可合 / 建议先改再合**。发现分级：

- **blocking**：正确性、安全、数据、并发问题，或与声明意图相悖——**blocking 未解决不得宣称 review 通过**；
- **important**：维护性、性能、可测试性隐患，需要处理或被用户明确接受；
- **nit**：风格与细节，可选。

## 收尾

- 始终在对话中输出审查目标标识、结论（通过 / 需修改）与发现清单。
- 作为来源流程创建的 reviewer 时只返回报告，不写 work 文档、不路由其他 skill；调用方负责处理 findings、复审与持久化，本 skill 不保存复审轮次或重试状态。
- 仅用户直接调用且明确要求留痕时，才把结论摘要写进对应 `.codestable/work/{slug}.md`；审计问题只建议后续使用 `cs-issue` / `cs-feat`，不当场转入或顺手修。
- 审查中发现可复用的坑，推荐用 cs-keep 沉淀；用户拒绝即跳过。
