---
name: cs
description: >
  CodeStable：一套软件演化理解（Vision/Project Spec/Epic/Issue + .cs/ 制度记忆），按用户当前姿态行动——讨论、快改、受管理实现、修 bug、整理愿景/规格、现状理解、关闭收尾、按需 review。
  触发：cs、CodeStable、讨论/先聊清楚、快速/快改/直接开干、穿刺、修 bug/debug、整理 vision/spec、关闭/收尾、review、这系统怎么工作、项目已有 .cs/ 且在处理愿景规格 bug 实现关闭时。
  调用 cs 不等于跑完整流程：先判姿态再行动。仅用户明确要求时才初始化 .cs/。
---

# cs — CodeStable

CodeStable 是**软件演化的理解方式**，不是强制流水线，也不是 Agent 编排器。

- **理解（世界模型）**：目标世界 / 当前真相 / 有界大变化 / 可关闭行动，记在 `.cs/`
- **姿态（用户此刻要什么）**：讨论、快交付、受管理推进、修坏的、维护规格……
- **手法**：现状说明、穿刺、Review——挂在姿态里，不单独占入口

**调用本技能 ≠ 跑完整生命周期。** 先定姿态，再只读该姿态需要的 reference；同一会话可换姿态，**不必**向用户宣布“进入某模式”。

---

## 1. 先定姿态（入口）

从用户原话与上下文选**一个主姿态**；选中后**立刻**读「必读」列，再动手。未发生的姿态文件不要预读。

