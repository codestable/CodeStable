<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-31-6366F1?style=flat-square" alt="CodeStable Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## 安装

Codex plugin marketplace：

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable
codex plugin add codestable@codestable
```

Claude plugin marketplace：

```text
/plugin marketplace add liuzhengdongfortest/CodeStable
/plugin install codestable@codestable
```

`skills` CLI：

```bash
npx skills@latest add liuzhengdongfortest/CodeStable
```

如果你的 `skills` CLI 没有通过 marketplace catalog 发现插件实体，可用深扫兜底：

```bash
npx skills@latest add liuzhengdongfortest/CodeStable --full-depth
```

CodeStable 插件只打包 `plugins/codestable/skills/` 下的 `cs` / `cs-*` skills；仓库根目录不再保留独立 skill 目录。

## 升级

发布新版本后，先看 `CHANGELOG.md` 确认版本变化，再按你的安装入口刷新。

Codex plugin marketplace：

```bash
codex plugin marketplace upgrade codestable
codex plugin add codestable@codestable
```

Codex 当前 CLI 没有单独的 `plugin update` 子命令；`marketplace upgrade` 会刷新 Git marketplace snapshot，`plugin add` 从刷新后的 snapshot 安装当前版本。

Claude plugin marketplace：

```text
/plugin marketplace update
/plugin update codestable@codestable
```

Claude 更新后需要重启 Claude Code 才会应用新版插件。

`skills` CLI：

```bash
npx skills@latest update
```

如果旧安装器没有记录来源，重新执行上面的 `npx skills@latest add liuzhengdongfortest/CodeStable` 安装命令即可。

只需要一键，开始工作：

```bash
/cs-onboard
```

之后日常使用时，不知道该用哪个技能就喊根入口：

```bash
/cs
```

`cs` 会读你的诉求，告诉你这次该走哪个 `cs-xxx`。

---

## 缘起

我在开发一套新的 Harness Agent（[MA](https://github.com/liuzhengdongfortest/MA)），一开始当然是 VibeCoding——我只写设计和需求，代码由 AI 来改。这样支撑了大部分特性的开发。直到有一天 Codex 反复解决不了一个我认为比较简单的问题，并且反复在同一个地方犯错。我就知道项目需要一套工作流来维持它继续进行了。

我调研了 OpenSpec、SuperPowers、Oh-My-OpenAgent 这一类工具，没一个用着顺手：

- **OpenSpec** 太简单，没有复利工程，生成的 Spec 抽象到人类没法读
- **SuperPowers** 没有流程约束，不知道该用哪个
- **Oh-My-OpenAgent** 太重，且哲学上认为"人介入 = 失败"

CodeStable 的目标是**解决严肃工程的软件实现和编码问题**，不是造一个新名词、追求热点。

---

## 与其他框架的核心区别：编排的目标是谁

我看了一圈现在主流的 AI 编码框架——Superpowers、CCW、Oh-My-OpenAgent 等等——它们其实都在做**同一件事**：

> **如何把 Agent 编排得更好。** 让它们组队、协作、头脑风暴、跑流水线、自动接力。围绕的实体始终是 **Agent**。

CodeStable 走的是**另一个方向**：

> **编排的不是 Agent，而是软件本身的生命周期。** 围绕的实体是**构成软件的要素**——每一个需求、每一个架构决定、每一个特性、每一个 bug、每一条历史里留下来的约束。

<table>
<tr><th></th><th>Agent 编排派</th><th>CodeStable</th></tr>
<tr><td><b>核心实体</b></td><td>Agent / Role / Team</td><td>Requirement / Architecture / Feature / Issue / Decision</td></tr>
<tr><td><b>主线问题</b></td><td>Agent 之间怎么分工、传递、协调？</td><td>软件的需求、约束、决策怎么被记下来、被检索、被复用？</td></tr>
<tr><td><b>状态存在哪</b></td><td>Agent 的 session / 消息总线 / 队列</td><td>项目里的 <code>.codestable/</code> 文件树（人和 AI 都能读）</td></tr>
<tr><td><b>解决的痛点</b></td><td>单 Agent 能力不够，需要协同放大</td><td>软件复杂度膨胀撑破上下文、隐知识丢失、需求漂移</td></tr>
<tr><td><b>对人的定位</b></td><td>人少介入越好，理想是全自动</td><td>人在环 —— 程序员对整体把控负责，AI 是高效的执行体</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)


**这两个方向没有谁对谁错。**

如果你的任务是"用 AI 跑一个端到端的自动化产线"、"让多个 Agent 互相讨论方案"，Agent 编排派会更顺手。

如果你的任务是"维护一个会跨年迭代的严肃软件"、"让今天写下的需求和决策三个月后还能被准确召回"——那 CodeStable 这套以软件要素为中心的建模会更合适。

我做 CodeStable 是因为我相信：**软件工程的混乱本质上不是 Agent 不够强，而是要素没被组织好**。Agent 再强，也写不了一个把需求、架构、历史决策全丢失的项目。

---

## 设计：实体 + 流程

CodeStable 顺着软件编码的真实流程来设计，把开发活动建模成一组**实体**和**流程**。

### 实体

| 实体 | 英文 | 干什么 |
|------|------|--------|
| **需求** | requirements | 原始用户故事 + 领域术语（CONTEXT.md）+ 架构决策（ADR）。最终的逃生通道——代码烂成一坨屎时，可以摒弃所有代码、让 AI 重新生成 |
| **Epic** | epic | “我想要一个权限校验系统”这类大需求的主入口；用户侧叫 epic，第一版内部仍复用 `.codestable/roadmap/` 和 roadmap doc_type |
| **目标** | goals | 限定起点和终点，写起点报告后让 AI 自主迭代实现/验证，完成前用 subagent 做功能验收 |
| **特性** | feature | 实际落地的工程执行过程，人与 AI 共同协作，对 design / 实现 / 验收负责；每个阶段之间有显式的 Gate 卡口 |
| **问题** | issue | 开发完成后的 BUG 单子，AI 和人一同解决 |
| **重构** | refactor | 代码腐化时的整理过程（beta） |
| **知识** | compound | 复利工程的知识库，沉淀踩过的坑、好做法、调研结论（`cs-keep`）；碎片化项目约定写入 `attention.md`（`cs-note`） |

### 流程

| 流程 | 推荐主入口 | 说明 |
|------|------------|------|
| **特性引入** | `cs-feat` | 一个入口端到端推进 design → design-review → 用户确认 → goal 包长程执行 implementation → `cs-code-review` → QA → acceptance |
| **大需求端到端** | `cs-epic` | 大需求规划 → 规划审查 → 用户确认 → 子 feature design/review → goal 执行包 → 派发可见 goal driver（失败则输出 `/goal` 指令） |
| **目标达成** | `cs-goal` | 限定起点/终点 → grill 写起点报告 → 自主实现/验证/迭代 → subagent 功能验收 |
| **问题修改** | `cs-issue` | 一个入口端到端推进 report → analyze → fix → `cs-code-review` |
| **代码重构** | `cs-refactor` | 行为等价重构；内部判定标准模式或 fastforward mode，完成后进入 `cs-code-review` |
| **对外文档** | `cs-docs` | 写或更新开发者指南、用户指南、API 参考；知识库卫生仍由 `cs-docs-neat` 负责 |

`cs-code-review` 是各执行流末端、commit 前的横切质量门禁。阶段或里程碑收尾时，用 `cs-docs-neat` 整理 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆，避免文档与代码脱节。

> 强分支保护：`cs-onboard` 可选释放 `codestable-ai-branch-guard` hook，拦截 AI 在 `main`/`master` 上直接实现，强制走 worktree。详见 `cs-onboard` 的「分支保护 hook」。


---

## 技能总览

### 推荐主入口

| 分组 | 技能 | 用途 |
|---|---|---|
| 根入口 | `cs` | 不知道用哪个时轻量分诊到主入口 |
| 接入 | `cs-onboard` | 把 CodeStable 接入新仓库或已有零散文档仓库 |
| 需求 & 领域 | `cs-req` / `cs-domain` | 沉淀能力愿景、领域术语、ADR 和 context 拓扑 |
| Epic | `cs-epic` | 大需求端到端：规划、review、子 feature design、goal 包 |
| 讨论入口 | `cs-brainstorm` | 想法模糊时分诊到 feature、epic 或 brainstorm note |
| 目标 | `cs-goal` | 限定起点/终点后自主迭代到验收 |
| 特性流程 | `cs-feat` | 新特性端到端：design、review、impl、code review、QA、accept |
| 问题流程 | `cs-issue` | 问题修复端到端：report、analyze、fix、review |
| 重构流程 | `cs-refactor` | 行为等价重构，含标准模式和 fastforward mode |
| 横切审查 | `cs-code-review` | 实现完成后、commit 前的只读代码审查 gate |
| 审计 | `cs-audit` | 主动扫描 bug、安全、性能、可维护性和架构偏离 |
| 知识沉淀 | `cs-keep` / `cs-note` | 沉淀 compound 知识或短项目注意事项 |
| 对外文档 | `cs-docs` | 写开发者指南、用户指南、API 参考 |
| 文档收尾 | `cs-docs-neat` | 同步 `.codestable/`、README/docs、agent 入口和记忆 |

### 长期兼容入口

旧技能名继续可用，但只转入对应主入口，不维护独立规则：

- Feature：`cs-feat-design` / `cs-feat-design-review` / `cs-feat-impl` / `cs-feat-qa` / `cs-feat-accept` / `cs-feat-ff`
- Issue：`cs-issue-report` / `cs-issue-analyze` / `cs-issue-fix`
- Refactor：`cs-refactor-ff`
- Docs：`cs-doc-tutorial` / `cs-doc-api`
- Epic：`cs-roadmap` / `cs-roadmap-review` / `cs-roadmap-impl-goal`

完整技能目录见 [SKILL_CATALOG.md](./SKILL_CATALOG.md)。日常不知道用哪个时直接调用 `/cs`。

---

## 工作流示意

CodeStable 的技能不是一条线性流水，而是**分层 + 事件驱动**的：

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-epic          # 用户侧大需求入口，内部暂用 roadmap 存储
    ├── cs-goal
    ├── cs-brainstorm
    ├── cs-feat     -> cs-code-review
    ├── cs-issue    -> cs-code-review
    ├── cs-refactor -> cs-code-review
    ├── cs-docs
    └── cs-keep / cs-note / cs-docs-neat
```

