---
adr: "005"
title: "CodeStable v2 项目知识分层与 Epic 生命周期"
status: Accepted
date: 2026-08-01
supersedes: ["004"]
applies-to:
  - "plugins/codestable/skills/"
  - ".codestable/"
  - "README.md"
  - "WORKFLOW.md"
enforcement: test
stage: [author, onboard, design, review, release]
lint: "python3 -m pytest tests/test_v2_architecture_contract.py tests/test_skill_contracts.py tests/test_v2_documentation_contract.py tests/test_skills_cli_distribution.py"
---

# ADR-005: CodeStable v2 项目知识分层与 Epic 生命周期

## Context

ADR-004 把 v2 收敛为独立安装的 thin-harness skills，并把项目骨架压缩为 `attention.md`、
`lessons/` 与 `work/`。这消除了 v1 runtime 和阶段产物的耦合，但也留下两个缺口：公开文档
承诺旧知识仍可检索，实际 skills 却没有可靠覆盖 `features/`、`issues/`、`goals/` 等历史目录；
`cs-epic` 又会在验收后删除唯一的 Epic work 文档，使长期目标、最终范围和整体验收无法成为
稳定项目上下文。

Epic 同时需要长期可读的产品意图和短期可变的执行状态。把两者继续塞进一个临时 work 文件，
或者恢复 v1 `cs-goal` 的 YAML 状态机与逐轮报告，都会让其中一侧失真。

## Decision

- v2 仍只交付八个主 skill 和 `cs-code-review` 兼容别名；skill 独立安装，context/helper 归
  owning skill，不调用 sibling skill 或集中式 onboard runtime。v2 不向项目复制或刷新通用
  reference、gate、tool、hook、gitignore 或 runtime manifest，也不执行 legacy runtime。
- 新项目的基础骨架仍只预建 `attention.md`、`lessons/` 与 `work/`。首次创建 Epic 时，项目若
  已有明确的 Epic、RFC 或 initiative 归宿就沿用；否则按需创建 `.codestable/epics/`，
  `cs-onboard` 不预建空目录。
- 每个 Epic 分成两层且只保留一个事实 owner：永久 Epic 文档承载起点、目标、范围、非目标、
  验收标准、带稳定 ID/依赖/验收要点的已批准子项、关键决策、最终交付索引、整体验收、遗留
  风险和长期 `status`；`work/epic-{slug}.md` 只保存永久文档指针、`approved_revision`、执行
  `phase`、当前子项 ID、各 ID 的进度、下一步、阻塞、`item_progression`、`milestone_commit`、
  `remote_publish`、临时决策记录以及证据或 commit 指针，不复制子项定义、目标、验收或最终结论。
- 本 ADR 补充批准前路线发现语义：proposed/planning 期间路线尚不清晰时，永久 Epic 文档就是唯一
  路线文档，同时也是文档内路线地图；不新增独立 map、issue 或第三套状态。可精确陈述的
  `待决策` 节点记录可读名称、`AFK` / `HITL`、依赖、解决方式与证据，frontier 只由依赖已进入
  `关键决策` 的节点派生，不另存状态或清单；仍不可精确陈述的内容留在 `尚未明确`。
- AFK 事实由 agent 调查；需要产品判断、用户偏好、外部权限或真实取舍的 frontier 节点进入 HITL。
  agent 必须先给事实、选项、取舍、建议与路线影响，不得替 owner 回答，也不得把沉默当作选择；
  HITL 不是新的 owner gate 或批准。每次解决后，节点在 `待决策`、`尚未明确`、`关键决策` 与
  `非目标` 之间原子迁移，并重新派生 frontier。
- route clear 前不得保留未解决的 `HITL` 节点；仍有效的节点必须由 owner 明确解决或确认移入
  `非目标`，只有因已确认上游决策而机械失效的节点可带依据删除，agent 不得单方判定其超出范围或
  失效。只有 AFK 局部未知可以下放到子项。prerequisite 涉及外部权限、代码外副作用或不可逆动作时
  必须是 HITL，执行前仍须另获对应权限或确认，HITL 回答本身不构成授权。
