<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-29-6366F1?style=flat-square" alt="CodeStable Skills"/>
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

CodeStable 插件只打包 `plugins/codestable/skills/` 下的 `cs` / `cs-*` skills；仓库根目录中的其他 skill（如 `browser-bridge`）不属于 CodeStable 插件资产。

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
| **路线图** | roadmap | "我想要一个权限校验系统"——直接塞 feature AI 接不住，先拆成路线图分步推进；`cs-roadmap-review` 做独立规划审查，`cs-roadmap-impl-goal` 把大需求一路推到 `/goal` 指令 |
| **目标** | goals | 限定起点和终点，写起点报告后让 AI 自主迭代实现/验证，完成前用 subagent 做功能验收 |
| **特性** | feature | 实际落地的工程执行过程，人与 AI 共同协作，对 design / 实现 / 验收负责；每个阶段之间有显式的 Gate 卡口（design-review / code-review / qa） |
| **问题** | issue | 开发完成后的 BUG 单子，AI 和人一同解决 |
| **重构** | refactor | 代码腐化时的整理过程（beta） |
| **知识** | compound | 复利工程的知识库，沉淀踩过的坑、好做法、调研结论（`cs-keep`）；碎片化项目约定写入 `attention.md`（`cs-note`） |

### 流程

| 流程 | 关键技能链 | 说明 |
|------|------------|------|
| **特性引入** | `cs-feat` → `cs-feat-design` → `cs-feat-design-review` *(Gate)* → `cs-feat-impl` → `cs-code-review` *(Gate)* → `cs-feat-qa` *(Gate)* → `cs-feat-accept` | 想清楚 → 方案独立审查 → 逐步编码 → 代码审查 → QA → 验收闭环 |
| **大需求端到端** | `cs-roadmap` → `cs-roadmap-review` *(Gate)* → 用户确认 → `cs-roadmap-impl-goal` → `/goal` 指令 | 大需求拆成路线图 → 独立规划审查 → 逐个 feature 自动推进至验收 |
| **目标达成** | `cs-goal` | 限定起点/终点 → grill 写起点报告 → 自主实现/验证/迭代 → subagent 功能验收 |
| **问题修改** | `cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix` → `cs-code-review` *(Gate)* | 跟 AI 说哪里有问题 → 分析根因 → 定点修复 → 合并前独立评审 |
| **代码重构** | `cs-refactor` (beta) → `cs-code-review` *(Gate)* | 软件架构腐化不是一蹴而就的。AI 辅助重构，但**终归是人在重构**——还在迭代中，欢迎赐教 |

`cs-code-review` 是各执行流末端、commit 前的横切质量门禁。阶段或里程碑收尾时，用 `cs-docs-neat` 整理 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆，避免文档与代码脱节。

> 强分支保护：`cs-onboard` 可选释放 `codestable-ai-branch-guard` hook，拦截 AI 在 `main`/`master` 上直接实现，强制走 worktree。详见 `cs-onboard` 的「分支保护 hook」。


---

## 技能总览

