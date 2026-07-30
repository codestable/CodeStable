# CodeStable Skill Fixture Patterns

为 `cs-*` skill 设计行为回归时读取本规范。fixture 验证决策；静态 contract 验证 shape、
placement、reference link 与 invariant。两者不能互相冒充。

## 目录

- [按 Shape 选择](#按-shape-选择)
- [基础 Fixture](#基础-fixture)
- [恢复与等待](#恢复与等待)
- [Runtime 与 Handoff](#runtime-与-handoff)
- [ContextPlan](#contextplan)
- [演进回归](#演进回归)

## 按 Shape 选择

fixture 数量由 fragility 和分支数决定，不要求每个 skill 固定 5-8 个：

| Shape | 最小建议 |
|---|---|
| `NoActiveSkill` | 验证没有新增 active trigger，并记录已有 canonical owner 或更小归属 |
| `ThinOperator` | 1 个 happy path；存在危险边界时再加 failure/forbidden case |
| `ContextualWorkflow` | 每个高风险 branch 一个 decision case；resume/terminal 各有正反例 |
| `ToolBackedWorkflow` | 真实 runtime conformance；unknown/schema mismatch fail closed |
| `ShimSkill` | canonical target 与 legacy preset passthrough 各一项断言 |
| `ReferenceSkill` | 不造 routing fixture；验证归属、链接、load condition 和无 active workflow |

一个 fixture 只验证一个 decision。不要把 routing、输出格式、artifact 内容和 context action
混进同一 case。

## 基础 Fixture

使用小型 YAML/JSON，并显式断言最近的 unsafe sibling outcome：

```yaml
name: no-design-routes-to-design
skill: cs-feat
step: restoreFeatureStage
state:
  feature_dir_exists: true
  has_design: false
  qa_status: missing
expect:
  result_type: RoutedTo
  stage: Design
  must_not_route_to: Implementation
```

### Owner Checkpoint

checkpoint case 必须证明这是 owner decision，而不是 missing input 或普通等待：

```yaml
name: review-passed-requires-owner-confirmation
step: selectNextAction
state:
  design_status: draft
  design_review: passed
expect:
  result_type: HumanCheckpoint
  reason: ConfirmDesign
  must_not_route_to: GoalPackage
```

同时增加 typed resume case，防止自由文本或错误 checkpoint 被接受：

```yaml
name: confirm-design-resumes-through-main-entry
step: entrypoint
input:
  resume:
    kind: ConfirmDesign
    decision: Approved
state:
  design_status: draft
  design_review: passed
expect:
  result_type: RoutedTo
  stage: GoalPackage
  must_not_result_type: NeedsHuman
```

再加一个错误 `resume.kind` -> `Blocked InvalidResume` 或 `NeedsHuman` 的负例。

### Forbidden Action

```yaml
name: docs-skill-must-not-change-code
step: planAction
input:
  request: update public docs for the auth API
expect:
  result_type: RoutedTo
  stage: Docs
  forbidden_actions:
    - edit_source_code
    - git_push
```

### Failure Path

```yaml
name: ambiguous-feature-target-needs-human
step: restoreFeatureTarget
state:
  matching_features:
    - .codestable/features/2026-07-01-auth
    - .codestable/features/2026-07-03-auth-refresh
expect:
  result_type: NeedsHuman
  reason_contains: which feature
```

failure fixture 应断言当前 artifact 与安全下一步，而不只是结果名称。

## 恢复与等待

### Awaiting Run Identity

外部工作已启动时，正例必须携带真实 run identity：

```yaml
name: active-driver-is-awaiting
step: restoreGoalRun
state:
  goal_run_state: active
  run_id: run-20260730-01
expect:
  result_type: Awaiting
  run_id: run-20260730-01
  must_not_result_type: HumanCheckpoint
```

缺失 id 的 companion case 必须 fail closed：

```yaml
name: active-driver-without-id-is-invalid
step: restoreGoalRun
state:
  goal_run_state: active
  run_id: null
expect:
  result_type_any: [Blocked, NeedsHuman]
  must_not_result_type: Awaiting
```

对含混 legacy `blocked` state 也增加拒绝恢复的 case。terminal case 带 stale driver metadata，
验证 terminal precedence。

### 完整生命周期

长任务分别覆盖：

- ready -> dispatch；
- active + run id -> `Awaiting`；
- completed + stale run metadata -> `Completed`；
- fallback artifact -> canonical handoff；
- unknown/legacy ambiguous state -> fail closed。

不要用一个含多个转移的 fixture 代替这些单决策 case。

## Runtime 与 Handoff

### Real Runtime Conformance

`ToolBackedWorkflow` 的 fixture 必须调用真实 router/hook/parser。输入使用当前 persisted schema，
断言真实 stdout/JSON/exit status，再映射到 contract outcome。

禁止在测试中重写一个同构 branch table；那只能证明测试模型自洽，不能证明生产 runtime
与 harness aligned。至少覆盖：

- 正常 outcome；
- unknown enum / schema mismatch；
- terminal precedence；
- typed resume 或 external run id（如适用）。

### Canonical Handoff

```yaml
name: upstream-routes-to-canonical-feature-entry
skill: cs-brainstorm
step: handoff
input:
  intent: add public auth API
  artifact: .codestable/brainstorms/auth.md
expect:
  route_to: cs-feat
  must_not_set:
    - requested_stage
    - requested_mode
```

只有 shim fixture 可以断言 legacy preset：

```yaml
name: legacy-qa-entry-routes-to-main-skill
skill: cs-feat-qa
step: entrypoint
input:
  args: ""
expect:
  route_to: cs-feat
  requested_stage: qa
  must_not_define_independent_rules: true
```

handoff 还应验证 target、artifact identity、relevant evidence、pending owner decision 和
recovery pointer 没有丢失。

### Fastforward Eligibility

```yaml
name: fastforward-rejects-public-contract-change
step: chooseMode
input:
  args: --mode fastforward add new public auth API
state:
  crosses_public_contract: true
expect:
  result_type: RoutedTo
  stage: Design
  must_not_route_to: FastForward
```

## ContextPlan

常规单轮 routing fixture 看不到文件是否被加载或重复读取。因此：

- 静态 contract 验证每个 source 的 `loadWhen`、`sufficientWhen`、`reuseKey` 和
  `stopCondition`；
- cross-file test 验证顶层只引用、不复制 reference；
- 有 tool-enabled/action trace 时，才断言 entry 未加载无关 StageContext、同一 reuse key
  未重复读取、batch child 收到结构化复用 flag；
- 不把“结果路由正确”报告成 ContextPlan 加载行为已验证。

## 演进回归

每次 production failure 或 owner correction：

1. 用失败时的最小 repository facts 建一个 regression fixture；
2. 断言正确 outcome 和最近的错误 sibling outcome；
3. 在可能时证明它对修复前版本失败；
4. 修正 canonical rule/runtime，而不是只放宽 oracle；
5. rule 经 `placeRule` 下沉后，保留相同的行为回归。

oracle 可以接受语义等价措辞，例如 `result_type_any` / `target_any`；但不能把安全上不同的
`NeedsHuman`、`HumanCheckpoint`、`Awaiting`、`Blocked` 合并为等价结果。

## Selection Checklist

提交前确认：

- fixture 数量与 shape/fragility 相称；
- 每个 fixture 只有一个 decision；
- 高风险 branch 有 nearest unsafe negative assertion；
- checkpoint 有 typed resume 正反例；
- `Awaiting` 有 run-id 正反例；
- tool-backed case 调用真实 runtime；
- cross-skill handoff 进入 canonical main entry；
- ContextPlan 只声明实际可观察的证据；
- 新事故/owner correction 在最近的确定性层获得回归。
