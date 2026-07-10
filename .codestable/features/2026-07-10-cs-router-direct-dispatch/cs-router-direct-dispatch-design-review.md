---
doc_type: feature-design-review
feature: 2026-07-10-cs-router-direct-dispatch
status: passed
reviewed: 2026-07-10
round: 3
---

# cs-router-direct-dispatch feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-design.md`
- Checklist: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-checklist.yaml`
- Intent / brainstorm: none；输入来自上一轮审查建议与用户“根据你的建议优化”
- Roadmap / requirement: none
- Related docs: skill entry simplification refactor design、execution/shared conventions、README/WORKFLOW/catalog 中英文镜像
- Code facts checked: root/brainstorm/audit skills、routing fixtures/scorer/prompt builder、相关 pytest

### Independent Review

- Status: completed
- Detection: paseo
- Provider / agent: `claude/claude-fable-5` / `24353714-0887-4a28-8b69-f104dfbbcfdf`
- Raw output: Fable 返回 4 important、3 nit、2 suggestion、2 residual-risk，无 blocking
- Merge policy: 已逐条对照 design、skill、tests 与 experiments 事实核验
- Gate effect: important 修订后必须启动新 Task agent 做 round 2，未通过前不得实现

## 2. Design Summary

- Goal: 明确行动请求由 `cs` 同轮转交目标主 skill；咨询/介绍不执行；歧义只问一个问题
- Key contracts: 入口模式先于目标分类、专用 workflow 优先、下游 gate 保持有效
- Steps: 4；风险热点在结果词汇、onboard 前置链和二级出口 checkpoint
- Checks: 16；覆盖 root、共享约定、docs、fixtures 和回归验证
- Baseline / validation: `pytest -q tests` 206 passed；裸 pytest 与 package check 有已知基线

## 3. Findings

### blocking

none

### important

- [x] FDR-001 `design §2.1` 结果构造子与 routing harness 固定词汇不对齐，Clarify 无对应 outcome。
  - Evidence: design 原定义 `Dispatch | Recommendation | Overview | NeedsHuman`；buildprompt 使用既有 result_type 枚举。
  - Impact: `cs-routing-001` 无法稳定机械判分。
  - Expected fix scope: 复用 RoutedTo/HumanCheckpoint/Completed/NeedsHuman。
- [x] FDR-002 `design §1.3 / scenario 8` 未定义 onboard 后原始行动诉求的去向。
  - Evidence: 原方案同时要求单一转交和 onboard 后继续工作。
  - Impact: 可能复活要求用户重新调用的死端，或绕过 onboard checkpoint。
  - Expected fix scope: 把 onboard 定义为串行前置 gate 例外。
- [x] FDR-003 `checklist S2` 未区分 brainstorm 待确认出口与 audit 已确认出口。
  - Evidence: brainstorm 硬性边界要求阶段间人工 checkpoint；audit 用户选择 finding 已构成确认。
  - Impact: 一律直转会打穿 brainstorm checkpoint，一律停下又保留多余调用。
  - Expected fix scope: 共享约定区分两种出口语义。
- [x] FDR-004 `execution-conventions.md` 模板与 runtime copy 缺静态一致性护栏。
  - Evidence:现有 copy 测试只覆盖 shared/agent/solution-depth conventions。
  - Impact:本 feature 的共享真相可能静默漂移。
  - Expected fix scope: 将 execution-conventions 加入既有 copy 测试列表。

### nit

- [x] FDR-005 定义删除 L0-L4 后的最小 route brief。
- [x] FDR-006 同步更新 `cs` frontmatter description，并保留 argument/default fallback 契约。
- [x] FDR-007 明确更新旧 router 场景断言与硬编码 helper。

### suggestion

- [x] FDR-008 冲突 fixtures 使用 `must_not_target`，并覆盖两个独立诉求的执行顺序。
- [x] FDR-009 用中英文正向/反向文案断言机械锁定 docs 投影。

### learning

- routing Spec 的结果构造子应优先复用评测 harness 的既有 result_type 词汇。

### praise

- 入口模式先于目标分类，正确隔离了“咨询误执行”风险。
- 明确请求不做全局扫描、由目标 skill 恢复仓库事实，能减少重复上下文成本。

## 4. User Review Focus

- 用户已确认：行动请求同轮开始目标 workflow，咨询请求只给建议。
- implement 重点遵守：onboard 串行前置、二级出口 checkpoint、原始请求保留。
- code review / QA 重点复核：真实 fixtures、文档死端措辞、runtime copy 一致性。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | warn | E | 场景完整，但原结果词汇不可机械判分 | 修 FDR-001 |
| DoD Contract | warn | C | 命令存在；裸 pytest/package 有基线 | 校正核心命令 |
| Steps and checks traceability | pass | E | 4 steps 与 checks 均可回到 design | none |
| Roadmap contract compliance | n/a | E | 非 roadmap feature | none |
| Module interface design | pass | C | 复用 installed skill seam，不加 adapter | final review 复核 |
| Validation and artifacts | warn | C | runtime check 存在，copy test 漏 execution | 修 FDR-004 |

Summary: E=3, C=3, H=0, H-only core checks=none。

## 6. Residual Risk

- Execute / Advise 边界仍是语义判断，fixtures 只能抽样；由目标 skill checkpoint 继续兜底。
- 长会话压缩后 preflight 可能需按 execution conventions 重新确认。

## 7. Verdict

- Status: changes-requested
- Next: 修订 design/checklist 后启动新的 Claude Fable Task agent 做 round 3 design review

## 8. Round 2 Addendum

### Independent Review

- Status: completed
- Detection: paseo
- Provider / agent: `claude/claude-fable-5` / `eb9797e9-68e5-4e92-a301-876920356d47`
- Result: round 1 的 FDR-001/002/004 已关闭；FDR-003 部分关闭；新增 2 important、3 nit、2 suggestion

### Important

- [x] FDR-R2-001 brainstorm case 1/2/3/4 未全部归类，硬性边界 6 与确认后同轮加载字面冲突。
  - Fix scope: case 1/2/4 定为待确认，case 3 定为已确认；同步改写硬性边界。
- [x] FDR-R2-002 system-overview 模板/runtime copy 与 execution-conventions 一样需要逐字一致性测试。
  - Fix scope: 加入既有 runtime reference copy 测试列表。

### Adopted Nit / Suggestion

- route brief 明确只用于 Execute / Advise。
- frontmatter description 给出窄触发面，root 新增 contracts。
- 删除 L0-L4 时明确 approval 指针由下游权威保留。
- fixtures 显式使用 `must_not_target` 锁冲突路线。

## 9. Round 3 Final Review

### Independent Review

- Status: completed
- Detection: paseo
- Provider / agent: `claude/claude-fable-5` / `4ed01a11-d37e-4608-b0cb-04c24e290027`
- Result: 无 blocking、无 important；round 1/2 findings 均已关闭，verdict 为 `approve`

### Adopted Nit

- `must_not_target` 只锁禁止 target；咨询与双诉求用 `expect.result_type` 锁 outcome。
- brainstorm 硬性边界明确 case 3 的 ready 拆解表述本身视为确认。
- 实现时同步检查 brainstorm 各 case 退出、硬性边界与常见错误中的旧触发口径。

### Residual Risk

- Execute / Advise 仍是语义判断，由冲突 fixtures 与目标 skill checkpoint 共同兜底。
- onboard 串行前置链用前置跳、恢复跳分别取证，多轮连续性仍依赖同一会话上下文。

### Final Verdict

- Status: passed
- Next: 按 approved checklist 进入 implementation
