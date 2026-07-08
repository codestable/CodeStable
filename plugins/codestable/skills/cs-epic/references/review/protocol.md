# Epic Review Protocol

本阶段是 roadmap 交给用户人工确认前的规划审查 gate。它只读 roadmap、items、相关文档和必要代码事实，只写 `{slug}-roadmap-review.md`，不直接改 roadmap、不替用户批准 roadmap、不推进 feature design。

目标不是追求"规划看起来完整"，而是确认这份 roadmap 已经具备让用户有效 review 的条件：目标可证伪、范围边界清楚、模块拆分与接口契约可执行、子 feature 可独立验证、依赖 DAG 合理、风险和验证策略提前暴露。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md`。roadmap 的具体结构以目标 `{slug}-roadmap.md` / `{slug}-items.yaml` 和项目内共享口径为准。
> 报告语言：roadmap-review 报告正文必须按 `.codestable/attention.md` 用**中文**；若草稿用了英文，落盘前先改写为中文。frontmatter / yaml 字段不翻译。

---

## 输入

进入 review 前必须读取：

- `.codestable/attention.md`
- `.codestable/roadmap/{slug}/{slug}-roadmap.md`
- `.codestable/roadmap/{slug}/{slug}-items.yaml`
- roadmap 目录下相关 `drafts/` 材料（只读与本次候选直接相关的）
- roadmap frontmatter 指向的 requirement / architecture 文档
- roadmap 第 7 节观察项提到的相关文档
- 相关 compound 沉淀：用项目搜索工具按大需求关键词检索 decision / learning / explore / trick
- items.yaml 中已存在 `feature` 字段的 feature design / acceptance（update 模式或复审时）
- roadmap 中接口契约或模块拆分引用到的关键代码位置
- 独立 Task agent reviewer 输出（如果本轮已启动）

没有代码引用时不强行扫全仓库；但 roadmap 声称复用现有模块、接口、命令、配置或数据结构时，必须读对应代码或文档事实核验。

---

## 启动检查

1. roadmap 主文档存在，frontmatter `doc_type=roadmap`，`slug` 与目录一致，`status` 是 `draft|active|paused|completed` 之一。
2. items.yaml 存在，`roadmap` 与 slug 一致，`items` 非空。
3. items.yaml 每条有 `slug` / `description` / `depends_on` / `status` / `feature` / `minimal_loop`。
4. 依赖图能解析；有循环、自指、未知依赖时直接列 blocking。
5. 如果已有 `{slug}-roadmap-review.md`：
   - `status: passed` 且 roadmap/items 未变化：提示可进入用户 review。
   - `status: changes-requested` / `blocked`：读取旧 findings，确认是否复审。
   - roadmap/items 已变化：重新 review，并在报告里记录轮次。

---

## 独立 Task agent reviewer gate

本阶段必须优先启动独立 Task agent reviewer；本规则对**每一轮 review 都成立**——设计/规划修订后的 round 2+ 重审不得以主 agent 本地重审代替独立审查；当前 agent 的本地审查只能作为合并与事实核验，不能替代独立审查。只有运行时确实没有 Task agent 能力、provider 不可用且无法配置，或用户在看到降级风险后明确授权，才允许 `local-only` / `skipped-by-user`。批量 roadmap、赶时间、主 agent 自认为风险低，都不是降级理由；需要授权降级时，先按 `.codestable/reference/approval-conventions.md` 写 `approval-report.md`，再让用户选择。

一旦本轮应该启动或已经启动独立 Task agent reviewer，它就是本轮 review gate 的输入。主 agent 可以先做本地审查草稿，但不能在 reviewer 返回前定稿 `{slug}-roadmap-review.md`、不能给出 `passed`、不能把 roadmap 交给用户确认。reviewer 卡住、失败、权限阻塞或耗时过长时，只能把本轮标成 `blocked` / `independent-review-pending`，让用户决定继续等待、重试 reviewer，或明确降级为 local-only review。

**检测由主 agent 在运行时自检自己的工具**，不靠脚本猜环境——主 agent 最清楚自己手上有哪些工具。按 Task agent 选择规则启动独立 Task agent reviewer（优先 Paseo subagent，否则当前宿主原生 Codex/Claude Task/Agent）：

1. **有 `mcp__paseo__create_agent` 工具**：必须优先用 Paseo subagent 做只读独立审查（首选：能换 provider，做到真正异构审查）。启动前先加载 / 读取 `paseo` skill 的当前说明，并遵守它的规则：读取 `~/.paseo/orchestration-preferences.json`，使用 `providers.audit`，不要硬编码 Claude 或 Codex。不要无限轮询运行中的 agent；如果 reviewer 已启动但结果未返回，停止在 review gate，记录 pending/blocked，等待通知或用户决定。
2. **否则有当前宿主原生 Codex/Claude Task/Agent 工具**：用原生 Task agent 做独立上下文审查。如属同类 agent，在报告里记录降级和残余风险。
3. **两者都没有**：本地 review 只能在记录 `local-only` 且获得必要授权后定稿；没有授权时报告 `blocked`，不要伪装启动。

独立 Task agent reviewer prompt 必须只给原始材料和边界，不透露本地 review 结论：

```text
你是 CodeStable roadmap 的独立规划审查 agent。只读，不修改文件，不更新 roadmap/items。

