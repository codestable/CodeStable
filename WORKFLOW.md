# CodeStable v2 工作流与项目结构

## 工作流

CodeStable v2 是 8 个独立安装的 thin-harness skill，加一个项目记忆闭环。`cs` 判别用户
此刻要执行、先讨论、咨询还是了解体系：明确行动默认优先同轮直转；先讨论的请求在当前会话
收敛并按授权移交；咨询只给推荐；无诉求时介绍体系。

```text
不确定入口       -> cs
先讨论 / 对齐     -> cs -> cs-feat / cs-issue / cs-epic
仓库接入 / v1 升级 -> cs-onboard
只诊断 / 排查     -> cs-issue（无产品 diff，不进入 change review）
新功能           -> cs-feat
获授权修复 bug / 性能回退 / 行为异常 -> cs-issue
行为等价重构      -> cs-refactor
大需求拆解        -> cs-epic -> cs-feat / cs-issue / cs-refactor
独立审查 / 审计   -> cs-review
经验与项目记忆    -> cs-keep
```

### 会话内讨论与 handoff

- 明确行动默认优先同轮直转；用户显式要求先讨论时才覆盖该默认。调查仓库事实后仍无法安全判断
  行动类型或 owning skill，且产品决策会实质改变建档或改代码路径时，也可进入 Discuss；owning
  skill 已可判定时，目标、边界与验收细化交给该 skill，不在入口层增加 gate。
- 讨论只存在于当前会话：仓库可核实的事实由 agent 自行调查，一次只问一个真正需要 owner 决定的
  问题，并用精确术语、具体场景和边界案例检验理解。它不创建 discussion work 游标或 transcript；
  未收敛讨论不跨会话恢复。
- handoff-ready 时，packet 保存目标入口、原始诉求、目标或期望行为、范围、非目标、验收、已核实
  仓库事实及来源、owner 决策、未决风险与资产指针。已有执行授权时同轮移交给 `cs-feat`、
  `cs-issue` 或 `cs-epic`，不再询问“是否继续”；讨论过程本身不产生授权，handoff 不扩大授权，
  也不替代 owning skill 的 review、验证或 owner gate。
- 原始问答、未决讨论和候选分支不落盘。稳定术语进入项目已有 canonical 术语归宿，结构性取舍仅在
  难逆转、缺少上下文会令人意外且存在真实取舍时进入 ADR；任务契约、永久 Epic、attention 与
  lessons 由 owning skill 按既有规则毕业。没有 canonical 归宿时请 owner 选择，不新建平行真相。
- 三个已确认出口之外的结果按 `cs` 既有 Execute / Advise 规则同轮直转或推荐，不获得 handoff 的
  不重复确认特权。只授权讨论时，`cs` 返回已确认结论并推荐由 `cs-keep` 或 owning skill 完成毕业。

### 共享语言

共享语言是条件式设计纪律，不是所有任务的固定阶段：

- 普通改动沿用已有单义术语时不增加产物、问题或 gate。只有新词、重载词或相邻概念边界会改变
  目标、行为、归属、事实权威、生命周期、契约或验收时才触发。
- Feature 要求局部语义清晰：canonical 名称、紧凑定义、排除含义和一个边界场景足以让实现、API、
  schema、文档与测试表达同一行为。Epic 要求概念体系清晰：跨概念关系、权威与不变量进入永久
  Epic，并成为 Route Clear 的组成部分。
- 仓库事实由 agent 核实；产品含义与概念边界进入 HITL，由 owner 在事实、选项与取舍明确后决定。
  这不是新的 owner gate，也不把可调查事实上交给用户。
- 稳定领域术语进入项目已有 canonical 领域文档；架构角色留在当前设计，结构性取舍按条件进入 ADR。
  没有归宿时先留在 task packet 或永久 Epic 并给出建议落点；owner 可在既有 gate 或后续治理中选择，
  未选择不阻塞当前交付，也不自动创建 `CONTEXT.md` 或平行词典。
