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

使用 Skills CLI 安装：

```bash
npx skills add liuzhengdongfortest/CodeStable
```

默认安装到当前项目；希望所有项目都能使用时加 `-g`：

```bash
npx skills add liuzhengdongfortest/CodeStable -g
```

本地开发时，在仓库根目录验证安装发现：

```bash
npx skills add . --list
```

只需要一个入口，先让它接入项目：

```bash
/cs 请在这个项目接入 CodeStable
```

之后整理愿景、讨论需求、维护规格、直接修改、实现 issue、关闭沉淀都使用同一个入口：

```bash
/cs
```

`cs` 会先理解用户此刻是在提问、构想、讨论还是要求行动，再按需使用 vision spec、project spec、epic spec 或 issue。CodeStable 改变 AI 的判断，不要求用户走固定流程。

仓库只分发 `skills/cs/` 这一个 Skill；行动规则、设计原则、模板和脚本都在其内部按需加载。版本号记录在 `VERSION`，发布说明写入 `CHANGELOG.md`。

## 升级

发布新版本后，先看 `CHANGELOG.md`，再更新已经安装的 `cs`：

```bash
npx skills update cs
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
<tr><td><b>核心实体</b></td><td>Agent / Role / Team</td><td>vision spec · project spec · epic spec · issues</td></tr>
<tr><td><b>主线问题</b></td><td>Agent 之间怎么分工、传递、协调？</td><td>软件的目标世界、当前真相、变更线和可关闭事项怎么被组织、推进、沉淀？</td></tr>
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

## 设计：vision spec + project spec + epic spec + 按需 issues

CodeStable 的核心是四种信息责任：目标应用全景、项目当前真相、大需求活规格边界、值得持续管理的可关闭行动。它们不是必须依次经过的流水线。

### vision spec —— 目标中的应用世界

vision spec 放在 `.cs/vision/`。它帮助个人开发者把脑内产品世界逐渐外化：用户最终怎样获得结果、应用由哪些能力区域组成、有哪些奇思妙想、候选方向和互斥方案，以及哪些部分已规划、建设或成为现实。

Vision 是一棵可递归展开的产品地图。每层 `index.md` 以用户旅程为主阅读路径、能力版图为辅助视角；AI 不只转录用户原话，还负责帮助定位、分层、建立关联并指出冲突。Vision 不是 roadmap 或任务面板，详细进度仍留在 Epic / Issue。

### project spec —— 项目主线真相

project spec 放在 `.cs/spec/`。它面向第一次进入项目的开发者：这个项目当前是什么、已有能力和边界怎样成立、架构怎么细化、统一语言在哪里。目标未来属于 Vision；Project Spec 只写当前稳定真相。

统一语言放在离它生效范围最近的入口文档里，不另起一套 domain 目录。spec 不记流水账，只写当前为什么这样设计、哪些边界成立、哪些取舍被确认。

### epic spec —— 有边界的活规格

大需求放在 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`。Epic 可以从 Vision 摘取一段目标，也可以直接来自当前问题；这个 `spec.md` 是唯一权威入口，同时承载状态、当前规格、架构考量、直接切片与 issue 链接、阻碍、关闭条件和毕业候选。

Epic 不是计划容器，也不是 project spec 的缩小版。它是一条有边界的演进线：大到值得 review 架构决策和关键抽象，小到能在合理时间内多轮反馈。跨模块、会多轮变化、需要分批推进或规格还会持续微变的需求，才需要 epic；小而明确的改变按管理价值选择直接实现或独立 issue。

epic 下的 issue 关闭时，先回写 epic spec；等人确认整个 epic 完成，再由 AI 把毕业结论合并回 project spec。

### issues —— 按需使用的可关闭行动

Issue 适合存在范围取舍、需要多轮或跨会话推进、需要交接留痕，或用户明确希望追踪的改变。简单、明确、一次完成的 bug、功能或 chore 可以直接修改和验证，不必为了使用 CodeStable 建 Issue。大需求进入 Epic 后，也只在持续管理确有价值时分批切 Issue。

关闭规则很简单：独立 issue 回写 project spec；探索型 issue 把确认后的稳定理解合并进 project spec；epic issue 先回写 epic spec；epic 人工关闭后合并 project spec，并检查来源 Vision 的实现状态与链接。

## 质量如何贯穿变化

CodeStable 使用 [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) 的九项产品质量特征作为统一语言：功能适宜性、性能效率、兼容性、交互能力、可靠性、信息安全性、可维护性、灵活性和安全性（Safety）。这是工程判断框架，不是 ISO 合规或认证声明。

```text
Vision 中的目标质量方向
                    ↓ 摘取与确认
Project / Epic Spec 中的稳定质量约束
                    ↓ 继承
Talk / Explore / Complain 的风险发现
                    ↓ 选择
Issue 中的具体质量目标 / 直接改变的必要边界
                    ↓ 落实
Design 判断 → Do 证据 → Close 检查与回写
```

