---
name: cs-roadmap-impl-goal
description: CodeStable 大需求端到端 goal 编排技能。用于用户给出一个较大软件需求，并希望先用 cs-roadmap 沉淀 roadmap，再为 roadmap items 中每个子 feature 完成 cs-feat-design/checklist，经过用户确认后输出一条可直接粘贴的 /goal 指令，由 goal 会话循环逐个 feature 执行 cs-feat-impl、cs-feat-review 和 cs-feat-accept，直到整个 roadmap 验收完成。触发：用户说“做完整个 roadmap”、“把这个大需求拆完并自动推进”、“生成 goal 指令跑完整个 CodeStable roadmap”、“像 supergoal 一样规划并执行这些 features”、“一次性跑完 roadmap 里的所有 feature”等。
---

# cs-roadmap-impl-goal

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

## 目标

把一个大需求变成可审阅、可恢复、可自动推进的 CodeStable roadmap 执行包：

1. 先按 `cs-roadmap` 规范澄清需求并创建 / 更新一份 roadmap。
2. 用户确认 roadmap 后，为 roadmap items 里的每个子 feature 运行 `cs-feat-design`，生成 design + checklist。
3. 用户确认所有 feature design 后，输出一条可直接粘贴的 `/goal` 指令。
4. `/goal` 会话按顺序循环执行每个 feature：`cs-feat-impl` → `cs-feat-review` → 必要时 review-fix → `cs-feat-accept` → 更新状态 → 下一个 feature。
5. 全部 feature 验收后，做整个 roadmap 的最终审计；只有审计通过才打印完成标记。

注意：不要把长任务正文塞进 `/goal` 参数。长协议和 feature 执行规格写入 roadmap 自己的目录，`/goal` 只引用这些文件和终止标记。

---

## 目录约定

**复用 `cs-roadmap` 的目录，不创建独立顶层目录。**

在现有 roadmap 目录下增加 goal 执行文件：

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── goal-plan.md          # 本次 goal 执行总览：假设 / 风险 / feature 顺序 / 验证命令
├── goal-state.yaml       # goal 会话实时状态
├── goal-protocol.md      # 从本技能 references/protocol.md 复制并按 slug 落地
└── goal-features/
    └── {feature-slug}.md # 每个 feature 的执行规格，指向 design/checklist
```

普通 feature 仍放在标准目录：

```text
.codestable/features/{YYYY-MM-DD}-{feature-slug}/
├── {feature-slug}-design.md
├── {feature-slug}-checklist.yaml
├── {feature-slug}-review.md       # goal 执行时生成
└── {feature-slug}-acceptance.md   # goal 执行时生成
```

---

## 两次确认门禁

本技能必须按两次确认推进，不能跳过。

### 第一次确认：roadmap

先完成 `cs-roadmap` 的 new / update 流程：

- 澄清大需求目标、范围、明确不做、成功标准。
- 读取 `.codestable/attention.md`、相关 requirements / architecture / compound / history features。
- 写 `{slug}-roadmap.md` 和 `{slug}-items.yaml`。
- 自查模块拆分、接口契约、依赖 DAG、最小闭环、safety net / polish / harden、验证入口、交付物、知识回写候选。
- 把完整 roadmap 给用户 review。

只有用户明确确认 roadmap 后，才进入所有 feature design 阶段。

### 第二次确认：所有 feature design

对 roadmap items 里的每个 planned 子 feature，按依赖顺序逐个完成 `cs-feat-design`：

- 创建 feature 目录。
- 写 `{feature-slug}-design.md`，frontmatter 带 `roadmap` / `roadmap_item`。
- 写 `{feature-slug}-checklist.yaml`。
- 按现有 `cs-feat-design` 约定，把 items.yaml 对应条目更新为 `in-progress` 并填写 `feature` 字段。
- design 必须包含：基线预检、必跑验证命令、交付物、验收场景证据类型、清洁度规则、可独立验证 steps。

全部 feature design 都写完后，一次性给用户 review。用户可能反复修改任意一个 design；每次修改后同步更新 checklist、goal-plan、goal-features。只有用户明确确认所有 design 后，才输出 `/goal`。

用户确认所有 design 后，先把每份 `{feature-slug}-design.md` 的 frontmatter `status` 从 `draft` 改为 `approved`，再生成 goal 执行包。`cs-feat-impl` 和 `cs-feat-accept` 都要求 design 已 approved；不要把 draft design 交给 goal 会话。

---

## 生成 goal 执行包

在 `.codestable/roadmap/{slug}/` 内写：

### `goal-plan.md`

包含：

- roadmap 路径和 items.yaml 路径
- feature 执行顺序
- 每个 feature 的一句话交付物
- 关键假设
- Top 3 风险与缓解
- 必跑验证命令集合
- 预检策略
- 最终审计会核验的交付物类型

### `goal-state.yaml`

格式：

```yaml
roadmap: "{slug}"
status: ready-to-dispatch
baseline_ref: "{git rev-parse HEAD 或 no-git}"
current_feature: 1
features:
  - slug: "{feature-slug}"
    roadmap_item: "{feature-slug}"
    feature_dir: ".codestable/features/YYYY-MM-DD-{feature-slug}"
    design: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-design.md"
    checklist: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-checklist.yaml"
    review: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-review.md"
    acceptance: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-acceptance.md"
    status: pending
