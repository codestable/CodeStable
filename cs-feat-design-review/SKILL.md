---
name: cs-feat-design-review
description: feature design 人工确认前的方案审查 gate。对照 {slug}-design.md、{slug}-checklist.yaml、相关 roadmap / requirement / architecture / compound / 代码事实做只读 review，产出 {slug}-design-review.md；按 Task agent 选择规则启动独立审查（Paseo subagent 优先，否则原生 Codex/Claude Task/Agent），主 agent 等待结果、事实核验并合并定级。触发：用户说"review 这个 design"、"feature design 人审前先独立审查"、"跑 cs-feat-design-review"、"方案审查"。
---

# cs-feat-design-review

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

本阶段是 feature design 交给用户人工确认前的方案审查 gate。它只读 design、checklist、相关文档和必要代码事实，只写 `{slug}-design-review.md`，不直接改 design/checklist、不替用户批准 design、不进入实现。

目标不是替用户做产品判断，而是确认这份 design 已经具备让用户有效 review 和让下游稳定执行的条件：需求边界可核对、名词层和编排层有代码事实支撑、steps 可独立验证、checks 能回到 design 证据、风险 / 基线 / 交付物 / 清洁度可被后续 implement、code review、QA 和 acceptance 消费。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md`。feature design 的具体结构以目标 `{slug}-design.md` / `{slug}-checklist.yaml` 和项目内共享口径为准。
> 报告语言：plan review / design-review 报告正文默认用**中文**（见 `.codestable/attention.md` 报告语言节）；frontmatter / yaml 字段不翻译。

---

## 输入

进入 review 前必须读取：

- `.codestable/attention.md`
- `.codestable/features/{feature}/{slug}-design.md`
- `.codestable/features/{feature}/{slug}-checklist.yaml`
- 同目录的 `{slug}-intent.md` / `{slug}-brainstorm.md`（如果存在）
- design frontmatter 指向的 requirement 文档
- design frontmatter 指向的 roadmap 主文档和 items.yaml（如果有 `roadmap` / `roadmap_item`）
- design 第 4 节指向的 architecture 文档
- 相关 compound 沉淀：用项目搜索工具按 feature 关键词检索 decision / learning / explore / trick
- design 中引用到的关键代码位置、接口、类型、组件、命令、配置
- 独立 Task agent reviewer 输出（如果本轮启用了 Paseo 或其他 reviewer）

没有代码引用时不强行扫全仓库；但 design 声称复用、修改、挂载或约束某个现有模块时，必须读对应代码或文档事实核验。

---

## 启动检查

1. design 存在，frontmatter `doc_type=feature-design`，`feature` 与目录一致，`status` 通常是 `draft`；复审已 approved 设计时要确认用户确实要求重新审查。
2. checklist 存在，`feature` 与目录一致，`steps` 非空，`checks` 非空；缺 checklist 时报告 `blocked`，回 `cs-feat-design` 生成 review candidate checklist。
3. checklist 的 `steps.status` 和 `checks.status` 在人审前都应是 `pending`；已有 `done/passed` 说明阶段混乱，报告 `blocked`。
4. 从 roadmap 起头时，roadmap item 必须能在 items.yaml 中找到，design 的 `roadmap_item` 与 feature slug 对齐。
5. 如果已有 `{slug}-design-review.md`：
   - `status: passed` 且 design/checklist 未变化：提示可进入用户整体 review。
   - `status: changes-requested` / `blocked`：读取旧 findings，确认是否复审。
   - design/checklist 已变化：重新 review，并在报告里记录轮次。

---

## 独立 Task agent reviewer 增强项

本阶段默认由当前 agent 做本地方案审查；独立 Task agent reviewer 是增强项，不是硬依赖。检测不到 Task agent、provider 未配置或用户明确要求快速完成时，可以继续本地 review，并在报告里记录 `Independent reviewer: local-only` / `skipped-by-user`。

但一旦本轮已经启动独立 Task agent reviewer，它就是本轮 review gate 的输入。主 agent 可以先做本地审查草稿，但不能在 reviewer 返回前定稿 `{slug}-design-review.md`、不能给出 `passed`、不能把 design 交给用户确认。reviewer 卡住、失败、权限阻塞或耗时过长时，只能把本轮标成 `blocked` / `independent-review-pending`，让用户决定继续等待、重试 reviewer，或明确降级为 local-only review。

**检测由主 agent 在运行时自检自己的工具**，按 `.codestable/reference/execution-conventions.md` 的 Task agent 选择规则启动独立 Task agent reviewer：Paseo subagent 优先，否则用当前宿主的原生 Codex/Claude Task/Agent。都没有则本地 review，记录 `local-only`，并写入 `approval-report.md` 请 owner 授权降级；不要伪装启动。不要无限轮询运行中的 agent；若已启动但未返回，停止在 review gate，记录 pending/blocked，等待通知或用户决定。

Task agent prompt 必须只给原始材料和边界，不透露本地 review 结论：

```text
你是 CodeStable feature design 的独立方案审查 agent。只读，不修改文件，不更新 design/checklist。

