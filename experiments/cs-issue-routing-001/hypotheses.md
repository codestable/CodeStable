# Hypotheses — cs-issue-routing-001（预注册：写于任何 routing eval 运行之前）

## 背景

用户质疑：加固式重构加的 `## Spec`（restoreIssueStage）与正文状态机表格并列冗余，contracts 保护的是装饰。为回答"Spec 到底改不改变 agent 路由行为"，做三方 routing A/B/C：

- `original`：重构前（HEAD，只有中文状态机表格，无 Spec）
- `hardened`：加固式（表格 + Spec 并列冗余）
- `baseline`：重写式（live 版：删表格，`restoreIssueStage` 是唯一路由真相）

## 评测方式

routing-decision fixtures（10 个，覆盖 restoreIssueStage 全分支 + 快速通道 + 新能力转 cs-feat + 模糊目标 NeedsHuman）。build_routing_prompt 给 skill 全文 + 仓库状态，模型只输出 JSON 决策；routing_decision scorer 机械比对（[measured]）。k=3 × 3 模型（sonnet/haiku/gpt-5.5）。

## H1（主假设）

**三个变体的 routing_ok 无显著差异**（|Δ| < 0.10）——即路由正确性主要由"规则是否写清楚"决定，与表达形式（表格 vs Haskell Spec vs 两者并列）关系不大。

若成立：Spec 的价值定位应诚实降级为"可读性/可测性组织"，而非"行为增益"；重写式的意义在删冗余（token 更少、单一真相易维护），不在提升路由。

## H2（对立假设，若 H1 不成立）

- H2a：`baseline`（Spec 唯一真相）显著更高 → 形式化分支函数比中文表格更能约束路由，"prompt-as-code 真做法"有行为增益。
- H2b：`original`（只有表格）显著更高 → Spec 的 Haskell 语法反而干扰小模型，重构有害，应回退。
- 显著判据：跨 ≥2 个模型同向、|Δ| ≥ 0.10、且逐 fixture 检查非单点噪声。

## 诚实 caveats

1. 本文件在 routing eval 任何一次运行之前写就（真预注册）；但 fixtures 由同一作者基于 baseline 的 Spec 分支设计，可能存在**利于 Spec 表达形式**的选择偏差——original 的表格行为若与 Spec 分支有语义出入，以 fixture expect 为准（其 oracle 是"当前认定的正确行为"）。
2. routing_ok 是机械比对 [measured]，但 target 匹配用了 normalize+包含的宽松规则，可能对措辞不同的正确答案漏判——逐 evidence 抽查后再下结论。
3. k=3、n=30/cell（10 fixtures × 3），单元格 [underpowered]；跨 3 模型 × 10 fixtures 聚合后可到可用功效。

## 运行中校准记录（按 caveat 2 预案执行，2026-07-07）

首批段（sonnet）逐 evidence 抽查发现 4 个 fixture 的 oracle 对 original 系统性不公平——original 没有 Spec 引入的类型名词汇，答案语义正确但措辞不同（如 `rt-i09` 三变体全答 `GoalHandoff/cs-feat`、`rt-i03` original 答 "confirm fix plan"）。已放宽：`rt-i09` +result_type_any、`rt-i03` +target_any、`rt-f02` +target_any、`rt-f05` +result_type_any。**所有段（新旧）统一用校准后 oracle 离线重打分**（`rescore-routing.py`，从 evidence.observed 重算，零 API），口径一致。`rt-f04` 保持严格未放宽——它是真实路由分歧（见下），不是措辞差异。

## 已发现的真实优化项（待全段跑完后实施 + 复评）

- **cs-feat rt-f04**（ff 请求 + 跨公开契约）：全模型 baseline 0.67 / original 0.33。live Spec 中 ff-不合格分支与 `ConfirmScopeChange` 存在优先级歧义。
  **已实施两轮措辞优化并复评（2026-07-07，cs-feat 全部 routing 段与 k5 baseline 段完成后才改 live）**：
  - 轮1：guard 注释明确「不合格不停等确认」+ ConfirmScopeChange 加「仅长程执行中」限定 → sonnet 0/3→3/3，但 haiku 3/3→0/3（新注释"并说明"引导它答 NeedsHuman——reason 全对、outcome 类型错）。
  - 轮2：负向澄清「结果是 RoutedTo Design（不是 NeedsHuman、不是 checkpoint）」 → haiku 3/3、sonnet 3/3、gpt 3/3，**rt-f04 = 1.00 跨三模型**。
  - 诚实声明：rt-f04 已进入优化循环、不再是 held-out fixture；其分数是针对性措辞迭代（两轮为限）的结果。轮1 的 haiku 翻转是教训：给中小模型的澄清要**排除错误选项**，只加正向描述可能引入新歧义。