- design / contract review 检查先定义后使用、全文同义和场景一致，但不能替 owner 证明理解。owner 在 review 后
  的术语问题若揭示契约级不同理解，候选仍未清晰；纯实现细节解释不重开设计。

任务类型只决定工程方法，实际风险决定保障强度：

```text
执行流程 = 最小闭环 + 每个未排除风险所要求的最少保障
```

独立 review 不是默认步骤。一个风险只增加与它直接对应的保障，不自动打开整套流程。

选择最小闭环前，基于目标以及预计/实际触及的路径、符号、信任边界和代码外副作用，对下列风险做
一次静默、有界核对，不生成逐项报告或新产物。一次最低成本定向核实后仍不能排除时先按风险存在处理，
或继续定向诊断到能够判定。不得以“没有注意到风险”作为降级依据。规模只作影响面证据：行数、文件数、文案/代码类型和 task kind 都不能
代替语义风险。

按风险事实只增加直接对应的保障：

- 目标、根因或实现方向不确定，或存在会改变结果的真实取舍 → 定向诊断、提问或 design；需要 owner
  选择时确认。
- 破坏兼容性或改变多消费者依赖的公开契约 → 契约确认、对应契约测试与 canonical 文档；兼容范围或
  消费者影响仍不确定时增加独立 review。
- 改变权限、安全、隐私或其他信任边界 → 定向威胁/安全证据与独立 review；改变 owner 授权边界时确认。
- 改变持久化数据、schema 或迁移路径 → 兼容/迁移验证、适用的备份与回滚/恢复证据、独立 review；
  破坏性或不可逆时确认。
- 改变并发、顺序或一致性语义 → 对应竞态/顺序验证与独立 review；语义存在取舍时确认。
- 产生不可恢复的代码外副作用 → 执行前确认，提供适用的 dry-run、幂等、补偿或恢复证据，并独立 review。
- 性能回退或性能敏感路径变化 → 定向 profile、基线或前后对比；SLO、成本或传播范围重大/不确定时
  再增加独立 review。
- 改动影响面广或失败可跨模块传播 → 扩大到受影响回归；消费者或失败范围仍不确定、失败代价重大时，
  才增加全量验证或独立 review。

用户指出“流程太重 / 只是小改动 / 文档比代码多”时，这是重新核对风险和保障的触发信号，
不是无条件跳过安全门槛。停止继续增加产物并重算；仍需保留门槛时只说明阻止降级的具体风险。
连续性需要不是风险门槛：跨会话、多人交接或用户要求留痕只增加单一临时 work 游标。普通改动选择成本最低且足够
权威的定向验证，不自动叠加全量套件、浏览器 smoke 或独立 review。

- `cs-feat` 从最小闭环开始，按上述风险映射逐项增加保障；只有需要 owner 选择时才确认。
- `cs-issue` 先针对用户实际症状建立可重复的失败信号。只要求诊断时保持零产品改动，结论明确归为
  已证实根因、可证伪假设或证据不足；获授权修复后，沿用同一信号证明红到绿。
- `cs-refactor` 先建立等价性证据，分步改动并持续保持验证为绿；全部完成后运行覆盖受影响调用点
  和模块的回归，只有全量套件按独立风险决定是否叠加。
- 性能回退或异常变慢进入 `cs-issue`；没有既有异常、仅要求行为等价的主动优化仍进入 `cs-refactor`。
- `cs-epic` 用永久 Epic 文档维护批准后的交付契约，用临时 work 游标恢复活动执行；拆解、契约变化和整体验收分别经过 owner gate。
- 需要独立审查时由外层主流程创建 reviewer；reviewer 每轮执行一次 `cs-review`，返回结果前不再创建子 agent。每个独立审查阶段的首轮使用 fresh reviewer；reviewer 独立性要求它独立于实现者，不要求对自身上一轮审查失忆。
- 一个独立审查阶段由单一审查目的界定；design review、change review、contract review 与 Epic final acceptance 是不同阶段。只有为本阶段 findings 所作修复的复审，才属于同一阶段并沿用原 reviewer lineage；审查目的变化时开启新阶段。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 model；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。具体后端与 model 约束属于项目上下文，不进入 shipped skill。
- 外层主流程派发前冻结一个明确的审查目标（diff review 优先 staged diff，也可用明确 range/patch；
  design review 可冻结仓库内已有 design 文档版本，或 task packet 内原样全文 + SHA-256；audit 冻结
  commit + 范围标识）。使用 packet 时首轮把全文与 hash 原样交给 reviewer，reviewer 审查的目标就是该文本；
  finding-driven follow-up 携带最新全文、前后 hash 与修复摘要。reviewer 返回前不移动目标或
  对应工作树；目标变化则本轮失效。
