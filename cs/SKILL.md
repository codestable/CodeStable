---
name: cs
description: CodeStable 工作流根入口，介绍体系全貌并把诉求路由到对应 cs-* 子技能。触发：用户只输入 `cs`、说"介绍一下 codestable"、"该用哪个技能"、"不知道用哪个"，或诉求还很开放未收敛。本技能只做路由不做事。
---

# cs

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

`cs` 是 CodeStable 工作流家族的统一入口。用户开口大概率不会指名某个 `cs-xxx`——可能只说"我想加个权限校验"、"这个地方有 bug"、"介绍下 codestable"，甚至只发一个 `cs`。本技能负责接住开放式输入，弄清意图，路由到对的子技能。

**两件事，仅此两件**：

1. 用户带具体诉求 → 匹配场景路由表，告诉用户该触发哪个 `cs-*`，并简单说明为什么
2. 用户想了解体系 / 说不清想做什么 → 给精简体系速读 + 让用户挑或描述更具体的诉求

**本技能不做事**：不写 spec / 不读写 `.codestable/` 下内容产物 / 不替子技能跑流程。产出只有"建议触发哪个子技能"。

---

## 收到调用先做的扫描

回应前每次都做（几个 tool 调用就够）：

1. **看仓库有没有接入 CodeStable**——`Glob .codestable/` 看顶层目录
2. **存在**——必须先 `Read .codestable/attention.md`（如果缺失提示骨架不完整，先补齐或重跑 `cs-onboard`）；再 `Read .codestable/reference/system-overview.md`（如果有）；`Glob` 一下 `features/` `issues/` `roadmap/` 看进行中的工作（拿目录名就够，不逐份读）
3. **不存在**——后面提示用户先走 `cs-onboard`
4. **看用户原话**——开放式还是带具体诉求？带诉求匹配路由表，没诉求给体系介绍

扫完才回应。让用户感觉你心里有数。

---

## 体系一图速读（用户没具体诉求 / 让你介绍时讲这个）

CodeStable 把开发活动建模成 **8 个实体 + 4 个流程**，所有产物聚在 `.codestable/`：

```
.codestable/
├── requirements/    需求 + 领域模型（VISION + capability + CONTEXT.md + adrs/）
├── roadmap/         规划层（roadmap / roadmap-review / goal 执行包）
├── goals/           目标实体（限定起点/终点，自主迭代 + subagent 功能验收）
├── features/        新增能力 spec 聚合根（design / design-review / impl / review / qa / accept）
├── issues/          修 bug spec 聚合根（report / analyze / fix）
├── refactors/       重构 spec 聚合根（beta）
├── audits/          审计实体（主动扫描发现清单，不定修）
└── compound/        知识沉淀（cs-keep 写自由 markdown，grep 检索）
```

**四条流程**：

- **新增能力**：`cs-feat-design` → `cs-feat-design-review` → `cs-feat-impl` → `cs-code-review` → `cs-feat-qa` → `cs-feat-accept`（想法模糊先 `cs-brainstorm` 分诊）
- **目标达成**：`cs-goal`（限定起点/终点 → interview/grill 写起点报告 → 自主实现/验证/迭代 → 完成前 subagent 功能验收）
- **修 bug**：`cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix`
- **重构**（beta）：`cs-refactor` / `cs-refactor-ff`

**横切**：commit 前走 `cs-code-review` 独立评审；流程跑完发现"值得记下来" → `cs-keep` 沉淀到 `compound/`（纯 markdown，grep 检索）。

**核心理念**：编排的是软件本身的生命周期（需求、领域模型、特性、bug、决策），不是 Agent。人在环——程序员对整体把控负责，AI 是高效执行体。

> 项目已 onboard 的话更详细总览看 `.codestable/reference/system-overview.md`。

---

## 场景路由表

匹配用户的话到表里某行，告诉用户："你这个诉求建议走 `cs-xxx`，因为 {一句话理由}"。

### Route Governance

`cs` 必须保持轻量只做路由，但每次路由都说明 governance 边界。默认输出短 route brief：

```text
Route: {目标 skill 或阶段}
Context: {L0-L4}
Reason: {为什么这条路由合适}
Not routing to: {排除的相邻流程，如有歧义}
Escalation: {什么情况会抬升 context level}
Next: {用户该触发什么，或这条路由会决定什么}
```

Context level 只说明轻重，`cs` 阶段不生成重型产物：

- L0：纯状态 / 验证 / 同步。
- L1：本地、可逆、不改变长期 intent。
- L2：需要 owner 选择、授权、接受、延期或 sign off。
- L3：会改变长期 spec、future agent 输入、capability boundary 或公开契约。
- L4：旧 spec 漂移、冲突、source-of-truth 不清，需要 inventory / rehabilitation。

