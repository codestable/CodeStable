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

CodeStable 把开发活动建模成 **7 个实体 + 3 个流程**，所有产物聚在 `.codestable/`：

```
.codestable/
├── requirements/    需求实体（"为什么要有这个能力"，只记现状）
├── architecture/    架构实体（"系统现在长什么样"，只记现状）
├── roadmap/         规划层（"接下来怎么做这块大需求 + 模块切 + 接口定"）
├── features/        新增能力 spec 聚合根（design / impl / review / accept）
├── issues/          修 bug spec 聚合根（report / analyze / fix）
├── refactors/       重构 spec 聚合根（beta）
├── audits/          审计实体（主动扫描发现清单，不定修）
└── compound/        知识沉淀（learning / trick / decision / explore）
```

**三条流程**：

- **新增能力**：`cs-feat-design` → `cs-feat-impl` → `cs-feat-review` → `cs-feat-accept`（想法模糊先 `cs-brainstorm` 分诊）
- **修 bug**：`cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix`
- **重构**（beta）：`cs-refactor` / `cs-refactor-ff`

**横切**：流程跑完发现"值得记下来" → `cs-learn` / `cs-trick` / `cs-decide` / `cs-explore` 沉淀到 `compound/`。

**核心理念**：编排的是软件本身的生命周期（需求、架构、特性、bug、决策），不是 Agent。人在环——程序员对整体把控负责，AI 是高效执行体。

> 项目已 onboard 的话更详细总览看 `.codestable/reference/system-overview.md`。

---

## 场景路由表

匹配用户的话到表里某行，告诉用户："你这个诉求建议走 `cs-xxx`，因为 {一句话理由}"。

| 用户说什么 / 想做什么 | 路由到 |
|---|---|
| 仓库还没有 `.codestable/` | **先 `cs-onboard`**——所有其他 cs-* 都依赖这个目录 |
| 想法还模糊 / "有想法没想清楚" / "先聊聊" / "不知道是不是新功能" | `cs-brainstorm`（分诊后路由到 design / feature-brainstorm 落盘 / roadmap） |
| 新功能 / "加个 X" / "实现 XX" | `cs-feat`（路由 design / ff / impl / accept） |
| BUG / 异常 / 报错 / "这里不对" / "文档错了" | `cs-issue`（路由 report / analyze / fix） |
| 代码优化 / 重构 / 重写（行为不变） | `cs-refactor` / `cs-refactor-ff` |
| 摸代码 / "X 是怎么实现的" / 提问调研 | `cs-explore` |
| 审查系统 / 扫描 bug / 审计代码 / "有哪些问题" / "哪里可以优化" | `cs-audit`（主动扫描发现，只列清单不定修） |
| 补 / 更新需求文档 | `cs-req` |
| 补 / 更新 / 检查架构文档 / "刷新架构 doc" / "做架构体检" | `cs-arch` |
| 大需求拆解 / "我想要一个 X 系统" / 排期规划 / 模块拆分 + 接口契约 | `cs-roadmap` |
| 技术选型 / 长期约束 / 编码规约 | `cs-decide` |
| 踩坑回顾 / 经验总结 / "值得记下来" | `cs-learn` |
| 可复用编程模式 / 库用法 / "以后做 X 就该这样" | `cs-trick` |
| 一两行的项目注意事项 / 编译特殊设置 / 命令陷阱 / "记到 attention.md" | `cs-note` |
| 开发者指南 / 用户指南 | `cs-guide` |
| 库 API 参考 | `cs-libdoc` |
| 用户在 feature / issue 流程中间问"下一步" | 路由到对应入口（`cs-feat` / `cs-issue`），让该入口判断当前阶段 |

**判不出来 / 太抽象**："听起来像 {猜测}，但你描述里 {缺什么}。是 {选项 A} 还是 {选项 B}？" 让用户选不要硬猜。

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

### 沉淀类技能的细分

判别口诀：

- 回顾"做 X 时踩了 Y" → `cs-learn`
- 处方"以后做 X 就这样做" → `cs-trick`
- 规定"全项目今后都按 X 来" → `cs-decide`
- 调查"X 现在是什么样" → `cs-explore`
- 一两行常驻提示"CodeStable 技能每次启动都得知道 X" → `cs-note`（写到 `.codestable/attention.md`）

判不出问用户："这个你想记成 {踩坑回顾 / 复用处方 / 长期规约 / 调研存档 / 常驻提示} 哪一种？"

---

## 介绍模式（用户只说想了解 / 不知道做什么）

按这个顺序讲，**不一次倒出全部**：

1. 一句话：CodeStable 是面向严肃工程的 AI 编码工作流，编排软件生命周期而不是 Agent
2. 6 实体 + 3 流程的速读图
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
- **不替子技能做决策**——不在本技能做 brainstorm 分诊，不判 cs-arch 走哪个模式
- **不一次推荐多个技能**——每次只指一条路；两个独立诉求分两轮
- **不重复体系总览细节**——`.codestable/reference/system-overview.md` 才是权威完整版
- **不绕过 `cs-onboard`**——仓库没接入就先 onboard
