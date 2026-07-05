# Feature QA Protocol

本阶段是 review 通过后、acceptance 前的 QA gate。它只读代码和产物、运行验证命令 / 浏览器 / API / 手工检查，并写 `{slug}-qa.md`。默认不改代码、不改 checklist、不改 design；发现失败后回到 `cs-feat` implementation 阶段的 qa-fix。

QA 的目标不是再做一遍 code review，也不是最终归档验收报告。它回答一个问题：在当前工作区里，design 承诺的关键行为是否有足够的运行证据，review 指出的测试焦点和 residual risk 是否被实际覆盖。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。

---

## 独立 QA Task agent（可选）

QA 可以按 `.codestable/reference/agent-conventions.md` 的 Task agent 选择规则，启用独立 runner 来执行浏览器、API、CLI、集成测试或环境复核，尤其是高风险功能、外部集成、真实浏览器路径和 goal 模式中的核心验收路径。但它是辅助执行者，不是 QA owner：

- 主 agent 负责建立 Verification Matrix、决定哪些证据阻塞、核验 runner 输出，并写 `{slug}-qa.md` 的最终 verdict。
- runner 默认只读代码和产物，只运行验证；如需改测试或配置，必须退回 `cs-feat` implementation 阶段 qa-fix。
- runner 输出必须被写入 QA 报告的证据来源；未经主 agent 本地核验的结论只能作为 `residual-risk` 或待复核项。
- runner 输出被消费并写入 QA 报告后，按 Task agent 生命周期关闭该 runner；容量失败只在失败后清理最老已完成 agent 并重试一次。
- 普通低风险非功能性 feature 不强制独立 runner，避免把 QA 成本固定放大。

---

## 输入

进入 QA 前必须读取：

- `.codestable/attention.md`
- `{slug}-design.md`
- `{slug}-checklist.yaml`
- `{slug}-review.md`
- goal / gate 模式下的 `{slug}-evidence-pack.md`、`{slug}-gate-results.json`、`{slug}-dod-results.json`
- 实现完成汇报 / review-fix 汇报（如有）
- `git status --short`
- `git diff`（有 staged diff 时也读 `git diff --cached`）
- design 里的必跑验证命令 / 基线风险 / 验收场景 / 证据类型 / 清洁度规则
- review 报告第 4 节 Test And QA Focus 和第 5 节 Residual Risk
- 项目测试入口：README、package scripts、Makefile、CI 配置、历史 acceptance / qa 报告里与本 feature 相关的命令
- feature 性质判断：功能性 / 非功能性，以及哪些场景是核心验收路径

如果工作区有 feature 外的既有 dirty 文件，记录 baseline/无关变更；QA 结论只覆盖本 feature 可归因的改动。无法区分归因时写 `blocked` 或 `residual-risk`，不要假装通过。

---

## Feature 性质与证据硬门

QA 先判定 feature 性质，再决定必须拿到什么证据。这个判定写进 QA 报告，acceptance 会复核。

### 功能性 feature

满足任一条件就按功能性处理：

- 改变用户可见行为、UI、API、CLI、后台任务、权限、持久化、集成、运行时路由或错误语义。
- roadmap / design 的成功标准里出现“用户能...”“系统会...”“真实请求 / turn / smoke / e2e / browser / API”等运行行为。
- review 把某条验证标成必须覆盖，且它对应实际运行路径。

功能性 feature 的核心路径不能降级成 residual-risk：

- design 第 3 节关键场景、checklist `checks`、roadmap success criterion、review Test And QA Focus 中属于核心功能路径的项，必须有实际运行证据：unit / integration / e2e / browser / API / CLI / manual smoke 任选合适组合，但证据必须能观察到行为。
- 只跑 typecheck / lint / diff review，不能证明核心功能路径通过。
- 外部凭证、服务、设备、网络或成本导致核心路径无法运行时，结论是 `blocked`；如果实现明显缺测试或行为失败，结论是 `failed`。
- 只有 design 在实现前已明确把某条路径定义为“条件性非阻塞”（例如 CI 无 auth 时只验证 unavailable path），且 QA 已验证替代路径和 skip reason，才允许把这条写成 residual-risk。QA 现场不能临时把原本的核心验收路径改成非阻塞。

### 非功能性 feature

以下类型默认按非功能性处理，除非它同时改变运行行为：

- 文档、architecture / roadmap / requirement / learning 回写。
- 纯重构、命名整理、目录迁移、死代码清理，且声明行为不变。
- 测试补强、类型补强、lint/build 配置、脚本整理、生成物同步。
- 内部设计文档、协议说明、agent skill 文案更新。