L2/L3 需 owner 审批/选择/授权/接受风险时，子流程先按 `.codestable/reference/approval-conventions.md` 在对应 unit 写 `approval-report.md`（design / issue analysis / acceptance 等阶段报告已承载审批上下文则免）。`cs` 自身通常只路由；唯一例外：route choice 本身需 owner 选择且无明确 unit 时，当 intake decision 写 `.codestable/brainstorms/{slug}/approval-report.md` 再 owner-stop，不要只给 chat-only brief。

升级触发器：需 owner 判断方向/授权/接受风险/finish-merge readiness；可能改长期 requirement / architecture / roadmap / decision / guide / skill；fast path 发现 capability boundary / public contract / future-agent instruction / spec drift；旧文档冲突或不确定哪个 canonical。路由不确定就按上面规则停下让用户选，不硬猜。

| 用户说什么 / 想做什么 | 路由到 |
|---|---|
| 仓库还没有 `.codestable/` | **先 `cs-onboard`**——所有其他 cs-* 都依赖这个目录 |
| 限定起点和终点 / 明确验收结果 / "帮我达成这个 goal" / "自主迭代直到完成" / "grill me 后开干" | `cs-goal`（起点 / iteration 报告；实现由 AI 自主推进；完成前 subagent 功能验收） |
| 想法还模糊 / "有想法没想清楚" / "先聊聊" / "不知道是不是新功能" | `cs-brainstorm`（分诊后路由到 design / feature-brainstorm 落盘 / roadmap） |
| 新功能 / "加个 X" / "实现 XX" | `cs-feat`（路由 design / ff / impl / accept） |
| BUG / 异常 / 报错 / "这里不对" / "文档错了" | `cs-issue`（路由 report / analyze / fix） |
| 代码优化 / 重构 / 重写（行为不变） | `cs-refactor` / `cs-refactor-ff` |
| 审查系统 / 扫描 bug / 审计代码 / "有哪些问题" / "哪里可以优化" | `cs-audit`（主动扫描发现，只列清单不定修） |
| 补 / 更新需求文档 | `cs-req` |
| 拍板技术决策 / 加领域术语 / 项目要分子系统 | `cs-domain` |
| 大需求拆解 / "我想要一个 X 系统" / 排期规划 / 模块拆分 + 接口契约 | `cs-roadmap` |
| roadmap 人工确认前的规划审查 / "review 这个 roadmap" | `cs-roadmap-review` |
| 推进已有 roadmap / 执行整个 roadmap / "继续 roadmap" / "用 goal 稳步推进 roadmap" | `cs-roadmap-impl-goal` |
| feature design 人工确认前的方案审查 / "review 这个 design" | `cs-feat-design-review` |
| 合并前审一下 / "code review" / "代码评审" / 准备 PR / merge | `cs-code-review`（对当前 diff 做独立评审，质量门禁） |
| 术语 / 领域模型 / 架构决策 (ADR) / "这块属于哪个 context" | `cs-domain` |
| 摸代码调研 / 踩坑回顾 / 技术选型 / 长期约束 / 编码规约 / 可复用模式 / 库用法 / "值得记下来" | `cs-keep` |
| 一两行的项目注意事项 / 编译特殊设置 / 命令陷阱 / "记到 attention.md" | `cs-note` |
| 开发者指南 / 用户指南 | `cs-doc-tutorial` |
| 库 API 参考 | `cs-doc-api` |
| 阶段收尾 / 整理文档 / 同步 `CLAUDE.md` 或 `AGENTS.md` / 新人交接 | `cs-docs-neat` |
| 用户在 feature / issue 流程中间问"下一步" | 路由到对应入口（`cs-feat` / `cs-issue`），让该入口判断当前阶段 |

**判不出来 / 太抽象**："听起来像 {猜测}，但你描述里 {缺什么}。是 {选项 A} 还是 {选项 B}？" 让用户选不要硬猜。

### Route Level Quick Reference