- `cs-review` 是只读叶子执行器，也承接模块或全仓 audit；修复与复审由外层主流程负责。
- 有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不创建正式里程碑。主流程处理 findings 后修复、重新验证并冻结新的完整目标；仅因 findings 修复产生的复审沿用同一 reviewer 的同一 session，以 follow-up 继续。复审检查完整当前候选与本轮修复增量，逐项报告 `resolved` / `unresolved` / `new findings`，不得只核对旧 finding 或机械打勾。
- 同一审查阶段累计最多 3 个有终态报告的轮次，更换 reviewer 不重置计数。只有原 run/session 失败或不可恢复、能力不满足、目标、范围、设计或核心路径发生重大变化、reviewer 声明无法继续独立判断，或 owner 要求第二意见时才更换 reviewer；更换时重新创建 fresh reviewer。完成所选保障后，实际触发 review 时才要求通过审查门槛，并且只有已有 commit 授权时才形成语义原子里程碑；WIP/checkpoint 只作恢复或隔离基线，不代表通过。
- Epic 同一时间只允许一个 `current_item`；这是串行约束，不是每个子项的人工 gate。连续策略下，普通子项达到语义原子里程碑后自动进入下一项，不得询问“是否继续下一项”或终态返回；逐项暂停必须是 owner 明示策略或真实门槛。
- 健康运行中的 reviewer 与原 run/target 绑定；running，或 Awaiting 携带同一可查询 run identity 且仍为活动态时继续等待，不因后来发现更优创建方式而取消、重复创建或并行补发。只有终止无报告、run identity 不可恢复、能力不满足或目标失效时，本轮才失败且不计审查轮次；外层主流程先诊断再决定有界重试、更换创建方式或上交，不盲目重发。
- `cs-keep` 把高频事实压进 attention，把尚未被更强 owner 承接的经验暂存为 lesson，并推动它们
  毕业到机械 guard、项目文档或 ADR。

普通任务不生成阶段文档。diff、测试输出和交付说明就是证据；只有跨会话、多人交接或用户
要求留痕时，才维护一个 work 文档，完成后删除或按用户要求保留。

## 项目内持续学习

- 四个 task skill 在任务内静默观察。lesson 只做一次有界、最低成本的定向核实，不为此运行大范围
  测试或反复复现；仍不足时跳过，不阻塞正常任务。只有当前事实成立，且真实改变计划或验证，或
  明确排除一个具体且合理的错误路径时，才报告为
  `经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}`；纯关键词碰撞不算复用。
- 晶化候选只存在于当前会话内。普通任务最多展示一条最高价值候选，无强信号就不显示；
  Epic 子项不新增暂停，每项最多把一条去重候选写入既有游标证据区，最终毕业清单统一处理。
- lesson 生命周期为 observed / validated / retired。新条目从 observed 开始，只有独立后续任务中
  的有效命中和成功验证才能进入 validated，并须记录实际行为变化与本次通过的验收证据；事实反证、
  scope 失效或已有更强 owner 时进入 retired。
- read-repair 只允许已有命中条目的窄状态维护；稳定 validated 命中不写文件。
  新 lesson 仍需显式授权，规则/scope 改写、晋升、删除和跨项目分享也不能从任务执行授权中推断。
- 机械 guard 优先：能在当前任务范围内落成测试、checker、lint、类型或 helper 的错误，不再写重复
  lesson。经验最终进入一个 canonical owner；不保存 transcript、逐次命中日志或后台 telemetry。

