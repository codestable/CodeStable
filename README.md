<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

方法论一句话：**thin harness, thick context**——给强模型写责任，不写步骤；上下文按需检索，不预载。

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

当前 `skills` CLI 的 `add` / `update` 不会自动删除新版 package 已移除的旧 skill，因此从 v1.0.4 升级到 v2.0.0 时，先用第一条命令精确删除 24 个退役入口，再完整安装 v2 的 8 个。CLI 按名称删除，不校验安装来源：命令不会影响其他名称，但如果你用相同名称维护过自定义或第三方 skill，请先备份并从删除列表移除对应名称。以后同一 major 内升级只需重新执行 `add`。如果原来是项目级安装，两条命令都去掉 `-g` 并在项目中执行。项目里的 v1 历史资产（`compound/`、`features/` 等目录与旧工具）原样保留、不需要逐仓库刷新运行时，且继续被 v2 的开工检索覆盖——历史沉淀在升级后仍会被读到。

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

## 设计：thin harness, thick context

核心判断：**模型越强，越该给它写责任，而不是写步骤。** CodeStable 不用状态机、流程 gate 和阶段产物去"防"模型，而是交付 8 个 30–60 行的**薄责任契约**——每个 skill 只说三件事：要达成什么、不可越过什么、如何证明完成。路线交给模型自己找。

规则减薄不等于没有边界。留下来的都是一句话可判定的**硬门槛**：

| 流程 | 入口 | 硬门槛 |
|------|------|--------|
| **特性引入** | `cs-feat` | 高风险设计先落盘 work 文档，由外层主流程创建 reviewer 做独立 review 后再交人确认，不 auto-approve；测试设施可用时测试先行；完成必须附可核验证据 |
| **问题修复** | `cs-issue` | 没有能明确变红的验证不许猜根因；修复完成时变红的验证必须变绿 |
| **代码重构** | `cs-refactor` | 先有能自证行为等价的验证再动代码；发现要改行为立即停下转向 |
| **大需求** | `cs-epic` | 永久 Epic 文档保存全景，临时 work 游标保存执行状态；拆解、范围性变化、fresh reviewer 整体验收后最终接受分别经过三道 owner gate |
| **独立审查** | `cs-review` | 只读叶子执行器，单轮返回发现，不创建子 agent；blocking 未解决不得通过，修复与最多 3 轮复审由外层主流程负责 |

工程判断力不占常驻上下文：模块深度、实现经济性、debug 升级路径这些"怎么做好"的判据放在**按需加载的 references** 里，进入对应场景才读——thin harness 管可靠，thick context 管质量。

### 知识的六个归宿

沉淀的原则是**各归其位、没有档案馆**：

| 归宿 | 承载什么 |
|------|--------|
| `attention.md` | 每次会话必读的项目事实，≤25 条 |
| `lessons/` | 一条一文件的坑、技巧、调研结论；写入必须有可追溯证据，先查重合并 |
| 项目文档 / ADR | 当前事实与结构性决策的 canonical owner——CodeStable 不建平行真相 |
| 永久 Epic 文档 | 长期保存目标、范围、已批准子项、关键决策、交付索引与整体验收 |
| `work/` | 进行中的跨会话任务；Epic work 只作指向永久文档、批准 revision 与执行进度的临时游标 |
| git / PR | 执行历史 |

Epic 优先沿用项目已有的 Epic、RFC 或 initiative 归宿，否则首次需要时才创建 `.codestable/epics/`；`cs-onboard` 不预建空目录。拆解经独立 design review 后由 owner 确认；目标、范围、非目标、验收、子项或重大风险变化时 owner 重新确认；全部子项完成后，由 fresh reviewer 按最新 owner 已批准的标准做终态整体验收，再由 owner 最终接受。终态先补齐永久档案并完成毕业，再删除 Epic work 游标，永久 Epic 文档不删除。

v1 的 `roadmap/`、`features/`、`issues/`、`refactors/`、`goals/`、`compound/`、`audits/`、`brainstorms/` 与 `feedback/` 九个历史知识目录只按任务关键词只读检索并引用来源；不生成、不原地改写、不批量迁移，也不写回。新结论进入永久 Epic、项目文档、ADR 或 `lessons/`。

既有 `.codestable/requirements/` 只有在 `.codestable/attention.md` 明确登记为 canonical requirement 位置时才可维护，否则同样只读。新项目沿用自身文档结构，不默认创建该目录；没有 canonical 归宿时先请 owner 选择并登记到 `attention.md`。

`cs-epic` 承担有价值的目标契约、恢复游标、owner gate 与终态验收；不会恢复 `cs-goal` 入口、goal package、`state.yaml`、逐轮 iteration 报告或 runtime gate。

普通 work 文档完成后**先毕业再删除**：最终报告必须列出毕业清单——哪条结论进了哪个项目文档、沉了哪条 lesson，无可毕业则明说——不列清单不得删；毕业目标位置不存在时给出建议落点等用户拍板，拍板前文档保留。

---

## 技能总览

### 当前 8 个 skill

| 分组 | 技能 | 用途 |
|---|---|---|
| 导航 | `cs` | 明确行动诉求同轮直转对应入口；咨询只推荐；导览不写文件 |
| 接入 | `cs-onboard` | 为仓库创建最小项目记忆骨架 |
| 功能 | `cs-feat` | 实现新功能或功能改造，流程强度与风险相称 |
| 问题 | `cs-issue` | 用红到绿证据修复 bug 或既有行为异常 |
| 重构 | `cs-refactor` | 在行为等价证据下调整结构或性能 |
| 大需求 | `cs-epic` | 拆解、确认并长程推进多个子项；子设计就近内联、高风险才独立落盘 |
| 审查 | `cs-review` | 叶子执行器，单轮完成 diff / design / repo 审计，不再委派 agent |
| 记忆 | `cs-keep` | 沉淀有证据的经验与项目事实，自动判层 |

`cs-code-review` 是 `cs-review` 的别名（只转发，不含独立规则）。完整目录见
[SKILL_CATALOG.md](./SKILL_CATALOG.md)；不知道用哪个时调用 `/cs` 获取推荐。

---

## 工作流与项目记忆

所有入口共用一条执行主线：**理解相关事实 → 行动 → 相称的验证 → 交付结果**。风险每次按当前事实重判，没有持久 lane、没有阶段状态机；普通任务零 CodeStable 产物——diff、测试输出和交付说明就是证据。

沉淀的价值在被读到：负责具体任务的 `cs-feat`、`cs-issue`、`cs-refactor` 与 `cs-epic` 开工前按任务关键词检索 `lessons/`、项目文档与上述 v1 历史目录，命中必须报告来源路径；历史目录只读，不写回。

`cs-onboard` 在项目根生成最小 `.codestable/`：

```text
.codestable/
├── attention.md
├── lessons/
└── work/
```

`.codestable/epics/` 仅在没有现成 Epic 归宿且首次创建 Epic 时按需出现；`.codestable/requirements/` 不属于默认骨架。skill 专属 context/helper 归 owning skill；项目需求、领域模型与 ADR 继续使用项目自己的文档结构，requirements 位置只有经 `attention.md` 显式登记才是可维护的 canonical owner——CodeStable 不建平行真相。

完整工作流与持久化约定见 [WORKFLOW.md](./WORKFLOW.md)。

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

- [x] 简化 cs skills 体系：收敛为 8 个独立 thin-harness skill
- [x] v2 dogfood 闭环运转：同轮直转、毕业清单、work 类型前缀、3 轮复审上限等规则均由真实使用反馈驱动落地
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
