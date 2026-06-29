---
name: cs-code-review
description: 横切代码审查 gate——任何流程（feature / issue / refactor / fastforward）实现完成后、commit 前，对照对应 spec 产物和当前 git diff 做独立只读 code review，产出 {slug}-review.md；按 Task agent 选择规则启动独立审查（Paseo subagent 优先，否则原生 Codex/Claude Task/Agent），最终由本 skill 合并定级。有 blocking findings 时回到对应实现技能修复，通过后交回上游收尾（feature 进 cs-feat-qa，其余进各自验收/提交）。触发：用户说"做代码审查"、"code review"、"review 这次改动"、"合并前审一下"、"跑 cs-code-review"。
---

# cs-code-review

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

本技能是**横切代码审查 gate**：任何流程实现完成后、commit / QA / 验收前，对当前改动做独立只读 review。它只读代码和产物，只写 `{slug}-review.md`，不直接修代码、不更新 checklist、不改 spec、不替代 QA 或 acceptance。

审查目标不是追求完美代码，而是确认本次改动没有降低系统代码健康，并且确实朝对应 spec（design / fix-note / refactor-design / 用户确认范围）的目标前进。能自动格式化或 lint 的问题不要手工阻塞；会影响正确性、维护性、安全、性能、可测试性、需求满足或后续验收可信度的问题必须指出。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。
> 报告语言：code review 报告正文默认用**中文**（见 `.codestable/attention.md` 报告语言节）；frontmatter / yaml 字段不翻译。

## 进入来源（横切）

| 来源 | 进入点 | spec 产物 | 通过后去向 |
|---|---|---|---|
| `cs-feat-impl`（标准 feature） | impl 完成、QA 前 | design + checklist | `cs-feat-qa` |
| `cs-feat-ff`（feature 快速通道） | ff-note 落盘、commit 前 | ff-note + 用户原始需求 | 收尾提交 |
| `cs-issue-fix` | fix-note 落盘、commit 前 | report + analysis + fix-note | 收尾提交 |
| `cs-refactor` | apply-notes 完成、commit 前 | scan + refactor-design + checklist | 收尾提交 |
| `cs-refactor-ff` | 自证通过、commit 前 | 用户确认的重构范围 + 验证命令 | 收尾提交 |
| ad-hoc / pre-merge | 用户要求 | 用户指定范围 / git range | 给结论 |

**不是 `cs-audit`**：audit 主动扫一片代码找潜在问题；code review 只审当前变更范围。

---

## 输入

进入 review 前必须读取：

- `.codestable/attention.md`
- 来源的 spec 产物（feature 看 `{slug}-design.md` + `{slug}-checklist.yaml`；issue 看 report+analysis+fix-note；refactor 看 scan+refactor-design+checklist；ff / ad-hoc 看用户确认范围）
- 实现完成汇报 / 最近实现记录（如果在对话里，按对话事实引用；如果已落文件，读文件）
- `git status --short`
- `git diff`（有 staged diff 时也读 `git diff --cached`）
- diff 涉及的人写代码文件和相邻关键调用点
- spec 指向的 architecture / requirement / roadmap 相关文档（只读，判断改动是否会影响归并；feature 即 design 第 4 节）
- goal / gate 模式下的 evidence pack、gate results、DoD results；缺失时回 implementation gate 补证据，不现场猜测
- 独立 Task agent reviewer 输出（如果本轮启用了 Paseo 或其他 reviewer）

如果工作区有本轮范围外的既有 dirty 文件，先记录为 baseline/无关变更；审查结论只针对本轮可归因的改动。无法区分归因时写成 `residual-risk`，不要把不确定当通过。

---

## 启动检查

先按「进入来源」表确认本轮来源，再做对应前置校验：

1. 来源的 spec 产物存在且已定稿——feature 看 `{slug}-design.md`（`doc_type=feature-design`、`status=approved`、`feature` 与目录一致）+ `{slug}-checklist.yaml`（`steps` 全 `done`）；issue 看 report+analysis+fix-note；refactor 看 scan+refactor-design+checklist；ff / ad-hoc 看用户确认范围。缺定稿 spec 时退回对应实现技能，不硬审。
2. goal / gate 模式下，先读取 `{slug}-evidence-pack.md`、`{slug}-gate-results.json` 和 `{slug}-dod-results.json`；缺失或 gate blocking 未解释时退回 implementation.before_review。
3. 当前 diff 能看到本轮实现改动；完全没有代码或产物改动时退回来源实现技能。
4. 如果已有 `{slug}-review.md`：
   - `status: passed` 且 diff 未变化：提示按表进入「通过后去向」。
   - `status: changes-requested` / `blocked`：读取旧 findings，确认是否处于 review-fix 后的复审。
   - diff 已变化：重新 review，并在报告里记录这是第几轮。