- 九特征用于扫描风险，不生成九项“满足 / 不适用”清单。
- Vision 可以保存目标质量方向，但摘取开发切片时重新确认；Issue 只选择会改变设计或验收的质量目标。
- 相关 spec 约束自动继承；Agent 主动识别普通工程风险，指标阈值、显著成本、兼容策略和目标冲突由用户决定。
- 选中即承诺：Design 必须逐项目标响应，Do 必须留下证据，Close 只在证据足够时通过。
- 直接改变不生成形式化质量清单，但仍须守住相关 spec、用户要求、安全、数据保护、可访问性和必要验证。
- 可测试性属于可维护性的子特性；可观测性继续作为支撑可靠性、可分析性和验证的工程手段，不另造一套质量模型。

## 实现如何保持经济性

CodeStable 把“少写代码”收紧成**最小充分变化**：先理解触发到结果的真实路径，再从不新增、删除或收窄、复用现有归属、标准库、平台原生能力和已安装依赖一路判断，最后才写新代码。最小 diff 必须落在正确责任边界；在症状旁边堆局部 guard，不算小。

- 不为想象中的未来提前增加单实现接口、无人修改的配置、纯转发 wrapper 或新依赖。
- 有意采用带容量、环境或算法上限的简单方案时，记录已知上限、升级触发和升级方向；触发尚未发生时不提前建设，已经发生时也不能把它藏成“以后再做”。
- 非平凡逻辑至少留下一个会在行为损坏时失败的最小可运行检查，优先复用现有测试入口，不为窄变化搭一套新框架。
- 输入校验、数据保护、信息安全、可访问性、危险操作护栏、用户明确要求和已选质量目标不参与删减。
- 没有真实对照基线时，只汇报删除或避免新增了什么，不虚构代码、成本或时间收益数字。

## UI 规格如何使用图

当 UI 的空间关系、信息层级或多状态交互会影响需求理解时，CodeStable 要求在 Vision 或 spec 中提供可版本化的可视化规格；没有相关 UI 或只是简单文案 / 样式变化时不生成空章节。

- ASCII 线框图表达布局、区域、层级和主要控件，Mermaid 表达页面流程或状态迁移。
- Vision Spec 画跨 Epic 的目标应用体验与候选方向；Project Spec 只画当前稳定界面；Epic Spec 明确本次目标变化；Issue 只画局部；Design 映射到组件、状态和数据流。
- 图下标注角色与入口、交互与关键状态、稳定约束和仅作示意的部分。图与文字冲突时必须先消歧，不能让实现者自己猜。
- 截图、高保真设计稿和原型可以作为视觉证据，但不能成为唯一规格；线框图澄清交互目标，也不能替代可运行行为和可访问性验证。

---

## 技能总览

仓库只分发一个 `cs` Skill。用户不再选择十几个技能名；`cs` 先判断用户此刻要做什么，再按需加载内部模式：

| 意图 | `cs` 内部行为 |
|---|---|
| 首次接入 | 创建或补齐 `.cs/` 骨架，不擅自迁移旧需求 |
| 构想整个应用 | 帮用户把脑内世界整理成 `.cs/vision/` 中可导航的产品地图，不强迫立即开发 |
| 局部想法模糊、需要规划 | 调查上下文、澄清真问题，确认后直接改变、更新 Vision、形成 issue / epic，或继续探索 |
| 规格变化 | 维护 project spec 或唯一的 epic `spec.md` |
| 行为不符合预期 | 用反馈回路诊断、修复和验证；简单 bug 可直接闭环，需要追踪时建 issue |
| 明确改变 | 用户已授权时直接实现；有 issue 就回写，没有就不补造事项 |
| 系统如何工作仍说不清 | 从触发到结果做轻量 Explore；复杂或可复用时升级独立探索 issue |
| 值得复用 | 写入 notes、Agent 指令或 tools；未知流程由用户带路跑通 |

内部行动规则和代码设计、debug、文档组织等原则放在 `cs/references/`，只有当前场景需要时才进入上下文。

---

## 结构如何演化

CodeStable 不是一条线性流水，而是四类信息按需协作：

```text
Vision Spec ──摘取目标切片──> Epic Spec ──按需分批──> Issues
     │                         │                       │
     │                         └──关闭毕业─────────────┤
     │                                                 ↓
     └──目标世界                        Project Spec（当前现实）

简单明确的改变 ──直接实现与验证──> Project Spec（仅在当前真相需要更新时）
```

**怎么读这张图：**

- **vision spec 是目标世界，project spec 是当前现实**——二者不同是产品仍在演化，不是谁覆盖谁
- **epic spec 是活规格边界**——从 Vision 摘取或从现实问题圈住一段变化，毕业后合入 Project Spec，并同步 Vision 的实现状态
- **issue 是可选的持续管理实体**——有追踪价值时使用；简单明确的改变直接实现与验证
- **辅助资料是飞轮**：任何事项跑完发现"这事值得记下来"都能触发沉淀，沉淀又被下一次同类工作读到——这是 CodeStable "复利"的物理实现