- 只有会改变目标、范围、非目标、验收、子项边界、依赖或重大风险的路线级迷雾清除，且子项已成为
  带稳定 ID、owning skill、依赖与验收的可交付契约时，才算路线清晰、可审查、可执行。route clear
  不是新的 owner gate；之后仍进入既有 design review 和首次 owner 确认。起草 proposed 永久 Epic
  时同步创建 planning work 游标；批准前 `current_item` 保持 `null`。游标缺失时先查找已有
  `status: proposed` 的在途 Epic，再补游标，不创建重复 Epic。
- 永久文档 `status` 只允许 `proposed -> active -> accepted`；owner 放弃时可从任一非终态转为
  `cancelled`，被后继 Epic 取代时可转为 `superseded`。work 的 `phase` 只允许
  `planning -> executing -> acceptance`；阻塞只写 `blocked_by`，解除后仍处于原 phase，不另造状态。
- `approved_revision` 在 planning 时为 `pending`。拆解确认本身不等于版本控制授权；首次 owner
  gate 同时一次性确定 `item_progression: continuous | per-item | parallel`、
  `milestone_commit: authorized | manual` 与 `remote_publish: each-milestone | final | manual`。
  `milestone_commit: manual` 只能搭配 `item_progression: per-item` 和 `remote_publish: manual`，
  `remote_publish: each-milestone` 只能搭配 `milestone_commit: authorized`，
  `item_progression: parallel` 只能搭配 `milestone_commit: authorized`；进入 executing 前不得保留
  `pending` 或非法组合。
  owner 确认 proposed 文档和策略后，主流程机械地把永久文档置为 `active`，以
  `shasum -a 256 <epic-file>` 得到完整文件 SHA-256，只写入 work 游标并把 phase 推进为 executing；
  确认前不得写入候选 hash。active 期间永久文档保持冻结，
  日常进度和临时决策只写 work；目标、范围、非目标、验收、子项定义或重大风险变化时更新
  永久文档，按与首次激活相同的 review、owner 确认和中断规则替换该 hash。确认前不得写候选
  hash；任一激活步骤中断且无法恢复 owner 确认证据时重新确认，不把 `pending` 或候选值当批准。
- 恢复执行以仓库事实为准：先定位 work 游标，读取其 Epic 指针、phase 与批准 hash，并核对
  active 永久文档的当前 SHA-256 和三个执行策略字段；有效字段直接沿用，不重新询问是否继续。
  旧游标缺字段或组合非法时暂停一次请 owner 补记/修正；owner 中途改变策略只更新 work 游标，
  不改变永久文档或批准 hash，agent 不得从历史操作推断授权。
- Epic 保留三个 owner gate：拆解经独立 design review 后确认目标、边界、验收与子项；目标、
  范围、非目标、验收、子项增删/定义或重大风险变化时重新确认；全部子项完成并由 fresh
  reviewer 对最新 owner 已批准的验收标准做整体验收后，由 owner 最终接受。边界内的日常技术
  选择和不改变依赖/验收的子项顺序微调不新增人工 gate。
- 本 ADR 经实际 Epic 执行反馈补充连续推进语义：`continuous` 与 `per-item` 下同一时间只有一个 `current_item` 是
  串行约束，不是每个子项的人工 gate。`item_progression: continuous` 时，非最终子项成为语义原子里程碑后，
  按永久文档顺序自动选择第一个依赖已满足的未完成子项并在同一受托主流程继续；普通子项完成
  不得成为终态返回或“是否继续下一项”的人工 checkpoint。逐项暂停只来自 owner 明示的
  `per-item` 策略、既有 owner/owning-skill gate、真实阻塞、新增权限或需 owner 接受的 findings。
- 并行推进不改变 owner gate 与文档职责：`item_progression: parallel` 由首次 gate 批准，主流程是
  唯一编排者与唯一游标 writer，把依赖互不阻塞的子项委派给隔离工作区中的 worker（隔离与
  branch 策略仍归宿主，见 ADR-002），并按完成顺序串行集成：以不推进主历史的方式合入、在合并
  结果上重跑该子项权威验证，验证通过后才创建语义原子里程碑；全部合格 worker 创建能力或隔离能力均不可用时本会话内
  退化为串行推进，不改变已记录的策略字段。并发子项的恢复记录（run identity、隔离工作区、基线）
  持久化在游标 `active_items`；协议细节归 `cs-epic` 的 `references/parallel-execution.md`。