---

## 独立 Task agent reviewer（双环节）

本阶段是**双环节 review**，两个环节互补：

| 环节 | 目的 | 是否 gate 必需 |
|---|---|---|
| **A 独立隔离 agent review** | spec 视角整体审查，用**独立上下文**避免主 agent 确认偏误 | 是（gate 放行靠它） |
| **B OCR 行级扫描** | 行级 bug / 安全 / 代码模式扫描，补 A 的盲区 | 否（装了就跑，缺了降级） |

**检测由主 agent 在运行时自检自己的工具**，不靠脚本猜环境——主 agent 最清楚自己手上有哪些工具。

---

### 环节 A：独立隔离上下文 agent review（gate 必需）

主 agent 按 `.codestable/reference/execution-conventions.md` 的 Task agent 选择规则启动独立 Task agent reviewer：Paseo subagent 优先，否则用当前宿主的原生 Codex/Claude Task/Agent；都没有则记 `local-only`，不能伪装启动。gate 默认不放行，需用户明确降级（见 `reviewer` 字段）。

独立 Task agent reviewer prompt（只给原始材料，不透露主 agent 的任何 review 结论）：

```text
你是 CodeStable 本次改动的独立代码审查 agent。只读，不修改文件，不更新 checklist/design。

请读取：
- .codestable/attention.md
- {design_path}
- {checklist_path}
- {evidence_pack_path}、{gate_results_path}、{dod_results_path}（存在时）
- 当前 git status / git diff / staged diff
- diff 涉及的人写代码和相邻关键调用点

按严重度输出：blocking / important / nit / suggestion / learning / praise / residual-risk。
每条 finding 必须有 file:line 或仓库事实证据、影响、建议修复边界。
额外输出 Test And QA Focus：QA 必须重点复核的场景、建议新增或加强的测试、review 无法确认的点。
不要写 {slug}-review.md；只把审查结果回传给主 agent。
```

---

### 环节 B：OCR 行级扫描（装了就跑）

主 agent 自检 `ocr` CLI 是否可用：

```bash
which ocr && ocr llm test
```

可用则自动调用（不需要用户显式要求），用 `--background` 传入 spec 摘要提升质量：

```bash
ocr review --audience agent --background "{feature slug / 目标 / 本次改动范围}"
```

**OCR 只能审本轮 scope，不能用裸 workspace 模式发现 scope。**`ocr review` 默认会审 staged + unstaged + **untracked**；Roadmap 多 feature 连续执行时，历史 dirty/untracked 会让 OCR 越扫越大。调用规则：

1. 先建立 `current_scope_files`：优先取 scope-gate / evidence pack 的 `changed_files`，否则取 `{feature-base}..HEAD` 或实现汇报中的本轮文件。
2. 已提交 diff → 用 `ocr review --audience agent --from {feature-base} --to HEAD`。
3. 未提交 diff → 只有 `git status --short` 的所有非 ignored 路径都属于 `current_scope_files`，才可裸跑 `ocr review`；否则记 `skipped-scope-ambiguous`，改为本地行级审查 `current_scope_files`。
4. 合并 OCR finding 前，**丢弃**命中以下路径的 finding，无论 OCR 是否扫到——
   - `.codestable/`（CodeStable 自己的 spec / 工具产物，永远不是行级代码审查对象）
   - 任何 `.` 开头的目录（`.git/`、`.claude/`、`.venv/` 等）
   - `.gitignore` 命中的文件（`git check-ignore <path>` 为真）
   未被 `.gitignore` 忽略、且属于 `current_scope_files` 的 untracked 新增文件必须被本轮 review 覆盖。

OCR 的 High / Medium / Low 映射到 cs-code-review 严重度后合并：

| OCR 优先级 | 映射规则 |
|---|---|
| High | 有仓库事实支撑 → `blocking`/`important`；证据不足 → `residual-risk` |
| Medium | `nit` 或 `suggestion` |
| Low | 丢弃（视为噪音），不进入报告 |

OCR 不做 spec-fit 判断；mapping 后的 finding 必须经主 agent 本地事实核验才能升级为 `blocking`。`ocr` 未安装 / `ocr llm test` 失败 → 记 `not-available`，提示用户走 `cs-onboard` 的 open-code-review 段安装并配置；不阻塞本轮。注意 `ocr llm test` 超时（`context deadline exceeded`）多半是配置用了旧 `llm.*` 块——ocr v1.x 需用 `provider`/`providers` 体系，详见 onboard 段或 `codestable-doctor.py` 的 OCR 体检。

---

### 合并原则

A、B 两环节可并行启动。一旦某环节已启动，主 agent **不能在其返回前定稿 `{slug}-review.md`、给出 `passed` 或进入通过后去向**。

