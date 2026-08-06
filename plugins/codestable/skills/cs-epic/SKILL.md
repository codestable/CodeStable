---
name: cs-epic
description: 大需求或系统级能力的路线发现、拆解与长程推进。单个功能走 cs-feat，bug 走 cs-issue。
argument-hint: "[大需求描述]"
---

# cs-epic

把一个大需求从路线迷雾收敛成可执行契约，再逐个完成可交付子项，并让用户始终看得到全景。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按任务关键词在存在的 `.codestable/lessons/`、项目文档以及 v1 只读知识目录 `.codestable/roadmap/`、`.codestable/features/`、`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、`.codestable/audits/`、`.codestable/brainstorms/`、`.codestable/feedback/` 中 grep；命中要报告来源路径。上述 v1 目录只读，不得继续生成、原地改写或批量迁移；新结论毕业到永久 Epic、项目文档、ADR 或 lesson。
- `.codestable/requirements/` 仅在 `.codestable/attention.md` 明确记录为 canonical requirement 位置时才可维护；owner 首次指定时先把该项目事实写入 attention。未记录时只读，不存在时不新建 `.codestable/requirements/`；新项目沿用项目自身文档结构，归宿未定的稳定契约先留在永久 Epic。
- 有匹配的 `.codestable/work/epic-{slug}.md` 时先恢复：读取其永久 Epic 指针、`phase`、
  `approved_revision`、`item_progression`、`milestone_commit` 与 `remote_publish`，核对 active 永久文档的
  当前 SHA-256。游标未命中时，先在项目已有明确的 Epic、RFC 或 initiative 归宿中按任务关键词扫描
  `status: proposed` 的在途 Epic；存在 `.codestable/epics/` 时也按相同条件扫描其中候选。两类归宿并存
  时都纳入候选，项目已有归宿优先。唯一命中时只补回缺失的 planning 游标并恢复。命中多个时按 slug、
  任务关键词与永久文档指针消歧；仍不能唯一确定时列出候选并请 owner 选择，不自动合并、补游标或
  新建 Epic。仓库事实优先于聊天历史；hash、策略字段或仓库事实不一致时先修复或请求上下文，不创建
  重复 Epic。
- 起草 proposed 永久 Epic 文档时，同时创建或复用对应 work 游标并保持 `phase: planning`、`approved_revision: pending`、`current_item: null`。
- 同一会话由 `cs` 交入且带已确认 handoff 时，直接消费目标入口、原始诉求、目标或期望行为、范围/非目标、验收、已核实仓库事实及来源、owner 已确认的术语与决策、未决风险、canonical 资产指针或资产候选；packet 精确范围内已确认的事项不重复询问。handoff 只证明当前会话共识，不扩大实现、commit、发布或写入授权，也不替代本 skill 的 review、验证与确认门槛；字段缺失、仓库事实冲突、出现会改变结果的新风险、缺少会改变方向的事实或超出已确认边界时再按本 skill 规则确认。
- handoff 只用于起草 proposed 永久 Epic 文档，不替代 fresh design review、批准 hash 或第一道 owner gate。
- 澄清需求：只问会改变拆解方向的问题（目标边界、优先级、验收口径），一次最多 3 个，形成共识即停。
- 新词、重载词或相邻概念边界会改变目标、范围、事实权威、生命周期、验收或子项契约时，读取
  `references/shared-language.md`；即使不触发完整路线发现，也必须达到其中可判定的 Language Clear
  条件。已有单义术语不增加章节或提问。
- 完成有界仓库调查和当前最多 3 个方向性澄清后，若仍因多个相互依赖的路线级决策而无法写出
  可审查的 proposed Epic，且预计不能在当前会话收敛，路线尚不清晰时才读取
  `references/wayfinding.md`。路线已清晰、只是单个局部技术未知，或仅因高风险、文件多、跨会话时跳过。

## 持续学习

检索到 lesson 后先做 read-repair。只做一次有界、最低成本的定向核实，优先读取已有代码、测试或
canonical 文档；不得仅为核实 lesson 运行大范围测试或反复复现。仍不足时跳过该 lesson，不阻塞正常任务。
只有 scope 符合、未退役、当前事实成立，并真实改变计划或验证，或明确排除一个具体且合理的错误路径
的条目才算有效命中；按
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
发生，只补一次代表性证据；必须记录 lesson 实际改变的计划或验证，或明确排除的具体且合理错误路径，
以及本次通过的验收证据。`observed|validated -> retired` 仅在当前仓库事实直接反证或发现已有
canonical owner 时发生，只写原因与替代/反证指针。窄维护不新建事实、不改规则、不扩 scope、不新增
gate，随当次代码、证据和
游标进入同一语义原子 milestone；稳定 validated 命中不写文件。需要改写结论或证据不足时只给
候选，新结论不得通过复活 retired 条目获得 validated 身份；窄维护必须在最终报告列出文件变化。

当前任务范围内能直接落成 red -> green 测试/checker 的约束优先机械化，不另写重复 lesson；会扩大
范围时只给候选。用户已明确说“记住 / 更新 / 退役”时，同轮按 `cs-keep` 处理，不重复确认。Epic
子项不展示、不询问；每个子项至多把一条去重候选写入既有游标证据区，使用 `晶化候选：{rule}`
marker，最终毕业清单一次处理并复用最终 owner gate。

## 双层 Epic 文档

Epic 天然跨会话，但稳定上下文和活动状态不得混写：

- **永久 Epic 文档**：项目已有明确 Epic、RFC 或 initiative 归宿时沿用；否则首次创建时按需建立 `.codestable/epics/{slug}.md`，`cs-onboard` 不预建该目录。永久 Epic 文档就是唯一路线文档，proposed 阶段就是低分辨率文档内路线地图；它是起点、目标、范围、非目标、验收标准、条件式共享语言与概念边界、带稳定 ID/依赖/验收要点的子项契约、关键决策、最终交付索引、整体验收、遗留风险与长期 `status` 的唯一 owner。路线发现期间还暂存带依赖的 `待决策` 与 `尚未明确`，不新增独立 issue、map 或第三套状态。
- **执行游标**：`.codestable/work/epic-{slug}.md` 只保存永久文档指针、`approved_revision`、执行 `phase`、当前子项 ID、各 ID 进度、下一步、`blocked_by`、`item_progression`、`milestone_commit`、`remote_publish`、parallel 策略下的 `active_items` 恢复记录、临时决策及证据/commit 指针；不得复制目标、验收、子项定义或最终结论。

永久文档最小结构：

带条件注释的小节按条件创建，未触发时整节不写入。

```markdown
---
status: proposed
created: YYYY-MM-DD
work: ../work/epic-{slug}.md
---
# {epic 名}
起点 / 目标 / 范围 / 非目标 / 验收标准
## 共享语言与概念边界
<!-- 仅在术语歧义会改变路线时创建；链接已有 canonical 定义，只补本 Epic 的局部边界与关系 -->
## 关键决策
- **DEC-1 · {可读名称}**：{结论与理由；证据或资产指针}
## 待决策
- **DEC-2 · {可读名称}** `[AFK|HITL]`
  - question: {一个现在能精确陈述、且会改变路线的问题}
  - depends_on: [{完整决策名称} | none]
  - method: research | owner-dialogue | prototype | prerequisite
  - evidence: {pointer | pending}
