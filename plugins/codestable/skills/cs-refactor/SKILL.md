---
name: cs-refactor
description: 行为等价的重构、拆分、性能优化。会改变外部可观察行为的诉求走 cs-feat 或 cs-issue。
argument-hint: "[重构目标]"
---

# cs-refactor

改结构，不改行为，并且能证明行为没变。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按目标模块关键词 grep `.codestable/lessons/`、`.codestable/compound/` 与项目文档，命中要报告来源路径。
- 先确认诉求真是行为不变：一旦包含"顺便支持 X / 改成 Y"，把那部分拆出去转 `cs-feat` 或 `cs-issue`，不夹带。
- 结构好坏用**深度**衡量：小接口承载大行为是深，接口和实现一样复杂是浅；重构应让调用方用更少认知换更多能力，不为"看起来干净"搬家，不把模块越拆越碎。

## 硬门槛

- **先有能自证等价的验证，再动代码**：覆盖目标行为的测试、类型检查或可对照的输出基线。没有就先补验证或与用户确认等价判据，不许裸改。
- 行为等价是底线：过程中发现必须改变外部可观察行为时停下报告，让用户决定转向，不擅自继续。
- 分步改，每步之后跑验证；全部完成后跑完整验证并附输出。验证变红时先恢复绿再继续。

## 风险升级

跨模块大范围重构、改公开 interface 内部实现、或影响性能敏感路径时，动手前先给用户一页改动清单（动哪些点、顺序、每步验证方式）确认。完成后默认由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review`，reviewer 内不得再创建子 agent；仅微小整理可说明后跳过。主流程处理 findings，需要复审时重新创建 reviewer，累计最多 3 轮；超限仍有 blocking 或分歧时交用户裁决，不得继续对轮或宣称完成。

- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet；reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证、重新冻结审查目标并创建 fresh reviewer。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。

## 收尾

- 报告：改了什么结构、等价性证据（验证输出）、遗留事项。
- 需要跨会话继续时写 `.codestable/work/refactor-{slug}.md`（目标 / 现场 / 边界 / 证据 / 验收 / 状态与未决六节；work 文档一律带类型前缀）。完成后先在报告列毕业去向（结论进哪、lesson 沉哪，或明说无可毕业）再删除；目标位置不存在时在清单中建议落点请用户拍板，拍板前不删。用户要求留档则保留。
- 本轮若踩坑或被纠偏，推荐用 cs-keep 沉淀一条；用户拒绝即跳过。
