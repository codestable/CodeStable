---
name: cs-epic
description: 大需求或系统级能力的拆解与长程推进。单个功能走 cs-feat，bug 走 cs-issue。
argument-hint: "[大需求描述]"
---

# cs-epic

把一个大需求拆成可交付的子项，逐个做完，并让用户始终看得到全景。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按任务关键词在存在的 `.codestable/lessons/`、项目文档以及 v1 只读知识目录 `.codestable/roadmap/`、`.codestable/features/`、`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、`.codestable/audits/`、`.codestable/brainstorms/`、`.codestable/feedback/` 中 grep；命中要报告来源路径。上述 v1 目录只读，不得继续生成、原地改写或批量迁移；新结论毕业到永久 Epic、项目文档、ADR 或 lesson。
- `.codestable/requirements/` 仅在 `.codestable/attention.md` 明确记录为 canonical requirement 位置时才可维护；owner 首次指定时先把该项目事实写入 attention。未记录时只读，不存在时不新建 `.codestable/requirements/`；新项目沿用项目自身文档结构，归宿未定的稳定契约先留在永久 Epic。
- 有匹配的 `.codestable/work/epic-{slug}.md` 时先恢复：读取其永久 Epic 指针、`phase` 和 `approved_revision`，核对 active 永久文档的当前 SHA-256。仓库事实优先于聊天历史；不一致时先修复或请求上下文，不创建重复 Epic。
- 澄清需求：只问会改变拆解方向的问题（目标边界、优先级、验收口径），一次最多 3 个，形成共识即停。

## 双层 Epic 文档

Epic 天然跨会话，但稳定上下文和活动状态不得混写：

- **永久 Epic 文档**：项目已有明确 Epic、RFC 或 initiative 归宿时沿用；否则首次创建时按需建立 `.codestable/epics/{slug}.md`，`cs-onboard` 不预建该目录。它是起点、目标、范围、非目标、验收标准、带稳定 ID/依赖/验收要点的子项契约、关键决策、最终交付索引、整体验收、遗留风险与长期 `status` 的唯一 owner。
- **执行游标**：`.codestable/work/epic-{slug}.md` 只保存永久文档指针、`approved_revision`、执行 `phase`、当前子项 ID、各 ID 进度、下一步、`blocked_by`、临时决策及证据/commit 指针；不得复制目标、验收、子项定义或最终结论。

永久文档最小结构：

```markdown
---
status: proposed
created: YYYY-MM-DD
work: ../work/epic-{slug}.md
---
# {epic 名}
起点 / 目标 / 范围 / 非目标 / 验收标准
## 子项契约
- ITEM-1：{类型；依赖；验收要点；必要的设计要点}
## 关键决策
## 最终交付索引
## 整体验收
## 遗留风险
```

work 游标最小结构：

```markdown
---
epic: ../epics/{slug}.md
phase: planning
approved_revision: pending
current_item: ITEM-1
next_action: review and confirm the proposed Epic
blocked_by: null
---
## 子项进度
- [ ] ITEM-1
## 临时决策与证据
```

永久 `status` 只允许 `proposed -> active -> accepted`，owner 放弃或用后继 Epic 取代时转 `cancelled` / `superseded`；work `phase` 只允许 `planning -> executing -> acceptance`，阻塞只写 `blocked_by`。owner 确认 proposed 文档后，主流程机械置 `active`，用 `shasum -a 256 <epic-file>` 计算完整文件 SHA-256，只写入 work 的 `approved_revision` 并进入 executing；确认前保持 `pending`。active 期间永久文档冻结，日常进度与临时决策只写 work；目标、范围、非目标、验收、子项定义或重大风险变化时，按相同规则更新永久文档、重新 review/确认并替换 hash。

子项设计就近优先：简要设计属于永久文档的子项契约；高风险细节可独立落 `work/feat-{slug}.md`，frontmatter 标 `epic: {epic-slug}`，work 游标只记录路径和进度。子项增删、依赖或验收变化属于契约变化；不改变依赖/验收的顺序微调只更新游标。

## 硬门槛

- **拆解方案必须经用户确认**（目标、边界、验收、子项契约）后才开始执行；交确认前由当前主流程创建一个 fresh reviewer，让其单轮执行 `cs-review` 的 design review，reviewer 内不得再创建子 agent。主流程处理 findings 并按需重新创建 reviewer，累计最多 3 轮，超限连分歧一起上交。执行中要改变目标、范围、非目标、验收、子项定义或重大风险，先更新永久文档、重新 review 并征得同意。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet；reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证、重新冻结审查目标并创建 fresh reviewer。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 每次只推进一个已确认子项。子项通过其 owning skill 的验证与审查后，已获 commit 授权时把代码、证据和 work 游标更新收成一个语义原子里程碑，再进入下一子项；未获 commit 授权时先向用户交付可提交 checkpoint，不把多个子项堆进同一 diff。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。
- 每个子项按其类型的纪律执行（cs-feat / cs-issue / cs-refactor 的门槛照常生效），完成即更新 work 游标的 ID 进度、证据和 commit 指针；文档与事实不一致时以仓库事实为准并修正文档。
- 全部子项完成后把 phase 置为 acceptance，运行集成验证，并由当前主流程创建 fresh reviewer，对最新 owner 已批准的验收标准做 `cs-review` audit/acceptance review。主流程处理 findings，门槛通过后给出各子项结果、验证证据与遗留项，**不代替用户做整体验收**，停下等 owner 最终接受。

## 收尾

- owner 接受后先把最终范围、关键决策、交付索引、整体验收、遗留风险与毕业清单写入永久 Epic，再用终态更新置 `accepted` 并移除 `work` 指针。稳定产品契约进 canonical requirement/项目文档，结构性决策进 ADR，经验进 lessons；目标位置不存在时请 owner 选择，确定前结论留在永久 Epic。
- 终态 `accepted` / `superseded` / `cancelled` 是不可恢复执行的持久信号。无论中断时还剩 work 指针、游标或所属子项 work，都从仓库事实幂等续做：补齐终态记录与毕业清单、移除指针、删除 Epic 游标，再按 frontmatter `epic:` 清理全部子项 work；不得恢复执行或创建重复 Epic，永久 Epic 文档不得删除。
- 不恢复 `cs-goal` 入口、goal package、`state.yaml`、逐轮 iteration 报告或 legacy runtime gate；目标契约、恢复游标、owner gate 和终态验收都由上述双层文档承担。
- 本轮若踩坑或被纠偏，推荐用 cs-keep 沉淀一条；用户拒绝即跳过。
