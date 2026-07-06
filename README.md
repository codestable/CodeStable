<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-16-6366F1?style=flat-square" alt="Skills"/>  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## 安装

Codex plugin marketplace：

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable
codex plugin add codestable-lite@codestable-lite
```

如果 `codestable-lite` 还没有合到默认分支，Codex 可以直接指定分支：

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable --ref codestable-lite
codex plugin add codestable-lite@codestable-lite
```

本地开发测试也可以直接加本地 marketplace：

```bash
codex plugin marketplace add D:\playground\CodeStable
codex plugin add codestable-lite@codestable-lite
```

Claude plugin marketplace：

```text
/plugin marketplace add liuzhengdongfortest/CodeStable
/plugin install codestable-lite@codestable-lite
```

注意：Claude 远程 marketplace 会从 GitHub 仓库默认分支读取 `.claude-plugin/marketplace.json`。如果 `codestable-lite` 还只在非默认分支上，先用本地路径测试：

```bash
git clone -b codestable-lite git@github.com:liuzhengdongfortest/CodeStable.git CodeStable-LITE
```

```text
/plugin marketplace add ./CodeStable-LITE
/plugin install codestable-lite@codestable-lite
```

也可以用 skills CLI：

```bash
npx skills@latest add liuzhengdongfortest/CodeStable
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

CodeStable 插件只打包 `plugins/codestable-lite/skills/` 下的 `cs` / `cs-*` skills；仓库根目录不再保留独立 skill 目录。版本号统一记录在 `VERSION`，发布说明写入 `CHANGELOG.md`。

## 升级

发布新版本后，先看 `CHANGELOG.md` 确认版本变化，再按你的安装入口刷新。

正式发布给 Claude 用户前，必须把 `.claude-plugin/marketplace.json`、`plugins/codestable-lite/` 和 `VERSION` 推到仓库默认分支，或改用一个默认分支就是 LITE 的独立仓库。

Codex plugin marketplace：

```bash
codex plugin marketplace upgrade codestable-lite
codex plugin add codestable-lite@codestable-lite
```

Claude plugin marketplace：

```text
/plugin marketplace update
/plugin update codestable-lite@codestable-lite
```

skills CLI：

```bash
npx skills@latest update
```

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
<tr><td><b>核心实体</b></td><td>Agent / Role / Team</td><td>project spec · epic spec · issues</td></tr>
<tr><td><b>主线问题</b></td><td>Agent 之间怎么分工、传递、协调？</td><td>软件的当前真相、变更线和可关闭事项怎么被组织、推进、沉淀？</td></tr>
<tr><td><b>状态存在哪</b></td><td>Agent 的 session / 消息总线 / 队列</td><td><code>.cs/</code> 文件树（人和 AI 都能读）</td></tr>
<tr><td><b>解决的痛点</b></td><td>单 Agent 能力不够，需要协同放大</td><td>软件复杂度膨胀撑破上下文、隐知识丢失、需求漂移</td></tr>
<tr><td><b>对人的定位</b></td><td>人少介入越好，理想是全自动</td><td>人在环 —— 程序员对整体把控负责，AI 是高效的执行体</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)


**这两个方向没有谁对谁错。**

如果你的任务是"用 AI 跑一个端到端的自动化产线"、"让多个 Agent 互相讨论方案"，Agent 编排派会更顺手。

如果你的任务是"维护一个会跨年迭代的严肃软件"、"让今天写下的需求和决策三个月后还能被准确召回"——那 CodeStable 这套以软件要素为中心的建模会更合适。

我做 CodeStable 是因为我相信：**软件工程的混乱本质上不是 Agent 不够强，而是要素没被组织好**。Agent 再强，也写不了一个把需求、取舍、历史决策全丢失的项目。

---

## 设计：project spec + epic spec + issues

早期 CodeStable 把开发拆成 6 个实体、3 条流水线。继续收敛后，核心变成三件事：项目主线真相、大需求变更线、可关闭执行片段。

### project spec —— 项目主线真相

project spec 放在 `.cs/spec/`。它面向第一次进入项目的开发者：这个项目是什么、往哪走、需求怎么细化、架构怎么细化、统一语言在哪里。它是树，不是二级目录；每一层 `index.md` 都要先建立方向感，再指向子文档。

统一语言放在离它生效范围最近的入口文档里，不另起一套 domain 目录。spec 不记流水账，只写当前为什么这样设计、哪些边界成立、哪些取舍被确认。

### epic spec —— 大需求变更线

大需求放在 `.cs/epics/YYYY/MM/DD/{短语}/`。一个 epic 目录包含 `index.md`、`spec.md`、`plan.md`：导读、当前规格和架构考量、本轮可计划范围。实现中规格补充、修改或推翻，都回到同一个 epic spec，而不是新建流水 `changes.md`。

epic 下的 issue 关闭时，先回写 epic spec；等人确认整个 epic 完成，再由 AI 把毕业结论合并回 project spec。

### issues —— 可关闭执行片段

小 bug、小功能、局部 chore 不必进 epic，可以直接成为独立 issue。大需求才进入 epic，并从 epic spec 分批切 issue。issue 只承载一次可验证变更，不负责解释整个需求世界。

关闭规则很简单：独立 issue 直接回写 project spec；探索型 issue 经过人确认后把 issue 内文档合并进 project spec；epic issue 先回写 epic spec；epic 人工关闭后再合并回 project spec。

---

## 技能总览

<table>
<tr><th>分组</th><th>技能</th><th>用途</th></tr>
<tr><td><b>根入口</b></td><td><code>cs</code></td><td>统一入口——介绍体系 + 把开放式诉求路由到正确的 cs-* 子技能。不知道用哪个就喊它</td></tr>
<tr><td><b>接入</b></td><td><code>cs-onboard</code></td><td>把 CodeStable 接入仓库：创建或补齐 <code>.cs/</code> 工作区和基础实体目录</td></tr>
<tr><td><b>讨论入口</b></td><td><code>cs-talk</code></td><td>想法模糊或信息缺失时的讨论 + 整理：先查仓库上下文，聊清楚后写入 <code>talks/</code></td></tr>
<tr><td><b>规格入口</b></td><td><code>cs-spec</code></td><td>维护 project spec 或 epic spec：需求、架构考量、统一语言、本轮可计划范围和未确认问题</td></tr>
<tr><td><b>投诉入口</b></td><td><code>cs-complain</code></td><td>行为不符合预期时，建 bug issue，建立反馈回路，诊断根因，修复验证并回写</td></tr>
<tr><td><b>计划入口</b></td><td><code>cs-plan</code></td><td>读取 <code>talks/</code> 或 epic spec 的本轮可计划范围，先给计划草案；用户确认后生成独立 issue、新 epic 或 epic issue</td></tr>
<tr><td><b>设计入口</b></td><td><code>cs-design</code></td><td>面向单个 issue 做教程式实现设计，写回功能分工、请求/数据流、设计侧重点、边界、改动路线和验证；需要详细测试策略时也在这里讨论</td></tr>
<tr><td><b>执行入口</b></td><td><code>cs-do</code></td><td>按 issue 的实现设计写代码、验证，并回写执行记录</td></tr>
<tr><td><b>关闭入口</b></td><td><code>cs-close</code></td><td>关闭 issue 或 epic，按归属沉淀到 project spec / epic spec；git 仓库里提交相关代码和 .cs 回写</td></tr>
<tr><td><b>系统理解</b></td><td><code>cs-spec-explore</code></td><td>把 project spec 缺口变成探索型 issue，在 issue 内写可讨论文档，确认关闭后再合并主线</td></tr>
<tr><td rowspan="2"><b>辅助资料</b></td><td><code>cs-note</code></td><td>坑点 / 技巧 / 调研 / 命令陷阱等写入 <code>notes/</code>，一两行启动必读事实写入 <code>facts.md</code></td></tr>
<tr><td><code>cs-maketools</code></td><td>人带 AI 跑通未知流程，沉淀 notes、facts 引用和可选 tools</td></tr>
<tr><td rowspan="4"><b>原则</b></td><td><code>cs-how-codedesign</code></td><td>设计模块接口和能力归属时，把模块做深，把接缝放在真正会变化的位置</td></tr>
<tr><td><code>cs-how-debug</code></td><td>先复现和收集证据，解释触发到症状的因果链，再做最小修复</td></tr>
<tr><td><code>cs-how-docs</code></td><td>把 project spec、epic spec、探索型 issue、notes、README 等组织成可阅读的知识空间，而不是平铺内容</td></tr>
<tr><td><code>cs-how-great-skills</code></td><td>写新技能或审视旧技能时，判断背景、原则和应用场景是否清楚</td></tr>
</table>

---

## 工作流示意

CodeStable 不是一条线性流水，而是**project spec + epic spec + issues** 的循环：

```
═══════════════════════════════════════════════════════════════
 根入口 · 路由                            （任何时刻都可调用）
   cs ──▶ 介绍体系 / 把开放式诉求路由到下面的子技能
