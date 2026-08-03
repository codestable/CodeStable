---
name: cs-feat
description: 实现新功能或功能改造。不用于纯 bug 修复（cs-issue）、行为等价重构（cs-refactor）、大需求拆解（cs-epic）。
argument-hint: "[功能描述]"
---

# cs-feat

把一个功能做出来，流程强度与风险相称：普通改动直接做，高风险改动先对齐设计。

## 开工

- 有 `.codestable/attention.md` 就先读。
- 按功能关键词检索 `.codestable/lessons/`、项目文档，以及存在的 v1 只读知识目录：`.codestable/roadmap/`、`.codestable/features/`、`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、`.codestable/audits/`、`.codestable/brainstorms/`、`.codestable/feedback/`；命中要报告来源路径。上述 v1 目录不得继续生成、原地改写或批量迁移，新结论按归属进入 v2 Epic、项目文档、ADR 或 lesson。
- 既有 `.codestable/requirements/` 只有在 `.codestable/attention.md` 明确记录其为 canonical requirement 位置时才可维护；owner 在当前任务首次指定时，先把该项目事实写入 attention。没有显式记录时只读检索，不存在时不新建 `.codestable/requirements/`。
- 同一会话由 `cs` 交入且带已确认 handoff 时，直接消费目标入口、原始诉求、目标或期望行为、范围/非目标、验收、已核实仓库事实及来源、owner 已确认的术语与决策、未决风险、canonical 资产指针或资产候选；packet 精确范围内已确认的事项不重复询问。handoff 只证明当前会话共识，不扩大实现、commit、发布或写入授权，也不替代本 skill 的 review、验证与确认门槛；字段缺失、仓库事实冲突、出现会改变结果的新风险、缺少会改变方向的事实或超出已确认边界时再按本 skill 规则确认。
- 写代码前先看相邻实现，写得像这个项目原本的代码。
- 动手前先定归属：这能力属于哪里、沿用现有词汇叫什么——不丢进最近的文件、不起新同义词。结构与取舍拿不准时读 `references/code-design.md` 与 `references/economy.md`（最小充分 ≠ 最小 diff；有界简化必须记上限、触发与方向）。
- 新词、重载词或相邻概念边界会改变行为、归属、公开契约或验收时，读取
  `references/shared-language.md`；普通改动沿用已有单义词汇时跳过，不增加 glossary、提问或产物。
- 对照检查：目标、现场上下文、边界与取舍、证据要求、验收标准。缺少会改变实现方向的事实时先问，一次最多 3 个问题，形成可执行共识即停；不问不影响方向的细节。

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
范围时只给候选。用户已明确说“记住 / 更新 / 退役”时，同轮按 `cs-keep` 处理，不重复确认。普通任务
只在强信号成立时展示最高价值一条，首行固定 `晶化候选：{rule}`，并给出证据、范围和建议归宿；无
强信号完全不显示模板，没有记忆写入授权时不落盘。

## 默认执行

理解相关事实 → 实现 → 运行相称的验证 → 交付结果。普通任务不生成 CodeStable 产物，git diff、测试输出和交付说明就是证据。

## 保障选择

`执行流程 = 最小闭环 + 每个未排除风险所要求的最少保障`。最小闭环是理解事实 → 最小完整改动 →
最窄权威验证 → 交付。选择它之前，基于目标及预计/实际触及的路径、符号、信任边界和代码外副作用，
对风险做一次静默、有界核对；不生成产物或逐项报告。一次最低成本定向核实后仍不能排除时先按风险
存在处理，或继续定向诊断到能够判定。不得以“没有注意到风险”作为降级依据。

每个新增门槛都要说明“风险事实 → 增加的保障”。一个风险只增加与它直接对应的保障，不自动启用
整套 design、全量回归、独立 review、work 文档或 Epic final acceptance 路径。行数、文件数、
文案/代码类型和 task kind 都不是风险的替代指标。用户指出“流程太重 / 只是小改动 / 文档比代码多”
时，这是重新核对风险和保障的触发信号，不是无条件跳过安全门槛。停止继续增加产物并重算；仍需
保留门槛时只说明阻止降级的具体风险。

独立 change review 不再默认发生。改变权限、安全、隐私或其他信任边界，持久化数据、schema
或迁移路径，并发、顺序或一致性语义，以及不可恢复的代码外副作用时触发；破坏兼容性、多消费者
契约、性能敏感路径或广传播面只在影响/正确性仍不确定或失败代价重大时触发；用户明确要求时也触发。
review 实际触发后才应用 `审查协议` 中的 reviewer 创建、目标冻结、lineage、findings 与轮次条款。

按风险事实最小增加保障：

- 目标、根因或实现方向仍不确定，或存在会改变结果的真实取舍 → 定向诊断、提问或 design；需要
  owner 选择时确认。
- 破坏兼容性或改变多消费者依赖的公开契约 → 契约确认、对应契约测试与 canonical 文档；兼容范围
  或消费者影响仍不确定时独立 review，不把所有公开 interface 改动自动视为高风险。
- 改变权限、安全、隐私或其他信任边界 → 定向威胁/安全证据与独立 review；改变 owner 授权边界时确认。
- 改变持久化数据、schema 或迁移路径 → 兼容/迁移验证、适用的备份与回滚/恢复证据、独立 review；
  破坏性或不可逆时确认。
- 改变并发、顺序或一致性语义 → 对应竞态/顺序验证与独立 review；语义存在取舍时确认。
- 产生不可恢复的代码外副作用 → 执行前确认，提供适用的 dry-run、幂等、补偿或恢复证据，并独立 review。
- 性能回退或性能敏感路径变化 → 定向 profile、基线或前后对比；SLO、成本或传播范围重大/不确定时
  再增加独立 review。
- 改动影响面广或失败可跨模块传播 → 扩大到受影响回归；只有消费者或失败范围仍不确定、高失败代价
  等独立风险存在时才做全量验证或独立 review。

design 被触发时，最低内容写清改什么、契约变化或不变、真实取舍，并把影响面分为必须修改 / 需要验证 /
仍待调查；没有的条目明确写无。task packet 形式也必须包含这些内容。共享语言分支与完整 design 独立
触发：触发时把 canonical 术语、定义、排除含义与边界场景写入已有 design 或 task packet，或链接项目
已有的 canonical 定义；当前会话内完成且两者都不存在时写入现有交付摘要，不为术语另建 artifact。
跨会话且前述载体不存在时写入既有 work 游标的 `边界` 节，不为术语新建 work。未触发时不增加章节、
问题或产物。

连续性需要不是风险门槛：跨会话、多人交接或用户要求留痕只增加单一临时 work 游标。普通改动选择
成本最低且足够权威的验证；已有定向测试足够时不叠加全量套件、浏览器 smoke 与独立 review。存在会
卡死方案的技术风险时，按 `references/code-design.md` 的穿刺协议先打通风险主路径。

## 硬门槛

- 真实取舍或风险需要 owner 选择时**不得代替用户确认设计**，不 auto-approve，不因对话历史推断同意。
- 项目已有测试设施时优先测试先行：先写能表达验收行为的失败测试再实现；确实无法自动化时与用户确认验证方式。
- 声称完成前必须给出**与声明相称的可核验证据**：目标行为的观察结果、测试输出；只说"应该可以"不算完成。

## 审查协议

以下 reviewer 创建、目标冻结、lineage、findings 与轮次条款仅在 review 被触发后生效；commit / 里程碑
授权门槛始终生效。

- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 `model`；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。
- 没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。
- 审查前冻结一个明确目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本，合法形式是仓库内已有 design 文档版本，或 task packet 内原样全文 + SHA-256；audit 冻结 commit + 范围标识），把目标标识写入 task packet。packet 形式首轮把全文与 hash 原样交给 reviewer，reviewer 审查的目标就是该文本；finding-driven follow-up 携带最新全文、前后 hash 与修复摘要。reviewer 返回前不改目标或对应工作树。有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不得创建正式里程碑 commit；处理后重跑验证并重新冻结完整审查目标。
- 仅在跨会话恢复、agent 交接或隔离 reviewer 需要不可变基线时，且已有 commit 授权，才可在私有工作分支创建明确标记的 WIP/checkpoint commit；它不代表 review 通过或任务完成，交付前按仓库策略 fixup/squash。
- 本 skill 的确认与验证门槛均满足、blocking 清零且其余 important 已处理或被用户明确接受后，已有 commit 授权时才创建语义原子的正式里程碑 commit；未获授权则只报告可提交状态，不自行提交。
- 一个独立审查阶段由单一审查目的界定；design review、change review、contract review 与 Epic final acceptance 是不同阶段。只有为本阶段 findings 所作修复的复审，才属于同一阶段并沿用原 reviewer lineage；审查目的变化时开启新阶段。
- 每个独立审查阶段的首轮必须由当前主流程创建一个 fresh reviewer，与实现者保持独立；reviewer 单轮执行 `cs-review`，其内部不得创建子 agent。
- 主流程处理 findings 后先修复并重跑验证，再冻结新的完整审查目标；仅因处理 findings 产生的修复，复审必须沿用同一 reviewer 的同一 session，以 follow-up 继续。复审同时检查完整当前候选与本轮修复增量，逐项报告 `resolved` / `unresolved` / `new findings`；不得只核对旧 finding 或机械打勾。reviewer 独立性要求它独立于实现者，不要求对自身上一轮审查失忆。
- 同一审查阶段累计最多 3 个有终态报告的轮次；更换 reviewer 不重置计数。只有原 run/session 失败或不可恢复、能力不满足、目标、范围、设计或核心路径发生重大变化、reviewer 声明无法继续独立判断，或 owner 要求第二意见时，才可更换 reviewer；更换时创建 fresh reviewer。超限仍有 blocking 或分歧时交用户裁决，不得继续对轮或宣称完成。
- reviewer 创建后绑定该运行并记录 run identity：目标有效、能力仍满足，且 reviewer 状态为 running，或 `Awaiting` 携带可查询的同一 run identity 且查询仍为活动态时为健康；状态健康时等待终态报告，不因后来发现更优创建方式而取消、重复创建或并行补发。仅在运行明确失败或终止无报告、idle / `Awaiting` 且无可恢复 run identity、能力不满足或目标失效时，本轮失败且不计轮次；不得盲目重发，先检查 task packet 与 agent 状态，再决定一次有界重试、更换创建方式或交用户。

## 收尾

- 报告：做了什么、改动文件、验证结果、遗留事项。
- 需要跨会话继续、多人交接或用户要求留痕时写 `.codestable/work/feat-{slug}.md`；高风险本身不自动建 work。work 文档一律带类型前缀 feat- / issue- / refactor- / epic-，整理时按前缀分流去向，含目标 / 现场 / 边界 / 证据 / 验收 / 状态与未决六节。完成后先在最终报告列**毕业清单**——哪条结论进了哪个项目文档、沉了哪条 lesson，无可毕业内容则明说——然后才删除；目标位置不存在时给出建议落点请用户拍板，拍板前保留。用户要求留档则保留。
- 属于某个 Epic 的子功能时：独立子功能 work 文档的 frontmatter 标 `epic: {epic-slug}`；日常进展和完成状态只更新 Epic work 游标中对应稳定 ID 的进度与证据指针。永久 Epic 文档在 `active` 期间保持冻结，不因日常进度或子功能 work 回链而修改；需要改变子项定义、依赖或验收时交 `cs-epic` 走边界重确认。
