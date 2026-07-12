<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-1-6366F1?style=flat-square" alt="Skills"/>  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
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

只需要一个入口，先让它接入项目：

```bash
/cs 请在这个项目接入 CodeStable
```

之后讨论需求、维护规格、修 bug、实现 issue、关闭沉淀都使用同一个入口：

```bash
/cs
```

`cs` 会理解当前信息处于 project spec、epic spec 还是 issue 层级，按需读取内部规则并直接执行当前获得授权的工作。

CodeStable 插件只打包 `plugins/codestable-lite/skills/cs/` 这一个 skill；行动规则、设计原则、模板和脚本都在其内部按需加载。版本号统一记录在 `VERSION`，发布说明写入 `CHANGELOG.md`。

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

早期 CodeStable 把开发拆成 6 个实体、3 条流水线。继续收敛后，核心变成三件事：项目主线真相、大需求活规格边界、可关闭执行片段。

### project spec —— 项目主线真相

project spec 放在 `.cs/spec/`。它面向第一次进入项目的开发者：这个项目是什么、往哪走、需求怎么细化、架构怎么细化、统一语言在哪里。它是树，不是二级目录；每一层 `index.md` 都要先建立方向感，再指向子文档。

统一语言放在离它生效范围最近的入口文档里，不另起一套 domain 目录。spec 不记流水账，只写当前为什么这样设计、哪些边界成立、哪些取舍被确认。

### epic spec —— 有边界的活规格

大需求放在 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`。这个 `spec.md` 是 epic 的唯一权威入口，同时承载状态、当前规格、架构考量、推进范围、issue 列表、阻碍、关闭条件和毕业候选。实现中规格补充、修改或推翻，都回到同一个 epic spec，而不是拆出重复的 `index.md`、`plan.md` 或流水 `changes.md`。

Epic 不是计划容器，也不是 project spec 的缩小版。它是一条有边界的演进线：大到值得 review 架构决策和关键抽象，小到能在合理时间内多轮反馈。跨模块、会多轮变化、需要分批 issue 或规格还会持续微变的需求，才需要 epic；小 bug、小功能、局部 chore 直接进独立 issue。

epic 下的 issue 关闭时，先回写 epic spec；等人确认整个 epic 完成，再由 AI 把毕业结论合并回 project spec。

### issues —— 可关闭执行片段

小 bug、小功能、局部 chore 不必进 epic，可以直接成为独立 issue。大需求才进入 epic，并从 epic spec 分批切 issue。issue 只承载一次可验证变更，不负责解释整个需求世界。

关闭规则很简单：独立 issue 直接回写 project spec；探索型 issue 经过人确认后把工作区里的候选文章按 spec 规范合并进 project spec；epic issue 先回写 epic spec；epic 人工关闭后再合并回 project spec。

---

## 技能总览

插件只有一个 `cs` 技能。用户不再选择十几个技能名；`cs` 先判断当前信息属于哪一层，再按需加载内部模式：

| 意图 | `cs` 内部行为 |
|---|---|
| 首次接入 | 创建或补齐 `.cs/` 骨架，不擅自迁移旧需求 |
| 想法模糊、需要规划 | 调查上下文、澄清真问题，确认后形成独立 issue、探索 issue 或 epic |
| 规格变化 | 维护 project spec 或唯一的 epic `spec.md` |
| 行为不符合预期 | 建 bug issue，用反馈回路完成诊断、修复和验证 |
| 明确 issue | 按需要设计、实现、验证；只有用户要求收尾时才关闭和提交 |
| 系统未知 | 在探索 issue 中形成候选文章，确认关闭后毕业到 project spec |
| 值得复用 | 写入 notes、facts 或 tools；未知流程由用户带路跑通 |

内部行动规则和代码设计、debug、文档组织等原则放在 `cs/references/`，只有当前场景需要时才进入上下文。

---

## 结构如何演化

CodeStable 不是一条线性流水，而是**project spec + epic spec + issues** 的循环：

```text
Project Spec ──小而明确的变化──> Issue ──关闭回写──> Project Spec
     │
     └──大而不稳定的变化──> Epic Spec ──分批推进──> Issues
                                  ↑                    │
                                  └──验证与新认知──────┘