---

## 运行时结构

让 `/cs` 接入项目后，会在项目根生成 `.cs/`——规格、事项和知识产物的聚合根，也是统一技能运行时读写的工作区。

```
你的项目/
├── .cs/
│   ├── talks/                # 讨论整理（确认后才落盘）
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── vision/               # vision spec：目标应用全景
│   │       ├── index.md
│   │       └── ...           # 以用户旅程为主线递归展开
│   ├── spec/                 # project spec：项目主线真相
│   │       ├── index.md
│   │       └── ...           # 按阅读路径递归拆分，每层可有自己的 index.md
│   │
│   ├── issues/               # 可关闭事项，按创建日期分片
│   │   ├── YYYY/MM/DD/{status}-{短语}.md   # 普通 issue
│   │   └── YYYY/MM/DD/{status}-{短语}/     # 完整 Explore：index + 触发到结果的路径文章
│   ├── epics/                # 大需求活规格边界
│   │   └── YYYY/MM/DD/{短语}/
│   │       └── spec.md       # 唯一权威入口：规格、直接切片、issues、阻碍和关闭条件
│   │
│   ├── notes/                # 知识笔记，纯 markdown，全文检索
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # 跑通后按需沉淀的共享脚本
│
└── （其他项目文件）
```

**几条要点：**

- 规格、事项和知识产物聚在 `.cs/` 下，"上次那个变更当时怎么搞的"三秒能找到
- `vision/` 保存目标应用全景、候选与互斥方向；AI 帮助用户整理地图，用户确认后写入
- `spec/` 是 project spec，面向第一次进入项目的开发者组织主线需求、架构考量、统一语言和阅读路径
- `epics/` 是大需求活规格边界；关闭后合并 project spec，并检查来源 Vision 的实现状态和链接
- 简单明确的改变可以直接实现与验证，不要求创建 Issue；复杂度、风险、跨会话或留痕价值足够时再使用 Issue
- 修改代码前先沿“触发如何产生结果”顺清现状；能在当前上下文或目标 issue 紧凑说明就走轻量 Explore，解释不清、跨越多个边界或值得复用时才升级完整 Explore
- 完整 Explore 的 `index.md` 只建立一句话模型、探索边界和阅读路径；路径文章再逐层展开主路径、关键责任、数据、状态、相关分支和证据
- 探索关闭后，稳定 How it works 理解按渐进式披露进入 project spec；具体改动的影响分析留在目标 issue，证据与已排除理解留在 Explore issue
- talks / notes 默认写入 `YYYY/MM/DD/{短语}.md` 日期分片，epics 写入 `YYYY/MM/DD/{短语}/` 工作区，普通 issues 写入 `YYYY/MM/DD/{status}-{短语}.md`，探索型 issue 写入 `YYYY/MM/DD/{status}-{短语}/` 工作区；查找时递归搜索对应目录
- `notes/` 是知识笔记，纯 markdown 无 frontmatter，靠全文检索——好写好搜；日常“记下来”由 `cs` 判断写 notes 还是项目 Agent 指令
- 用户带路跑通的未知流程写入 `notes/`；只有它是相关工作开始前的稳定前置时，才在 `AGENTS.md` 或 `CLAUDE.md` 加一行引用，必要时再沉淀到 `tools/`
- Agent 框架会自行注入项目根的指令文件，`cs` 不主动读取或把它们纳入 `.cs/` 结构；跨 Agent 的短规则优先写已有 `AGENTS.md`，只对 Claude 生效的规则写 `CLAUDE.md`
- Markdown 应当适当精简，但不设统一行数上限；核心结构、背景、原则和契约要完整留在主叙事中，只把特定场景才需要或妨碍阅读的细节按渐进式披露拆到同目录资源

### 硬约束

> CodeStable 只有一个 `cs` 安装单元。它的核心结构和共同边界写在 `SKILL.md`，场景化行动规则与原则放在同一技能的 `references/`，模板和脚本也必须留在同一技能包内。
>
> `SKILL.md` 必须明确说明何时读取每个 reference，不能把核心契约藏起来，也不能一次加载所有场景材料。目标应用全景进入 `.cs/vision/`，项目稳定真相进入 `.cs/spec/`，可复用知识进入 `.cs/notes/`，启动必读短规则直接进入项目 `AGENTS.md` 或 `CLAUDE.md`。

`cs` 先判断用户此刻是在提问、构想、讨论还是要求行动，再选择内部模式。已掌握且没有变化迹象的 vision、project spec、epic spec 或目标 issue 不机械重读；目标文件在写入前必须确认当前版本。

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

- [ ] Vision 整理与开发切片体验继续打磨
- [ ] 直接改变、Issue 与 Epic 之间的自适应行动判断继续打磨
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