请读取：
- .codestable/attention.md
- {roadmap_path}
- {items_path}
- roadmap frontmatter 指向的 requirement / architecture 文档
- roadmap 相关 compound / draft 材料
- roadmap 引用到的关键代码或命令入口

按 epic review 的严重度语义输出：blocking / important / nit / suggestion / learning / praise / residual-risk。
重点审查：目标完成信号、范围与明确不做、模块拆分、interface depth / seam placement / adapter、接口契约可执行性、子 feature 原子性、依赖 DAG、最小闭环、验证策略、风险缓解、知识回写点、用户是否能据此有效拍板。
每条 finding 必须有 roadmap/items/doc/code 事实证据、影响、建议修复边界。
不要写 {slug}-roadmap-review.md；只把审查结果回传给主 agent。
```

主 agent 仍是最终审查责任方：必须逐条核验独立 Task agent reviewer 的 finding，去重、定级、合并进 `{slug}-roadmap-review.md`。未经本地事实核验的外部结论只能写 `residual-risk` 或忽略，不能直接升级成 `blocking`。

---

## 审查流程

### 1. 范围与事实

- 用 roadmap 第 1/2 节确认目标、覆盖范围、明确不做、关键假设。
- 用第 3/4 节确认模块拆分和接口契约是否足够支撑多个 feature 共用。
- 用第 5 节和 items.yaml 对齐所有子 feature：slug、描述、所属模块、依赖、状态、feature 绑定、minimal_loop。
- 用相关 req / arch / compound 判断有没有冲突、重复规划或遗漏约束。
- 用代码事实核验 roadmap 对现有模块、命令、接口、配置、数据结构的描述。

### 2. 独立审查合并

- 记录主 agent 自检结果：`paseo` / `native-agent` / `local-only`。
- 没有启动独立 Task agent reviewer 时，记录确无能力 / provider 不可用 / 用户授权降级；未满足这些条件时不得定稿 `passed`。
- 启动 Paseo subagent / 原生 Task agent 后，最终 verdict 必须等 reviewer 返回。
- reviewer 返回后逐条做本地事实核验；能用文档 / 代码 / items 证据支撑才合并。
- reviewer 结果合并进 `{slug}-roadmap-review.md` 后，按 Task agent 生命周期关闭该 reviewer。
- reviewer 失败、权限阻塞、超时或仍在运行时，不要默默降级；报告 `status: blocked`。

### 3. 规划审查

至少覆盖：

- 目标完成信号：是否能观察、能验收、能判定完成 / 未完成。
- 范围与明确不做：是否具体，能否防止后续 feature 偷偷扩范围。
- 模块拆分：职责是否清楚，是否有重复模块、万能模块、遗漏模块。
- Module/interface 设计：是否制造 pass-through module；跨模块 interface 是否 deep；seam / adapter 是否真实需要；dependency strategy 是否支撑后续测试。
- 接口契约：是否写到函数签名 / 数据结构 / 协议字段 / 错误码级别；无跨模块接口时是否明确写明。
- 子 feature 原子性：每条能否独立 design / implement / review / QA / accept；描述是否可证伪。
- 依赖 DAG：是否无环，依赖理由是否具体，最弱依赖是否先验证。
- 最小闭环：第一条或最小路径做完后是否能端到端演示。
- 验证与基线：是否识别 build / typecheck / lint / test / e2e / 手工验证入口；基线不稳时是否安排 safety net。
- 风险与恢复：Top 风险、外部依赖、迁移 / 权限 / 安全 / 回滚是否提前暴露。
- 交付物与知识回写：后续 acceptance 是否能从仓库事实核验产物；稳定约定 / 坑点是否有沉淀候选。

### 4. Roadmap Review Invariants 与证据分级

每轮 review 必须形成 Evidence Confidence Ledger。证据分级只描述依据来源，不计算质量分：

- `E` Embedded：roadmap / items.yaml / checklist / 命令输出里直接可见。
- `C` Context：相关 req / arch / compound / 代码事实支撑。
- `H` Heuristic：工程经验或 reviewer 判断，缺少直接仓库证据。

核心 invariants：

- Granularity Gate 能解释为什么进入 roadmap，而不是 single feature / brainstorm。
- Goal Coverage Matrix 中每个核心完成信号都有 item、验证入口和 evidence type。
- items.yaml 仍是 DAG，且最小闭环可独立验收。
- 接口契约可被 feature-design 当硬约束。
- 跨模块 interface 有 depth / seam / dependency strategy 依据；无跨模块接口时明确 not-applicable。
- 核心检查若只有 `H` 证据，不能静默 `passed`；至少写入 residual risk，必要时列 important / blocking finding。

---

## 严重度

- `blocking`：必须先修。会导致用户无法有效 review、feature 不能独立执行、接口契约不可用、依赖循环、明显违反 req / arch、关键风险未覆盖、验收不可证伪。
- `important`：应该修；若用户决定延后，必须在 roadmap review 和用户 review 摘要中明确记录。
- `nit`：小的清晰度或一致性建议，不阻塞。
- `suggestion`：替代拆法或补强思路，不要求本次采用。
- `learning`：知识性说明，不要求动作。
- `praise`：记录值得保留的规划做法；少量即可。
- `residual-risk`：review 无法完全消除的不确定性，需要用户 review 或后续 feature-design 重点复核。

不要把个人偏好的拆法升级成 blocking。blocking 必须能用 roadmap 契约、items 事实、相关文档、代码事实或可靠工程原则支撑。

---

## 报告模板

报告路径：`.codestable/roadmap/{slug}/{slug}-roadmap-review.md`。

```markdown
---
doc_type: roadmap-review
roadmap: {slug}
status: passed|changes-requested|blocked
reviewed: YYYY-MM-DD
round: 1
---

