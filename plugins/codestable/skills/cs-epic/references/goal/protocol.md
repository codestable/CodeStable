# Epic Goal Package Protocol

## 目标

把一个大需求变成可审阅、可恢复、可自动推进的 CodeStable roadmap 执行包：

1. 先按 `cs-epic` planning 阶段规范澄清需求并创建 / 更新一份 roadmap，运行 `cs-epic` review 阶段并处理到通过。
2. 用户确认 roadmap 后，为 roadmap items 里的每个子 feature 进入 `cs-feat` design 阶段，并带内部上下文 `epic_child_batch: true`；生成 design + checklist，运行 `cs-feat` design-review 阶段并处理到通过。
3. 用户确认所有 feature design 后，输出一条可直接粘贴的 `/goal` 指令，并优先尝试用可见 Task agent goal driver 派发。
4. `/goal` 会话按顺序循环执行每个 feature：`cs-feat` implementation 阶段 → `cs-code-review` → 必要时 review-fix → `cs-feat` QA 阶段 → 必要时 qa-fix 后重跑 review/QA → `cs-feat` acceptance 阶段 → 更新状态 → 下一个 feature。
5. 全部 feature 验收后，做整个 roadmap 的最终审计；只有审计通过才打印完成标记。

注意：不要把长任务正文塞进 `/goal` 参数。长协议和 feature 执行规格写入 roadmap 自己的目录，`/goal` 只引用这些文件和终止标记。

---

## 目录约定

**复用 `cs-epic` planning 阶段的目录，不创建独立顶层目录。**

在现有 roadmap 目录下增加 goal 执行文件：

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── {slug}-roadmap-review.md
├── goal-plan.md          # 本次 goal 执行总览：假设 / 风险 / feature 顺序 / 验证命令
├── goal-state.yaml       # goal 会话实时状态
├── goal-protocol.md      # 从 support/protocol*.md 复制并按 slug 落地
├── goal-protocol-feature-loop.md
├── goal-protocol-gates.md
├── goal-protocol-audit.md
├── goal-audit.md         # goal 会话结束前生成的最终 roadmap 审计报告
└── goal-features/
    └── {feature-slug}.md # 每个 feature 的执行规格，指向 design/checklist