## Epic 生命周期

Epic 把长期产品意图与短期执行状态分成两层，并且只保留一个事实 owner：

大需求在 `proposed + planning` 阶段路线尚不清晰时，`cs-epic` 才做批准前路线发现：

- 永久 Epic 文档就是唯一路线文档；在 proposed 阶段，永久 Epic 文档本身就是路线地图。现在能精确
  陈述、且会改变路线的问题以带可读名称、`AFK|HITL`、依赖与解决方式的节点放在 `待决策`；
  frontier 只由依赖已经解决的待决策派生，不另存状态或清单。暂时不能精确陈述的路线级迷雾放在 `尚未明确`。
  不新增独立 issue、map 或第三套状态。
- AFK 事实由 agent 定向调查；只有产品判断、用户偏好、外部权限或真实取舍进入 HITL。agent 先给
  事实、选项与取舍、建议及路线影响，但不得替 owner 回答 HITL 问题，也不得把沉默当作选择；一次
  只推进一个 HITL frontier 节点。HITL 不是新的 owner gate，也不代表 Epic 已获批准。route clear
  前不得保留未解决的 HITL 节点；仍有效的 HITL 节点必须由 owner 明确解决或确认移入 `非目标`，
  agent 不得单方判定其超出范围或失效。涉及外部权限或副作用的 prerequisite 仍须另获对应权限或确认。
- 决策答案进入 `关键决策`，并从 `待决策` 移除；答案显露的新问题从 `尚未明确` 提升，超出目的地
  的内容进入 `非目标`，随后重新派生 frontier。决策问题不一对一复制成执行子项。work 只保存当前
  frontier 决策名称、下一步、阻塞和证据指针，路线清晰前 `current_item` 保持 `null`。
- 当剩余未知不能再改变目标、范围、非目标、验收、子项边界、依赖或重大风险，且带稳定 ID、
  owning skill、依赖与验收的子项契约已形成，此时路线清晰、可审查、可执行。route clear 不是新的
  owner gate；完整 proposed Epic 随后进入现有 design review 和第一道 owner 确认。
- 路线已经清晰、只是单个局部技术未知，或仅因高风险、文件多、跨会话时跳过路线发现，仍由对应
  owning skill 处理局部设计与保障。

- **永久 Epic 文档**优先沿用项目既有 Epic、RFC 或 initiative 归宿；没有明确归宿时，首次
  创建才按需建立 `.codestable/epics/{slug}.md`，`cs-onboard` 不预建 `.codestable/epics/`。
  它唯一拥有起点、目标、范围、非目标、验收标准、带稳定 ID/依赖/验收要点的已批准子项、
  关键决策、最终交付索引、整体验收、遗留风险和长期 `status`。
- **临时执行游标** `.codestable/work/epic-{slug}.md` 只保存永久文档指针、
  `approved_revision`、执行 `phase`、当前子项 ID、各 ID 进度、下一步、`blocked_by`、临时
  决策、`item_progression`、`milestone_commit`、`remote_publish` 以及证据/commit 指针；不得复制
  目标、验收、子项定义或最终结论。owner 确认后以永久文档完整 SHA-256 固定批准 revision；
  active 期间永久文档冻结，日常进度与执行策略只更新游标。

Epic 保留三道 owner gate：

1. proposed 拆解先由当前主流程创建 fresh reviewer 做 design review；处理 findings 后按同一 lineage 复审，owner
   确认目标、边界、验收和子项契约，才进入执行。
2. 永久文档已批准后的执行中，目标、范围、非目标、验收、子项增删/定义或重大风险变化时，更新
   永久文档；契约变化形成新的 contract review 审查阶段，由 fresh reviewer 审查并由 owner 确认。
   边界内技术选择和不改变
   依赖/验收的顺序微调不增加 gate。
3. 全部子项完成并通过集成验证后，游标进入 acceptance；final acceptance 是独立审查阶段，
   当前主流程另建 fresh reviewer 开始新的 lineage，不沿用子项、design review 或 contract review 的 lineage，对最新
   owner 已批准的验收标准做 final acceptance review，门槛通过后仍由 owner 最终接受。