请读取：
- .codestable/attention.md
- {design_path}
- {checklist_path}
- 同目录 intent / brainstorm（如有）
- 相关 roadmap / requirement / architecture / compound 文档
- design 引用到的关键代码、接口、类型、组件、命令入口

按 cs-feat-design-review 的严重度语义输出：blocking / important / nit / suggestion / learning / praise / residual-risk。
重点审查：需求边界、术语冲突、名词层现状→变化、编排层流程、挂载点可卸载性、结构健康度、验收契约、steps 原子性、checks 来源、基线与验证命令、交付物、清洁度、roadmap 接口契约遵守情况。
每条 finding 必须有 design/checklist/doc/code 事实证据、影响、建议修复边界。
不要写 {slug}-design-review.md；只把审查结果回传给主 agent。
```

主 agent 仍是最终审查责任方：必须逐条核验 reviewer 的 finding，去重、定级、合并进 `{slug}-design-review.md`。未经本地事实核验的外部结论只能写 `residual-risk` 或忽略，不能直接升级成 `blocking`。

---

## 审查流程

### 1. 范围与事实

- 用 design 第 0/1 节确认术语、需求摘要、明确不做、复杂度档位、关键决策。
- 用第 2.1 / 2.2 节确认名词层和编排层是否都有"现状 → 变化"，且现状指向真实代码 / 文档。
- 用第 2.3 节确认挂载点是否按"删掉 feature 是否消失"收紧。
- 用第 2.4 节和 checklist steps 对齐推进策略、退出信号和验证动作。
- 用第 2.5 节确认结构健康度评估覆盖文件级 + 目录级，微重构只做"只搬不改行为"。
- 用第 3/4 节确认验收契约、架构回写预判、证据类型。
- 从 roadmap 起头时，额外核对 roadmap 第 4 节接口契约是硬约束，design 没有私自绕开。

### 2. 独立审查合并

- 记录主 agent 自检结果：`paseo` / `native-agent` / `local-only`。
- 没有启动独立 Task agent reviewer 时，记录原因，本地 review 可以定稿。
- 启动 Task agent 后，最终 verdict 必须等 reviewer 返回。
- reviewer 返回后逐条做本地事实核验；能用 design / checklist / 文档 / 代码证据支撑才合并。
- reviewer 失败、权限阻塞、超时或仍在运行时，不要默默降级；报告 `status: blocked`。

### 3. 方案审查

至少覆盖：

- 需求边界：用户目标、核心行为、成功标准、明确不做是否可核对。
- 术语与现状：关键术语是否与代码 / 架构 / 历史 feature 冲突；现状描述是否真实。
- 名词层：值对象、实体、接口、类型、组件 props/events 是否讲清变化。
- 编排层：主流程图、分支、错误语义、幂等、并发、可观测点是否能跑通。
- 挂载点：是否列了真实对外注册点，而不是内部改动文件清单。
- 结构健康度：微重构是否必要且边界安全；目录 convention 候选是否合理。
- 验收契约：正常 / 边界 / 错误路径是否覆盖，是否有证据类型。
- checklist：steps 是否独立可验证，exit_signal 是否 yes/no，checks 是否都能追溯到 design。
- 基线与验证：必跑命令、预检策略、基线红灯归因是否写清。
- 交付物与清洁度：acceptance 是否能从仓库事实核验；调试输出、TODO、死 import 等规则是否明确。

### 4. Feature Design Review Invariants 与证据分级

每轮 review 必须形成 Evidence Confidence Ledger。证据分级只描述依据来源，不计算质量分：

- `E` Embedded：design / checklist / roadmap item / 命令输出里直接可见。
- `C` Context：相关 req / arch / compound / 代码事实支撑。
- `H` Heuristic：工程经验或 reviewer 判断，缺少直接仓库证据。

核心 invariants：

- Acceptance Coverage Matrix 覆盖每个核心验收场景。
- 每个核心场景能追踪到 checklist step、证据类型和命令 / 动作。
- checklist steps 独立可验证，checks 能回到 design 来源。
- roadmap 起头的 design 没有绕开 roadmap 接口契约。
- DoD Contract 覆盖 Design / Implementation / Review / QA / Acceptance DoD、Validation Commands 和 Required Artifacts。
- checklist `dod.commands` 若存在，字段使用 `{id, command, core, failure_handling}`；design 表格只是人读投影。
- 核心检查若只有 `H` 证据，不能静默 `passed`；至少写入 residual risk，必要时列 important / blocking finding。

---

## 严重度

- `blocking`：必须先修。会导致 design 不能被用户有效 review、实现无稳定契约、roadmap 契约被绕开、steps/checks 无法执行、验收不可证伪、关键风险没有验证路径。
- `important`：应该修；若用户决定延后，必须在 design review 和用户 review 摘要中明确记录。
- `nit`：小的清晰度或一致性建议，不阻塞。
- `suggestion`：替代设计思路或补强建议，不要求本次采用。
- `learning`：知识性说明，不要求动作。
- `praise`：记录值得保留的设计做法；少量即可。
- `residual-risk`：review 无法完全消除的不确定性，需要用户 review、implementation、code review、QA 或 acceptance 重点复核。

不要把个人偏好的实现写法升级成 blocking。blocking 必须能用 design 契约、checklist、roadmap/req/arch、代码事实或可靠工程原则支撑。

---

## 报告模板

报告路径：`.codestable/features/{feature}/{slug}-design-review.md`。

```markdown
---
doc_type: feature-design-review
feature: {feature}
status: passed|changes-requested|blocked
reviewed: YYYY-MM-DD
round: 1
---