<table>
<tr><th>分组</th><th>技能</th><th>用途</th></tr>
<tr><td><b>根入口</b></td><td><code>cs</code></td><td>统一入口——介绍体系全貌 + 把开放式诉求路由到正确的 cs-* 子技能。不知道用哪个时就喊它</td></tr>
<tr><td><b>接入</b></td><td><code>cs-onboard</code></td><td>把 CodeStable 接入到一个新仓库 / 已有零散文档的仓库；释放 reference/、tools/ 和可选的分支保护 hook</td></tr>
<tr><td rowspan="2"><b>需求 & 领域</b></td><td><code>cs-req</code></td><td>整理 / 沉淀能力愿景 doc</td></tr>
<tr><td><code>cs-domain</code></td><td>维护 <code>requirements/CONTEXT.md</code> 术语表 + <code>requirements/adrs/</code> 架构决策（守门 3 判据 + Nygard 四节）+ 单/多 context 拓扑</td></tr>
<tr><td rowspan="3"><b>路线图</b></td><td><code>cs-roadmap</code></td><td>承载一块大需求的事前规划：概设（模块拆分）+ 架构层详设（接口契约 / 共享协议）+ 子 feature 拆解清单</td></tr>
<tr><td><code>cs-roadmap-review</code></td><td>roadmap 人审前的独立规划审查 Gate，支持 Paseo 多 agent 辅助审查，产出 <code>{slug}-roadmap-review.md</code></td></tr>
<tr><td><code>cs-roadmap-impl-goal</code></td><td>大需求端到端编排：roadmap → review → 用户确认 → 逐 feature design/checklist/design-review → 输出可粘贴的 <code>/goal</code> 指令</td></tr>
<tr><td><b>讨论入口</b></td><td><code>cs-brainstorm</code></td><td>想法模糊时的统一讨论入口，做分诊：直接 design / 进 feature 写 brainstorm.md / 移交 roadmap</td></tr>
<tr><td><b>目标</b></td><td><code>cs-goal</code></td><td>限定起点/终点，写起点报告后让 AI 自主迭代实现/验证，完成前用 subagent 做功能验收</td></tr>
<tr><td rowspan="8"><b>特性流程</b></td><td><code>cs-feat</code></td><td>新特性子流程入口，按已有产物自动路由到对应阶段</td></tr>
<tr><td><code>cs-feat-design</code></td><td>起草 <code>{slug}-design.md</code> + <code>{slug}-checklist.yaml</code> 作为后续唯一输入</td></tr>
<tr><td><code>cs-feat-design-review</code> ✦Gate</td><td>design 人审前的独立方案审查，支持 Paseo 多 agent，产出 <code>{slug}-design-review.md</code></td></tr>
<tr><td><code>cs-feat-impl</code></td><td>按 checklist 推进写代码；也处理 review-fix 和 qa-fix 回流</td></tr>
<tr><td><code>cs-code-review</code> ✦Gate</td><td>任何流程实现后、commit 前的横切只读代码审查，产出 <code>{slug}-review.md</code>；blocking 时回到 impl</td></tr>
<tr><td><code>cs-feat-qa</code> ✦Gate</td><td>代码审查通过后的本地 QA 验证，产出 <code>{slug}-qa.md</code>；失败时回到 impl 的 qa-fix</td></tr>
<tr><td><code>cs-feat-accept</code></td><td>对照 design 核实现 + review/QA 报告做验收闭环，回写 requirement / roadmap</td></tr>
<tr><td><code>cs-feat-ff</code></td><td>超轻量通道：不写 design、不分阶段，让 AI 直接做</td></tr>
<tr><td rowspan="4"><b>问题流程</b></td><td><code>cs-issue</code></td><td>问题修复子流程入口</td></tr>
<tr><td><code>cs-issue-report</code></td><td>把脑子里的问题落成可复现、可追溯的 report</td></tr>
<tr><td><code>cs-issue-analyze</code></td><td>找根因、评估修复风险、给方案</td></tr>
<tr><td><code>cs-issue-fix</code></td><td>定点修复 + 验证 + 写 fix-note</td></tr>
<tr><td rowspan="2"><b>重构流程</b></td><td><code>cs-refactor</code></td><td>(beta) 重构主流程：scan → design → apply，每步人工放行</td></tr>
<tr><td><code>cs-refactor-ff</code></td><td>(beta) 轻量重构通道：识别 1-3 条低风险优化，一次确认，原地改</td></tr>
<tr><td><b>审计</b></td><td><code>cs-audit</code></td><td>主动扫描代码：bug 隐患 / 安全漏洞 / 性能问题 / 架构偏离，产出批量发现清单</td></tr>
<tr><td rowspan="2"><b>知识沉淀</b></td><td><code>cs-keep</code></td><td>坑点 / 技巧 / 决策 / 调研沉淀到 <code>compound/</code>，纯 markdown，grep 检索</td></tr>
<tr><td><code>cs-note</code></td><td>碎片化项目约定（编译 flag / 路径陷阱 / 命令别名）追加到 <code>attention.md</code></td></tr>
<tr><td><b>文档整理</b></td><td><code>cs-docs-neat</code></td><td>阶段/里程碑收尾时同步 <code>.codestable/</code>、README/docs、<code>CLAUDE.md</code> / <code>AGENTS.md</code> 和 agent 记忆，防止文档与代码脱节</td></tr>
<tr><td rowspan="2"><b>对外文档</b></td><td><code>cs-doc-tutorial</code></td><td>对外的开发者指南 / 用户指南（任务导向，怎么用 X 做 Y）</td></tr>
<tr><td><code>cs-doc-api</code></td><td>从源码反推的 API 参考（逐条目，给读者查零件）</td></tr>
</table>