═══════════════════════════════════════════════════════════════
                          │
        ┌─────────────────┼─────────────────┐
   （未接入）          （想法模糊）        （spec 需要更新）       （已接入）
   cs-onboard         cs-talk ─────┐      cs-spec ─────┐      cs-plan ─▶ cs-design ─▶ cs-do ─▶ cs-close
   搭骨架              查上下文 + talks│      project/epic│      草案确认后生成事项 → 设计 issue → 执行验证 → 按归属沉淀
                                  └───────────────┴────▶ 独立 issue / epic / epic issue
                       cs-complain ─▶ 行为跑偏时完成 bug 诊断修复闭环
═══════════════════════════════════════════════════════════════
 spec · 当前真相和变更线               （.cs/spec/ 和 .cs/epics/）
───────────────────────────────────────────────────────────────
   project spec ─▶ 项目是什么 / 往哪走 / 能力地图 / 架构地图 / 统一语言 / 阅读路径
   epic spec    ─▶ 大需求改变什么 / 为什么这样设计 / 本轮可计划范围 / 未确认问题
   cs-spec      ─▶ 维护 project spec 或 epic spec；写考量，不写流水 changes
   cs-plan      ─▶ 从 talks 或 epic spec 先给计划草案；确认后落成独立 issue / 新 epic / 本轮 epic issue
