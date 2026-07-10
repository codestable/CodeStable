<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

严肃工程不止于"用 AI 写代码"，更在于**用工程方法约束 AI 本身**：skill 不靠感觉写、靠可复现实验证明与迭代——见 [技能怎么迭代：工程化的 build → evaluate 闭环](#技能怎么迭代工程化的-build--evaluate-闭环)。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-32-6366F1?style=flat-square" alt="CodeStable Skills"/>
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

如果旧安装器没有记录来源，重新执行上面的 `npx skills@latest add liuzhengdongfortest/CodeStable` 安装命令即可。升级时应更新完整 CodeStable 插件，不要只替换根 `cs` skill；runtime 刷新还需要同版本的 `cs-onboard` 及其工具。全局插件升级后，建议在每个已接入项目中显式执行 `/cs-onboard --mode refresh-runtime`，立即刷新并核验 repo-local runtime。即使不手动执行，下一次 CodeStable preflight 也会比较 `.codestable/runtime-manifest.json` 与当前插件版本，在 manifest 缺失、版本不匹配或 runtime capability 缺失且受管路径干净时自动刷新；它不会在后台扫描所有仓库。遇到 `managed-paths-dirty`、未接入或骨架不完整时会停下提示，不会强制覆盖。

只需要一键，开始工作：

```bash
/cs-onboard
```

之后日常使用时，不知道该用哪个技能就喊根入口：

```bash
/cs
```

`cs` 会先判断你要执行、咨询还是了解体系：行动请求同轮直转，咨询请求只给建议；信息不足时只问一个聚焦问题。

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

---

## 技能总览

### 推荐主入口

| 分组 | 技能 | 用途 |
|---|---|---|
| 根入口 | `cs` | 行动请求同轮直转，咨询请求只给建议；介绍体系时不启动下游流程 |
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
| 反馈 | `cs-feedback` | 收集 CodeStable skill 使用问题，自动采集本机历史并准备 GitHub issue |
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

## 工作流与运行时

CodeStable 是分层、事件驱动的：`cs` 先判入口模式，行动请求同轮直转，咨询请求只给建议；`cs-feat` / `cs-issue` / `cs-refactor` 按仓库事实恢复阶段并经过 `cs-code-review`，其中 issue / refactor 在 review、blocking 或用户确认 checkpoint 停下；`cs-epic` 编排 planning、批量子 design 和 goal driver；旧阶段技能只保留为兼容入口。

`cs-onboard` 在项目根生成 `.codestable/`，集中保存 requirements、roadmap、goals、features、issues、refactors、audits、compound、gates 与共享 reference。Python 工具脚本从已安装的 `cs-onboard` skill 包运行，不再复制到每个 repo。

- `requirements/` 保存长期能力、术语和 ADR；`roadmap/` 保存待执行规划。
- feature / issue / refactor 各自按工作项聚合产物；`compound/` 是统一知识沉淀目录。
- 普通 skill 不读取 sibling skill 的深层 reference；共享规则由 `cs-onboard` 释放到 `.codestable/reference/`，兼容入口只转交主入口。

完整工作流、目录树和跨 skill 引用约束见 [WORKFLOW.md](./WORKFLOW.md)。

---

## 设计哲学

CodeStable 与 OMO 做的是**完全相反**的哲学。

- OMO 认为：人只要干预就是失败的信号
- CodeStable 认为：**程序员是软件编码中的在环对象**——可以对黑盒实现不了解，但对整体实现必须有所把控，必要时也可深入

软件架构必须要 **可演进**、**可观测**、**可控制**。

也许这一点在 AI 发展强大以后会变得不再重要，但**当下这样做能让程序员在现状下舒服**——这就是价值所在。

CodeStable 面向真实开发场景，对此进行建模，期望通过一个闭环系统处理开发中常见的问题。**现有大部分框架围绕 AI 建模，而不是围绕人。** 我认为这些框架的作者驱动 AI 的能力很强，但绝对不是严肃软件的开发者——因为缺少对软件开发中需求和设计的基础组织能力，缺乏对代码实现的尊重。

---

## 技能怎么迭代：工程化的 build → evaluate 闭环

CodeStable 的 skill 不靠"感觉写得更清楚了"来演进，而是**用可复现的实验来证明和优化**。这套方法把"prompt 工程"变成了"有度量的软件工程"。

**两个配套工具（仓库内，不随插件交付）：**

- `build-cs-skill`：skill 的编写协议（prompt-as-code）——把每个 skill 写成"可执行契约"：`## Spec` 状态机作为唯一的路由真相，frontmatter `contracts` 锚定行为不变量，散文降到最少。
- `eval-cs-skill`：skill 的评测引擎——把 skill 的关键决策做成 **decision fixtures**（给定仓库状态 → 期望的下一步），让真实模型跨供应商（Claude / GPT）多次作答，用程序机械判分（`[measured]`），而不是靠人或裁判打分。

**闭环：** `编写 → 评测 → 定位失败 → 优化 → 复评 → 结论回写方法论`。

一次真实成果（2026-07，7 个主入口 skill × 3 模型 × 每题 3 次，见 `experiments/*/results.md`）：把 skill 从"规则散落在文档里"重写成"`Spec` 作为唯一的 prompt 路由真相"后，历史 campaign 的路由决策正确率**从均值 0.807 提升到 0.975**；且用数据否定了一个直觉误区——"新旧两种写法并排放"反而有害（某 skill 上比不改还低）。这些量化结论已回写进 `build-cs-skill` 的 authoring 规则，指导后续所有 skill 的编写。后续状态 schema / fixtures 变化须重新测量，不沿用旧 artifacts 为当前 HEAD 背书。

**再进一层：结果层评测（从"路由对不对"到"活干得好不好"）**。用**种子仓库**（自建、零训练污染、含演进历史与真实"做旧"）+ **隐藏验收测试**（模型不可见，跑完机械判分）+ **真 agent 端到端跑**，让 `cs-issue` / `cs-feat` 的产出被测试判定，并对照"有 skill vs 裸 agent"回答 skill 值不值得存在。约 90 次真实全流程后的**诚实结论**（方案与数据见 `docs/cs-skill-e2e-eval-plan.md`、`experiments/*-e2e-*/results.md`）：

- **修复/实现能力对现代模型已是天花板**——协同根因、症状误导类 bug，连小模型都能一次修对；skill 的可测价值**不在"帮模型把活干对"**。
- **真实增益在过程契约**：有 skill 的组稳定产出 fix-note / design 等可追溯产物，裸 agent 零产物——买到的是组织记忆和可复核性，代价约 +20~30% token。
- **design 阶段对弱模型有方向性增益**（隐含需求覆盖），与路由层"增益集中在非顶级模型"同构。

**生产反馈也接进同一个闭环**：一次真实使用中发现 `cs-feat` 在 review 第二轮由主 agent 本地自审、没派独立审查。分诊定位为主入口缺 P1 约束 + 规则没点名"每一轮"，修复后固化成回归 fixture（模型提及独立 reviewer：修复前 1/9 → 后 9/9）——**生产偶发变成机械护栏**。

> 认知诚实是这套体系可信度的来源：每次"skill 好像有问题"，分诊纪律都先排查评测自己的缺陷（题目偏差、环境缺失、判分口径）——反复发现问题多在评测侧，skill 与模型被证明是讲道理的。所有数值带 `[measured]/[soft]/[underpowered]`，假设先于实验冻结注册。

---

## Roadmap

CodeStable 会根据模型能力的发展进行调整。如果未来某个模型做到某个模块的稳定产出，那么这个模块就可以删除。

- [x] 简化 cs skills 体系：核心保留 `cs-feat` / `cs-epic` / `cs-issue` 等主入口，兼容入口收薄
- [x] 端到端测评 · 基础路由评测：decision fixtures + 跨模型机械判分，[measured] 证明重构增益
- [x] 端到端测评 · 效果评测：种子仓库 + 隐藏验收测试 + 真 agent 对照裸 agent，`cs-issue`/`cs-feat` 已跑，诚实测出能力边界与过程契约价值
- [ ] 效果评测扩容：cs-epic 多子 feature 端到端；design 对弱模型增益补统计功效
- [ ] 代码重构流程需要强化（`cs-refactor` 还在 beta）
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
