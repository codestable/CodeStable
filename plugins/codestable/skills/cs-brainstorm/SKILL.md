---
name: cs-brainstorm
description: 模糊想法分诊。触发：用户想先聊、brainstorm、方向摇摆；不处理 bug/重构。
---

# cs-brainstorm

brainstorm 是"讨论层"统一入口。

三件最重要的事：

- **brainstorm 是创意空间不是审计关卡**——探索 / 质疑 / 改主意 / 聊着聊着发现真正想做的是另一件事都正常
- **任何话题都可以聊**——用户想聊库 / Schema / 接口就聊；TA 提出来说明心里有谱，趁早讨论清楚 design 阶段更省力，不设话题黑名单。
- **AI 是思考伙伴不是记录员**——用户来这步是想被挑战、被启发，不是被一条条问题填表。如果只是把用户的话整理一遍写下来这步就白做了

> 共享路径和命名约定看 `.codestable/reference/shared-conventions.md`。需要 owner 在 interview / grill 中做路线、范围或下一步审批时，先读 `.codestable/reference/approval-conventions.md` 并把 `approval-report.md` 写到对应 brainstorm / feature / roadmap 目录。

---

## 分诊

### 四种 case 速览

| case | 规模 | 用户状态 | 产物 |
|---|---|---|---|
| **case 1：已经够清楚** | 不限 | 一句话能说清做什么 / 为谁 / 怎么算成功 / 不做什么 | 确认后同轮进 `cs-feat` design |
| **case 2：小需求** | 单 feature | 知道要解决什么问题，对解法 / 边界还摇摆 | 落 feature brainstorm，确认后同轮进 `cs-feat` design |
| **case 3：大需求，拆解 ready** | 多 feature | 心里已有大致模块划分，想直接做拆解和接口契约 | 不落盘，同轮进 `cs-epic` |
| **case 4：大需求，想 grill** | 多 feature | 还不想拆——想先 grill、发散、产生想法存着 | 落 open brainstorm，确认后同轮进 `cs-epic` |

判错 case 不是灾难——**允许升降级**。case 2 聊着发现范围越聊越大切 case 3/4，case 3 聊着发现需要先 grill 切 case 4，case 4 grill 完可以直接拆切 case 3，当场切换出口。

出口语义：case 1 / case 2 / case 4 是待确认出口；case 3 的 ready 拆解表述本身视为确认，是已确认出口。

### 开聊前检查

每次都做：