```

普通 feature 仍放在标准目录：

```text
.codestable/features/{YYYY-MM-DD}-{feature-slug}/
├── {feature-slug}-design.md
├── {feature-slug}-checklist.yaml
├── {feature-slug}-design-review.md
├── {feature-slug}-review.md       # goal 执行时生成
├── {feature-slug}-qa.md           # goal 执行时生成
└── {feature-slug}-acceptance.md   # goal 执行时生成
```

---

## 两次确认门禁

本协议必须按两次确认推进，不能跳过。

### 第一次确认：roadmap

先完成 `cs-epic` planning 阶段的 new / update 流程，并通过人审前 review gate：

- 澄清大需求目标、范围、明确不做、成功标准。
- 读取 `.codestable/attention.md`、相关 requirements / architecture / compound / history features。
- 写 `{slug}-roadmap.md` 和 `{slug}-items.yaml`。
- 自查模块拆分、接口契约、依赖 DAG、最小闭环、safety net / polish / harden、验证入口、交付物、知识回写候选。
- 运行 `cs-epic` review 阶段，如果有 blocking / blocked，先修订或等待 reviewer；不要把未通过 review gate 的 roadmap 给用户确认。
- 把完整 roadmap + items.yaml + `{slug}-roadmap-review.md` 给用户 review。

只有用户明确确认 roadmap 后，才进入所有 feature design 阶段。

### 第二次确认：所有 feature design

对 roadmap items 里的每个 planned 子 feature，按依赖顺序逐个完成 `cs-feat` design 阶段的候选设计阶段。调用 `cs-feat` 时必须带内部上下文 `epic_child_batch: true`，表示这是 `cs-epic` 批量子设计流程，不是普通单 feature 流程：

- 创建 feature 目录。
- 写 `{feature-slug}-design.md`，frontmatter 带 `roadmap` / `roadmap_item`，正文按 `.codestable/attention.md` 的报告语言落盘（默认中文）。
- 写 `{feature-slug}-checklist.yaml`。
- 运行 `cs-feat` design-review 阶段；Task agent 可用时每份 design-review 都必须有独立 reviewer 结果。批量生成多个 feature 不是 local-only 降级理由；有 blocking / blocked / pending 时先修订、等待 reviewer 或让用户明确授权降级，不进入用户二次确认。
- 按现有 `cs-feat` design 阶段约定，把 items.yaml 对应条目更新为 `in-progress` 并填写 `feature` 字段。
- design 必须包含：基线预检、必跑验证命令、交付物、验收场景证据类型、清洁度规则、可独立验证 steps。

每完成一个子 feature 的 design-review passed 后，立即运行 `python3 .codestable/tools/codestable-workflow-next.py epic --roadmap .codestable/roadmap/{slug} --json`，按 hook 输出继续处理下一个 planned / in-progress 子 feature；不要停下来要求用户确认该单个 design，也不要把该 design 改成 `approved`。单个 child 完成不是本阶段退出条件，不能用 final answer 把“下一步继续处理下一个 child”交还给用户；若 preflight 刚完成 runtime 同步，从仓库事实恢复 batch loop；除非 hook 返回 `user_gate` / `blocked`、遇到 pending / 授权问题或用户明确要求停止，否则必须在同一轮里继续 batch loop。

这里把 `cs-feat` design 阶段普通模式里的单 feature 用户整体 review 推迟到本协议统一处理：每份 design 先保持 `draft`，不要逐个改 `approved`。全部 feature design 都写完且 design-review 都 passed 后，一次性给用户 review。用户可能反复修改任意一个 design；每次修改后同步更新 checklist，并对实质变化重跑 `cs-feat` design-review 阶段。只有用户明确确认所有 design 后，才输出 `/goal`。

用户确认所有 design 后，先把每份 `{feature-slug}-design.md` 的 frontmatter `status` 从 `draft` 改为 `approved`，再生成 goal 执行包。`cs-feat` implementation 阶段和 `cs-feat` acceptance 阶段都要求 design 已 approved；不要把 draft design 交给 goal 会话。

---

## 生成 goal 执行包

在 `.codestable/roadmap/{slug}/` 内写：

### `goal-plan.md`

包含：

- roadmap 路径和 items.yaml 路径
- feature 执行顺序
- 每个 feature 的一句话交付物
- 每个 feature 的性质：functional / non-functional / mixed
- roadmap 级核心验收路径：必须真实运行的用户 / API / CLI / 后端 / e2e / smoke 场景；没有则写 none，并说明为什么这是纯非功能性 roadmap
- 关键假设
- Top 3 风险与缓解
- 必跑验证命令集合
- 最终聚合测试命令集合：roadmap 完成前必须重跑的 build / typecheck / lint / unit / integration / e2e / smoke；纯非功能性 roadmap 可用静态 / 一致性 / schema / 文档校验替代，但要写理由
- 预检策略
- DoD Policy、Gate Policy、Provider Policy
- Provider Policy 必须写明 archguard / meta-cc unavailable 记录 fallback，不自动阻塞；provider warning 需由 review / QA / audit 解释
- 验证工具缺失时的恢复策略：只能补测试依赖、锁文件或既有 runner 配置，不能新增同名 shim 或伪造验证结果
- 最终审计会核验的交付物类型
- 最终审计必须运行 `codestable-goal-consistency-gate.py --roadmap {roadmap-path}`
- 最终审计会聚合 goal-evidence-summary、provider warnings、E/C/H summary 和 H-only core checks

### `goal-state.yaml`

生成前必须先探测 git 基线：

1. 运行 `git rev-parse --is-inside-work-tree`。
2. 返回 `true` 时，运行 `git rev-parse HEAD`，把得到的 SHA 写入 `baseline_ref`。
3. 返回非 git 仓库时，`baseline_ref: no-git`。
4. 在 git 仓库内但无法取得 HEAD 时，先停止并修复基线（例如还没有任何提交），不要写 `no-git` 伪装成非 git 仓库。

格式：

```yaml
roadmap: "{slug}"
status: ready-to-dispatch
baseline_ref: "{git rev-parse HEAD 或 no-git}"
driver_kind: none            # paseo|native|none，派发成功后写回
driver_id: ""
current_feature_index: 0
features:
  - slug: "{feature-slug}"
    roadmap_item: "{feature-slug}"
    feature_dir: ".codestable/features/YYYY-MM-DD-{feature-slug}"
    design: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-design.md"
    checklist: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-checklist.yaml"
    review: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-review.md"
    qa: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-qa.md"
    acceptance: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-acceptance.md"
    status: pending