- 已启动的 reviewer 返回 → 逐条本地事实核验，去重，合并进报告，保留来源标注（`paseo` / `native-agent` / `ocr` / `local`）。
- reviewer 失败 / 卡住 / 权限阻塞 → 报告 `status: blocked`，记录 `pending|failed|blocked` 和原因，让用户决定：重试、等待或明确降级。
- 不要无限轮询；等通知或用户带回结果。

未经本地仓库事实核验的外部结论只能写 `residual-risk` 或忽略，不能直接升级为 `blocking`。

**`reviewer` 字段（gate 锚点）**，按本轮实际完成的环节写：

| 值 | 含义 | gate |
|---|---|---|
| `subagent+ocr` | 环节 A（Task agent）+ 环节 B 都完成（理想） | 放行 |
| `subagent` | 环节 A 完成，OCR 不可用 / 跳过 | 放行 |
| `ocr` | 仅 OCR，缺 Task agent review | 需 override |
| `self` | 两环节都缺 | 需 override |

gate 默认要求 `subagent` 或 `subagent+ocr`；`ocr` 和 `self` 需配 `CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1` 才放行。OCR 不能替代环节 A——目的不同（A 是 spec 隔离审查，B 是行级扫描）。

## 审查流程

### 1. 上下文与范围

- 用 design 第 1/2/3 节确认目标、明确不做、关键决策、验收场景。
- 用 checklist steps 确认实现声称已经完成的范围。
- 用 `git status` / `git diff` 列出真实改动文件，标出新增、修改、删除、未跟踪、staged。
- 判断 diff 大小和风险：跨模块、跨边界、数据迁移、权限/安全、并发/异步、用户可见 UI、公共 API、测试缺口。

### 2. 独立审查合并

- 主 agent 自检工具：是否有 Task agent 能力（Paseo subagent / 原生 Codex/Claude Task/Agent），`which ocr` 是否可用。
- 环节 A（独立隔离 Task agent）和环节 B（OCR）可并行启动，互不等待。
- 本地可以先做整体审查草稿，但最终 verdict 必须等所有已启动 reviewer 返回后才能定稿。
- 每环节返回后：逐条本地事实核验，OCR 结果按 High/Medium/Low 映射严重度，能复现 / 有证据才采纳；证据不足只写 residual-risk。
- 某环节失败 / 卡住：不要默默降级；报告该环节 `failed|blocked`，交给用户决定重试或明确降级。
- 报告里保留来源：标注每条 finding 来自哪个 reviewer（`paseo` / `native-agent` / `ocr` / `local`）。

### 3. 整体审查

先看整体，再看行级细节：

- design fit：实现是否满足 design，又没有偷偷扩范围。
- 架构 fit：新代码是否放在正确层次，是否绕过既有抽象、引入反向依赖或过度耦合。
- 复杂度：是否为当前问题引入过度泛化、补丁分支、参数膨胀、大函数/大类继续膨胀。
- 测试策略：现有测试和新增测试是否能证明关键场景；测试是否会在代码坏掉时真实失败。
- 风险面：错误处理、数据校验、安全边界、权限、并发、幂等、性能、可观测性、回滚/卸载。
- 文档/归并影响：是否出现 acceptance 必须回写的 architecture / requirement / roadmap 变更。

### 4. 行级审查

对人写代码逐文件审查，至少覆盖：

- 逻辑正确性：边界值、空值、异常路径、状态转换、时序问题、off-by-one。
- 错误处理：错误语义是否明确，是否吞错，是否把恢复逻辑和业务逻辑搅在一起。
- 数据与安全：输入验证、注入风险、敏感信息、权限检查、跨租户/跨用户隔离。
- 性能与资源：重复 IO、N+1、无界循环/缓存、内存泄漏、未释放资源。
- 并发/异步：竞态、死锁、取消、重入、重复提交、幂等。
- 可维护性：命名是否沿用 design 术语，是否复用已有 helper，是否新增重复逻辑。
- 清洁度：调试输出、临时 TODO/FIXME、注释掉代码、未使用 import、方案外文件。

生成代码、锁文件、大数据文件可以抽样，但报告里要说明抽样范围。人写业务代码不能跳过不看。

### 5. 结论

把发现按严重度归类，并给出明确 verdict：

- `passed`：没有 blocking；important 已修复、无重要项、或用户明确接受延后。
- `changes-requested`：有 blocking，或 important 多到会影响验收可信度。
- `blocked`：缺少关键输入、diff 归因无法判断、设计/实现状态不满足 review 前置条件，或本轮已启动独立 Task agent reviewer 但结果仍 pending / failed / blocked 且用户尚未确认降级。