# {slug} roadmap 审查报告

## 1. Scope And Inputs

- Roadmap: {path}
- Items: {path}
- Related docs: {requirements / architecture / compound / drafts}
- Code facts checked: {paths / none}

### Independent Review

- Status: not-available|skipped-by-user|local-only|pending|completed|failed|blocked
- Detection: paseo|native-agent|local-only|skipped
- Provider / agent: {providers.audit / agent id / none}
- Raw output: {摘要 / 路径 / none}
- Merge policy: {已逐条核验 / 未启用原因 / pending 时不得定稿}
- Gate effect: {none | blocks final verdict until completed / user-approved downgrade}

## 2. Roadmap Summary

- Goal completion signal: {摘要}
- Module split: {摘要}
- Interface contracts: {摘要}
- Items: {数量 + minimal loop + 风险热点}
- Dependency shape: {DAG / 问题}

## 3. Findings

### blocking

- [ ] RMR-001 `{path#section|items.slug|file:line}` {问题}
  - Evidence: {事实}
  - Impact: {为什么阻塞用户 review / 后续 feature}
  - Expected fix scope: {修复边界}

### important

- [ ] RMR-00N `{证据位置}` {问题}
  - Evidence: {事实}
  - Impact: {影响}

### nit

- [ ] RMR-00N `{证据位置}` {建议}