```

`current_feature_index` 是 **0-based**，指向 `features` 数组中下一个要处理的元素；第一个 feature 必须是 `0`。每个 feature accepted 后必须 scoped-commit 且确认工作树干净，再加 1。展示给用户的 `Feature: N/总数` 仍使用 1-based。roadmap item 若在执行前被标 `dropped`，不要写入 `goal-state.features`；已进入 `goal-state.features` 的条目必须走到 `accepted` 或回退修复。

与单 feature goal 不同，epic goal 用 `current_feature_index` 表示跨 feature 进度，并用每个 `features[].status` 表示单个 feature 状态；单 feature 内部的 implementation / review / QA / acceptance 细粒度阶段仍由对应 feature 产物和 `goal-protocol-feature-loop.md` 核验，不在 epic 顶层 state 里再复制一套 `stage` 字段。

### `goal-protocol*.md`

从 `support/protocol.md`、`protocol-feature-loop.md`、`protocol-gates.md`、`protocol-audit.md` 复制到 roadmap 目录，并把 `{roadmap-slug}` / `{roadmap-path}` / `{roadmap-file}` / `{items-file}` 替换为本次实际值。不要替换 `<feature-slug>` 这类运行时占位；它们必须保留给 goal 会话在每个 feature 边界填写。

`goal-protocol-gates.md` 是 Gate Policy 的运行时权威入口；`scope-gate`、`dod-runner`、`evidence-pack` 等具体脚本由 `cs-onboard` 安装到项目 `.codestable/tools/`。缺脚本时先按 CodeStable preflight 恢复；不要把缺失脚本当作 gate passed。

### `goal-features/{feature-slug}.md`

每个 feature 一份，包含：

- 对应 roadmap item
- design / checklist / design-review / review / QA / acceptance 路径
- 依赖项
- feature 性质：functional / non-functional / mixed
- 核心运行路径：功能性 feature 必填；非功能性 feature 写 none + 替代证据
- 必跑命令
- Feature DoD、stage gates、gate 输入产物、失败恢复路径
- 验收证据
- 交付物
- 清洁度规则
- 失败恢复边界

---

## 自查

输出 `/goal` 前必须自查并修正：

1. roadmap items 是否 DAG，无循环依赖。
2. 每个 item 是否已有 design + checklist。
3. roadmap review 是否存在且 `status: passed`，没有 unresolved blocking finding。
4. 每个 item 是否已有 design-review 且 `status: passed`，没有 unresolved blocking finding，并记录已完成独立 reviewer 或用户明确降级。
5. 每份 design 是否已 `status: approved`，且 frontmatter 的 `roadmap` / `roadmap_item` 与 items.yaml 一致。
6. 每个 checklist step 是否可独立验证，且初始 `steps.status` 为 `pending`、`checks.status` 为 `pending`。
7. 每个 feature 是否有必跑命令 / 基线风险 / 交付物 / 清洁度规则。
8. 每个 goal-feature spec 是否写明 design-review / review / QA / acceptance 产物路径，以及 review blocking / QA failed 的返回路径。
9. `goal-state.yaml` 是否能断点恢复，且 `current_feature_index` 使用 0-based 语义。
10. `goal-plan.md` 是否写明 roadmap 级核心验收路径、最终聚合测试命令、非功能性替代证据策略、DoD Policy、Gate Policy、Provider Policy。
11. 用户是否已明确确认 roadmap 和所有 feature design。
12. `goal-protocol*.md` 是否都低于 300 行，且没有把 roadmap slug 误替换进 feature 标记；`Feature:` 行必须使用 `<feature-slug>` 或真实当前 feature slug。
13. 验证命令如果依赖外部测试工具，goal-plan / goal-feature spec 是否说明真实 runner 或依赖安装方式；不能通过新增 `pytest.py`、`jest`、`go` 等同名 shim 绕过。
14. 最终审计是否能从仓库事实核验每个交付物，运行 goal consistency gate，并会落盘到 `{roadmap-path}/goal-audit.md`。

---

## 输出和派发 goal 指令

确认通过后，读取 `support/goal-command-template.md`，替换 `{slug}`，准备一条 fenced `/goal`。

然后按 `.codestable/reference/agent-conventions.md` 的 Goal driver 派发规则执行：

- 有可见 Paseo subagent 或可见 native Task/Agent 时，用上面生成的同一条 literal `/goal` 指令作为 driver 初始任务启动 driver，并把 agent id / run id / 查看方式告诉用户。
- driver 不可见、不可追踪、缺授权或派发失败时，不启动后台任务，只打印 fenced `/goal`，让用户粘贴到新的 agent 会话执行。
- 主 agent 不能仅凭“已派发”宣布 roadmap 完成；完成必须由 goal 产物和 transcript 标记证明。

---

## 完成判据

本阶段完成于：goal 包已落盘，且已派发可见 Goal driver 或已把可直接粘贴的 `/goal` 指令交给用户。

真正的 roadmap 完成由 goal 会话负责，必须满足：

- 所有 goal-state features 状态为 `accepted`
- roadmap items 全部 `done` 或带理由 `dropped`
- 每个 feature 有 review 报告，且无 unresolved blocking findings
- 每个 feature 有 QA 报告，且无 unresolved failed / blocked items
- 每个 feature 有 acceptance 报告
- `{roadmap-path}/goal-audit.md` 存在，记录最终聚合测试、roadmap 级核心验收路径、跳过项、re-verified / trust-prior 和结论
- architecture / requirement / roadmap 回写完成
- 最终审计通过
- 已做 learning reflection：筛出 pitfall / knowledge 候选，并建议用户确认后再运行 `cs-keep`
- 已提示用户可运行 `cs-docs-neat`，同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆
- transcript 打印 `CS_ROADMAP_GOAL_COMPLETE`

注意：goal 会话只自动做学习点反思和候选筛选，不自动写 `.codestable/compound/`。长期知识库归档必须由用户确认后触发 `cs-keep`，按它自己的查重、提炼、review、归档流程执行。

---

## 资源

写 `goal-protocol*.md` 时读取 `support/protocol.md`、`support/protocol-feature-loop.md`、`support/protocol-gates.md`、`support/protocol-audit.md`。输出 slash command 时读取 `support/goal-command-template.md`。