**怎么读这张图：**

- `cs` 只做轻量分诊到主入口，不再把用户导向阶段技能。
- `cs-feat` / `cs-issue` / `cs-refactor` 是连续编排入口，按仓库事实恢复阶段。`cs-issue` / `cs-refactor` 在 review、blocking 或用户确认 checkpoint 停下；`cs-feat` 只在 design gate 停下，用户确认后经可见 goal driver 长程完成 impl、review、QA、accept。
- `cs-epic` 负责大需求规划和 goal 执行包，用户确认后派发可见 goal driver 长程执行；第一版内部仍使用 `.codestable/roadmap/`，不批量迁移历史产物。
- `cs-code-review` 是横切 gate；`cs-docs-neat` 是阶段收尾整理器；`cs-docs` 只写对外指南和 API 参考。
- 旧阶段技能是长期兼容入口，历史用户可以继续调用，但新文档和新提示词应使用主入口。

完整示意图另见 [WORKFLOW.md](./WORKFLOW.md)。

---

## 运行时结构

`/cs-onboard` 跑完后，会在你的项目根下生成 `.codestable/`，作为 requirements、roadmap、goals、features、issues、refactors、audits、compound、tools、hooks 和 reference 的聚合根。

```text
你的项目/
├── .codestable/
│   ├── attention.md                       # CodeStable 技能启动必读的项目注意事项
│   ├── requirements/                      # 需求 + 领域模型（cs-req / cs-domain 共同维护）
│   │   ├── VISION.md                      # 能力中心索引
│   │   ├── {slug}.md                      # 一个能力一份，扁平不分组
│   │   ├── CONTEXT.md                     # 领域术语表（cs-domain，lazy）
│   │   ├── CONTEXT-MAP.md                 # 多 context 拓扑入口（仅多 context 项目）
│   │   ├── adrs/                          # 架构决策记录（cs-domain，lazy）
│   │   │   └── NNN-{slug}.md              # Nygard 四节 + 状态机
│   │   └── {ctx}/                         # 子 context 子目录（仅多 context）
│   │       ├── CONTEXT.md
│   │       ├── adrs/
│   │       └── {capability}.md
│   │
│   ├── roadmap/                           # Epic 内部规划层（历史路径暂不迁移）
│   │   └── {slug}/
│   │       ├── {slug}-roadmap.md          # 主文档：背景 / 拆解 / 排期
│   │       ├── {slug}-items.yaml          # 机器可读子 feature 清单，acceptance 回写状态
│   │       ├── {slug}-roadmap-review.md   # 人审前的规划审查报告
│   │       └── drafts/                    # 可选：草稿 / 调研
│   │
│   ├── goals/                             # 目标驱动流程聚合根
│   │   └── {slug}/
│   │       ├── {slug}-start-report.md
│   │       ├── {slug}-state.yaml
│   │       ├── {slug}-iteration-*.md
│   │       └── {slug}-functional-acceptance.md
│   │
│   ├── features/                          # 特性流程聚合根
│   │   └── YYYY-MM-DD-{slug}/             # 一个 feature 一个目录
│   │       ├── {slug}-brainstorm.md       # 可选（cs-brainstorm 产出）
│   │       ├── {slug}-design.md           # 方案（cs-feat design 阶段）
│   │       ├── {slug}-checklist.yaml      # 推进清单（impl 跑、accept 回写）
│   │       ├── {slug}-design-review.md    # 人审前方案审查
│   │       ├── {slug}-review.md           # 实现后代码审查
│   │       ├── {slug}-qa.md               # 代码审查后 QA gate
│   │       └── {slug}-acceptance.md       # 验收报告（cs-feat acceptance 阶段）
│   │
│   ├── issues/                            # 问题流程聚合根
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-report.md           # 问题报告
│   │       ├── {slug}-analysis.md         # 根因分析（不显然时才有）
│   │       └── {slug}-fix-note.md         # 修复记录
│   │
│   ├── refactors/                         # 重构流程聚合根（beta）
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-scan.md
│   │       ├── {slug}-refactor-design.md
│   │       ├── {slug}-checklist.yaml
│   │       └── {slug}-apply-notes.md
│   │
│   ├── audits/                            # 审计发现与批量扫描产物
│   ├── brainstorms/                       # 独立头脑风暴产物
│   ├── compound/                          # 知识沉淀（复利工程）统一目录
│   │   └── YYYY-MM-DD-{slug}.md
│   │       # 纯 markdown，无 frontmatter，grep 检索（cs-keep 产出）
│   │
│   ├── gates/                             # workflow gate 配置（onboard 释放）
│   ├── tools/                             # 跨工作流共享脚本（onboard 释放）
│   └── reference/                         # 共享参考文档（onboard 释放）
│       ├── shared-conventions.md          # 跨技能口径 / 路径命名 / 元数据规范
│       ├── system-overview.md             # CodeStable 体系总览 + 场景路由
│       └── ...
│
└── AGENTS.md                              # 在项目根，不在 .codestable/ 里
```

