---
name: cs-epic
description: 大需求或系统级能力的拆解与长程推进。单个功能走 cs-feat，bug 走 cs-issue。
argument-hint: "[大需求描述]"
---

# cs-epic

把一个大需求拆成可交付的子项，逐个做完，并让用户始终看得到全景。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按需求关键词 grep `.codestable/lessons/`、`.codestable/compound/`、`.codestable/requirements/` 与项目文档，命中要报告来源路径；v1 存量 `.codestable/roadmap/` 有同主题规划时先读并在其基础上继续。
- 澄清需求：只问会改变拆解方向的问题（目标边界、优先级、验收口径），一次最多 3 个，形成共识即停。

## Epic 文档

epic 天然跨会话，全程维护一个 `.codestable/work/epic-{slug}.md`（work 文档一律带类型前缀）：

```markdown
# {epic 名}
目标 / 边界与取舍 / 验收标准

## 子项
- [ ] {子项一句话}（类型：feat/issue/refactor；依赖；验收要点；设计要点就写在此条目下）
- [ ] {高风险子项} → 设计独立落盘 [work/feat-{slug}.md](feat-{slug}.md)
- [x] {已完成子项} → 结果一句话
```

子项设计**就近优先**：默认写在子项条目下（几行要点即可）；只有触发风险升级信号的子项才独立落 `work/feat-{slug}.md`，其 frontmatter 标 `epic: {epic-slug}`，子项行回链——双向指针，平铺不建子目录。需要正式 requirement 文档时沿用项目已有位置（如 `.codestable/requirements/`），epic 文档里放指针，不复制两份。

## 硬门槛

- **拆解方案必须经用户确认**（子项清单、顺序、边界）后才开始执行；交确认前由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review` 的 design review，reviewer 内不得再创建子 agent。主流程处理 findings 并按需重新创建 reviewer，累计最多 3 轮，超限连分歧一起上交。执行中要增删子项或改边界，先更新文档并征得同意。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet；reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证、重新冻结审查目标并创建 fresh reviewer。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 每次只推进一个已确认子项。子项通过其 owning skill 的验证与审查后，已获 commit 授权时把代码、证据和 epic 状态更新收成一个语义原子里程碑，再进入下一子项；未获 commit 授权时先向用户交付可提交 checkpoint，不把多个子项堆进同一 diff。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。
- 每个子项按其类型的纪律执行（cs-feat / cs-issue / cs-refactor 的门槛照常生效），完成即更新 epic 文档状态——文档与事实不一致时以仓库事实为准并修正文档。
- 全部子项完成后**不代替用户做整体验收**：给出汇总（各子项结果、验证证据、遗留项）并停下等用户确认。

## 收尾

- 验收通过后压缩收尾：稳定结论进项目文档 / requirements，经验进 lessons，**先在最终报告列毕业清单**（每条结论去了哪；无可毕业内容则明说），再删除 epic work 文档**及其全部子项 work 文档**（按 frontmatter `epic:` 归属收拢）；不列清单不得删。毕业目标位置不存在时不擅自发明目录：清单中建议落点请用户拍板，拍板前相关 work 文档保留。用户要求留档则保留。
- 本轮若踩坑或被纠偏，推荐用 cs-keep 沉淀一条；用户拒绝即跳过。