Epic 关闭 ──稳定结论毕业──> Project Spec
```

**怎么读这张图：**

- **project spec 是主线，epic spec 是活规格边界**——大需求过程里的变化先留在 epic，毕业后再合主线
- **issue 可以独立，也可以隶属 epic**：小 bug/小功能直接 issue，大需求从 epic spec 分批切 issue
- **辅助资料是飞轮**：任何事项跑完发现"这事值得记下来"都能触发沉淀，沉淀又被下一次同类工作读到——这是 CodeStable "复利"的物理实现

---

## 运行时结构

让 `/cs` 接入项目后，会在项目根生成 `.cs/`——所有本地产物的聚合根，也是统一技能运行时读写的工作区。

```
你的项目/
├── .cs/
│   ├── facts.md              # 启动必读事实
│   ├── talks/                # 讨论整理（确认后才落盘）
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── spec/                 # project spec：项目主线真相
│   │       ├── index.md
│   │       └── ...           # 按阅读路径递归拆分，每层可有自己的 index.md
│   │
│   ├── issues/               # 可关闭事项，按创建日期分片
│   │   ├── YYYY/MM/DD/{status}-{短语}.md   # 普通 issue
│   │   └── YYYY/MM/DD/{status}-{短语}/     # 探索型 issue 工作区
│   ├── epics/                # 大需求活规格边界
│   │   └── YYYY/MM/DD/{短语}/
│   │       └── spec.md       # 唯一权威入口：规格、推进、issues、阻碍和关闭条件
│   │
│   ├── notes/                # 知识笔记，纯 markdown，全文检索
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # 跑通后按需沉淀的共享脚本
│
└── （事项默认留在 .cs/，方便人和 AI 一起读写）
```

**几条要点：**

- 所有本地产物聚在 `.cs/` 下，"上次那个变更当时怎么搞的"三秒能找到
- `spec/` 是 project spec，面向第一次进入项目的开发者组织主线需求、架构考量、统一语言和阅读路径
- `epics/` 是大需求活规格边界，目录内的 epic spec 承载过程中的补充、修改和推翻，关闭 epic 后再合并回 project spec
- `issues/` 可以承载探索型任务；候选文章、用户修正和证据索引留在 issue 工作区中讨论，用户确认关闭后再按 spec 规范合并进 project spec
- talks / notes 默认写入 `YYYY/MM/DD/{短语}.md` 日期分片，epics 写入 `YYYY/MM/DD/{短语}/` 工作区，普通 issues 写入 `YYYY/MM/DD/{status}-{短语}.md`，探索型 issue 写入 `YYYY/MM/DD/{status}-{短语}/` 工作区；查找时递归搜索对应目录
- `notes/` 是知识笔记，纯 markdown 无 frontmatter，靠全文检索——好写好搜；日常“记下来”由 `cs` 判断写 notes 还是 facts
- 用户带路跑通的未知流程写入 `notes/`，在 `facts.md` 加引用，必要时再沉淀到 `tools/`
- Markdown 应当适当精简，但不设统一行数上限；核心结构、背景、原则和契约要完整留在主叙事中，只把特定场景才需要或妨碍阅读的细节按渐进式披露拆到同目录资源

### 硬约束

> CodeStable 只有一个 `cs` 安装单元。它的核心结构和共同边界写在 `SKILL.md`，场景化行动规则与原则放在同一技能的 `references/`，模板和脚本也必须留在同一技能包内。
>
> `SKILL.md` 必须明确说明何时读取每个 reference，不能把核心契约藏起来，也不能一次加载所有场景材料。项目稳定知识仍沉淀到 `.cs/spec/`、`.cs/notes/`、`.cs/facts.md`。

`cs` 切换内部行动模式前先复用当前上下文：`facts.md`、project spec、epic spec 或目标 issue 等已经读过且无修改迹象，就不要机械重读；没读过、疑似变化、需要精确引用/写回，或需要新增局部时才补读。目标 issue、准备写回的 `.cs` 文件和代码文件，写入前必须确认当前版本。

要改体系口径，同步更新 `cs/SKILL.md`、相关 reference 和模板；项目自己的稳定需求和操作经验，放回 `.cs/` 对应实体。

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
- [ ] talk 初步规划与 epic spec 演进衔接继续打磨
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