首次 gate 一次性确定子项推进、里程碑 commit 与远端同步策略；拆解确认本身不等于版本控制授权。
策略写入 work 游标并在恢复时直接沿用，缺失或非法才暂停一次补记；owner 显式改变策略只更新游标，
不改变批准 hash。`milestone_commit: manual` 只能搭配 `item_progression: per-item`，
且只能搭配 `remote_publish: manual`；`remote_publish: each-milestone` 只能搭配
`milestone_commit: authorized`。

`item_progression: continuous` 时，非最终子项完成后按永久文档顺序选择第一个依赖已满足的未完成
子项，并在同一受托主流程继续。普通子项完成不是 owner gate；不得询问“是否继续下一项”，也
不得把它作为终态返回。`per-item` 时按已记录的逐项 checkpoint 策略暂停。子项 owning skill 自身的
门槛、需要 owner 明确接受的 important findings、真实阻塞、新增权限与最终 owner gate 仍可暂停。

`remote_publish: each-milestone` 在每个语义原子 commit 后按项目、宿主或 owner 已确定的
branch/remote 策略发布；`final` 在集成验证与 final acceptance review 通过后、请求 owner 最终接受前
发布一次；`manual` 时 agent 不执行远端发布。branch/remote 未明确或发布失败时写入阻塞并暂停，
agent 不自行选择或静默继续。

owner 接受后，先补齐永久 Epic 的最终范围、关键决策、交付索引、验收证据和遗留风险，再置为
`accepted`，移除 work 指针并删除 Epic/所属子项游标；永久 Epic 文档不得删除。`superseded` 或
`cancelled` 也按终态幂等收尾，不恢复执行或创建重复 Epic。不恢复 `cs-goal` 入口、goal package、
`state.yaml`、逐轮 iteration 报告或 legacy runtime gate。

## 项目记忆

`/cs-onboard` 为新项目创建最小骨架：

```text
.codestable/
├── attention.md    # 每次会话需要的少量项目事实，最多 25 条
├── lessons/        # 一条经验一个 Markdown 文件，按关键词检索
└── work/           # 活动中的跨会话任务，文件名带类型前缀 feat-/issue-/refactor-/epic-，完成即清
```

skill 专属 context 与 helper 分别由 owning skill 的 `references/` 和 `scripts/` 提供。项目
事实放在上述目录、按需创建的永久 Epic 归宿或项目既有文档与 ADR 中。skill 不读取 sibling
skill 文件，也不依赖集中式 onboard runtime；worktree、branch 和 agent backend 策略由宿主
或 owner 决定。

## v1 升级边界

v2 不迁移或清理 v1 项目的历史目录。`.codestable/roadmap/`、`.codestable/features/`、
`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、
`.codestable/audits/`、`.codestable/brainstorms/` 与 `.codestable/feedback/` 是只读历史知识源：
四个 owning task skills（`cs-feat`、`cs-issue`、`cs-refactor`、`cs-epic`）按任务关键词覆盖
全部九目录并引用命中路径；其他 skill 只检索自身契约明确点名的历史源，例如 `cs-keep` 只读
查重 `compound/`。所有 v1 历史源均不得继续生成、原地改写或批量迁移。

既有 `.codestable/requirements/` 只有在 `.codestable/attention.md` 明确记录其为 canonical
requirement 位置时才可维护；owner 首次指定时先把该项目事实写入 attention。没有显式记录就
按只读历史知识处理，也不默认创建该目录。新项目沿用自身文档结构；没有 canonical 归宿时先请
owner 选择并记录到 attention，稳定契约在确定前保留于永久 Epic。`reference/`、`tools/`、
`gates/`、`hooks/` 与 `runtime-manifest.json` 只作 legacy compatibility，v2 不执行旧 runtime。

v1.0.4 的 32 个 skill 在 v2 收敛为 8 个；其余 24 个入口已退役且不随 v2 安装。完整映射见
[SKILL_CATALOG.md](./SKILL_CATALOG.md)。