1. **扫一眼仓库（上下文幂等：先 Glob 发现、按需再读、已载复用）**——动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`；Glob `.codestable/` 发现 features / roadmap / brainstorms / compound / requirements 有哪些，**命中和本次讨论相关的才深读**：需要术语时读 `requirements/CONTEXT.md`、涉及已拍板决策时扫 `requirements/adrs/`、`grep -r` 关键词 compound/ 看相关坑、看相关 feature / roadmap / brainstorm；**若本会话已加载过则复用，不重复 Glob+Read**；Grep 用户描述里的关键词防术语冲突
2. **是不是接续之前的工作**：
   - `features/` 下有名字相近的 brainstorm？`roadmap/` 下有相近子目录？`brainstorms/` 下有相关创意记录？
   - 没有 → 当新讨论
   - 有 brainstorm 内容是中断留下的 → 读完汇报"上次聊到 {…}，接着聊还是推翻？"
   - 有同名 design.md → 告诉用户 design 已开，是不是走错入口
   - 有同名 roadmap → 这块已在 roadmap 跟进，是不是要推进具体子 feature
   - `brainstorms/` 下有相关创意记录 → 读完汇报"之前 {日期} 存过一份脑暴记录，方向是 {…}，接着聊还是直接拆 roadmap？"
3. **确认这是新功能 brainstorm**——bug 走 `cs-issue`，重构走 `cs-refactor`
4. **如果你已经能替用户写出 design 需求摘要的初稿**——当场判 case 1。揽下不属于自己的活是本阶段最大反模式

### 开场分诊：一两轮对话判 case

不是填表——分类题问太多用户觉得在走流程。

**用户只说一个模糊词 / 短句**（"我想要一个权限系统"、"想聊聊通知"）：

> 一句话先对齐：你想解决的是 {AI 复述的问题} 对吧？这块你脑子里多大范围——是"加一个小能力"那种一个 feature 能装下的，还是"一整块新子系统得分几轮做"的规模？

**用户带着方案来**（"我想做 X，里面有 a/b/c"）：

> 复述一下看对不对——你想解决的问题是 {P}，打算做 X 包含 a/b/c。这里 a/b/c 合起来更像一个 feature 能搞定，还是三件互相有依赖的事要分几轮？

用户自己拆成多件 → 多 feature 规模，追问"想直接拆 roadmap 还是先 grill 存着？"→ case 3 或 case 4；a/b/c 是同一件事的不同面 → case 2；用户听完复述说"对就是这个想清楚了"→ case 1。

**判 case 信号**（用户说不清就 AI 自判）：

- 每一条目标是**同一件事的不同角度**→ case 2
- 几条目标有**先后依赖**或**互相独立的子模块**，用户能说出大致拆法 → case 3
- 几条目标有**先后依赖**或**互相独立的子模块**，但用户说不清模块边界、想先发散探索 → case 4
- 聊两句"不做什么 / 核心行为 / 成功标准"都对上 → case 1

---

## 怎么聊（case 2 & case 4 共享工具箱）

以下对话方法对 case 2 和 case 4 通用。case 2 最终要收敛到一个选定方向，case 4 可以更开放、不强制收敛。

### 两条核心姿态

**1. 区分"用户说的"和"用户要的"**——开口第一句往往是 TA 想到的方案不是真要解决的问题。听到"我想做 X"先别顺着聊方案，先问"X 是为了解决什么场景下的什么问题"。常见发现：真问题不是 X 能解决的，或有更小、更轻、完全不同方向的解法。一旦进 design 方向就焊死——在用户自己还没意识到之前完成这件事是 brainstorm 阶段最大价值。

**2. 用户带着方案来时先评估再接受**——不要直接进入"那我们聊聊 a 怎么做"。先做：
- **复述 + 反向追问问题**——把方案翻成"你想解决的问题是不是 P"
- **评估并提替代**——看到方案有明显问题（解错了 / 过度工程 / 有现成更轻路径 / 踩 learning 坑），直接说出来，提 1-2 个明显不同的替代方向。**不要为了显得配合就闭嘴**

评估完发现方案确实合理 → "我觉得这个方向 OK 建议直接进 design"，别为凑流程硬发散——当场升级 case 1。

### 对话节奏

没有固定步骤。三个动作随时可回到上一步：

1. **挖问题**——按姿态 1 把"真正要解决的问题"问清楚，能用一句话复述、用户说"对就是这个"为止。**这一步价值最高不要急着跳过**

   **grill 档**（按需启动，默认不开）

   默认走轻问——一次复述对上就推进。下面任一信号出现切到 grill 档加深：

   - **显式请求**：用户说"多问几轮 / 帮我问清楚再开始 / grill 我"
   - **隐式信号**：连续两次复述被"差不多但不太对"驳回；同一概念用不同词反复互指（"权限 / 角色 / 租户"换着说指同一件事）；用户自己也说不清楚
   - **只在 case 2 / case 4 启动**——case 1 已清楚硬 grill 反人性，case 3 用户已 ready 拆解不需要 grill

   grill 档硬约束（防止没完没了）：

   - 最多 3-5 轮重点问题，一轮没拿到新增信息就退到发散
   - 每轮**一个问题 + 2-4 个有区别度的候选**让用户挑，不让 TA 自由作文；如果选项含义需要解释、答案会改变路线 / 范围 / 下一步，先产出 `approval-report.md`，不要只丢一个多选题
   - 遇到"得写起来才知道"的问题：标成 open question 直接跳过，不死磕
   - 用户开始敷衍 / 说"先这样吧 / 差不多了" → 立刻退到收敛，别再追问

2. **发散**——确认问题后再谈方案。提 2-3 个具体候选方向（用户带的方案算其中一个），每个 1-2 句描述 / 价值 / 代价。**至少有一个反直觉候选**（反转 / 去掉常见约束 / 跨领域类比）。所有候选呈现完再给推荐——先锚定再补别的会污染用户判断
3. **收敛**——选定方向后轻轻勾勒：核心行为？明显不做？最大未知？给 design 热身不是替 design 决定

### 最小 demo / spike

讨论中冒出"这个方向能不能走得通要看 X 实际是不是 Y"——不要靠脑补辩论，**停下来花 5-30 分钟搭个最小 demo 验一下**比再聊三轮更省时。

**默认不做**——大多数 brainstorm 是在比较权衡，demo 帮不上忙。同时满足下面三条才主动提议：

1. **是事实问题不是偏好问题**——某 API 实际行为 / 库是否真支持 / 性能特征是否成立，不是"哪种风格更好"
2. **结果会改变方向**——验出来不管成败，讨论都能收敛
3. **成本可控**——你判断 5-30 分钟内能搭出能跑的东西。超过这个量该走 `cs-feat` fastforward mode 直接做或拆成正式 feature

提议格式：**"这块靠想不准，我做个最小 demo 验一下 {要验的事}，5-10 分钟，OK 吗？"** 用户秒过 / 拒绝即可。

**spike 落地约定**：
- case 2：实验代码扔 `.codestable/features/{feature}/` 下（和 brainstorm note 同目录），文件随便起名（`spike.py` / `try-{topic}.ts`）
- case 4：spike 放 `.codestable/brainstorms/{slug}/`，跟 brainstorm.md 挨着
- 验完不强制清理——留着以后看也行；用户嫌乱说一声再删
- **结果必须回写 brainstorm note**——成败都要在"已敲定"那节记一条："{结论} —— 已用 spike 验证（代码见 `{路径}`）"，避免 design / roadmap 阶段再起疑重做

case 1 / case 3 也能借这个动作（不强求落 brainstorm note），逻辑一样：事实存疑 + 改变方向 + 成本可控。

### 对话中的坑

- **一次只问一个问题**——抛三五个用户只回最容易答的
- **先给选项再提问**——能用 2-4 个具体有区别度的选项让用户挑就别让 TA 自由作文
- **不要主动把话题拉回"用户感知层面"**——用户想聊库 / Schema / 接口 / 选型就跟着聊；AI 自己别主动开技术细节话题填时间，但用户开了的话题就认真陪聊。某问题的答案得看代码 → 按需读代码再带回对话

---

## 横切：拍板了结构性决策？

任何 case 下，讨论过程中只要拍板了符合 **ADR 3 判据**（难回退 + 不显然 + 真实权衡）的结构性决策——典型如选了某个库 / 模块拆分方式 / 跨模块通信模式 / 一个稳定的"我们不做 X"——提示用户：

> 这条决策听起来该写一条 ADR（难回退 + 选了具体方案）。要不要现在走 `cs-domain` 落一条 ADR？

用户决定。**不在 brainstorm 里直接写 ADR**，由 cs-domain 处理。

---

## 四种 case

### case 1：已经够清楚

**信号**：一句话能说出做什么 / 为谁 / 怎么算成功 / 不做什么；聊两句核心行为 / 成功标准都对上。

**处理**：
1. 告诉用户"这块你已经想清楚了：{AI 一句话复述}。建议直接进 `cs-feat` design 阶段——brainstorm 对你没增量"
2. **看聊过程有没有非琐碎技术决策**——讨论了具体库选型 / Schema / 接口形态 / 跨模块约定，落一份精简 brainstorm（只填"已敲定的设计点"那节）让 design 直接读到不必重讨；纯方向确认没聊技术细节就裸退不落盘
3. 停下来确认是否进入 design；不替用户点头

**退出**：用户确认后在当前 run 加载 `cs-feat`，从零写 design；轻量落盘时同时传递 `{路径}`，不要求用户重新调用或重述

---

### case 2：小需求 → feature brainstorm

**信号**：知道要解决什么问题、大致做哪块，一个 feature 能装下，但对解法 / 边界还摇摆。

**怎么聊**：按上节"怎么聊"工具箱推进——挖问题 → 发散 → 收敛。收敛到选定方向后落盘。

**升降级**：
- 聊着发现规模超出单 feature → 写 `approval-report.md` 解释"直接拆 roadmap vs 先 grill 存着"，再让 owner 选 → case 3 或 case 4
- 聊着发现已经全清楚 → case 1

**落盘**：收敛完成后写 `.codestable/features/{feature}/{slug}-brainstorm.md`。

目录约定：
- 日期前缀：从环境信息取今天日期
- slug：根据方向自拟英文小写连字符，写进 note 时告诉用户。design 阶段改名只 rename slug 部分日期别动
- 目录不存在就创建；已存在回到开聊前检查的接续逻辑

只在用户确认进 design 那一刻落盘——对话期间不写文件。`status` 固定 `confirmed`，没有 draft。

文档模板见同目录 `reference.md` 的"feature brainstorm 模板"。frontmatter 字段口径跟 design / acceptance 共用一组，看 `shared-conventions.md` 第 1 节。

**退出**：如果只是轻确认，主动问"这块够清楚了可以进 design 吗？"；如果需要解释方案 / 代价 / 默认后果，先在 feature 目录写 `approval-report.md` 再让 owner 确认。确认后落盘，并在当前 run 加载 `cs-feat` design，传递 `{路径}` 与已敲定方向。如果愿景（用户故事 / 痛点 / 边界）已经聊透了，可先询问是否用 `cs-req draft` 落 requirement；这也是待确认出口，不能替用户改道

---

### case 3：大需求 → epic 直接拆

**信号**：多 feature 规模，用户心里已有大致模块划分，能说出拆法，想直接做拆解和接口契约。

**处理**：
1. 告诉用户"听起来是多个 feature 的集合，单 feature 装不下。`cs-epic` 会做拆解和依赖梳理，现在继续进入它的 planning"
2. 把已聊的信息汇总让 epic planning 接手不用重来：真问题 / 大致范围 / 已提到的可能子模块（一句话各一）；**聊到的跨模块接口形态、共享协议、技术选型一并列出**——这些是内部 roadmap 主文档"架构层详设"节的种子
3. **不落盘**——`cs-epic` planning 自己建目录和主文档

**退出**：ready 拆解已经构成用户确认；附聊到的要点汇总，直接在当前 run 加载 `cs-epic` planning，不落盘

---

### case 4：大需求 → brainstorms 创意空间

**信号**：多 feature 规模，但用户说不清模块边界、想先发散探索——"帮我问问清楚"、"先把想法理一理存着"、"方向还乱，聊开了再说"。

这是创意空间，不是设计文档。目标是产生可留存的想法、方向和洞察，供后续 epic planning 消费。

**怎么聊**：启动 grill 档（见上节"对话节奏 > grill 档"），同时自由发散——聊方案、聊类比、聊技术可能性、聊限制。对话比 case 2 更开放，不急着收敛。

**升降级**：
- grill 完感觉够清楚了想直接拆 → case 3；沿用 case 4 已落的 brainstorm.md（如有）后同轮加载 `cs-epic`，不新建 case 3 产物
- 聊着发现其实一个 feature 能装下 → case 2
- 聊着发现已经全清楚 → case 1

**落盘**：用户说"先这样"/"差不多了"/"存一下"，或 AI 判断 grill 已到 3-5 轮上限，主动说"这块我先帮你落到 brainstorms 里，之后 `cs-epic` 会读到"。

路径：`.codestable/brainstorms/{slug}/`

```
.codestable/brainstorms/{slug}/
└── brainstorm.md    创意记录
```

目录不存在就创建。slug 根据方向自拟英文小写连字符。

文档模板见同目录 `reference.md` 的"open brainstorm 模板"。

- `doc_type: brainstorm` 区别于 case 2 的 `feature-brainstorm`
- 比 case 2 模板更自由——不要求"选定方向"，允许保留多个倾向
- 不需要"考虑过的方向"那种结构化对比——那是 design 前的事，这里只是创意记录

**和 epic 的衔接**：`cs-epic` planning 阶段启动时会搜 `.codestable/brainstorms/` 看有没有相关 brainstorm。如果有，内部 roadmap 主文档把 brainstorm 当输入材料读，不重复分诊直接拆。

**退出**：落盘后告诉用户"想法存到 `{路径}` 了"，并询问是否现在进入 epic planning；只有用户确认后才在当前 run 加载 `cs-epic`，同时传递该路径。如果 grill 中愿景已经比较清楚，可先询问是否用 `cs-req draft` 落 requirement；未经确认不自动改道

---

## 硬性边界

1. **不跳过分诊**——任何长度的讨论开始前都要先判 case
2. **不替用户决定规模**——case 2 / 3 / 4 边界模糊就问用户"你脑子里这块是一个 feature 能装下的规模吗，还是需要先 grill 存着"
3. **不落盘非 case 2 / case 4 产物**——case 1 / 3 不写文件
4. **不处理 bug / 重构**
5. **不在 case 1 / 3 启动 grill 档**——case 1 已清楚硬 grill 反人性，case 3 用户已 ready 拆解不需要 grill
6. **确认前不启动 design 或 roadmap**——case 1 / 2 / 4 必须等用户点头，点头后同轮加载目标；case 3 的 ready 拆解已是确认，直接继续 `cs-epic`

---

## 常见错误

- 跳过分诊默认所有讨论按 case 2 推进——大需求被硬塞进一个 feature
- 分诊问得像问卷——一两轮该有方向；问到第三轮还在对齐规模说明方法错了
- case 1 硬凑 brainstorm note——用户已清楚还写一份模板，后人误以为这里发生过有价值讨论
- case 3 自己做拆解——越俎代庖，那是 roadmap 的产物
- 升降级信号不理——范围扩大还继续 case 2，最后落一份塞不下所有子模块的 note
- 把 case 4 当 case 3 处理——用户想 grill 存着，却直接移交 roadmap 把未成形的想法硬拆成 feature
- 把 case 3 当 case 4 处理——用户已经 ready 拆解，却强行 grill 拖延节奏
- 把待确认出口写成"请重新触发目标 skill"——多制造一次调用；正确行为是确认后同轮加载
- 一次只给一个方案让用户评价——用户被锚定提不出别的方向
- 复述用户方案就落盘——记录员心态，AI 没提供思考伙伴的价值
