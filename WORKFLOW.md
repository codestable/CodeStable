# CodeStable v2 工作流与项目结构

## 工作流

CodeStable v2 是 8 个独立安装的 thin-harness skill，加一个项目记忆闭环。`cs` 判别用户
此刻要执行、先讨论、咨询还是了解体系：明确行动默认优先同轮直转；先讨论的请求在当前会话
收敛并按授权移交；咨询只给推荐；无诉求时介绍体系。

```text
不确定入口       -> cs
先讨论 / 对齐     -> cs -> cs-feat / cs-issue / cs-epic
仓库接入 / v1 升级 -> cs-onboard
新功能           -> cs-feat ---------\
bug / 行为异常    -> cs-issue ----------> cs-review（高风险或按需）
行为等价重构      -> cs-refactor ------/
大需求拆解        -> cs-epic -> cs-feat / cs-issue / cs-refactor
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

执行强度与风险相称：

- `cs-feat` 默认直接理解、实现、验证；公开契约、数据、权限、并发或真实方案取舍先经用户确认。
- `cs-issue` 先建立能明确变红的验证，再修复并证明它变绿。
- `cs-refactor` 先建立等价性证据，分步改动并持续保持验证为绿。
- `cs-epic` 用永久 Epic 文档维护批准后的交付契约，用临时 work 游标恢复活动执行；拆解、契约变化和整体验收分别经过 owner gate。
- 需要独立审查时由外层主流程创建 reviewer；reviewer 单轮执行 `cs-review`，返回结果前不再创建子 agent。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 model；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。具体后端与 model 约束属于项目上下文，不进入 shipped skill。
- 外层主流程派发前冻结一个明确的审查目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），reviewer 返回前不移动目标或对应工作树；目标变化则本轮失效。
- `cs-review` 是只读叶子执行器，也承接模块或全仓 audit；修复与复审由外层主流程负责。
- 有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不创建正式里程碑；修复后重新验证、冻结目标并创建 fresh reviewer。只有审查门槛通过且已有 commit 授权时才形成语义原子里程碑；WIP/checkpoint 只作恢复或隔离基线，不代表通过。
- Epic 同一时间只允许一个 `current_item`；这是串行约束，不是每个子项的人工 gate。连续策略下，普通子项达到语义原子里程碑后自动进入下一项，不得询问“是否继续下一项”或终态返回；逐项暂停必须是 owner 明示策略或真实门槛。
- 健康运行中的 reviewer 与原 run/target 绑定；running，或 Awaiting 携带同一可查询 run identity 且仍为活动态时继续等待，不因后来发现更优创建方式而取消、重复创建或并行补发。只有终止无报告、run identity 不可恢复、能力不满足或目标失效时，本轮才失败且不计审查轮次；外层主流程先诊断再决定有界重试、更换创建方式或上交，不盲目重发。
- `cs-keep` 把高频事实压进 attention，把尚未被更强 owner 承接的经验暂存为 lesson，并推动它们
  毕业到机械 guard、项目文档或 ADR。

普通任务不生成阶段文档。diff、测试输出和交付说明就是证据；只有跨会话、多人交接或用户
要求留痕时，才维护一个 work 文档，完成后删除或按用户要求保留。

## 项目内持续学习

- 四个 task skill 在任务内静默观察，只把经当前代码、测试或 canonical 文档核实且真实改变计划或
  验证的 lesson 报告为 `经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}`；
  纯关键词碰撞不算复用。
- 晶化候选只存在于当前会话内。普通任务最多展示一条最高价值候选，无强信号就不显示；
  Epic 子项不新增暂停，每项最多把一条去重候选写入既有游标证据区，最终毕业清单统一处理。
- lesson 生命周期为 observed / validated / retired。新条目从 observed 开始，只有独立后续任务中
  的有效命中和成功验证才能进入 validated；事实反证、scope 失效或已有更强 owner 时进入 retired。
- read-repair 只允许已有命中条目的窄状态维护；稳定 validated 命中不写文件。
  新 lesson 仍需显式授权，规则/scope 改写、晋升、删除和跨项目分享也不能从任务执行授权中推断。
- 机械 guard 优先：能在当前任务范围内落成测试、checker、lint、类型或 helper 的错误，不再写重复
  lesson。经验最终进入一个 canonical owner；不保存 transcript、逐次命中日志或后台 telemetry。

## Epic 生命周期

Epic 把长期产品意图与短期执行状态分成两层，并且只保留一个事实 owner：

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

1. proposed 拆解先由当前主流程创建 fresh reviewer 做 design review；处理 findings 后，owner
   确认目标、边界、验收和子项契约，才进入执行。
2. 目标、范围、非目标、验收、子项增删/定义或重大风险变化时，更新永久文档，重新 review
   并由 owner 确认；边界内技术选择和不改变依赖/验收的顺序微调不增加 gate。
3. 全部子项完成并通过集成验证后，游标进入 acceptance；当前主流程创建 fresh reviewer，
   对最新 owner 已批准的验收标准做 final acceptance review，门槛通过后仍由 owner 最终接受。

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