```

### `goal-protocol.md`

从 `references/protocol.md` 复制到 roadmap 目录，并把 `{slug}` / 路径替换为本次实际值。

### `goal-features/{feature-slug}.md`

每个 feature 一份，包含：

- 对应 roadmap item
- design / checklist / review / acceptance 路径
- 依赖项
- 必跑命令
- 验收证据
- 交付物
- 清洁度规则
- 失败恢复边界

---

## 自查

输出 `/goal` 前必须自查并修正：

1. roadmap items 是否 DAG，无循环依赖。
2. 每个 item 是否已有 design + checklist。
3. 每份 design 是否已 `status: approved`，且 frontmatter 的 `roadmap` / `roadmap_item` 与 items.yaml 一致。
4. 每个 checklist step 是否可独立验证，且初始 `steps.status` 为 `pending`、`checks.status` 为 `pending`。
5. 每个 feature 是否有必跑命令 / 基线风险 / 交付物 / 清洁度规则。
6. 每个 goal-feature spec 是否写明 review 产物路径、acceptance 产物路径和 review blocking 的返回路径。
7. `goal-state.yaml` 是否能断点恢复。
8. 最终审计是否能从仓库事实核验每个交付物。
9. 用户是否已明确确认 roadmap 和所有 feature design。

---

## 输出给用户的 goal 指令

确认通过后，打印一条 fenced `/goal`，然后停止：

```text
/goal "执行 CodeStable roadmap 目录 .codestable/roadmap/{slug} 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md；按 goal-state.yaml 的 features 顺序循环处理每个 feature：读取 goal-features/{feature-slug}.md、对应 design 和 checklist，完成 cs-feat-impl，再完成 cs-feat-review；如果 review 有 blocking findings，按 review-fix 修复后重跑 cs-feat-review；review passed 后完成 cs-feat-accept，并更新 goal-state.yaml 与 roadmap items。每个 feature 验证通过后打印 CS_ROADMAP_GOAL_FEATURE_DONE。所有 feature 完成后，按 goal-protocol.md 做最终 roadmap 审计。只有当 CS_ROADMAP_GOAL_COMPLETE 出现在 transcript 中，且所有 feature 都已 review passed 且 accept、最终审计通过、没有 CS_ROADMAP_GOAL_HANDOFF，本 goal 才算完成。"
```

只输出指令，不替用户执行；slash command 只能由用户粘贴触发。

---

## 完成判据

本技能阶段完成于：用户拿到可直接粘贴的 `/goal` 指令。

真正的 roadmap 完成由 goal 会话负责，必须满足：

- 所有 goal-state features 状态为 `accepted`
- roadmap items 全部 `done` 或带理由 `dropped`
- 每个 feature 有 review 报告，且无 unresolved blocking findings
- 每个 feature 有 acceptance 报告
- architecture / requirement / roadmap 回写完成
- 最终审计通过
- 已做 learning reflection：筛出 pitfall / knowledge 候选，并建议用户确认后再运行 `cs-learn`
- transcript 打印 `CS_ROADMAP_GOAL_COMPLETE`

注意：goal 会话只自动做学习点反思和候选筛选，不自动写 `.codestable/compound/`。长期知识库归档必须由用户确认后触发 `cs-learn`，按它自己的查重、提炼、review、归档流程执行。

---

## 资源

写 `goal-protocol.md` 时读取 `references/protocol.md`。
