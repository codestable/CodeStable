<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-13-6366F1?style=flat-square" alt="Skills"/>  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## 安装

```bash
npx skills add https://github.com/liuzhengdongfortest/CodeStable
```

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

> **编排的不是 Agent，而是软件本身的生命周期。** 围绕的实体是**构成软件的要素**——每一个变更、每一条取舍、每一个被否决的方案、每一条历史里留下来的约束。

<table>
<tr><th></th><th>Agent 编排派</th><th>CodeStable</th></tr>
<tr><td><b>核心实体</b></td><td>Agent / Role / Team</td><td>变更轴（issue / epic）· 现状轴（context）</td></tr>
<tr><td><b>主线问题</b></td><td>Agent 之间怎么分工、传递、协调？</td><td>软件的需求、约束、取舍怎么被记下来、被检索、被复用？</td></tr>
<tr><td><b>状态存在哪</b></td><td>Agent 的 session / 消息总线 / 队列</td><td><code>.codestable/</code> 文件树 + 可选 GitHub issue（人和 AI 都能读）</td></tr>
<tr><td><b>解决的痛点</b></td><td>单 Agent 能力不够，需要协同放大</td><td>软件复杂度膨胀撑破上下文、隐知识丢失、需求漂移</td></tr>
<tr><td><b>对人的定位</b></td><td>人少介入越好，理想是全自动</td><td>人在环 —— 程序员对整体把控负责，AI 是高效的执行体</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)


**这两个方向没有谁对谁错。**

如果你的任务是"用 AI 跑一个端到端的自动化产线"、"让多个 Agent 互相讨论方案"，Agent 编排派会更顺手。

如果你的任务是"维护一个会跨年迭代的严肃软件"、"让今天写下的需求和决策三个月后还能被准确召回"——那 CodeStable 这套以软件要素为中心的建模会更合适。

我做 CodeStable 是因为我相信：**软件工程的混乱本质上不是 Agent 不够强，而是要素没被组织好**。Agent 再强，也写不了一个把需求、取舍、历史决策全丢失的项目。

---

## 设计：两根正交的轴

早期 CodeStable 把开发拆成 6 个实体、3 条流水线。用下来发现实体太多、流程太硬——feature / issue / refactor 其实是同一种东西（可关闭的变更），requirements / roadmap / architecture 也都在描述同一件事（现状）。于是收敛成**两根正交的轴**。

### 变更轴 —— 要做、做完会关闭的事

bug、重构、小功能、大需求，本质都是"一件要做、做完就关闭的变更"，只是大小和类型不同。它们落在 GitHub issue 或本地（onboard 时选一种）。

- **`cs-issue`** —— 一件可关闭的变更，tag 分 `bug` / `refactor` / `feature` / `chore`。闭环：记清楚 → 定位 → 改 + 验证 → 关闭回写
- **`cs-epic`** —— 大到塞不进单条 issue 的：先定架构（模块拆分 + 接口契约），再拆成带依赖 DAG 的子 issue
- **`cs-audit`** —— 主动扫描发现器 + 对账 context，产出 triage 清单，选中的升级成 issue

### 现状轴 —— 现在是什么、为什么这样

这是 CodeStable 的北极星：**读它即知代码的需求与取舍**。它只记代码本身展示不出来的东西——为什么这样、为什么不那样、被否决的方案、哪根轴会变。代码讲"做了什么"，context 补"为什么"，合起来才是完整图景，谁都不重复谁。

- **`cs-context`** —— 领域词汇表 + 取舍说明（happy path / 边界条件 / 为什么需要灵活性）。不引用代码位置、不记历史叙事

### 两轴怎么咬合

变更轴是增量，现状轴是这些增量积分出的当前真相。**一条 issue / epic 关闭时，把毕业的取舍回写 context。** context 不记历史（那在关闭的 issue 里），issue 不长期描述现状。写代码的纪律（`cs-code`）和知识沉淀（`cs-keep`）横切两轴。