完整技能目录见 [SKILL_CATALOG.md](./SKILL_CATALOG.md)。日常不知道用哪个时直接调用 `/cs`，它会按诉求路由到对应技能。

---

## 工作流示意

CodeStable 的技能不是一条线性流水，而是**分层 + 事件驱动**的：根入口路由、onboard、长效档案、roadmap 规划、feature / issue / refactor 执行流，以及横切的知识沉淀。

```text
═══════════════════════════════════════════════════════════════════════
 根入口 · 路由                              （任何时刻都可以调用）
───────────────────────────────────────────────────────────────────────
   cs ──▶ 介绍体系 / 把开放式诉求路由到下面任一具体子技能
          （本身不做事，只做分诊和提示）
═══════════════════════════════════════════════════════════════════════
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        （未接入）        （已接入）      （想了解体系）
         走阶段 0       直达 1~4 层 / 横切    给速读
              │
              ▼
═══════════════════════════════════════════════════════════════════════
 阶段 0 · 接入                                  （只在新项目跑一次）
───────────────────────────────────────────────────────────────────────
   cs-onboard ──▶ 生成 .codestable/ 骨架 + 释放 reference/、tools/
                  可选：释放 codestable-ai-branch-guard hook（强制走 worktree）
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 1 层 · 长效档案（"系统现在长什么样"，只记现状）
───────────────────────────────────────────────────────────────────────
   cs-req     ──▶ .codestable/requirements/{slug}.md      能力愿景
   cs-domain  ──▶ .codestable/requirements/CONTEXT.md     领域术语
                  .codestable/requirements/adrs/NNN-*.md  架构决策（守门 3 判据）
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 2 层 · 规划（"接下来打算怎么做这块大需求"，大需求才需要）
───────────────────────────────────────────────────────────────────────
   cs-roadmap ──▶ .codestable/roadmap/{slug}/
                    ① 概设       —— 拆成哪几个模块 / 组件
                    ② 架构层详设 —— 接口契约 / 共享协议
                    ③ 子 feature —— 多条可执行的 feature 清单

   cs-roadmap-review ✦Gate ──▶ 独立规划审查 → {slug}-roadmap-review.md
                                支持 Paseo 多 agent；不通过不能推进实现

   cs-roadmap-impl-goal ──▶ 为每个子 feature 完成 design/checklist/design-review
                             → 输出可直接粘贴的 /goal 指令
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 讨论入口（可选 · 想法模糊时进入，做分诊后路由到下游）
───────────────────────────────────────────────────────────────────────
                          ┌── case 1 已经够清楚 ──▶ cs-feat-design
   cs-brainstorm ────────▶┼── case 2 小需求方向定 ─▶ feature 流（落 brainstorm.md）
                          └── case 3 大需求只有一个词 ─▶ cs-roadmap
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 3 层 · 执行流程（按事件类型选一条进入）
───────────────────────────────────────────────────────────────────────

  ▸ 事件：新增能力                                          ┌──────────────┐
                                                           │  features/   │
       cs-feat-design                                      │  YYYY-MM-DD- │
           │                                               │  {slug}/     │
           ▼                                               │              │
       cs-feat-design-review ✦Gate ── 不通过回 design      │ -design.md   │
           │ 通过                                          │ -checklist.  │
           ▼                                               │  yaml        │
       cs-feat-impl                                        │ -review.md   │
           │                                               │ -qa.md       │
           ▼                                               │ -acceptance  │
       cs-code-review ✦Gate ────── blocking 回 impl        │  .md         │
           │ 通过                                          └──────────────┘
           ▼
       cs-feat-qa ✦Gate ────────── 失败回 impl
           │ 通过
           ▼
       cs-feat-accept

       cs-feat-ff ──(轻量直通车，跳过 design/gate，直接 impl → review)──▶

  ▸ 事件：修复缺陷                                          ┌──────────────┐
       cs-issue-report ─▶ cs-issue-analyze ─▶ cs-issue-fix │  issues/     │
                                              ─▶ cs-code-review ✦Gate      │
                                                           └──────────────┘

  ▸ 事件：代码腐化（beta）                                   ┌──────────────┐
       cs-refactor / cs-refactor-ff ─▶ cs-code-review ✦Gate│  refactors/  │
                                                           └──────────────┘

  ▸ 事件：目标驱动                                          ┌──────────────┐
       cs-goal ──▶ grill 起点报告 ─▶ 自主 impl/验证/迭代    │  goals/      │
                   ─▶ subagent 功能验收                     └──────────────┘
═══════════════════════════════════════════════════════════════════════
                              │
          ┌───────────────────┴───────────────────┐
          ▼ 任意阶段觉得"这个值得记下来"都能触发    ▼ 阶段/里程碑结束触发
═══════════════════════════════════════════════════════════════════════
 横切层 · 知识沉淀 & 文档整理
───────────────────────────────────────────────────────────────────────
   cs-keep  ──▶ .codestable/compound/YYYY-MM-DD-{slug}.md
                 纯 markdown，无 frontmatter，grep 检索
                 下一次 cs-feat-design / cs-issue-analyze 会回头 grep 复用

   cs-note  ──▶ .codestable/attention.md（碎片约定：flag / 路径 / 别名）

   cs-docs-neat ──▶ 同步 .codestable/、README/docs、CLAUDE.md / AGENTS.md
                     防止文档与代码脱节
═══════════════════════════════════════════════════════════════════════
```

