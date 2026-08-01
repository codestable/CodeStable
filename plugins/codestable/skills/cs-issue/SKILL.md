---
name: cs-issue
description: 修复 bug、报错或既有行为异常。不用于新功能（cs-feat）或行为等价重构（cs-refactor）。
argument-hint: "[问题描述]"
---

# cs-issue

修一个 bug，并证明它修好了。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按错误信息与相关模块关键词检索 `.codestable/lessons/`、项目文档，以及存在的 v1 只读知识目录：`.codestable/roadmap/`、`.codestable/features/`、`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、`.codestable/audits/`、`.codestable/brainstorms/`、`.codestable/feedback/`；这个坑可能踩过，命中要报告来源路径。上述 v1 目录不得继续生成、原地改写或批量迁移，新结论按归属进入 v2 Epic、项目文档、ADR 或 lesson。
- 对照检查：目标（期望行为）、现场（复现条件与环境）、边界（哪些不能动）、验收（怎么算修好）。缺少会改变修复方向的事实时先问用户，一次最多 3 个问题，形成共识即停。
- 诉求其实是新增能力而不是坏掉的行为时，转 `cs-feat`，不在 issue 里偷做。

## 硬门槛

- **没有稳定、快速、能明确变红的验证，不许猜根因、不许改代码。** 优先失败测试；无法自动化时与用户确认一个手工复现步骤。
- 声称修复完成前，**那条变红的验证必须变绿**，并附运行输出；相关既有测试不得变红。
- **根因是有效状态第一次变成无效的地方，不是报错处**；只消除因果断点，不在症状处堆特殊分支。
- 同一修复路径失败两次，停下来重新审视根因假设，不要变着花样重试；升级手段（可证伪假设、一次一个变量）与"怀疑结构"信号见 `references/debug.md`。

## 风险升级

修复涉及公开契约、持久化数据、权限或并发语义时，先停下说明影响面、获得用户确认再动。根源超出本次 scope（比如需要重构）时报告并让用户选择，不擅自扩大改动。

## 收尾

- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet；reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证、重新冻结审查目标并创建 fresh reviewer。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 修复完成后默认由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review`，reviewer 内不得再创建子 agent；仅单行级微小修复可说明后跳过。主流程处理 findings，需要复审时重新创建 reviewer，累计最多 3 轮；超限仍有 blocking 或分歧时交用户裁决，不得继续对轮或宣称完成。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。
- 报告：根因一句话、改动文件、验证结果。
- 需要跨会话继续时写 `.codestable/work/issue-{slug}.md`（目标 / 现场 / 边界 / 证据 / 验收 / 状态与未决六节；work 文档一律带类型前缀）。完成后先在报告列毕业去向（结论进哪、lesson 沉哪，或明说无可毕业）再删除；目标位置不存在时在清单中建议落点请用户拍板，拍板前不删。用户要求留档则保留。
- 本轮若踩了新坑或被用户纠偏，推荐用 cs-keep 沉淀一条；用户拒绝即跳过。