---

## 技能总览

<table>
<tr><th>分组</th><th>技能</th><th>用途</th></tr>
<tr><td><b>根入口</b></td><td><code>cs</code></td><td>统一入口——介绍体系 + 把开放式诉求路由到正确的 cs-* 子技能。不知道用哪个就喊它</td></tr>
<tr><td><b>接入</b></td><td><code>cs-onboard</code></td><td>把 CodeStable 接入仓库：搭骨架 + 分发共享资产 + 选变更轴载体（GitHub / 本地）+ 归旧档</td></tr>
<tr><td rowspan="4"><b>变更轴</b></td><td><code>cs-issue</code></td><td>一件可关闭的变更：bug / 重构 / 小功能 / 杂务，tag 分类型</td></tr>
<tr><td><code>cs-epic</code></td><td>大需求：先定架构（模块拆分 + 接口契约），再拆成带依赖的子 issue</td></tr>
<tr><td><code>cs-audit</code></td><td>主动扫描发现 + 对账 context，产出候选变更</td></tr>
<tr><td><code>cs-code</code></td><td>写代码的纪律：只写当前明确要的、漂移那刻停（横切，任何动手都用）</td></tr>
<tr><td><b>现状轴</b></td><td><code>cs-context</code></td><td>领域词汇表 + 取舍说明（happy path / 边界 / 为什么需要灵活性）</td></tr>
<tr><td><b>讨论入口</b></td><td><code>cs-clarify</code></td><td>想法模糊时的讨论 + 分诊：聊清楚后路由到直接写或 cs-epic</td></tr>
<tr><td rowspan="3"><b>横切 & 周边</b></td><td><code>cs-keep</code></td><td>坑点 / 技巧 / 决策 / 调研沉淀到 <code>compound/</code>，纯 markdown，全文检索</td></tr>
<tr><td><code>cs-note</code></td><td>一两行启动必读追加到 <code>attention.md</code></td></tr>
<tr><td><code>cs-convention</code></td><td>维护体系共享口径，分发成 <code>.codestable/convention.md</code></td></tr>
<tr><td rowspan="2"><b>对外文档</b></td><td><code>cs-doc-tutorial</code></td><td>对外的开发者指南 / 用户指南（任务导向，怎么用 X 做 Y）</td></tr>
<tr><td><code>cs-doc-api</code></td><td>从源码反推的 API 参考（逐条目，给读者查零件）</td></tr>
</table>

---

## 工作流示意

CodeStable 不是一条线性流水，而是**两轴 + 事件驱动**的：

```
═══════════════════════════════════════════════════════════════
 根入口 · 路由                            （任何时刻都可调用）
   cs ──▶ 介绍体系 / 把开放式诉求路由到下面的子技能
═══════════════════════════════════════════════════════════════
                          │
        ┌─────────────────┼─────────────────┐
   （未接入）          （想法模糊）        （已接入）
   cs-onboard         cs-clarify           直达两轴
   搭骨架 + 选载体      讨论 + 分诊
═══════════════════════════════════════════════════════════════
 变更轴 · 要做、做完会关闭的事         （GitHub issue 或本地）
───────────────────────────────────────────────────────────────
   cs-issue  ──▶ 一件可关闭的变更（bug / 重构 / 小功能 / 杂务）
   cs-epic   ──▶ 大需求：先定架构 → 拆成带依赖的子 issue
   cs-audit  ──▶ 主动扫描 + 对账 context → 候选 issue
        │   写代码靠 cs-code（漂移那刻停）
        ▼   关闭时把毕业的取舍回写 ▼
═══════════════════════════════════════════════════════════════
 现状轴 · 现在是什么、为什么这样        （.codestable/context/）
───────────────────────────────────────────────────────────────
   cs-context ──▶ 领域词汇表 + 取舍说明
                  （happy path / 边界 / 为什么需要灵活性）
                  北极星：读它即知代码的需求与取舍
═══════════════════════════════════════════════════════════════
            ▼ 任意时刻"这个值得记下来" ▼
 横切 · 知识沉淀（复利工程）
   cs-keep ──▶ .codestable/compound/   纯 markdown，全文检索
   cs-note ──▶ .codestable/attention.md  一两行启动必读
═══════════════════════════════════════════════════════════════
```

