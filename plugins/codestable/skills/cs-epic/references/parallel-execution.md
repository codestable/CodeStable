# cs-epic 并行执行协议

仅在 work 游标 `item_progression: parallel` 且批准 hash 有效时读取。本协议只改变已批准子项的调度与集成方式；三道 owner gate、审查协议、`milestone_commit` / `remote_publish` 语义、双层文档职责与暂停清单全部不变，并行不新增 owner gate。

## 进入与退化

- 进入条件：owner gate 已批准 `parallel` 且组合合法（必须 `milestone_commit: authorized`）；子项契约中存在至少两个依赖互不阻塞的未完成子项；当前会话按下述 worker 创建优先序能发现任一合格的有界、可管理 worker 创建能力，且宿主能提供隔离工作区（worktree/branch 策略归宿主，本协议不选择隔离实现、不命名具体后端）。
- 并行允许并发，不强制并发。全部合格 worker 创建能力或隔离能力均不可用、或可运行子项只剩一个时，本会话内退化为串行推进：语义与 `continuous` 相同，游标策略字段不变，报告中说明退化原因。退化不是策略变更，无须 owner 重新确认。

## 调度

- 可运行集合 = 已批准且未完成的子项中，依赖已全部完成、不在 `active_items`、且该 ID 没有未解除阻塞记录者。
- 进入 parallel executing 时在游标 frontmatter 初始化 `active_items: []` 并保持 `current_item: null`。每次派发把该子项的最小恢复记录写入 `active_items`：`{item, state, run: 创建方式与 run identity, workspace: 隔离工作区指针, base: 派发基线 commit}`；`state` 只允许沿 `dispatched -> delivered | blocked`、`delivered -> integrating | blocked`、`integrating -> integrated | blocked` 分支单向转换；`integrated` 随里程碑、`blocked` 随阻塞记录一并移出 `active_items`，`active_items` 只保留非终态项。
- parallel 下 `current_item` 只表示串行集成焦点：开始集成某个已交付子项时设置，里程碑创建或集成失败回滚后原子清空为 `null`；派发中与执行中的子项不占用 `current_item`。
- 每完成并集成一项，重算可运行集合并补发新就绪子项；仍有未完成子项但可运行集合与 `active_items` 均为空时按阻塞暂停。
- 并发上限取宿主能力与 owner 显式约束中的较小者；无明确约束时保持小并发（2–3），集成与验证吞吐不足时先收敛并发而不是积压未集成交付。

## 委派契约

- 每个并发子项对应一个 worker，携带 contextPacket：
  - goal：子项契约全文与稳定 ID、验收要点；
  - relevantContext：Epic 目标/范围/非目标摘要、相关共享语言术语、已完成依赖子项的交付指针；
  - scopeOwnership：只拥有本子项；列出明确不得触碰的路径与契约；
  - boundaries：隔离工作区路径；不得写 work 游标或永久 Epic 文档；不得执行远端发布；不得认领或修改其他子项；
  - evidence：owning skill 要求的验证证据种类；
  - returnContract：终态为 `completed`（证据 + 可集成交付指针 + 可选 `晶化候选：{rule}`）或 `blocked`（原因、已尝试路径与分类：`item-local` 指仅影响本子项的实现层阻塞；`epic-global` 指命中 SKILL.md 暂停清单的情形——契约或重大风险变化、新增权限、需要 owner 明确接受的 findings 等）。
- worker 按子项类型执行其 owning skill（cs-feat / cs-issue / cs-refactor）的完整纪律。worker 是范围受限的编排者：仅被授权按其 owning skill 的审查协议创建 reviewer；reviewer 是叶子执行器，不得再创建子 agent；worker 不得派发其他执行 agent。
- worker 创建沿用 SKILL.md reviewer 条款的能力发现顺序：受管理的结构化委派能力优先，其次宿主 subagent，最后本机有界 agent CLI，不得只扫 PATH；具体后端与 model 约束属于项目上下文，不写入本 skill。
- worker 承担实现纪律，选择目标是质量而非独立性：显式选择当前会话可用的最强稳定 model，默认与主流程同构即可，不为 worker 追求异构，禁止依赖默认模型。推理强度与子项契约的风险和设计密度相称：纯机械性子项可降档，含设计取舍、跨模块影响或高失败代价的子项用最强档，拿不准时不降档。异构优先只适用于 worker 为自己创建的 reviewer——相对 worker 这个实现者异构。
- 每个 worker 的创建方式、agent/model 与选择原因写入其 contextPacket 记录，与 reviewer task packet 同规。
- worker 在隔离工作区交付可集成状态：已有 commit 授权下的明确标记 WIP/checkpoint commit（对应 SKILL.md 隔离基线条款），或等效 patch；正式里程碑 commit 只由主流程创建。
- worker 运行健康与失败判定沿用 SKILL.md 的 run identity 条款：绑定运行等待终态返回，idle 且无可恢复 run identity 视为委派失败，先诊断再决定一次有界重派，不盲目重发。

## 单 writer 不变量

- work 游标与永久 Epic 文档只有主流程一个唯一 writer；worker 只在自己的隔离工作区内改动。
- worker 返回的进度、证据、阻塞与晶化候选由主流程统一落盘；晶化候选沿用既有毕业清单流程。
- 发现 worker 越权写共享状态时终止该 worker，改动不集成，诊断 packet 边界后重派。

## 串行集成与里程碑

- 集成按完成顺序串行，且验证通过前不推进主历史：主流程以不提前推进 HEAD、不引入 worker WIP 历史的方式把交付合入主工作区（squash 到工作树、patch 应用、`cherry-pick -n` 等；如用 merge 必须禁止 fast-forward 且不产生 merge commit），在合并结果上重跑该子项的权威验证；验证通过后才创建唯一的语义原子里程碑 commit，一次收口代码、证据与游标更新。验证失败则恢复到集成前基线，不留任何正式 commit，该子项按分类转 `blocked` 或退回原 worker 修复。不把多个子项堆进同一 diff，集成期间不并行执行第二个集成。
- merge 冲突归主流程：只涉及实现细节时就地解决并重跑验证；涉及子项契约、依赖或验收时按契约变化走 SKILL.md 重确认门槛。
- `remote_publish: each-milestone` 在每个集成后的语义原子 commit 后发布；`final` / `manual` 语义不变。

## 失败隔离与恢复

- `item-local` blocker 把该子项转 `blocked` 终态：移出 `active_items`，原因写入游标中该 ID 的进度与阻塞记录，不中断其他并发子项；阻塞解除后该子项重新进入可运行集合。全部剩余子项都不可运行时才整体暂停。
- `epic-global` blocker 不做隔离处理：停止补发新子项，写 Epic 级 `blocked_by` 并执行 SKILL.md 既有暂停协议；并行不得成为绕过 owner gate 或暂停清单的通道。
- 跨会话恢复以游标为准：已集成子项以 milestone commit 为准。`active_items` 中的子项先按恢复记录查询 run identity——运行仍健康则继续绑定等待，不重复派发；运行已终止的，按 `workspace` 与 `base` 收割隔离工作区中可核实的交付并集成；只有确认旧 run 不可恢复且交付不可核实时，才重派 fresh worker 并更新该项恢复记录。

## review 并发边界

- 子项级 review 属于 worker 内 owning skill 门槛，可与其他子项并行，各自 reviewer lineage 与轮次计数独立。
- Epic 级 design review、contract review 与 final acceptance review 不并行、不下放 worker，仍由主流程按 SKILL.md 审查协议执行；final acceptance 前必须完成全部子项集成。