<!-- 仅在触发路线发现时创建；route clear 冻结前移除本节 -->
## 尚未明确
<!-- 仅在触发路线发现时创建；暂时无法精确陈述的路线级迷雾不分配 DEC 名称或依赖；route clear 冻结前移除本节 -->
## 子项契约
- ITEM-1：{owning skill；可交付结果；依赖；验收要点；必要的设计约束}
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
current_item: null
next_action: {one concrete next action}
blocked_by: null
item_progression: pending
milestone_commit: pending
remote_publish: pending
---
## 子项进度
- [ ] ITEM-1
## 临时决策与证据
```

永久 `status` 只允许 `proposed -> active -> accepted`，owner 放弃或用后继 Epic 取代时转 `cancelled` / `superseded`；work `phase` 只允许 `planning -> executing -> acceptance`，阻塞只写 `blocked_by`。

路线发现沿用 `proposed + planning + approved_revision: pending`，不新增状态；route clear 前不得保留未解决的 HITL 节点；仍有效的节点必须由 owner 明确解决或确认移入 `非目标`，只有因已确认上游决策而机械失效的节点可带依据删除，agent 不得单方判定其超出范围或失效。会改变路线的术语必须已经单义化、定义或链接到 canonical owner，子项契约使用同一词汇；未清的产品含义或概念边界仍按 HITL 处理。路线清晰、可审查、可执行时，清退 `待决策` 与 `尚未明确` 两节：只把剩余 AFK 局部未知写入对应子项契约，仅把已解决决策和下放 AFK 局部未知带来的剩余风险写入 `遗留风险`，再冻结完整 proposed Epic 并进入现有 design review。route clear 不是新的 owner gate，也不代表所有局部实现细节都已决定；判断标准见 `references/wayfinding.md`。

拆解确认本身不等于版本控制授权；首次 owner gate 同时一次性确定 `item_progression: continuous | per-item | parallel`、`milestone_commit: authorized | manual` 与 `remote_publish: each-milestone | final | manual`，说明选择 `manual` commit 会逐项暂停，并写入 work 游标。`parallel` 仅在子项契约存在依赖互不阻塞、可并行交付的子项时提供；`item_progression: parallel` 只能搭配 `milestone_commit: authorized`。`milestone_commit: manual` 只能搭配 `item_progression: per-item`；`milestone_commit: manual` 只能搭配 `remote_publish: manual`；`remote_publish: each-milestone` 只能搭配 `milestone_commit: authorized`。`authorized + per-item` 是合法的显式逐项暂停策略。进入 executing 前不得保留 `pending` 或非法组合。

owner 确认 proposed 文档与上述策略后，主流程机械置 `active`，用 `shasum -a 256 <epic-file>` 计算完整文件 SHA-256，只写入 work 的 `approved_revision` 并进入 executing；批准后再把 `current_item` 设为第一个依赖已满足的子项（按永久文档顺序）；`item_progression: parallel` 例外：批准后初始化 `active_items: []` 并保持 `current_item: null`，`current_item` 只在串行集成期间按 `references/parallel-execution.md` 语义设置。确认前保持 `pending` 与 `current_item: null`。active 期间永久文档冻结，日常进度与临时决策只写 work；目标、范围、非目标、验收、子项定义或重大风险变化时，按相同规则更新永久文档、重新 review/确认并替换 hash。版本控制策略变化只按 owner 的显式表达更新游标字段，不修改永久文档或批准 hash，也不得从历史操作推断授权。Epic 内的已有 commit 授权只指 `milestone_commit: authorized`；其他值或仅有会话历史均不算。旧游标缺字段或组合非法时暂停一次补记/修正。

子项设计就近优先：简要设计属于永久文档的子项契约；高风险细节可独立落 `work/feat-{slug}.md`，frontmatter 标 `epic: {epic-slug}`，work 游标只记录路径和进度。子项增删、依赖或验收变化属于契约变化；不改变依赖/验收的顺序微调只更新游标。

## 硬门槛

- **拆解方案必须经用户确认**（目标、边界、验收、子项契约）后才开始执行；路线级迷雾未清时继续路线发现，不提前送审。路线清晰、可审查、可执行后，交确认前进入 design review 审查阶段，按下述 reviewer lineage 完成 `cs-review`。永久文档已批准后的执行中，要改变目标、范围、非目标、验收、子项定义或重大风险时，契约变化形成新的 contract review 审查阶段：先更新永久文档，由 fresh reviewer 重新 review 并征得同意。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本，合法形式是仓库内已有 design 文档版本，或 task packet 内原样全文 + SHA-256；Epic design review 优先冻结永久文档版本；audit 冻结 commit + 范围标识），把目标标识写入 task packet。packet 形式首轮把全文与 hash 原样交给 reviewer，reviewer 审查的目标就是该文本；finding-driven follow-up 携带最新全文、前后 hash 与修复摘要。reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证并重新冻结完整审查目标。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 一个独立审查阶段由单一审查目的界定；design review、change review、contract review 与 Epic final acceptance 是不同阶段。只有为本阶段 findings 所作修复的复审，才属于同一阶段并沿用原 reviewer lineage；审查目的变化时开启新阶段。
- 每个独立审查阶段的首轮必须由当前主流程创建一个 fresh reviewer，与实现者保持独立；reviewer 单轮执行 `cs-review`，其内部不得创建子 agent。
- 主流程处理 findings 后先修复并重跑验证，再冻结新的完整审查目标；仅因处理 findings 产生的修复，复审必须沿用同一 reviewer 的同一 session，以 follow-up 继续。复审同时检查完整当前候选与本轮修复增量，逐项报告 `resolved` / `unresolved` / `new findings`；不得只核对旧 finding 或机械打勾。reviewer 独立性要求它独立于实现者，不要求对自身上一轮审查失忆。
- 同一审查阶段累计最多 3 个有终态报告的轮次；更换 reviewer 不重置计数。只有原 run/session 失败或不可恢复、能力不满足、目标、范围、设计或核心路径发生重大变化、reviewer 声明无法继续独立判断，或 owner 要求第二意见时，才可更换 reviewer；更换时创建 fresh reviewer。超限仍有 blocking 或分歧时交用户裁决，不得继续对轮或宣称完成。
- `continuous` 与 `per-item` 策略下，同一时间只允许一个 `current_item`；这是串行约束，不是每个子项的人工 gate。`item_progression: parallel` 时，主流程是唯一编排者与唯一游标 writer，可同时推进多个依赖已满足的已批准子项：并发子项以 worker 委派到宿主提供的隔离工作区执行，并发集合记录在游标 `active_items`；调度、委派契约、单 writer 不变量、串行集成与能力回退按 `references/parallel-execution.md` 执行，仅在该策略生效时读取。`active` 且批准 hash 有效表示可执行已批准子项，恢复后沿用游标策略，不重新询问是否继续。
- 子项通过其 owning skill 选定的保障与验证后，按 `milestone_commit` 把代码、证据和 work 游标更新收成一个语义原子里程碑，不把多个子项堆进同一 diff。`item_progression: continuous` 时，非最终子项完成后自动选择永久文档顺序中第一个依赖已满足的未完成子项，更新 `current_item` / `next_action`，并在同一受托主流程中继续执行；仍有未完成子项但无可运行候选时按阻塞暂停。`item_progression: parallel` 时，worker 在隔离工作区交付后由主流程按完成顺序串行集成：逐项以不推进主历史的方式合入、在合并结果上重跑该子项权威验证，验证通过后才创建语义原子里程碑 commit，每集成一项即补发新就绪子项；并行允许并发但不强制，全部合格 worker 创建能力或隔离能力均不可用时本会话内退化为串行推进，不改变游标策略字段，并在报告中说明。不得询问“是否继续下一项”，不得把普通子项完成当作终态返回。
- `item_progression: per-item` 时，完成当前里程碑后按已记录的逐项 checkpoint 策略暂停；它是 owner 在首次 gate 或后续显式变更中选择的行为，不得伪装成默认连续模式。`milestone_commit: manual` 时只交付可提交 checkpoint，不自行 commit。
- `remote_publish: each-milestone` 时，每个语义原子 commit 后按项目、宿主或 owner 已确定的 branch/remote 策略发布；`final` 时，在集成验证与 final acceptance review 通过后、请求 owner 最终接受前发布一次；`manual` 时 agent 不执行远端发布。branch/remote 未明确时暂停请求上下文，不自行选择；发布失败时写入 `blocked_by` 并暂停，不静默继续。
- Epic 编排只在以下情况新增暂停：契约或重大风险变化、无法自行解除的阻塞/产品决策、新增权限、需要 owner 明确接受的 important findings、review 超限仍有分歧、旧游标策略缺失或非法、用户明确要求暂停，以及全部子项完成后的最终 owner gate。子项 owning skill 自身的确认门槛照常生效；已批准子项契约覆盖同一决策时不得重复确认，新出现且会改变结果的风险仍按 owning skill 或 Epic 重确认处理。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。
- 每个子项按其类型的纪律执行（cs-feat / cs-issue / cs-refactor 的门槛照常生效），完成即更新 work 游标的 ID 进度、证据和 commit 指针；文档与事实不一致时以仓库事实为准并修正文档。
- 全部子项完成后把 phase 置为 acceptance 并运行集成验证。final acceptance 是独立审查阶段，必须由当前主流程另建 fresh reviewer 开始新的 lineage，不得沿用子项、此前 design review 或 contract review 的 reviewer lineage；它对最新 owner 已批准的验收标准做 `cs-review` audit/acceptance review。主流程按同一 lineage 处理该阶段 findings，门槛通过后给出各子项结果、验证证据与遗留项，**不代替用户做整体验收**，停下等 owner 最终接受。

## 收尾

- owner 接受后先把最终范围、关键决策、交付索引、整体验收、遗留风险与毕业清单写入永久 Epic，再用终态更新置 `accepted` 并移除 `work` 指针。稳定产品契约进 canonical requirement/项目文档，结构性决策进 ADR，经验进 lessons；目标位置不存在时请 owner 选择，确定前结论留在永久 Epic。
- 终态 `accepted` / `superseded` / `cancelled` 是不可恢复执行的持久信号。无论中断时还剩 work 指针、游标或所属子项 work，都从仓库事实幂等续做：补齐终态记录与毕业清单、移除指针、删除 Epic 游标，再按 frontmatter `epic:` 清理全部子项 work；不得恢复执行或创建重复 Epic，永久 Epic 文档不得删除。
- 不恢复 `cs-goal` 入口、goal package、`state.yaml`、逐轮 iteration 报告或 legacy runtime gate；目标契约、恢复游标、owner gate 和终态验收都由上述双层文档承担。