**怎么读这张图：**

- **两轴是正交的**，不是时间顺序——变更轴随时开新的，现状轴随变更关闭被刷新
- **变更轴是增量，现状轴是积分**：一条 issue / epic 关闭时把毕业的取舍回写 context
- **横切是飞轮**：任何变更跑完发现"这事值得记下来"都能触发沉淀，沉淀又被下一次同类工作读到——这是 CodeStable "复利"的物理实现

---

## 运行时结构

`/cs-onboard` 跑完后，会在你的项目根下生成 `.codestable/`——所有本地产物的聚合根，也是各子技能运行时唯一会读写的工作区。

```
你的项目/
├── .codestable/
│   ├── attention.md          # 启动必读 + 变更轴载体（github / local）
│   ├── convention.md         # 体系共识（onboard 分发，勿手改）
│   │
│   ├── context/              # 现状轴（cs-context）
│   │   ├── CONTEXT.md        # 领域词汇表（lazy）
│   │   ├── CONTEXT-MAP.md    # 多 context 拓扑入口（仅多 context 项目）
│   │   └── {slug}.md         # 取舍说明，一块一篇
│   │
│   ├── issues/  epics/       # 变更轴——仅 local 载体模式建
│   │   └── YYYY-MM-DD-{slug}/ #（github 模式下 issue/epic 在 GitHub）
│   │
│   ├── compound/             # 知识沉淀，纯 markdown，全文检索（cs-keep）
│   │   └── YYYY-MM-DD-{slug}.md
│   │
│   ├── clarify/              # 大需求澄清记录（cs-clarify，lazy）
│   ├── tools/                # 跨工作流共享脚本（onboard 释放）
│   └── reference/            # 共享参考（onboard 释放）
│       ├── system-overview.md
│       ├── maintainer-notes.md
│       └── tools.md
│
└── （github 载体模式下，变更轴在 GitHub，本地只留 context / compound）
```

**几条要点：**

- 所有本地产物聚在 `.codestable/` 下，"上次那个变更当时怎么搞的"三秒能找到
- `context/` 是**现状轴**（词汇表 + 取舍说明），只描述当前真相、不记历史叙事；历史在关闭的 issue 里
- **变更轴载体二选一**：GitHub issue（用原生可关闭实体）或本地 `issues/ epics/`，onboard 时定，写进 `attention.md`
- `compound/` 是知识沉淀，纯 markdown 无 frontmatter，靠全文检索——好写好搜
- `convention.md` / `reference/` 由 `cs-onboard` 从技能包分发；要改共享口径走 `cs-convention`，新项目 onboard 自动带上新版

### 硬约束

> Skill 是独立安装单元，运行时**每个 skill 只能看到自己包内的文件**。A 技能的 SKILL.md 里写 `B-skill/reference/xxx.md` 这种引用在运行时**根本读不到**。
>
> 跨 skill 共享的口径必须走"工作项目"这一层：源真相在 `cs-convention`（落在 `cs-onboard/reference/convention.md`），由 `cs-onboard` 分发到项目的 `.codestable/convention.md`，其他 skill 用项目相对路径读取。

要改共享口径，走 `cs-convention` 改模板，新项目 onboard 时带上新版本；已有项目重跑 `cs-onboard` 同步。

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

- [ ] 变更轴 GitHub 载体模式打磨（`gh` 集成）
- [ ] `cs-audit` 对账 context 的能力强化
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