| 姿态 | 用户常这样说 | 必读 | 同时读（有需要才） | 默认边界 |
|---|---|---|---|---|
| **接入** | 初始化 cs、接入 CodeStable、补齐 `.cs/` | [onboard](references/onboard.md) | — | 须明确授权；不编造业务内容 |
| **讨论** | 聊聊、先理清、想清楚再做、帮我规划一下 | [talk](references/talk.md) | [docs](references/docs.md)；具体变化 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) | 确认前不落盘、不建 issue/epic/vision |
| **愿景** | 应用将来什么样、整理 vision、产品全景 | [vision](references/vision.md) | [docs](references/docs.md)；质量方向 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) | 确认后才写 vision；不强迫开开发事项 |
| **规格** | 维护 spec、当前真相、epic 活规格 | [spec](references/spec.md) | [docs](references/docs.md)；质量约束 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) | 只写仍成立的结论 |
| **理解现状** | 怎么工作的、这条链路、影响范围 | [explore](references/explore.md) | [docs](references/docs.md)；服务具体变化 → [quality](references/quality.md) | 先现状说明；值得复用再 Explore issue |
| **修 bug** | 坏了、不符合预期、debug、修这个 bug | [complain](references/complain.md) | [debug](references/debug.md)、[economy](references/economy.md)、[quality](references/quality.md)；结构 → [code-design](references/code-design.md) | 简单默认快改落 `ff`；复杂可受管理 |
| **设计** | 怎么实现、先设计、实现方案 | [design](references/design.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) | 不写代码；高风险标穿刺顺序 |
| **快交付** | 快速、快改、小改一下、直接开干、别走流程 | [fast](references/fast.md) | [economy](references/economy.md)；必要时 [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) | **默认**轻检索 + 验证 + **必留 `ff`**；用户明确不要痕迹才可无 `ff` |
| **受管理实现** | 做这个 issue、推进 epic、实现（有档）、穿刺/先打通 | [do](references/do.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；现状不清 → [explore](references/explore.md)；UI → [ui-spec](references/ui-spec.md) | 完成 ≠ 关闭；风险先穿刺再加厚 |
| **收尾** | 关闭、收尾、做完并沉淀、毕业回写 | [close](references/close.md) | [docs](references/docs.md)、[quality](references/quality.md)；有界简化 → [economy](references/economy.md) | 须用户授权关闭；**不**自动进 `done/` |
| **审代码** | review、评审、看看这 diff/PR | [code-design](references/code-design.md)（文末 Review） | [economy](references/economy.md)；相关 → [quality](references/quality.md) | 用户点名才做；默认只审不改 |
| **记知识** | 记一下坑、写 note | [note](references/note.md) | [docs](references/docs.md) | 同主题改原 note，不新建第二条 |
| **学流程** | 我带你跑一遍、教 AI 做某流程 | [maketools](references/maketools.md) | [docs](references/docs.md) | 危险操作前再确认 |

### 姿态判断规则

1. **用户授权与原话优先**于“看起来该走重流程”。
2. **小且明确、要快、未要求建档** → **快交付**（不是“先讨论一整轮”）。
3. **目标糊、取舍未定** → **讨论**；聊清后再切快交付 / 受管理 / 愿景等。
4. **已有常规 issue 或用户点名 issue/epic** → **受管理实现**（或先设计）。
5. **坏的是已有行为** → **修 bug**；新能力 → 快交付或受管理，不是 complain。
6. **只问怎么工作** → **理解现状**；不要默认开改。
7. **意图不清且选错会实质改变后续**（例如会不会建 issue、会不会改代码）→ 一句话推荐 + 理由，**请用户选**；不要默认重流程。
8. 写/改 **Agent 技能本身** → 独立技能 `great-skills`，不在本包。

### 管理强度（快交付 vs 受管理）

| 条件 | 选择 |
|---|---|
| 小、一次做完、低风险，或用户要快 | **快改** → 必留 `ff`（[fast](references/fast.md)） |
| 用户**明确**不要痕迹 / 别写 issue | 可无 `ff`；真相失效仍同步 spec 或标漂移 |
| 范围取舍、多轮、交接、显著风险、长期质量承诺 | **常规 issue**（`issue.md`，`type: feature\|bug\|chore\|refactor`） |
| 跨模块、多批、规格在边界内反复演化 | **Epic**；够清楚的切片可 epic 内直接推进 |
| 技术/集成/迁移风险需先证明可通 | **穿刺**（[do](references/do.md) 手法）再加厚 |
| 用户明确要管理 / 明确不要建档 | **服从用户** |

---

## 2. 世界模型（薄）

```text
Vision Spec ──摘取──> Epic Spec ──推进──> Issues（含 ff 快改痕迹）
     │                    │                    │
     │                    └──关闭毕业───────────┤
     └──目标世界              Project Spec（当前现实）
```

| 实体 | 路径 | 回答什么 |
|---|---|---|
| **Vision** | `.cs/vision/` | 应用最终什么样、旅程与能力、候选/互斥方向 |
| **Project Spec** | `.cs/spec/` | 现在仍然成立的项目真相（按场景/能力，不按代码目录） |
| **Epic** | `.cs/epics/{NNN}-o\|x-{名}/spec.md` | 有界大变化：已定/仍变、可推进什么（活规格） |
| **Issue** | `.cs/issues/{NNN}-o\|x-[{ff}-]{名}.md` 或 Explore 目录 | 可关闭行动；快改用 `ff` |

**为何分层：** 只靠 issue 会丢方向；只靠当前 spec 安放不了互斥构想；全塞进 project spec 分不清“现在”和“以后”；巨型 issue 关不掉。只把**值得跨会话**的信息写入 `.cs/`。

### 命名与序号（契约）

各树（issues / epics / notes / talks，**含 `done/`**）内 `NNN` **独立**：最大开头数字 + 1；至少三位，过 999 为 `1000`…，无上限。

| 形态 | 路径 |
|---|---|
| Issue 进行中 / 已关 | `{NNN}-o-{名}.md` / `{NNN}-x-{名}.md` |
| 快改 | `{NNN}-o\|x-ff-{名}.md`，`type: ff`，模板 `ff-issue.md` |
| Explore | `{NNN}-o\|x-{名}/` + `index.md` |
| Epic | `{NNN}-o\|x-{名}/spec.md`（每 epic 仅一份权威 spec） |
| 已整理 | `issues/done/`、`epics/done/` 下同名；**关闭不自动挪** |
| Talk / Note | `{NNN}-{名}.md`（无 `o/x/ff`） |

- 关闭：路径 `-o-` → `-x-`，序号与名称不变；`status: closed`。
- 常规 issue 模板：`templates/entities/issue.md`（`type: feature|bug|chore|refactor`）。
- **ff** 只四节：做了什么 / 改了哪些 / 怎么验证 / 对 `.cs/` 的影响；禁止迷你 Design。
- Talk：`.cs/talks/`；Note：`.cs/notes/`（同主题改原文件）；Tool：`.cs/tools/`。
- 启动短规则只进会注入的 `AGENTS.md` 或 `CLAUDE.md`（不两处重复）。**不建 `facts.md`。**

### 谁可以写哪一层

| 写入 | 时机 |
|---|---|
| Vision 目标内容 | 用户确认的愿景整理；实现结论要改目标须再确认 |
| Vision 实现程度/链接 | Epic **关闭**时按事实 |
| Project Spec | 独立 issue/Explore **关闭**毕业；Epic **关闭**合并；快改真相失效；规格姿态维护 |
| Epic Spec | 规格姿态；epic 下 issue 关闭回写 |
| Issue / ff | 受管理推进；快改完成后写/关 `ff` |

冲突：`用户最新确认 > 证据/代码 > 疑似过期 spec`；Epic 与 Vision 不一致时先说明是收窄实现还是改目标，不静默绕过。

### 完成 · 关闭 · done · Git

| | 含义 |
|---|---|
| **完成** | 实现与验证达成目标 |
| **关闭** | 用户授权收尾：`o`→`x`、毕业回写；git 中可按契约 commit 相关文件 |
| **整理进 done** | 仅用户主动要求时挪已 `-x-` 项；关闭/快改/会话结束**不自动**做；`done/` 仍参与检索 |

| 动作 | 默认 |
|---|---|
| 快改 | 验证后**必写** `ff`（或直接 `x-ff`）；不自动 commit/push |
| 受管理实现 | 完成即可；**不**自动关闭 issue；不 commit/push |
| 用户说做完/修好 | 完成验证；小改仍落 `ff`（除非不要痕迹）；常规 issue 不自动关 |
| 用户说关闭/收尾 | [close](references/close.md)；不自动进 `done/` |
| push / 部署 / 初始化或覆盖 `.cs/` / 关 epic / 破坏性操作 | **必须**明确授权 |

毕业摘要：独立 issue → project spec；epic 内 issue → epic spec；Epic 关闭 → project spec 并检查 Vision；ff 默认不大段毕业，真相失效则同步或标漂移。细则 [close](references/close.md)。

### 质量（一句）

ISO/IEC 25010:2023 九特征作统一语言，**不是**九项必填表。**选中即承诺。** 快改不写形式清单，仍须守 spec/用户要求与必要护栏（含信息安全性 vs 安全性勿混称“安全”）。见 [quality](references/quality.md)。

---

## 3. 开工协议

在**设计、实现、快改、修 bug、维护规格、穿刺**前，若项目有 `.cs/`，先做本协议（各 reference 不重复展开）：

1. **扫 `.cs/`**：路径浏览 + 关键词 grep。本会话同主题已扫且无新写入可复用。
2. **按权重深读**：`spec/`（最高）→ 相关 epic / notes → issues（含 `-x-`、`ff`、`done/`）→ 按需 talks/vision/tools。
3. **现状够用吗**：一句话触发→结果？不够 → 现状说明；跨多边界/要复用 → Explore issue。
4. **管理强度**：见上文表。
5. 与代码冲突：先核对证据，再改真相——不静默用代码盖掉已记录取舍，也不盲信过期文档。

有目标 issue 时确认**当前版本**；epic 下工作读对应 `spec.md`。

**`.cs/` 是制度记忆**：怪代码先查 spec；踩坑先查 notes；历史取舍先查 issue。

---

## 4. 授权边界（所有姿态共用）

- 方向已确认且用户要求执行 → 推进到**完成**或真阻塞；不在正常步骤间反复确认。
- 确认前：讨论不落盘；设计不写代码。
- 完成 ≠ 关闭；关闭 ≠ `done/`；实现/快改后**不**自动 Review、**不**自动 push。
- 初始化 `.cs/`、覆盖入口、关 epic、危险操作、推送、部署：须明确授权。

---

## 5. 原则文件何时加读

| 文件 | 何时 |
|---|---|
| [quality](references/quality.md) | 具体变化的讨论/设计/实现/关闭；质量相关 bug；spec 记约束 |
| [economy](references/economy.md) | 设计/实现/修 bug 取舍；关闭时发现有界简化 |
| [code-design](references/code-design.md) | 设计/受管理实现/结构问题；**Review 必读（含文末）** |
| [ui-spec](references/ui-spec.md) | UI 空间关系、信息层级、多状态 |
| [docs](references/docs.md) | 写或重组 vision/spec/explore/notes/talk 等文档 |
| [debug](references/debug.md) | 修 bug 升级慢路径时 |

模板：`templates/entities/`（`issue.md`、`ff-issue.md`、explore/vision/spec/talk/notes…）。初始化：`scripts/init_codestable.py`。产物格式以各 reference 为准，勿凭文件名猜。