非功能性 feature 不强制 e2e / browser / API / 手工真实链路；它可以用静态检查、diff 复核、文档一致性、类型检查、构建、目标测试、快照或 schema 校验通过。QA 报告必须写明“不需要端到端运行验证”的理由，以及本 feature 实际采用的替代证据。

如果非功能性 feature 触碰了生产路由、用户可见文案、权限、安全边界、数据迁移或外部集成，即使目标是“重构/整理”，相关触碰点仍按功能性核心路径验证。

## 启动检查

1. `{slug}-design.md` 存在且 `status=approved`。
2. `{slug}-checklist.yaml` 存在，`steps` 全 `done`，`checks` 仍未由 acceptance 全部通过。
3. `{slug}-review.md` 存在，frontmatter `doc_type=feature-review`、`status=passed`，无 unresolved `blocking` findings。
4. goal / gate 模式下，evidence pack、gate results、DoD results 必须存在；gate warnings 和 Residual Risks 纳入 QA matrix。
5. 如果 review 报告不是基于当前 diff：先回 `cs-code-review` 复审。qa-fix 或其他代码改动会让旧 review 过期。
6. 如果已有 `{slug}-qa.md`：
   - `status=passed` 且 diff 未变化：提示可进入 `cs-feat` acceptance 阶段。
   - `status=failed` / `blocked`：读取旧失败项，确认是否处于 qa-fix 后的复测。
   - diff 已变化：重新 QA，并在报告里记录轮次。

---

## QA 流程

### 1. 建验证矩阵

从 design 第 3 节关键场景、design 必跑命令、review Test And QA Focus、review residual risk、evidence pack 的 Validation Commands / DoD Results / Residual Risks 汇总 QA 矩阵：

- Feature type：functional / non-functional / mixed。
- 核心性：core-functional / supporting / non-functional。
- 场景：输入 / 触发 → 期望可观察结果。
- 证据类型：unit / function / integration / e2e / browser / API / manual / typecheck / diff。
- 命令或动作：具体命令、页面路径、API 请求、手工步骤。
- 失败判据：什么结果算 fail，不写"看起来正常"。
- 归因：本 feature / 既有基线 / 环境不可用 / 无法判断。

优先使用项目已有测试入口和既有工具，不为了 QA 临时引入新测试框架。需要新增测试代码时，QA 不直接写；把它记为 failed item，回 `cs-feat` implementation 阶段 qa-fix。

### 2. 运行验证

按从便宜到昂贵、从自动到手工的顺序运行：

1. 基线相关命令：typecheck / lint / build / targeted unit 或项目等价命令。
2. 与 feature 直接相关的 unit / function / integration / e2e 测试。
3. review 与 evidence pack 指出的重点验证、gate warnings 和 residual risk。
4. 功能性前端 / 用户可见改动：浏览器验证、截图或明确手工路径；只跑 typecheck 不算 QA 通过。
5. 功能性 API / 后端 / 运行时能力：真实请求、集成测试或可复现的命令行调用。
6. 非功能性改动：静态检查、diff 复核、文档一致性、schema/快照/类型/构建/目标测试，并记录为什么无需端到端运行。
7. 清洁度复核：debug 输出、临时 TODO/FIXME、注释掉代码、无用 import、方案外文件。

每条证据必须记录命令、退出码或观察结果。命令不可运行时写具体原因：缺依赖、服务不可启动、外部凭证缺失、环境限制、成本过高。不可运行不是自动通过。

### 3. 判定

- `passed`：所有 blocking QA items 通过；功能性核心路径都有运行证据；非功能性 feature 有充分替代证据和“不需要端到端运行”的理由；不可运行项只剩非核心 residual risk。
- `failed`：关键场景失败、必跑命令失败且归因本 feature、review 重点未覆盖、测试缺口会影响验收可信度、功能性前端未做浏览器验证、功能性 API / 运行时路径没有实际调用证据。
- `blocked`：输入缺失、review 未通过、环境不可用到无法判断核心行为、dirty diff 归因不清。

QA failed 时不要直接修代码。输出报告后进入 `cs-feat` implementation 阶段 qa-fix；qa-fix 修完必须先重跑 `cs-code-review`，再重跑 `cs-feat` QA 阶段。

`residual-risk` 只能承载非核心风险、明确延期项或非功能性无法完全复核的边界。它不能承载“核心功能路径没跑过”“真实用户路径没验证”“必跑命令没执行”这类验收缺口。

---

## 报告模板

报告路径：`.codestable/features/{feature}/{slug}-qa.md`。