═══════════════════════════════════════════════════════════════
 issues · 可关闭执行片段               （.cs/issues/）
───────────────────────────────────────────────────────────────
   cs-complain ─▶ 行为不符合预期时，反馈回路 → 诊断 → 修复验证 → 回写 bug issue
   cs-design ──▶ 针对单个 issue 做实现设计（功能分工 / 请求数据流 / 设计侧重点 / 边界 / 改动路线 / 验证；需要时含详细测试策略）
   cs-do     ──▶ 按 issue 写代码、验证、回写执行记录
   cs-close  ──▶ 独立 issue → project spec；epic issue → epic spec；epic 关闭 → project spec
   cs-spec-explore ─▶ 探索型 issue：issue 内文档 → 用户确认 close → project spec
═══════════════════════════════════════════════════════════════
            ▼ 任意时刻"这个值得记下来" ▼
 辅助资料 · 知识沉淀（复利工程）
   cs-note ──▶ .cs/notes/ 或 .cs/facts.md
   cs-maketools ─▶ 人带 AI 跑通未知流程 → notes + facts 引用 + 可选 tools
═══════════════════════════════════════════════════════════════
```

**怎么读这张图：**

- **project spec 是主线，epic spec 是变更线**——大需求过程里的变化先留在 epic，毕业后再合主线
- **issue 可以独立，也可以隶属 epic**：小 bug/小功能直接 issue，大需求从 epic spec 分批切 issue
- **辅助资料是飞轮**：任何事项跑完发现"这事值得记下来"都能触发沉淀，沉淀又被下一次同类工作读到——这是 CodeStable "复利"的物理实现

---

## 运行时结构

`/cs-onboard` 跑完后，会在你的项目根下生成 `.cs/`——所有本地产物的聚合根，也是各子技能运行时唯一会读写的工作区。

```
你的项目/
├── .cs/
│   ├── facts.md              # 启动必读事实
│   ├── talks/                # 讨论整理（cs-talk，lazy）
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── spec/                 # project spec：项目主线真相（cs-spec）
│   │       ├── index.md
│   │       └── ...           # 按阅读路径递归拆分，每层可有自己的 index.md
│   │
│   ├── issues/               # 可关闭事项，按创建日期分片，含 feature/bug/chore/explore
│   │   └── YYYY/MM/DD/{status}-{短语}.md
│   ├── epics/                # 大需求变更线
│   │   └── YYYY/MM/DD/{短语}/
│   │       ├── index.md      # epic 导读、状态和 issue 列表
│   │       ├── spec.md       # epic 当前需求、架构考量、统一语言
│   │       └── plan.md       # 本轮可计划范围和 issue 列表
│   │
│   ├── notes/                # 知识笔记，纯 markdown，全文检索（cs-note）
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # 跨工作流共享脚本（cs-maketools 按需沉淀）
│
└── （事项默认留在 .cs/，方便人和 AI 一起读写）
```

**几条要点：**

- 所有本地产物聚在 `.cs/` 下，"上次那个变更当时怎么搞的"三秒能找到
- `spec/` 是 project spec，面向第一次进入项目的开发者组织主线需求、架构考量、统一语言和阅读路径
- `epics/` 是大需求变更线，目录内的 epic spec 承载过程中的补充、修改和推翻，关闭 epic 后再合并回 project spec
- `issues/` 可以承载探索型任务；当前结论、当前理解和证据索引留在 issue 中讨论，用户确认关闭后再把毕业结论合并进 project spec
- talks / notes 默认写入 `YYYY/MM/DD/{短语}.md` 日期分片，epics 写入 `YYYY/MM/DD/{短语}/` 工作区，issues 写入 `YYYY/MM/DD/{status}-{短语}.md`；查找时递归搜索对应目录
- `notes/` 是知识笔记，纯 markdown 无 frontmatter，靠全文检索——好写好搜；日常“记下来”统一走 `cs-note`
- `cs-maketools` 会把人带路跑通的未知流程写入 `notes/`，在 `facts.md` 加引用，必要时再沉淀到 `tools/`
- 单个 Markdown 超过 150 行时，优先按渐进式披露拆到同目录资源，不为降行数硬压缩入口文件

### 硬约束

> Skill 是独立安装单元，运行时**每个 skill 只能看到自己包内的文件**。A 技能的 SKILL.md 里写 `B-skill/reference/xxx.md` 这种引用在运行时**根本读不到**。
>
> 跨 skill 的体系口径不要靠互相引用文件解决。`cs` 只做导览；行动技能要在本技能内说明自己的产物契约和边界。项目稳定知识沉淀到 `.cs/spec/`、`.cs/notes/`、`.cs/facts.md`。

各 cs 行动技能开始前都先复用当前上下文：`facts.md`、project spec、epic spec 或目标 issue 等已经读过且无修改迹象，就不要机械重读；没读过、疑似变化、需要精确引用/写回，或需要新增局部时才补读。目标 issue、准备写回的 `.cs` 文件和代码文件，写入前必须确认当前版本。

要改体系口径，更新相关技能自己的说明和模板；项目自己的稳定需求和操作经验，放回 `.cs/` 对应实体。

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

- [ ] 本地事项流打磨
- [ ] 规格澄清到 plan 的衔接继续打磨
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