**`reviewer` 字段（gate 锚点）**：`{slug}-review.md` 的 frontmatter `reviewer` 决定下游 worktree / commit / finish gate 是否放行，按「独立 Task agent reviewer（双环节）」实际完成情况写 `subagent+ocr` / `subagent` / `ocr` / `self`（语义见上节表）。任一已启动环节仍 pending / failed / blocked 时不定稿 `passed`，也不写 `subagent`。

---

## 严重度

- `blocking`：必须先修。会导致功能不满足 design、数据/安全/权限风险、明显 bug、验收无法可信执行、严重架构倒退、测试完全覆盖不到关键风险。
- `important`：应该修；若用户决定延后，必须在 review 报告和 acceptance residual risk 中明确记录。
- `nit`：小的清晰度或一致性建议，不阻塞。
- `suggestion`：替代实现思路，不要求本次采用。
- `learning`：知识性说明，不要求动作。
- `praise`：记录值得保留的好做法；少量即可。
- `residual-risk`：review 无法完全消除的不确定性，需要 QA / acceptance 重点复核。

不要把个人偏好升级成 blocking。blocking 必须能用仓库事实、design 契约、可靠工程原则或可复现实例支撑。

---

## 报告模板

报告落在来源流程的 spec 目录，文件名 `{slug}-review.md`；feature 来源即 `.codestable/features/{feature}/{slug}-review.md`，issue/refactor 等放各自流程目录。

完整 frontmatter 与各章节模板见同包 `references/report-template.md`（按已加载 `SKILL.md` 所在目录解析，不要按业务仓库根目录猜路径）。没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。

---

## review-fix 衔接

下一步去向按「进入来源」表确定（feature 来源即 review-fix→`cs-feat-impl`、通过→`cs-feat-qa`；issue/refactor/ff 各回对应实现技能与提交收尾）。

如果有 `blocking`：

1. 报告 `status: changes-requested`。
2. 告诉用户下一步触发来源实现技能的 review-fix 模式。
3. review-fix 只修 blocking findings；important 是否修由用户或实现者判断，但不能顺手扩大范围。
4. review-fix 完成后必须重跑本审查，不能跳过直接进入来源的通过后去向。

如果只有 `important`：

- 默认建议先修；如果用户明确接受延后，报告里把它移入 residual risk，并允许进入通过后去向。

如果没有 blocking，且 important 已处理或被明确接受：

- 报告 `status: passed`。
- 告诉用户下一步是「进入来源」表的通过后去向（feature→`cs-feat-qa`）。

---

## 退出条件

- [ ] 已读取 attention、来源 spec 产物、实现证据、git status、git diff 和相关代码。
- [ ] 已确认来源 spec 产物已定稿（feature 看 checklist steps 全 done）；否则退回来源实现技能。
- [ ] 主 agent 已自检 Task agent 能力（Paseo subagent / 原生 Codex/Claude Task/Agent）和 `ocr` CLI，记录可用情况。
- [ ] 环节 A（独立隔离 agent）和环节 B（OCR，可用时）均已启动，或记录跳过原因。
- [ ] 所有已启动的环节均已返回并逐条本地核验合并 / 驳回；否则报告 `status: blocked`，没有进入 QA。
- [ ] 已做整体审查和行级审查。
- [ ] 已明确区分 blocking / important / nit / suggestion / learning / praise / residual-risk。
- [ ] 已写来源 spec 目录下的 `{slug}-review.md`（feature 即 `.codestable/features/{feature}/{slug}-review.md`）。
- [ ] `status: passed` 时 frontmatter `reviewer` 已按双环节实际完成写 `subagent+ocr` / `subagent`（或确属无 subagent 平台的 `ocr` / `self` fallback）——这是下游 gate 的放行锚点。
- [ ] 有 blocking 时没有进入下游，而是指向来源实现技能的 review-fix。
- [ ] 无 blocking 时明确告诉用户「进入来源」表的通过后去向（feature→`cs-feat-qa`）。

---

## 容易踩的坑

- 边 review 边修代码，把只读 gate 变成实现阶段。
- 只看实现汇报，不看真实 `git diff`。
- 只看测试是否通过，不判断测试是否有效。
- 把格式、命名偏好、个人写法升级成 blocking。
- 发现设计外实现却不回到 design 契约判断。
- 外部 reviewer（Paseo / native-agent / OCR）的结论没经本地事实核验就直接照抄成 blocking。
- OCR High 直接映射成 blocking，跳过本地核验。
- 某路 reviewer 还没返回，就把本地 review 定稿为 passed。
- 某路 reviewer 卡住时不问用户就默默降级成 local-only。
- blocking 修完后跳过复审，直接验收。
- review 报告没有落盘，导致 acceptance 没有可追溯输入。