```markdown
---
doc_type: feature-qa
feature: YYYY-MM-DD-slug
status: passed|failed|blocked
tested: YYYY-MM-DD
round: 1
---

# {slug} QA 报告

## 1. Scope And Inputs

- Design: {path}
- Checklist: {path}
- Review: {path}
- Evidence pack: {path / none}
- Gate results: {path / none}
- DoD results: {path / none}
- Diff basis: {git status / git diff 摘要}
- Baseline dirty files: {none / 列表 + 归因}
- Feature type: functional|non-functional|mixed
- Core evidence gate: {功能性核心路径列表；非功能性写不需要端到端运行的理由}

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design S1 | core-functional/supporting/non-functional | {描述} | unit/integration/e2e/browser/API/manual/typecheck/diff | `{命令}` | {期望} | pass/fail/blocked |

## 3. Command Results

- `{命令}` → exit {code}：{摘要}
- 未运行：{命令} → {具体原因 + 是否阻塞}

## 4. Scenario Results

- [ ] QA-001 {场景}：pass/fail/blocked
  - Evidence: {输出 / 截图 / 请求响应 / 手工路径}
  - Notes: {归因 / 风险}

## 5. Findings

### failed

- [ ] QA-001 {失败项}
  - Evidence: {证据}
  - Impact: {为什么影响验收}
  - Expected fix scope: {只描述失败边界，不替实现写方案}

### blocked

- [ ] QA-00N {阻塞项}

### residual-risk

- {无法完全验证但不阻塞的风险；没有写 none}
- 不允许出现：功能性核心路径未运行、真实用户/API/运行时路径未验证、必跑命令未执行。

## 6. Cleanliness

- Debug output: pass/fail
- Temporary TODO/FIXME/XXX: pass/fail
- Commented-out code: pass/fail
- Unused imports / dead code from this feature: pass/fail
- Out-of-scope files: pass/fail

## 7. Verdict

- Status: passed|failed|blocked
- Next: `cs-feat` acceptance 阶段 | `cs-feat` implementation 阶段 qa-fix -> `cs-code-review` -> `cs-feat` QA 阶段 | 补齐环境后重跑 `cs-feat` QA 阶段
```

没有某类 finding 时写 `none`，不要删除章节；复测要能对比。

---

## qa-fix 衔接

如果 QA `failed`：

1. 报告 `status: failed`。
2. 告诉用户下一步进入 `cs-feat` implementation 阶段的 qa-fix 模式。
3. qa-fix 只修 QA failed / blocked items，不处理顺手发现，不扩大 feature 范围。
4. qa-fix 修完会改变 diff，必须重跑 `cs-code-review`；review passed 后再重跑 `cs-feat` QA 阶段。
5. QA passed 后才能进入 `cs-feat` acceptance 阶段。

如果 QA `blocked`：

- 先补环境 / 输入 / review 状态；不把 blocked 写成通过。

如果 QA `passed`：

- 告诉用户下一步是 `cs-feat` acceptance 阶段。

---

## 退出条件

- [ ] 已读取 attention、design、checklist、review、实现证据、git status、git diff。
- [ ] 已确认 review passed 且基于当前 diff。
- [ ] 已判定 feature type，并写明功能性核心路径或非功能性替代证据理由。
- [ ] 已建立 verification matrix，覆盖 design 关键场景、必跑命令、review Test And QA Focus、review residual risk、evidence pack commands / residual risks，并标出每项核心性。
- [ ] 已运行可运行的验证命令 / 浏览器 / API / 手工检查，并记录结果。
- [ ] 功能性核心路径都有实际运行证据；缺失则 QA 为 failed / blocked，不能写 passed。
- [ ] 非功能性 feature 如未做 e2e / browser / API，已写明为什么不需要，以及采用了哪些替代证据。
- [ ] 未运行项都有具体原因和阻塞判断。
- [ ] 已完成清洁度复核。
- [ ] 已写 `.codestable/features/{feature}/{slug}-qa.md`。
- [ ] failed / blocked 时没有进入 acceptance，而是指向 qa-fix 或补环境。
- [ ] passed 时明确告诉用户下一步 `cs-feat` acceptance 阶段。

---

## 容易踩的坑

- 把 QA 写成第二次 code review，不运行任何证据。
- 只跑 typecheck 就宣称前端用户路径通过。
- 把功能性核心路径没跑过写成 residual-risk，然后仍然 passed。
- 对文档 / 架构 / 测试补强类非功能性 feature 机械要求 e2e，而不是用更合适的静态 / 一致性 / 目标测试证据。
- 命令失败但归因不清就写 passed。
- QA 阶段直接修代码，绕过 qa-fix / review 复审。
- qa-fix 后跳过 review，直接重跑 QA 或进入 acceptance。
- 不记录未运行原因，导致 acceptance 无法判断剩余风险。