| Route | Default context | Escalate when |
|---|---|---|
| `cs-onboard` | L2/L4 | 旧文档需要 inventory、迁移或 trusted/stale 分类 |
| `cs-goal` | L1/L2 | 缺验收/起点状态需 grill + 起点报告；完成需 subagent 功能验收；spec/公开契约变更或反复 blocker → owner-stop |
| `cs-brainstorm` | L1→L2 | owner 接受某方向或要下一步可执行项 |
| `cs-roadmap` / `cs-roadmap-review` / `cs-roadmap-impl-goal` | L2/L3 | roadmap 牵涉 spec 变更、capability boundary 或 requirement delta |
| `cs-feat` | L1 | 阶段不明或用户须选 design / ff / impl / accept |
| `cs-feat-design` / `cs-feat-design-review` | L2/L3 | design 触达长期 spec 或 future agent 输入 |
| `cs-feat-impl` | L0/L3 | 实现偏离已确认 design/checklist/spec |
| `cs-code-review` / `cs-feat-qa` | L1/L3 | 评审/验证发现行为偏差、契约或 spec 影响 |
| `cs-feat-accept` | L3 | 验收写入或校验长期 architecture / requirement / roadmap / finish readiness |
| `cs-feat-ff` | L1/L3 | 快速通道发现 capability-boundary、public contract 或 spec 影响 |
| `cs-issue` / `cs-issue-report` | L1 | 路由不清或复现/影响需 owner 确认 |
| `cs-issue-analyze` | L2 | owner 须选修复方案或接受风险 |
| `cs-issue-fix` | L0/L3 | 修复暴露错误 spec、capability boundary 或公开行为变更 |
| `cs-refactor` / `cs-refactor-ff` | L1/L2 | 跨模块、有风险或行为边界不确定 |
| `cs-code-review` | L1/L3 | review 发现 Critical/Important 或触达长期 spec / 公开契约 |
| `cs-req` | L3 | 总是：需求工作改变 future agent 的 source-of-truth |
| `cs-arch` | L1/L3 | 出现 code/doc/intent 冲突 |
| `cs-audit` | L1/L2 | owner 须裁定修 / 延 / 忽略 |
| `cs-explore` | L1/L2 | 探索变成决策、规则或 spec 变更 |
| `cs-decide` | L2/L3 | 决策影响长期 spec 或项目级规则 |
| `cs-learn` / `cs-trick` / `cs-note` | L1/L2 | 经验升级为项目级规则或常驻指令 |
| `cs-guide` / `cs-libdoc` / `cs-docs-neat` | L1/L2 | 文档改变 user-facing 契约或公开理解 |
| `codestable-maintainer` | L2/L3 | 改 CodeStable 自身技能/harness/installed copy |

---

## 几种需要特别留心的情况

### 仓库还没接入

任何 cs-* 流程但 `.codestable/` 不存在 → 说明这一点建议**先 `cs-onboard`**。不要直接路由到 cs-feat / cs-issue——它们的 SKILL.md 都假设 `.codestable/` 已存在。

### 大需求被误当成 feature

"我想要一个权限系统 / 通知中心 / SSO 接入"这类**一眼看出做不完一个 feature** 的诉求 → 不路由到 `cs-feat`，路由到 `cs-brainstorm`（大概率判 case 3 → `cs-roadmap`）或直接 `cs-roadmap`。理由：直接起 feature 会变成巨型 design 塞不下。

### "改一下 X" 但 X 是已有功能

先问这是 **bug 修复**（X 现在表现错了）还是 **需求变更**（X 现在表现没错，但策略变了）：

- bug → `cs-issue`
- 需求变更 → `cs-req` 改需求 doc + 之后 `cs-feat` 跑实现

### 进行中的工作

扫描看到 `features/` 或 `issues/` 下已有相关目录 → 提一句"看到 `features/2026-04-22-xxx/` 已经存在，是接着做这个吗？" 让用户确认续作还是开新的。

### 沉淀类两个入口

- 写到 `.codestable/compound/` 一份独立 markdown（坑点 / 技巧 / 决策 / 调研，靠 grep 检索）→ `cs-keep`
- 一两行常驻提示"CodeStable 技能每次启动都得知道 X"（写到 `.codestable/attention.md`）→ `cs-note`

判不出问用户："这个是要写一份独立文档（cs-keep），还是一两行启动必读（cs-note）？"

---

## 介绍模式（用户只说想了解 / 不知道做什么）

按这个顺序讲，**不一次倒出全部**：

1. 一句话：CodeStable 是面向严肃工程的 AI 编码工作流，编排软件生命周期而不是 Agent
2. 9 实体 + 4 流程的速读图
3. 问用户"你现在最想从哪儿开始？"，给三个引子：
   - "我有个新功能想做" → cs-feat
   - "代码里有个 bug" → cs-issue
   - "项目还没接入 CodeStable" → cs-onboard

收住，别把所有子技能细节讲一遍。用户问到具体的再展开。

---

## 退出

本技能没有"落盘"。退出条件一条：

- [ ] 已告诉用户下一步触发哪个具体的 `cs-*` 子技能（或确认用户只是来了解，没要做事）

输出形如：

> 你这个诉求建议走 **`cs-xxx`**——{一句话理由}。
> 触发后它会 {简述会发生什么：会先扫已有 spec / 会让你先描述 / 会进入分诊 / ...}。
> 现在切到 `cs-xxx` 吗？

---

## 不做的事

- **不读写 `.codestable/` 下的内容产物**——这些是子技能的事
- **不替子技能做决策**——不在本技能做 brainstorm 分诊，不替 cs-domain 判断要不要写 ADR
- **不一次推荐多个技能**——每次只指一条路；两个独立诉求分两轮
- **不重复体系总览细节**——`.codestable/reference/system-overview.md` 才是权威完整版
- **不绕过 `cs-onboard`**——仓库没接入就先 onboard
