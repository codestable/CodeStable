---
name: cs-feat
description: 新功能开发的子流程入口，把"加个 X 能力"从想法走到验收闭环。触发：用户说"做新功能"、"加个 X"、"实现 XX"。只做路由，根据已有产物决定走 brainstorm / design / fastforward / implement / acceptance。不处理 bug。
---

# cs-feat

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

新功能流程在"需求"和"代码"之间塞了一份方案文件，让两边有交接点——AI 直接拿到需求就写代码会出三个老问题：名字跟原代码对不上、改着改着改出范围、改完不留存档。

```
(想法模糊先去 cs-brainstorm 分诊) → 方案设计（名词层 + 编排层 + 验收契约 + 推进策略切片）→ 分步实现 → 验收闭环
```

brainstorm 是讨论层独立入口，会分诊：case 1（清楚 → 直接 design）/ case 2（小需求继续讨论 → 落 brainstorm note）/ case 3（大需求 → 移交 `cs-roadmap`）。只有 case 2 在 feature 目录产出 brainstorm note。

本技能不写代码不写文档，只做一件事：看当前 feature 走到哪步，告诉用户该触发哪个子技能。

---

## 文件放哪儿

```
.codestable/features/{feature}/
├── {slug}-brainstorm.md       ← 阶段 0 产物（仅 case 2 落盘）
├── {slug}-intent.md           ← 阶段 1 可选前置草稿（用户自己写半成品）
├── {slug}-design.md           ← 阶段 1 方案文件
├── {slug}-checklist.yaml      ← 阶段 1 生成 steps + checks，2/3 阶段更新 status
└── {slug}-acceptance.md       ← 阶段 3 验收报告
```

目录命名 `YYYY-MM-DD-{英文 slug}`，日期取首次创建当天定了不动；slug 小写字母 / 数字 / 连字符。

为什么聚一起：以后查"那个导出 CSV 功能当时怎么决定的"，brainstorm / design / acceptance 都在一处。feature 和 issue 分别放在 `.codestable/features/` 和 `.codestable/issues/` 因为归档逻辑不一样。

实现 feature 时顺手发现的 bug → 记成新 issue，**不在 feature PR 里偷偷修**——验收时分不清范围，git blame 找不到为什么改。

---

## 四个阶段

| 阶段 | 子技能 | 产出 | 谁主导 |
|---|---|---|---|
| 0 brainstorm（可选，独立入口） | `cs-brainstorm` | case 2 时产出 brainstorm note | AI 思考伙伴，用户拍板 |
| 1 方案设计 | `cs-feat-design` | design.md + checklist.yaml | AI 起草，用户整体 review |
| 2 分步实现 | `cs-feat-impl` | 代码 + 阶段汇报 | AI 按方案执行 |
| 3 验收闭环 | `cs-feat-accept` | acceptance.md | AI 逐层核对，用户终审 |

阶段间有人工 checkpoint。上一阶段没拿到用户明确放行，下一阶段别开始——防止 AI 一口气从需求跑到代码、跑出来才发现走偏。

阶段 0 可选且是 feature 流程的**外部入口**——`cs-brainstorm` 同时服务 feature 和 roadmap。case 3（大需求）讨论被移交给 `cs-roadmap` 不再回 feature 流程；roadmap 拆出子 feature 后从 `cs-feat-design` 的"从 roadmap 条目起头"入口进来。

### Fastforward 模式

需求清楚 + 范围小时走完整四阶段太啰嗦。fastforward 把 design 压成 4 节（需求摘要 / 设计方案 / 验收标准 / 推进步骤），用户一次确认后直接实现。触发："快速模式"、"fastforward"、"直接开干"、"别那么多步骤"，去 `cs-feat-ff`。

**别走** fastforward：跨多个子系统、有术语冲突风险、推进步骤超过 4 步——这些情况跳过 design 意味着 AI 和用户没共同确认过同一份方案，实现完容易发现彼此理解不一样。

---

## 路由：用户现在该走哪个子技能

进入本技能先 Glob 一下 `.codestable/features/` 看已有产物。**不要只听用户口头描述**——用户说"设计写完了"不一定真完整，自己读一遍。

| 当前状态 | 触发哪个子技能 |
|---|---|
| 想法模糊，说不清真问题 / 边界 / 不做什么 | `cs-brainstorm` |
| 想法清晰（知道做什么 / 为谁 / 怎么算成功） | `cs-feat-design` |
| 用户说"开一个新需求 / 起草稿 / 新建 feature"想自己写半成品 | `cs-feat-design` 的"初始化模式"（建目录 + 空 intent，让用户填完再回） |
| 用户主动说"先 brainstorm 一下"、"有个想法没想清楚" | `cs-brainstorm` |
| `{slug}-intent.md` 已填好 | `cs-feat-design`（读 intent 作输入） |
| 用户说"快速模式 / fastforward" | `cs-feat-ff` |
| `{slug}-brainstorm.md` 已存在，要进设计 | `cs-feat-design` |
| `{slug}-design.md` 已 approved、代码没动 | `cs-feat-impl` |
| fastforward design 已确认 | `cs-feat-impl` |
| 代码已写完要验收 | `cs-feat-accept` |
| 用户说"我想要一个 X 系统"大需求 | 转 `cs-brainstorm` 分诊（大概率 case 3 → `cs-roadmap`） |
| roadmap 里某条子 feature 该启动 | `cs-feat-design` 的"从 roadmap 条目起头"入口 |
| 不确定 design 是否完整 | 自己读一遍，按上面对号 |

### 怎么判断该不该走阶段 0

判断信号不是"用户描述字数少"，是用户能不能清楚说出三件事：要解决的真问题 / 核心行为 / 一条明确的"不做什么"。三项有一项模糊就值得 brainstorm。

但别强推——用户明确说"想清楚了直接做设计"就尊重。不确定时问一句让用户选。**宁可漏判，别误判**——逼一个想清楚的用户做发散是浪费。

### brainstorm vs intent

两者都是 design 前置，区别在**谁在主导收敛**：

- brainstorm：用户脑子里模糊，AI 问用户答。判 case 3 时移交 `cs-roadmap` 不回 feature；只有 case 2 产出 brainstorm note
- intent：用户自己想好大致做法（100 字描述 + 相关数据结构），懒得口述就写成 `{slug}-intent.md` 给 AI 读

用户模糊触发"开一个新需求"时默认问"你想先聊清楚（brainstorm）还是自己写草稿（intent）？"，别自己挑。

---

## 与 issue 工作流的边界

- feature：从来没有的东西要加进来（新功能 / 新能力）
- issue：本来应该好的东西坏了（bug / 异常 / 文档错误）

灰色地带：feature 实现时发现的 bug 记成新 issue，不在 feature PR 顺手修。

---

## 相关文档

- `.codestable/reference/system-overview.md` — CodeStable 体系总览
- `.codestable/reference/shared-conventions.md` — 跨阶段共享口径、目录结构、checklist 生命周期
- `.codestable/attention.md` — CodeStable 启动注意事项和项目硬约束
- `.codestable/requirements/CONTEXT.md` + `requirements/adrs/` — 方案设计阶段需要查的领域术语与拍板决策
