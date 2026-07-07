# Hypotheses — cs-feat-refactor-ab-001

## 背景

用 build-cs-skill 对 cs-feat 做 prompt-as-code 重构（加 `## Spec` 状态机 + `## Workflow` 执行主线 + frontmatter `contracts`）。本实验用**真实 api** 验证重构未使 design 生成行为回退。

## H1（非劣性回归）

**重构版（baseline）的 design 语义召回不低于原版（original）。**

- variants：
  - `baseline` = 当前 cs-feat（重构版，runner 读 live `plugins/codestable/skills/cs-feat/SKILL.md`）
  - `original` = 重构前 HEAD 快照（`variants/original.md`，冻结对照）
- models（跨供应商）：`claude-sonnet-4-6`、`claude-haiku-4-5`、`gpt-5.5`、`gpt-5.4`
- k = 5，harness = `api`（真实）
- scorers：`planted_defect`（recall，measured）+ `recall_judge`（语义召回，soft）
- fixtures：8 个 design 生成样本（与 cs-feat-001 同源，此处冻结）

## 判据

跨全部四模型，满足任一即 **CONFIRMED 无回退**：
- 重构 recall_judge 均值 ≥ 原版 − 0.05；或
- 重构 95%CI 下界 ≥ 原版 − 0.05。

## 诚实 caveats（认知诚实，务必随 verdict 一起读）

1. **非盲预注册**：本 hypotheses 在重构完成、且 k=1/k=3 初步观察（均无回退）之后补写。方向（无回退）在重构时已假定；k=5 用于把 `[underpowered]` 观察坐实。**不宣称盲预注册**。
2. **judge 独立性（已处理）**：`judge_model=claude-opus-4-8`，**不在 model_list**，对全部被测（sonnet/haiku/gpt-5.5/gpt-5.4）均独立——同源偏差已消除。`judge_issues` 校验通过（无 warning）。opus 亦是四者之外能力最强的 oracle。
3. **recall_judge = soft**：LLM judge 是主观自评，按认知诚实规则标 soft（非 measured）。**真实 api 调用 ≠ measured**；measured 只给机械可验的 `planted_defect` recall。
4. **样本**：n=40/(variant×model)（8 fixture × k5）。够算 stderr，但为单实验、非多电池回归。

## 复现

见 `README.md`（真实 api 需 gateway credentials，**不入库**）。
