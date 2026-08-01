---
name: cs-feat
description: 实现新功能或功能改造。不用于纯 bug 修复（cs-issue）、行为等价重构（cs-refactor）、大需求拆解（cs-epic）。
argument-hint: "[功能描述]"
---

# cs-feat

把一个功能做出来，流程强度与风险相称：普通改动直接做，高风险改动先对齐设计。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按功能关键词 grep `.codestable/lessons/`、`.codestable/compound/`、`.codestable/requirements/` 与项目文档，命中要报告来源路径；写代码前先看相邻实现，写得像这个项目原本的代码。
- 动手前先定归属：这能力属于哪里、沿用现有词汇叫什么——不丢进最近的文件、不起新同义词。结构与取舍拿不准时读 `references/code-design.md` 与 `references/economy.md`（最小充分 ≠ 最小 diff；有界简化必须记上限、触发与方向）。
- 对照检查：目标、现场上下文、边界与取舍、证据要求、验收标准。缺少会改变实现方向的事实时先问，一次最多 3 个问题，形成可执行共识即停；不问不影响方向的细节。

## 默认执行

理解相关事实 → 实现 → 运行相称的验证 → 交付结果。普通任务不生成 CodeStable 产物，git diff、测试输出和交付说明就是证据。

## 风险升级信号

出现任何一条，走设计对齐再动手：把方案要点（改什么、契约变化、取舍、影响面——影响面分**必须修改 / 需要验证 / 仍待调查**三层）写入 `.codestable/work/feat-{slug}.md` → 由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review` 的 design review，reviewer 内不得再创建子 agent → 主流程处理 findings，需要时重新创建 reviewer，累计最多 3 轮，超限连分歧一起上交 → 交用户确认后动手。存在会卡死方案的技术风险时，先按风险降序垂直打通主路径再铺开（穿刺协议见 `references/code-design.md`）。信号清单：

- 公开 interface、持久化 schema 或跨模块协议变化；
- 权限、信息安全、数据迁移、并发或不可恢复副作用；
- 存在真实方案取舍，用户的选择会改变结果；
- diff 范围大，或无法建立可信的现状理解；
- 用户明确要求设计先行、独立 review 或正式验收。

## 硬门槛

- 触发升级信号时**不得代替用户确认设计**，不 auto-approve，不因对话历史推断同意。
- 项目已有测试设施时优先测试先行：先写能表达验收行为的失败测试再实现；确实无法自动化时与用户确认验证方式。
- 声称完成前必须给出**与声明相称的可核验证据**：目标行为的观察结果、测试输出；只说"应该可以"不算完成。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet；reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证、重新冻结审查目标并创建 fresh reviewer。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 改动完成后默认由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review`；仅文案级微小改动可说明后跳过。主流程处理 findings 并按需重新发起，累计最多 3 轮；超限仍有 blocking 或分歧时交用户裁决，不得继续对轮或宣称完成。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。

## 收尾

- 报告：做了什么、改动文件、验证结果、遗留事项。
- 高风险任务的 work 文档在设计对齐时已建立；其余任务需要跨会话继续、多人交接或用户要求留痕时补建 `.codestable/work/feat-{slug}.md`（work 文档一律带类型前缀 feat- / issue- / refactor- / epic-，整理时按前缀分流去向）。work 文档含目标 / 现场 / 边界 / 证据 / 验收 / 状态与未决六节，随进展更新（"状态与未决"记录进度与待用户确认项，供跨会话恢复）；完成后先在最终报告列**毕业清单**——哪条结论进了哪个项目文档、沉了哪条 lesson，无可毕业内容则明说——然后才删除 work 文档；不列清单不得删。毕业目标位置不存在时不擅自发明目录：清单中给出建议落点请用户拍板，**拍板前 work 文档保留不删**。用户要求留档则保留。
- 属于某个 epic 的子功能时：work 文档 frontmatter 标 `epic: {epic-slug}` 并在 epic 文档的子项行回链；完成后回报 `cs-epic` 更新其子项状态。
- 本轮若踩坑或被纠偏，推荐用 cs-keep 沉淀一条；用户拒绝即跳过。