**怎么读这张图：**

- **纵向是层次**，不是严格的时间顺序——长效档案层会反复被刷新，规划层只在大需求时进入。
- **✦Gate 是显式阻断点**：design-review / code-review / qa 三道 Gate 各自产出报告，有 blocking 发现时流程不能向前，必须回到对应 impl 修复后重新过 Gate。
- **第 3 层是事件入口**：来了新需求走 feature 流，发现 bug 走 issue 流，发现腐化走 refactor 流，目标驱动走 goal 流。
- **横切层是飞轮**：任何流程跑完发现"这事值得记下来"都可以触发 `cs-keep` 沉淀，沉淀的产物又会被下一次同类工作读到；`cs-docs-neat` 在里程碑收尾时统一整理文档防止漂移。

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
│   ├── roadmap/                           # 路线图（"接下来打算怎么走"）
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
│   │       ├── {slug}-design.md           # 方案（cs-feat-design）
│   │       ├── {slug}-checklist.yaml      # 推进清单（impl 跑、accept 回写）
│   │       ├── {slug}-design-review.md    # 人审前方案审查
│   │       ├── {slug}-review.md           # 实现后代码审查
│   │       ├── {slug}-qa.md               # 代码审查后 QA gate
│   │       └── {slug}-acceptance.md       # 验收报告（cs-feat-accept）
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
- `reference/` 是 `cs-onboard` 从技能包复制过来的；要改共享口径，改 `plugins/codestable/skills/cs-onboard/reference/` 模板，新项目 onboard 自动带上新版。

### 硬约束

> Skill 是独立安装单元，运行时**每个 skill 只能看到自己包内的文件**。A 技能的 SKILL.md 里写 `B-skill/reference/xxx.md` 这种引用在运行时**根本读不到**。
>
> 跨 skill 共享的参考文档必须走"工作项目"这一层：由 `cs-onboard` 从技能包复制到项目的 `.codestable/reference/`，其他 skill 用项目相对路径读取。

要改共享口径，改 `plugins/codestable/skills/cs-onboard/reference/` 下的模板，新项目 onboard 时带上新版本。

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
