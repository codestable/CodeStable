<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

严肃工程不止于"用 AI 写代码"，更在于**用工程方法约束 AI 本身**：skill 不靠感觉写、靠可复现实验证明与迭代——见 [技能怎么迭代：工程化的 build → evaluate 闭环](#技能怎么迭代工程化的-build--evaluate-闭环)。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-8-6366F1?style=flat-square" alt="CodeStable Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## 安装

Codex plugin marketplace：

```bash
codex plugin marketplace add codestable/CodeStable
codex plugin add codestable@codestable
```

Claude plugin marketplace：

```text
/plugin marketplace add codestable/CodeStable
/plugin install codestable@codestable
```

`skills` CLI：

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable
```

如果你的 `skills` CLI 没有通过 marketplace catalog 发现插件实体，可用深扫兜底：

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable --full-depth
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
npx skills@latest remove \
  cs-audit cs-brainstorm cs-doc-api cs-doc-tutorial cs-docs cs-docs-neat \
  cs-domain cs-feat-accept cs-feat-design cs-feat-design-review cs-feat-ff \
  cs-feat-impl cs-feat-qa cs-feedback cs-goal cs-issue-analyze cs-issue-fix \
  cs-issue-report cs-note cs-refactor-ff cs-req cs-roadmap \
  cs-roadmap-impl-goal cs-roadmap-review \
  -g -y
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

当前 `skills` CLI 的 `add` / `update` 不会自动删除新版 package 已移除的旧 skill，因此从 v1.0.4 升级到 v2.0.0 时，先用第一条命令精确删除 24 个退役入口，再完整安装 v2 的 8 个。CLI 按名称删除，不校验安装来源：命令不会影响其他名称，但如果你用相同名称维护过自定义或第三方 skill，请先备份并从删除列表移除对应名称。以后同一 major 内升级只需重新执行 `add`。如果原来是项目级安装，两条命令都去掉 `-g` 并在项目中执行。项目里的 v1 历史资产原样保留，不需要逐仓库刷新运行时。

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
<tr><td><b>状态存在哪</b></td><td>Agent 的 session / 消息总线 / 队列</td><td>项目文档与 <code>.codestable/</code> 项目记忆（人和 AI 都能读）</td></tr>
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

### 项目记忆

| 实体 | 干什么 |
|------|--------|
| **attention** | 每次会话都要知道的少量项目事实，保持在 25 条以内 |
| **lessons** | 一条一文件的踩坑、技巧和调研结论，靠关键词检索后按需加载 |
| **work** | 跨会话或多人交接的活动任务；普通任务不创建，完成后清理 |
| **项目文档 / ADR** | 需求、领域模型、公开契约与长期技术决策的 canonical owner |

### 流程

| 流程 | 推荐主入口 | 说明 |
|------|------------|------|
| **特性引入** | `cs-feat` | 默认直接理解、实现、验证；遇到高风险契约或真实取舍时先让用户确认 |
| **大需求端到端** | `cs-epic` | 维护一个 work 文档，确认拆解后逐个推进 feature / issue / refactor 子项 |
| **问题修改** | `cs-issue` | 先建立会变红的验证，再修复并证明它变绿 |
| **代码重构** | `cs-refactor` | 先建立等价性证据，分步调整结构并持续验证 |
| **代码审查 / 审计** | `cs-code-review` | 独立只读审查当前 diff，或按指定范围做 audit |
| **知识沉淀** | `cs-keep` | 把有证据的高频事实或可复用经验写入项目记忆 |

高风险改动或用户要求时，执行流调用 `cs-code-review` 做独立审查。文档与 ADR 由拥有该变化的开发任务同步，不再需要独立的阶段 skill。

---

## 技能总览

### 当前 8 个 skill

| 分组 | 技能 | 用途 |
|---|---|---|
| 导航 | `cs` | 明确行动诉求同轮直转对应入口；咨询只推荐；导览不写文件 |
| 接入 | `cs-onboard` | 把 CodeStable 接入新仓库或已有零散文档仓库 |
| 大需求 | `cs-epic` | 拆解、确认并长程推进多个子项 |
| 功能 | `cs-feat` | 实现新功能或功能改造，按风险升级设计确认与 review |
| 问题 | `cs-issue` | 用红到绿证据修复 bug 或既有行为异常 |
| 重构 | `cs-refactor` | 在行为等价证据下调整结构或性能 |
| 审查 | `cs-code-review` | 独立只读 diff review 或按需 audit |
| 记忆 | `cs-keep` | 沉淀有证据的高频事实与可复用经验 |

v1.0.4 的另外 24 个名称已退役且不随 v2 交付，不再安装兼容 shim。映射与升级边界见
[SKILL_CATALOG.md](./SKILL_CATALOG.md)；不知道用哪个时调用 `/cs` 获取推荐。

---

## 工作流与项目记忆

CodeStable v2 用 thin harness 保留责任、硬门槛和完成证据，把项目事实按需加载。`cs` 只做导航；功能、问题与重构入口直接完成工作，高风险或用户要求时再调用独立审查；`cs-epic` 用一个 work 文档维护跨会话全景。

`cs-onboard` 在项目根生成最小 `.codestable/`：

```text
.codestable/
├── attention.md
├── lessons/
└── work/
```

skill 专属 context/helper 归 owning skill；项目需求、领域模型与 ADR 继续使用项目自己的文档结构。v1 历史目录、tool、gate 与 hook 原样保留并可作为知识检索，但 v2 不执行旧 runtime，也不复制或刷新它们。

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

- `build-cs-skill`：skill 的编写协议（prompt-as-code）——用最小 harness 承载责任、上下文选择和硬 gate，阶段方法与项目事实按需加载；行为不变量由直接测试、decision fixtures 或真实 runtime gate 验证。
- `eval-cs-skill`：skill 的评测引擎——把 skill 的关键决策做成 **decision fixtures**（给定仓库状态 → 期望的下一步），让真实模型跨供应商（Claude / GPT）多次作答，用程序机械判分（`[measured]`），而不是靠人或裁判打分。

深层 `references/**/*.md` 只承载按条件加载的领域或阶段上下文；可机械判定的规则进入直接测试或 runtime gate，顶层只保留调用接口和失败语义。新增规则必须通过 `placeRule` 确认唯一 owner 与证据层级。

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

- [x] 简化 cs skills 体系：v2 收敛为 8 个独立 thin-harness skill，退役 24 个旧入口
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