- 远端发布不接管项目的 branch/remote 策略：`each-milestone` 在每个语义原子 commit 后按项目、
  宿主或 owner 已确定的策略发布，`final` 在集成验证与 final acceptance review 通过后、请求 owner
  最终接受前发布一次，`manual` 由 owner 自行处理。branch/remote 未明确或发布失败时写入阻塞并暂停，
  agent 不自行选择或静默继续。
- Epic 被接受后先写齐最终范围、关键决策、交付索引、验收证据、遗留风险与毕业清单，再用一次
  终态更新把永久文档置为 `accepted` 并移除临时 `work` 指针。稳定产品契约、结构性决策和经验
  分别毕业到 requirement、ADR 与 lesson；随后删除 Epic work 游标和所属子项 work，永久 Epic
  文档不得作为临时产物删除。owner 用后继 Epic 取代或取消当前 Epic 时，分别置为 `superseded`
  或 `cancelled`，记录后继/取消原因与已有交付，移除 work 指针，再按同一规则收尾。
- 终态 `status` 是不可恢复执行的持久信号。无论中断时 work 指针、游标或所属子项 work 还剩
  哪一部分，都从当前事实幂等续做：补齐终态字段与毕业清单、移除 work 指针、删除游标，再按
  frontmatter `epic:` 清理孤儿子项 work；不得恢复执行或新建重复 Epic。
- v1 的 `roadmap/`、`features/`、`issues/`、`refactors/`、`goals/`、`compound/`、`audits/`、
  `brainstorms/` 与 `feedback/` 是只读历史知识源：原样保留、按任务关键词检索、命中时引用来源；
  不得继续生成、原地改写、批量迁移或执行其中的 legacy runtime。v1 升级仓库里其他未被 v2
  明确拥有的既有 `.codestable/` 目录同样默认只读；新结论写入 v2 Epic、项目文档、ADR 或 lesson。
- 既有 `.codestable/requirements/` 只有在 `.codestable/attention.md` 明确记录其为 canonical
  requirement 位置时才可继续维护；owner 在当前任务首次指定时，先把该项目级事实写入
  attention。没有这条显式记录就按只读历史知识处理。`reference/`、`tools/`、`gates/`、
  `hooks/` 与 `runtime-manifest.json` 只作 legacy compatibility，不由 v2 skills 执行。
- 新项目的 requirement 沿用项目自身文档结构；没有 canonical 归宿时先请 owner 选择并把路径
  记录进 attention，不默认创建 `.codestable/requirements/`。归宿确定前，相关稳定契约留在永久
  Epic 文档，不因收尾而丢失。
- 不恢复 `cs-goal` 入口、goal package、`state.yaml`、逐轮 iteration 报告或 runtime gate。
  Goal 中有价值的目标契约、恢复游标、owner gate 与终态验收由 `cs-epic` 的上述两层文档承担。

## Consequences

- Epic 成为可长期检索的软件要素，活动执行状态仍能在 `work/` 中被快速恢复和完成即清。
- `.codestable/epics/` 是按需的第四类项目知识，而不是所有仓库都必须出现的新骨架目录。
- 一个 Epic 通常维护两份职责互斥的文档；skill 和测试必须阻止复制目标、验收、子项定义、
  长期 status 或最终结论到 work 游标，避免双重真相。执行中形成的临时决策先随证据记在 work，
  终态时再毕业到永久 Epic 的关键决策或独立 ADR。
- legacy 检索面扩大，但只按任务关键词读取，不把全部历史内容装入常驻上下文。
- v1 资产不会被破坏；被重新利用的知识通过引用和毕业进入新 owner，而不是静默改写历史。

## Rejected alternatives

- **完成后继续把 Epic 留在 `work/`**。拒绝：活动目录会不断累积已完成事项，恢复扫描失去意义。
- **验收后删除唯一 Epic 文档**。拒绝：目标、边界、决策与整体交付关系随之丢失。
- **恢复完整 `cs-goal` 状态机**。拒绝：YAML 投影、逐轮报告和 runtime gate 会重新引入 v1 的
  版本耦合与阶段产物负担。
- **把 Epic 全部写进 requirement 或 ADR**。拒绝：requirement 描述持续有效的产品契约，ADR
  描述结构性决策，二者都不应承担一次有界交付的全貌和验收索引。
- **批量迁移或原地更新 v1 历史目录**。拒绝：成本高且会改变历史证据；只读检索与按需毕业
  能保留来源并逐步提高新上下文质量。
