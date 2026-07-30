# CodeStable Skill Spec Standard

创建、精简或重构时遵循 `thin harness, thick context`：顶层 `SKILL.md` 只承担控制面，详细方法与项目事实按需加载。

## 目录

- [核心模型](#核心模型)
- [Shape 选择](#shape-选择)
- [规则放置](#规则放置)
- [Thin Harness 契约](#thin-harness-契约)
- [Haskell Contract Standard](#haskell-contract-standard)
- [恢复、等待与交接](#恢复等待与交接)
- [Runtime Alignment](#runtime-alignment)
- [Collaboration Contract](#collaboration-contract)
- [Evolution Admission / Compression](#evolution-admission--compression)
- [Preflight、失败与输出](#preflight失败与输出)

## 核心模型

```haskell
data SkillShape
  = NoActiveSkill
  | ThinOperator
  | ContextualWorkflow
  | ToolBackedWorkflow
  | ShimSkill
  | ReferenceSkill

data RulePlacement
  = Harness
  | StageContext
  | ProjectContext
  | DeterministicGate
  | Remove
```

`SkillShape` 描述交付形态，不是复杂度等级：

| Shape | 适用场景 | 顶层必须保留 |
|---|---|---|
| `NoActiveSkill` | 没有稳定且独立的用户请求到产物路径 | 不创建 active skill；报告更小的归属 |
| `ThinOperator` | 单一责任、少量分支、一次性产物或动作 | 责任、最小上下文、关键 gate、完成证据 |
| `ContextualWorkflow` | 有阶段、恢复、迭代或按阶段方法 | 责任、`ContextPlan`、最小决策面、恢复与完成契约 |
| `ToolBackedWorkflow` | 路由、状态检查或安全判断由确定性工具执行 | 工具调用条件、输入输出、fail-closed 规则、完成证据 |
| `ShimSkill` | 新发布契约明确要求一个 alias 转发到 canonical skill | 目标入口和原样透传的 preset/参数 |
| `ReferenceSkill` | 有独立分发价值但没有 active workflow | 参考内容、归属与加载条件 |

`NoActiveSkill` 是合法的构建结论。v2 已退役的 24 个旧名称必须保持 `NoActiveSkill`，迁移说明不构成恢复 shim 的发布契约。
`ReferenceSkill` 不注册 active `cs-*` 触发面。新的 `ShimSkill` 仍是独立安装单元，只按名称调用 canonical skill，不能读取 sibling skill 文件或复制其规则。

## Shape 选择

先定义一句话责任，再运行主 harness 的 `selectSkillShape`。以下内容解释其选择语义，不另建
一份路由表：

- 没有独立责任，或 reference/tool/现有 skill 已拥有该行为时，选择 `NoActiveSkill`。
- 多条实现路线均正确、没有持久状态时，优先 `ThinOperator`。
- 需要按仓库事实恢复阶段、处理 owner checkpoint 或跨会话继续时，选择
  `ContextualWorkflow`。
- 已有可靠 router、hook、parser 或 gate 能做确定性判断时，选择
  `ToolBackedWorkflow`。
- 只有新发布契约明确交付 alias 时选择 `ShimSkill`；已退役 v1 名称选择 `NoActiveSkill`。
- 知识有独立分发价值、但没有 active workflow 时，选择 `ReferenceSkill`。

以下任一条件会提高 fragility，并要求更低的自由度：

- 错误分支会越权、破坏安全边界或改变公开契约；
- 存在可恢复状态、owner checkpoint、外部运行或跨 skill handoff；
- 分支有相近但恢复方式不同的失败结果；
- prompt、持久化 schema 与真实 runtime 必须保持一致。

复杂度来自真实风险，不来自文档篇幅。不要因为 skill 是 active skill 就强制完整 workflow、
state machine 或 Haskell Spec。

## 规则放置

写顶层 harness 前，逐条处理现有规则：

使用主 harness 的唯一 `placeRule`。guard 顺序是语义：可机械规则先进入 gate；不可机械的
安全规则必须在 project/stage 分类前进入 harness；其余规则再按 project、stage、
every-invocation 和 remove 分类。reference 不复制第二份实现。

- `Harness`：不可机械化的安全规则，或每次调用在首次关键决策前都必须知道且会改变责任、
  权限、上下文选择、gate、恢复或完成判断的规则。
- `StageContext`：仅在某阶段、变体或方法被选中后才需要的协议、模板、示例和检查表。
- `ProjectContext`：ADR、术语、项目约束、既有模式与历史经验；放在 `.codestable/attention.md`、`.codestable/lessons/`、`.codestable/work/` 或项目既有文档中。
- `DeterministicGate`：能机械判定的安全、schema、状态、格式或同步约束；顶层只保留
  调用时机、输入输出和失败语义。
- `Remove`：模型可可靠推断、已被其他规则覆盖、只有历史解释或没有行为证据的内容。

一条规则只有一个 canonical owner。`SKILL.md` 与 reference 不得并列保存同一协议；
harness 只写 load condition 和接口，不复述 reference 正文。

## Thin Harness 契约

除 `NoActiveSkill` 和 `ReferenceSkill` 外，按需从以下契约中选择。没有对应行为时不要创建空章节。

### Trigger Contract

frontmatter `description` 是触发表面：

```text
Use when <specific request>. Produces <artifact/workflow>. Do not use for <adjacent skills>.
```

避免单独使用 `improve`、`optimize`、`analyze`、`review`、`help` 等宽泛词。

### Responsibility Contract

用一句话写清 skill 对哪个最终结果负责、不能替 owner 决定什么，以及完成需要什么证据。
不要预先规定模型可自行选择的实现路线、工具或局部设计。

Implementation freedom belongs to the executing agent.

### Context Contract

每个会读取仓库事实或 reference 的 skill 都要生成 `ContextPlan`：

```haskell
data ContextPlan = ContextPlan
  { entrySources : [ContextSource]
  , stageSources : Stage -> [ContextSource]
  }

data ContextSource = ContextSource
  { source         : Path
  , placement      : RulePlacement
  , loadWhen       : Predicate
  , purpose        : Purpose
  , sufficientWhen : Predicate
  , reuseKey       : Maybe ContextKey
  , stopCondition  : Maybe StopCondition
  }

buildContextPlan :: SkillShape -> [PlacedRule] -> ContextPlan
```

每个 source 都必须回答：何时加载、为何需要、何时已经足够、何时复用，以及缺失时是否停止。

- 入口只加载首次决策所需的最小事实。
- 选定阶段后先加载一个相关协议，再加载该协议明确请求的 support files。
- 同一会话已由 `reuseKey` 标记的项目事实应复用摘要，不重复读取。
- batch fan-out 必须传结构化复用信号；不能依赖“可能已经读过”的自然语言猜测。
- `thick context` 指高相关、可追溯、足以完成当前阶段，不是把所有 reference 和仓库文档
  全量倒入上下文。
- skill 专属知识放本 skill 的 `references/`；跨 skill 的项目事实放
  `.codestable/attention.md`、`.codestable/lessons/`、`.codestable/work/` 或项目既有文档与
  ADR。不要假设另一个 skill 或集中式 onboard runtime 可用。

### Decision / Gate Contract

只保留会改变路由、授权、停止或完成判断的决策面。简单 operator 可使用几条明确的
guard；存在闭合分支、恢复状态或高风险 fallback 时才使用 Haskell contract。

可机械执行的 gate 不要改写成冗长提示词。harness 只说明：

1. 何时调用；
2. 传入什么；
3. 哪些结果允许继续；
4. 工具不可用、返回未知值或 schema 不匹配时如何 fail closed。

### Done / Recovery Contract

完成必须同时说明产物、验证证据和可恢复状态。未完成时返回当前状态、缺失证据、安全
下一步，以及已写入的文件；不要以模糊的“继续吗”代替可执行下一步。

## Haskell Contract Standard

Haskell-style notation 是紧凑的决策契约，不是装饰，也不表示 Markdown 会编译。仅在
存在闭合 decision、transition、lifecycle、gate 或 invariant 时使用。

```haskell
contractDecision :: Input -> State -> Outcome

data Input = Start Request | Resume RepoFacts | Retry Evidence
data State = Pending | Active Progress | Terminal Result
data Outcome = Run Step | Completed Result | Blocked Reason
data Reason = InvalidTransition | MissingEvidence | ExternalUnavailable

contractDecision _ (Terminal result) = Completed result
contractDecision (Start request) Pending
  | valid request = Run Initialize
  | otherwise     = Blocked MissingEvidence
contractDecision (Resume facts) state = selectFromFacts facts state
contractDecision _ _ = Blocked InvalidTransition

mayComplete state = terminal state && requiredEvidencePresent state
```

应用以下语义：

- 每个公开 decision function 都有 `::` signature；有限选择使用闭合 `data` domain。
- equation/guard 明确把输入和状态映射到 outcome；guard 顺序就是优先级，wildcard 永远
  放最后。
- terminal、invalid、retryable failure、missing evidence 与 owner checkpoint 在恢复方式
  不同时必须保持不同 constructor。
- Use `NeedsHuman` for missing input/capability, `HumanCheckpoint` only for an actual owner decision,
  `Awaiting` for already-started external work, and `Blocked` for an observable terminal or
  retryable failure.
- Every `HumanCheckpoint` must have an explicit resume input or persisted state transition.
- A pending cross-skill handoff must retain its target and complete context, so resume does not depend
  on reclassification or chat memory.
- 在 staged workflow 中，the canonical main entry's tagged resume union 必须表达并原样转发
  每个 stage-level resume decision；reference 内局部闭合的 `Resume*` 类型不构成端到端覆盖。
- 每个 `Awaiting` 分支在返回前必须持久化 machine-readable state、reason 和 external run id；
  restore 必须拒绝缺失 id 和含混的 legacy `blocked` state。
- 全路径条件使用 `where` 或命名 predicate，例如 `mayComplete`、`invariant`、`converged`；
  不把必要分支藏在注释中。
- 迭代协议分别定义 `step`/`advance`、convergence 和 termination；第 n 轮演进的组件必须由
  后续真实迭代验证后才能声明稳定。
- 每个决策面以可观察 outcome 或明确 invalid transition 结束，不留省略号或散文默认分支。

同一分支逻辑不能同时存在 Haskell equation 与散文状态机表。散文只解释责任、输入输出和
不变量。

## 恢复、等待与交接

只有需要恢复的 `ContextualWorkflow` / `ToolBackedWorkflow` 才建立状态恢复：

```haskell
restoreState :: RepoFacts -> WorkflowState
selectNextAction :: WorkflowState -> EntryIntent -> Outcome
```

状态来自 `.codestable/` artifacts、status fields、review/QA/acceptance evidence、marker、git
diff/commit 或明确持久化 note，不来自聊天记忆。

- canonical 主入口负责恢复自身状态并选择内部 stage/lane。
- 普通 cross-skill handoff 只指定 canonical 主入口并携带 intent、artifact identity、
  relevant evidence、pending decision 与 recovery pointer。
- 只有 `ShimSkill` 可以传旧 `requested_stage` / `requested_mode` preset。
- 外部工作已启动才返回 `Awaiting`；先保存 external run identity，再返回等待状态。
- `HumanCheckpoint` 恢复输入必须 typed；确认不得通过自由文本猜测，也不能被自动继续绕过。

## Runtime Alignment

`ToolBackedWorkflow` 以真实 router/hook/parser/gate 作为确定性执行面；harness 描述责任、
调用条件、schema、invariant 和 outcome，不复制完整 branch table。

```text
persisted artifact fields -> normalized Spec state -> runtime outcome
```

共同检查：

- persisted fields/value 与 contract constructor 的显式映射；
- guard priority、invalid/terminal precedence；
- continue、dispatch、report、handoff、awaiting、completion 与 unknown outcome；
- typed resume、external run id 和 stale metadata 的处理；
- fixture 字段与真实 runtime schema。

存在 runtime 时必须用真实 router 做 conformance；手写一份测试 router 不是 alignment
evidence。确定性 helper 由 owning skill 的 `scripts/` 提供；v2 不新增或调用 repo-local
runtime。v1 项目里的旧 tool/gate 可以保留，但不构成新 skill 的依赖。

## Collaboration Contract

只有工作可以形成边界清楚、可独立验收的 scope 时才 dispatch agent。不要在 harness 中
预编排固定角色和逐步实现路线。

任务包必须是：

goal + relevant context + scope ownership + boundaries + evidence + return contract

子 agent 自主选择实现；返回改动、证据、风险和未决项。主 agent 持有全局责任、集成、
冲突处理和最终验证，owner decision 不能下放给子 agent 或用投票代替。

## Evolution Admission / Compression

新规则只有在事故、owner correction、重复错误、公开契约变化或明确验证缺口提供行为证据
后才准入。先替换/修正已有规则，再考虑新增。

```haskell
admitEvolution :: Evidence -> Rule -> Maybe RulePlacement
admitEvolution evidence rule
  | behaviorRelevant evidence = Just (placeRule rule)
  | otherwise                 = Nothing
```

准入后执行压缩：

1. 重新运行 `placeRule`；
2. 合并或替换语义重复的旧规则；
3. 将阶段知识、项目事实和机械判断下沉到正确 owner；
4. 删除不再影响责任、决策、gate、上下文选择、恢复或完成证据的文字；
5. 为行为变化在最近的确定性层增加回归；
6. 用无聊天历史的新 agent 检查冷启动、上下文选择、停止与完成。

顶层增长必须解释为什么该规则是所有调用在首次关键决策前都需要的。行数只是异常信号，
不是质量指标。

## Preflight、失败与输出

仅当目标依赖 CodeStable setup、仓库状态、artifact 写入或 agent dispatch 时才做 preflight：
首次进入读取 `.codestable/attention.md`（同一会话复用）；缺失则停止或路由 `cs-onboard`；
可能编辑时检查 git status 并保留无关改动。不要强加给 `ShimSkill`、`ReferenceSkill` 或
`NoActiveSkill`。

失败或暂停时报告当前 artifact、原因、安全下一步、已写文件和 retry 条件。最终输出包含
责任结果、`SkillShape`、`ContextPlan`、规则 placements、验证证据和下一动作/checkpoint。
