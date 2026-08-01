# CodeStable Skill Quality Gates

审查 `cs-*` skill 是否形成 `thin harness, thick context` 且能够持续演进时读取本规范。
这些 gate 验证行为与放置，不按章节数量或行数判定质量。

## 目录

- [Shape Selection Gate](#shape-selection-gate)
- [Thin Harness Gate](#thin-harness-gate)
- [Rule Placement Gate](#rule-placement-gate)
- [Context Plan Gate](#context-plan-gate)
- [Haskell Contract Semantics Gate](#haskell-contract-semantics-gate)
- [Runtime Alignment Gate](#runtime-alignment-gate)
- [Canonical Handoff Gate](#canonical-handoff-gate)
- [Collaboration Contract Gate](#collaboration-contract-gate)
- [Regression Ladder](#regression-ladder)
- [Evolution Admission Gate](#evolution-admission-gate)
- [Evolution Compression Gate](#evolution-compression-gate)
- [Live Host Safety Gate](#live-host-safety-gate)
- [Family Audit Coverage Gate](#family-audit-coverage-gate)

## Prompt-As-Code Rule

skill 是责任与决策契约，不是教程。质量来自：

- 窄而准确的触发面；
- 与 fragility 相称的 `SkillShape`；
- 正确的规则放置和最小 always-loaded harness；
- 高相关、按需加载且可复用的 `ContextPlan`；
- 可观察的 gate、失败与完成证据；
- 对高风险分支的 typed recovery 和确定性回归。

显式 state model 只属于确有闭合状态或恢复需求的 skill。简单 active operator 没有完整
workflow/Haskell state machine，不构成缺陷。

## Shape Selection Gate

先验证责任，再验证 shape：

| Shape | 通过条件 |
|---|---|
| `NoActiveSkill` | 没有独立责任；行为已有更小的 canonical owner；不创建 active trigger |
| `ThinOperator` | 单一责任；没有伪造阶段；少量 guard 足以安全完成 |
| `ContextualWorkflow` | 真实阶段/迭代/恢复存在；仓库事实决定状态；按阶段加载 context |
| `ToolBackedWorkflow` | 确定性工具实际存在；接口、失败和 alignment 可验证 |
| `ShimSkill` | 新发布契约明确交付 alias；仅转发 canonical entry 与 preset，不复制主规则 |
| `ReferenceSkill` | 只有独立分发的知识；有 load condition 且没有 active workflow |

以下情况拒绝 shape：

- 为了形式完整把单步 operator 扩写成 workflow；
- 有可恢复阶段却选择只靠聊天记忆的 `ThinOperator`；
- 声称 tool-backed 但没有真实可调用工具或 fail-closed 行为；
- reference 内容伪装成 active methodology skill；
- 已有 canonical owner 时仍创建重复 active skill。
- 为 v2 已退役名称恢复 compatibility shim。

## Thin Harness Gate

顶层 `SKILL.md` 只应包含每次调用在首次关键决策前必须知道的控制面：

- trigger 与 Responsibility Contract；
- Context Contract 及 source 的 load condition；
- 决策/授权/停止 gate；
- 必要的 typed resume、runtime interface 与 canonical handoff；
- Done / Recovery Contract；
- 只有发生 dispatch 时才加入 Collaboration Contract。

检查：

- 删除任一句 harness 文字，是否会改变责任、决策、gate、context 选择、恢复或完成证据？
- StageContext / ProjectContext 的正文是否被复制进顶层？
- tool 的确定性算法是否被提示词再次实现？
- 一个没有聊天历史的 fresh agent 能否从入口选对 context，并正确完成或停止？

简单 operator 的 30-80 行、workflow front door 的 60-120 行可作为增长警报，但不是硬性
验收线。超出时重新执行 placement；不要通过压缩语句牺牲必要语义来追求行数。

## Rule Placement Gate

Every new or changed rule must re-enter `placeRule`.

逐条验证：

- 能机械判定的规则进入 `DeterministicGate`，harness 只保留调用接口与失败语义；
- 不可机械化的安全规则，或所有调用首次关键决策前都需要且改变行为的规则，进入 `Harness`；
- 阶段/变体专属方法进入 `StageContext`；
- ADR、术语、项目历史和局部约束进入 `ProjectContext`；
- 可推断、重复、过时或没有行为证据的规则进入 `Remove`。

每条规则只能有一个 canonical owner。`SKILL.md`、reference、runtime 与项目 artifact
可以互相引用或映射，但不得复制同一协议正文。

## Context Plan Gate

每个 `ContextPlan` source 必须有：

- `loadWhen`：哪项决策或阶段触发加载；
- `purpose`：缺少它会做错什么；
- `sufficientWhen`：读到何处即可行动；
- `reuseKey`：同一 session/batch 如何识别已加载；
- `stopCondition`：必需 source 缺失或冲突时是否停止。

检查加载行为：

- entry 只加载首次决策所需的最小事实；
- 选中阶段后先加载恰好一个 stage protocol，再加载其明确请求的 support files；
- startup 不扫描或读取全部 references、ADR、compound 或历史 artifacts；
- thick context 的“厚”来自当前阶段的相关性、证据密度和完整性，不来自体积；
- 顶层只列 reference 的用途与 load condition，不复述 reference；
- skill 专属 reference 可随独立安装单元分发；跨 skill 的项目事实通过
  `.codestable/attention.md`、`.codestable/lessons/`、`.codestable/work/` 或项目既有文档
  与 ADR 获取，不读取 sibling skill 文件，也不依赖集中式 onboard runtime。

首次读取项目事实的价值必须保留；同一会话继续时复用已读摘要。batch fan-out 必须传
结构化 flag/reuse key，让 child 明确跳过 parent 已加载的全局输入，不能只写“如已读则复用”。

## Haskell Contract Semantics Gate

仅当目标存在闭合 decision、transition、lifecycle、gate 或 invariant 时要求 Haskell
contract；一旦使用，就按语义检查而不是只检查 fence：

- 至少一个 typed boundary (`::`) 或闭合 `data` domain 指明契约决定什么；
- 至少一个 equation/guard 将输入和状态映射到 outcome；
- guard priority 正确，wildcard 在最后，不吞掉具体 failure/terminal branch；
- terminal、failed、blocked、checkpoint、awaiting 与 invalid 在恢复不同处保持独立；
- completion prose 与命名 invariant/termination predicate 一致；
- 每个 stage-level resume decision 都能由 canonical main entry 表达并转发；
  a locally closed reference type does not prove end-to-end resume coverage；
- 每个 `HumanCheckpoint` 都有 typed resume input 或持久化 transition；
- 每个 `Awaiting` 都有 state/reason/external run id；真实 restore path rejects
  missing ids plus ambiguous legacy `blocked` states；
- constructor/field 与 sibling protocol、persisted artifact、fixture、真实 runtime 一致。

语法测试只能证明 decision surface 存在；高风险分支仍需 exact scenario 或真实 runtime
conformance。

## Runtime Alignment Gate

先区分决策 owner：

- `ContextualWorkflow` 的 prompt-routed 分支以一个 compact Haskell contract 为唯一 prompt
  truth，不再并列散文 branch table。
- `ToolBackedWorkflow` 的真实 router/hook/parser/gate 是确定性执行面；harness 只描述调用
  条件、schema、invariant、outcome 和 fail-closed 行为。

Tool-backed workflows must not copy the deterministic branch table into `SKILL.md` or a reference.
共同检查四个 surface：

- persisted fields/value 显式映射到 normalized state / contract constructors；
- guard order、invalid-state 与 terminal-state precedence 一致；
- outcome 区分 continue、dispatch、report、handoff、awaiting、completion 和 unknown；
- fixtures 使用当前字段，并覆盖 typed resume、run identity 与 stale metadata。

conformance 必须调用真实 runtime。单独手写的 test router 即使为绿色，也不能证明生产
alignment。schema 变化后，受影响的历史结果失效，必须重跑当前 fixture。

## Canonical Handoff Gate

cross-skill 路由必须 target the canonical main entry without selecting its internal stage/lane。
handoff packet 保留 intent、artifact identity、relevant evidence、pending owner decision 和
recovery pointer；接收方自行恢复状态。

只有 `ShimSkill` 可以传 legacy `requested_stage` / `requested_mode`。长任务已经启动
时，返回 `Awaiting` 前必须写入 external run identity；可见 fallback 不能丢失原 target 和
完整 context。

## Collaboration Contract Gate

先验证 topology：只有责任明确包含编排的 harness 是 `Orchestrator`；被委派完成具体产物或
审查的 agent 默认是 `LeafExecutor`，不得再 dispatch、follow up child、调用自身或兼容别名。
- shipped harness 只描述 subagent 创建与管理能力，具体后端/model pin 在项目上下文；创建 reviewer 前发现当前会话可调用的能力，不以 PATH 列表冒充；
- 创建方式依次选受管理结构化委派、宿主 subagent、有界一次性 agent CLI 回退，再按质量基线、异构偏好和最强稳定 model 选人并写入 task packet；
- 子 agent 不获无关 context 或固定实现步骤；返回含改动、证据、风险与未决项；
- 健康运行的 delegation 绑定原 run/target；活动 `Awaiting` 带同一可查询 run identity 时继续等待，不因更优创建方式取消或重复 dispatch；
- terminal failure 无报告，或 idle/silence without return payload 且无可恢复 run identity，或能力不匹配、target 失效时，才失败并允许有界切换；
- calling `Orchestrator` 持有集成、冲突、重试和最终验证；owner decision 不得委托或投票替代。
只有 scope 可独立拥有并有独立验收证据时才 dispatch，否则保持单 agent。

## Static Evidence Gate

静态检查保护行为骨架，不代替场景测试。优先验证：

- 关键 decision/runtime function 或 tool invocation；
- required artifact、checkpoint、forbidden action 与 run-id invariant；
- reference load condition、reuse guard 和 canonical handoff；
- deprecated key/入口使用显式负向断言，不写入 skill frontmatter。

不要锚定裸 type name、通用词、只出现在示例中的字符串或正常编辑极易变化的整句。

## Behavior Gate

对每个重要分支回答：

- 哪些 repository facts 触发它？
- 哪个 artifact/runtime result 证明它发生？
- 跳过什么会不安全？
- 最近的 unsafe sibling outcome 是什么？

一个 fixture 只断言一个 decision。无法直接测量 context action 时，先用静态检查
保护 load/reuse 规则；不要把单轮 routing 结果冒充“没有重复读取”的证据。

## Regression Ladder

选择能直接暴露缺陷的最便宜层；跨边界时再增加下游证据：

1. **Shape**：frontmatter、shape/placement、reference link、required/forbidden anchor、schema。
2. **Contract semantics**：Haskell domain、guard order、explicit negative/terminal branch、
   typed resume、run identity。
3. **Cross-file**：template/runtime copy equality、main/deep protocol agreement、deprecated term。
4. **Scenario**：exact facts -> exact outcome，并断言最近的 unsafe sibling outcome。
5. **Runtime conformance**：调用真实 router/hook/parser，不验证手写 mirror。
6. **Forward test**：把原始任务和 artifact 给 fresh agent，不泄露预期答案、缺陷或修复。

每个行为修正都在最近的确定性层获得回归。能做到时先证明该测试在修复前失败。基础设施
timeout 导致某层未运行时，不能报告整套验证通过。

## Evolution Admission Gate

新规则必须指向至少一种证据：

- 真实事故或 unsafe near miss；
- owner correction 或公开契约变化；
- 多次出现的同类错误/上下文缺口；
- 新增 runtime/schema invariant；
- forward test 暴露的可复现失败。

没有行为证据的解释性内容不进入 harness。准入前先检查能否修正现有规则、reference 或
gate；准入后重新 placement，并在 Regression Ladder 最近层增加回归。

## Evolution Compression Gate

禁止 additive-only evolution：不能把每次事故总结都追加到顶层并保留旧说法。

每轮演进后检查：

- Every new or changed rule must re-enter `placeRule`.
- 新规则是否替换了冲突、重复或过时规则；
- 可机械判断内容是否已迁移到 `DeterministicGate`；
- StageContext / ProjectContext 是否回到唯一 owner；
- 顶层每句话是否仍改变责任、决策、gate、context、恢复或完成；
- reference 与 `SKILL.md` 是否存在语义重复；
- fresh agent 冷启动能否选对 context、完成或安全停止。

行数增长只触发重新 placement 和压缩，不触发机械删词。压缩后不得损失 typed resume、
Awaiting identity、owner checkpoint、canonical handoff 或安全 gate。

## Live Host Safety Gate

执行前给每个命令分类：

| Impact | Allowed behavior |
|---|---|
| `Hermetic` | no external daemon or user home; preferred default |
| `Isolated` | temporary HOME/cache/socket/endpoint and test-owned children only |
| `LiveReadOnly` | identity/capability snapshots only; no lifecycle mutation |
| `LiveMutating` | explicit owner approval and a dedicated disposable environment required |

在存在 host-managed agent session 的开发机上：

- 禁止 stop/restart/archive/close/kill external services，禁止 broad `pkill` / `killall`；
- 不写用户的 agent home、route index、socket、endpoint 或 provider config；
- integration test 使用 per-run temporary home、endpoint、route/cache 和 bounded timeout；
- heavy suite、Go validation、multi-target builder、package install 串行执行，并声明
  worker/resource budget；
- 只清理由本次运行记录的 PID；signal 前立即核对 PID、UID、argv、process start identity、
  expected temp path/parent，任一不符就保留并报告；
- `LiveReadOnly` 前后比较 PID、UID、argv、version/server id、home 和 listen address；identity
  变化即失败。

完成要求：targeted deterministic layers 通过；列出 skipped heavy/live layers 及原因；
test-owned child 已回收或带 ownership warning 保留；external host identity 未变化。
CI or a quiet disposable host 应承担最终 full-suite/build matrix。

## Family Audit Coverage Gate

当请求覆盖一个 family 的全部 skill/reference 时，先递归发现 filesystem set，再
compare it with the reviewed/classified set by equality。包含所有非 `SKILL.md` Markdown，包括根层
`reference.md`，不能只枚举 `references/` 下的任意层级 `*.md`。

shipped active set 必须与 package manifest/distribution 精确相等，退役名称有负向断言；
accepted shims、Haskell contracts、structured references 进入显式互斥集合。subset 不足以证明完整。

跨 skill 路由还要断言 canonical main entry 规则；普通 operator/router/audit/workflow
handoff 不得预选接收方内部 stage/lane。

## Anti-Patterns

先修复以下问题，不要继续加 prose：

- 所有 active skill 被强制同一套 workflow/state machine；
- Haskell/工具 branch 与散文 branch table 并列；
- reference 在 startup 全量加载，或与 `SKILL.md` 重复并把“厚”理解为体积；
- routing/resume 依赖聊天记忆，或 `Awaiting` 没有 external run identity；
- shim 复制主规则，或普通 cross-skill handoff 预选接收方 stage/lane；
- Collaboration Contract 固定角色和实现步骤，却没有 scope ownership；
- project facts 在同一 session/batch 无条件重复读取；
- failure 只写“ask user”，或用 additive prose 替代 artifact、原因、安全下一步和旧规则修正。