**几条要点：**

- 所有产物都聚在 `.codestable/` 下，让"上次那个 feature / bug 当时怎么搞的"三秒能找到。
- `requirements/` 是**长效档案**（能力愿景 + 领域术语 CONTEXT.md + 拍板决策 adrs/），`roadmap/` 是**规划层**（接下来怎么走），两者刻意分开。
- `features/` `issues/` `refactors/` 用 `YYYY-MM-DD-{slug}/` 一个目录装齐所有相关 spec，不交叉。
- `compound/` 是**唯一**的知识沉淀目录，纯 markdown 无 frontmatter，靠 `grep -r` 检索——好写好搜。
- `.codestable/reference/` 是 `cs-onboard` 从技能包 `plugins/codestable/skills/cs-onboard/references/` 复制过来的；要改共享口径，改 skill 包内模板，新项目 onboard 自动带上新版。

### 硬约束

> 普通阶段规则不要从一个 skill 直接引用另一个 skill 的深层 `references/xxx.md`。阶段厚规则应放在主入口自己的 `references/` 下，或由 `cs-onboard` 释放到项目 `.codestable/reference/`。
>
> 兼容入口是唯一例外：它只读取同级主入口的 `SKILL.md` 进入主协议，不直接读取主入口的深层 reference。

要改共享口径，改 `plugins/codestable/skills/cs-onboard/references/` 下的模板，新项目 onboard 时带上新版本。

完整目录说明和跨 skill 引用约束见 [WORKFLOW.md](./WORKFLOW.md)。

---

## 设计哲学

CodeStable 与 OMO 做的是**完全相反**的哲学。

- OMO 认为：人只要干预就是失败的信号
- CodeStable 认为：**程序员是软件编码中的在环对象**——可以对黑盒实现不了解，但对整体实现必须有所把控，必要时也可深入

软件架构必须要 **可演进**、**可观测**、**可控制**。

也许这一点在 AI 发展强大以后会变得不再重要，但**当下这样做能让程序员在现状下舒服**——这就是价值所在。

CodeStable 面向真实开发场景，对此进行建模，期望通过一个闭环系统处理开发中常见的问题。**现有大部分框架围绕 AI 建模，而不是围绕人。** 我认为这些框架的作者驱动 AI 的能力很强，但绝对不是严肃软件的开发者——因为缺少对软件开发中需求和设计的基础组织能力，缺乏对代码实现的尊重。

---

## Roadmap

CodeStable 会根据模型能力的发展进行调整。如果未来某个模型做到某个模块的稳定产出，那么这个模块就可以删除。

- [ ] 代码重构流程需要强化（`cs-refactor` 还在 beta）
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