### suggestion

- [ ] RMR-00N {建议}

### learning

- {可复用规划经验或注意点}

### praise

- {值得保留的做法}

## 4. User Review Focus

- 用户需要重点拍板：{决策 / 假设 / 优先级}
- 后续 feature-design 需要重点复核：{接口 / 风险 / 验证}
- 不能靠 roadmap review 完全确认的点：{列表}

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass|warn|fail | E|C|H | {路径 / 事实 / 判断依据} | {none / 复核点} |
| Goal Coverage Matrix | pass|warn|fail | E|C|H | {依据} | {复核点} |
| DAG and minimal loop | pass|warn|fail | E|C|H | {依据} | {复核点} |
| Interface contract usability | pass|warn|fail | E|C|H | {依据} | {复核点} |
| Module interface depth | pass|warn|fail|n/a | E|C|H | {依据} | {复核点} |

Summary: E={n}, C={n}, H={n}, H-only core checks={列表或 none}。

## 6. Residual Risk

- {风险 + 用户 review / feature-design 如何处理；没有写 none}

## 7. Verdict

- Status: passed|changes-requested|blocked
- Next: 交给用户 review | 回 `cs-epic` planning 阶段 修订后重跑 `cs-epic` review 阶段 | 等独立 Task agent reviewer 完成 / 用户确认降级后重跑
```

没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。

---

## 退出条件

- [ ] 已读取 attention、roadmap、items、相关 req / arch / compound / drafts。
- [ ] 已按 roadmap 声明核验必要代码或命令事实。
- [ ] 已确认 items.yaml 可解析，依赖图无未知节点；有问题已列 finding。
- [ ] 已按 Task agent 选择规则启动独立 reviewer；若未启动，已记录确无能力 / provider 不可用 / 用户授权降级。
- [ ] 如果启动了独立 Task agent reviewer，已等到 completed 并逐条本地核验合并 / 驳回 findings；否则报告 `status: blocked`，没有进入用户 review。
- [ ] 已审查目标、范围、模块、接口、feature 原子性、依赖、最小闭环、验证、风险、知识回写。
- [ ] 已检查 Granularity Gate、Goal Coverage Matrix 和 Roadmap Review Invariants。
- [ ] 已写 Evidence Confidence Ledger；核心检查 H-only 时没有静默 passed。
- [ ] 已写 `.codestable/roadmap/{slug}/{slug}-roadmap-review.md`。
- [ ] 有 blocking / 未处理 important 时指向 `cs-epic` planning 阶段 修订并重跑 review。
- [ ] 无 blocking 且 important 已处理或明确接受时，明确告诉用户下一步是 roadmap 人工 review。

---

## 容易踩的坑

- 把 roadmap review 做成语病检查，没审接口契约和依赖图。
- 只读主文档，不核对 items.yaml。
- 不读 requirement / architecture，导致规划和现状冲突没发现。
- 接口契约写着"待定"也放过，后续每条 feature 各自发明接口。
- 子 feature 里塞多个可独立验收的交付，却只当一条。
- 把批量 roadmap 或赶时间当成 local-only 降级理由。
- 启动独立 Task agent reviewer 后结果还没回来，就把本地 review 定稿为 passed。
- 外部 reviewer 的结论没经本地事实核验就照抄。
- review 报告没有落盘，导致用户 review 和后续 design 没有可追溯输入。