# {slug} feature design 审查报告

## 1. Scope And Inputs

- Design: {path}
- Checklist: {path}
- Intent / brainstorm: {path / none}
- Roadmap: {path / none}
- Related docs: {requirements / architecture / compound}
- Code facts checked: {paths / none}

### Independent Review

- Status: not-available|skipped-by-user|local-only|pending|completed|failed|blocked
- Detection: paseo|native-agent|local-only|skipped
- Provider / agent: {providers.audit / agent id / none}
- Raw output: {摘要 / 路径 / none}
- Merge policy: {已逐条核验 / 未启用原因 / pending 时不得定稿}
- Gate effect: {none | blocks final verdict until completed / user-approved downgrade}

## 2. Design Summary

- Goal: {摘要}
- Key contracts: {名词层 / 编排层摘要}
- Steps: {数量 + 风险热点}
- Checks: {数量 + 来源完整性}
- Baseline / validation: {摘要}

## 3. Findings

### blocking

- [ ] FDR-001 `{path#section|checklist.step|file:line}` {问题}
  - Evidence: {事实}
  - Impact: {为什么阻塞用户 review / implement}
  - Expected fix scope: {修复边界}

### important

- [ ] FDR-00N `{证据位置}` {问题}
  - Evidence: {事实}
  - Impact: {影响}

### nit

- [ ] FDR-00N `{证据位置}` {建议}

### suggestion

- [ ] FDR-00N {建议}

### learning

- {可复用设计经验或注意点}

### praise

- {值得保留的做法}

## 4. User Review Focus

- 用户需要重点拍板：{决策 / 假设 / 不做范围}
- implement 需要重点遵守：{契约 / steps / 验证}
- code review / QA / acceptance 需要重点复核：{风险 / 证据}

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass|warn|fail | E|C|H | {路径 / 事实 / 判断依据} | {none / 复核点} |
| DoD Contract | pass|warn|fail | E|C|H | {依据} | {复核点} |
| Steps and checks traceability | pass|warn|fail | E|C|H | {依据} | {复核点} |
| Roadmap contract compliance | pass|warn|fail | E|C|H | {依据} | {复核点} |
| Validation and artifacts | pass|warn|fail | E|C|H | {依据} | {复核点} |

Summary: E={n}, C={n}, H={n}, H-only core checks={列表或 none}。

## 6. Residual Risk

- {风险 + 下游如何处理；没有写 none}

## 7. Verdict

- Status: passed|changes-requested|blocked
- Next: 交给用户整体 review | 回 `cs-feat-design` 修订后重跑 `cs-feat-design-review` | 等独立 Task agent reviewer 完成 / 用户确认降级后重跑
```

没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。

---

## 退出条件

- [ ] 已读取 attention、design、checklist、相关 intent / brainstorm / roadmap / req / arch / compound。
- [ ] 已按 design 声明核验必要代码、接口、类型、组件或命令事实。
- [ ] 已确认 checklist 可解析，steps/checks 都可追溯。
- [ ] 已运行独立 Task agent reviewer 检测，或记录为什么跳过。
- [ ] 如果启动了独立 Task agent reviewer，已等到 completed 并逐条本地核验合并 / 驳回 findings；否则报告 `status: blocked`，没有进入用户 review。
- [ ] 已审查需求边界、术语、名词层、编排层、挂载点、结构健康度、验收契约、steps/checks、基线、交付物、清洁度。
- [ ] 已检查 Acceptance Coverage Matrix、Feature Design Review Invariants 和 Evidence Confidence Ledger。
- [ ] 核心检查 H-only 时没有静默 passed。
- [ ] 已写 `.codestable/features/{feature}/{slug}-design-review.md`。
- [ ] 有 blocking / 未处理 important 时指向 `cs-feat-design` 修订并重跑 review。
- [ ] 无 blocking 且 important 已处理或明确接受时，明确告诉用户下一步是 feature design 人工 review。

---

## 容易踩的坑

- 把 design review 做成文案润色，没审 steps/checks 是否能执行。
- 只读 design，不核对 checklist 来源。
- roadmap 起头时不检查接口契约，导致 feature 偷偷绕开 roadmap。
- 现状段没读代码就放过，implement 阶段才发现设计站不住。
- steps 出现"和 / 以及 / 同时"却不复查是否该拆。
- 启动独立 Task agent reviewer 后结果还没回来，就把本地 review 定稿为 passed。
- 外部 reviewer 的结论没经本地事实核验就照抄。
- review 报告没有落盘，导致用户 review 和后续实现没有可追溯输入。
