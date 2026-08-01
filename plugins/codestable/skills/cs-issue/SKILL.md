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
- 同一会话由 `cs` 交入且带已确认 handoff 时，直接消费目标入口、原始诉求、目标或期望行为、范围/非目标、验收、已核实仓库事实及来源、owner 已确认的术语与决策、未决风险、canonical 资产指针或资产候选；packet 精确范围内已确认的事项不重复询问。handoff 只证明当前会话共识，不扩大实现、commit、发布或写入授权，也不替代本 skill 的 review、验证与确认门槛；字段缺失、仓库事实冲突、出现会改变结果的新风险、缺少会改变方向的事实或超出已确认边界时再按本 skill 规则确认。
- 对照检查：目标（期望行为）、现场（复现条件与环境）、边界（哪些不能动）、验收（怎么算修好）。缺少会改变修复方向的事实时先问用户，一次最多 3 个问题，形成共识即停。
- 诉求其实是新增能力而不是坏掉的行为时，转 `cs-feat`，不在 issue 里偷做。

## 持续学习

检索到 lesson 后先做 read-repair。只有 scope 符合、未退役、经当前代码/测试/canonical 文档核实，
并真实改变计划或验证的条目才算有效命中；按
`经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}` 报告。`retired` 不应用；
`observed` / `validated` 先核实再用；旧 lesson 缺 `status` 按 `observed` 读取，不批量迁移。只是相关
但没有改变行为时不制造复用证据；当前事实明确反证时立即停止应用，证据不足时不猜。

任务内只在内存保留最多 3 条候选，按新证据替换低价值项，不暂停或询问。强信号只包括：owner
纠正实际改变方案/代码/术语/验证；可复现证据推翻根因；同一路径失败两次后更换假设；
blocking/important finding 暴露未编码不变量；新 red -> green 捕获可复发失败；lesson 真实改变本次行为
或被反证；重复 workaround；方法显著降低重试、成本或风险。

候选还必须同时有可追溯证据、能写成未来动作、适用于本次精确 diff 之外、且没有现成 canonical
owner。网络波动、拼写、泛化口号、活动记录，以及已被机械 owner 完整覆盖的事实直接丢弃。

创建、改写规则/scope、晋升、删除与跨项目反馈仍须用户显式授权。为不中断 read-repair，仅对已有且
有效命中的 lesson 开放两种窄维护：`observed -> validated` 仅在独立后续任务确实采用并验证成功时
发生，只补一次代表性证据；`observed|validated -> retired` 仅在当前仓库事实直接反证或发现已有
canonical owner 时发生，只写原因与替代/反证指针。窄维护不新建事实、不改规则、不扩 scope、不新增
gate，随当次代码、证据和
游标进入同一语义原子 milestone；稳定 validated 命中不写文件。需要改写结论或证据不足时只给
候选，新结论不得通过复活 retired 条目获得 validated 身份；窄维护必须在最终报告列出文件变化。

当前任务范围内能直接落成 red -> green 测试/checker 的约束优先机械化，不另写重复 lesson；会扩大
范围时只给候选。用户已明确说“记住 / 更新 / 退役”时，同轮按 `cs-keep` 处理，不重复确认。普通任务
只在强信号成立时展示最高价值一条，首行固定 `晶化候选：{rule}`，并给出证据、范围和建议归宿；无
强信号完全不显示模板，没有记忆写入授权时不落盘。

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
