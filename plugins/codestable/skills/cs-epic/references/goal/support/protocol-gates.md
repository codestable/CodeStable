# Goal Gate Policy

## 1. 通用 Gate Result

每个 gate 输出：

```json
{
  "gate_id": "gate-name",
  "stage": "stage.name",
  "status": "passed|failed|blocked|skipped",
  "blocking": [],
  "warnings": [],
  "evidence": [],
  "providers": {}
}
```

`failed` 表示 gate 完成但有 blocking。`blocked` 表示缺输入或环境不可判断。`skipped` 只允许非核心 gate，必须写理由。

`status: protocol-only` 表示该 gate 是协议阶段规则，由对应 review / QA / acceptance / audit 技能读取 evidence 后执行；它不是可直接调用的脚本，机器 runner 不应把它当成缺失脚本。

## 2. feature_design.before_approve

必须有：

- design-review passed
- checklist YAML 可解析
- Acceptance Coverage Matrix
- DoD Contract

失败返回 design 修订；goal 模式不接管未 approved design。

## 3. implementation.before_review

必须运行：

- `scope-gate`
- `dod-runner`
- `evidence-pack`

`scope-gate` / `dod-runner` / `evidence-pack` 由 `cs-onboard` 安装到项目 `.codestable/tools/`；缺脚本说明项目骨架过旧，应先重跑 `cs-onboard` 刷新 gate runtime。

检查：

- checklist steps 全部 `done`。
- 当前 diff 没有未解释的范围外文件。
- 清洁度通过。
- checklist `dod.commands` 的 core 命令有执行证据。
- evidence pack 已生成并包含 Scope、DoD Results、Validation Commands、Scope And Cleanliness、Residual Risks。

失败返回 `cs-feat` implementation 阶段；缺 evidence 时补证据，不能进入 review。

## 4. review.before_pass

必须运行 `review-evidence-gate`。

检查：

- review 基于当前 diff。
- review `status=passed`。
- review 必须由独立 Task agent reviewer 完成；frontmatter `reviewer: subagent` 或 `subagent+ocr` 是默认放行锚点。`reviewer: ocr` / `self` 只能作为用户显式降级 fallback，不能静默通过。
- 无 unresolved blocking。
- review 明确消费 evidence pack 和 gate results。
- high-risk provider warnings 已解释或交给 QA。

失败返回 review-fix、补 evidence，或在 reviewer 不独立时 handoff / 启动独立 review。

## 5. qa.before_acceptance

必须运行 `qa-evidence-gate`。

检查：

- QA `status=passed`。
- QA matrix 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- 功能性核心路径有实际运行证据。
- 非功能性 feature 有替代证据理由。
- QA 没有把核心缺口写成 residual-risk。
- 高风险 feature 建议启用独立 QA Task agent；其输出必须由主流程核验并写入 QA 报告，runner 不替代正式 verdict，结果消费后按 Task agent 生命周期关闭。

失败返回 qa-fix，再重跑 review 和 QA。

## 6. acceptance.before_done

必须运行 `acceptance-dod-gate`。

检查：

- acceptance `status=passed`。
- checklist checks 全 `passed`。
- blocking DoD 均有 pass evidence。
- roadmap item 已回写。
- residual risk 不包含核心验收缺口。
- 可选只读 acceptance Task agent auditor 只能提供复核 findings；checklist / roadmap / requirement / acceptance 状态写入必须由主流程 owner 完成，结果消费后按 Task agent 生命周期关闭。

失败返回 acceptance 修；实现缺口回 impl 并重跑 review / QA / acceptance。

## 7. roadmap_audit.before_complete

必须运行：

- `goal-consistency-gate`
- `goal-audit-gate`

检查：

- goal-state 全部 features 为 `accepted`。
- items.yaml 条目均为 `done` 或有理由 `dropped`。
- 每个 feature 的 review / QA / acceptance / evidence pack / gate results / DoD contract results / DoD results 存在。
- review / QA / acceptance 均 `status=passed`，checklist steps 全 `done`，checks 全 `passed`。
- final aggregate commands 已重跑或有非核心 trust-prior 理由。
- provider warnings 已解释。
- goal-audit.md 已落盘且 `status=passed`。

失败进入 audit repair；三轮仍失败则 handoff。

## 8. Provider Policy

- provider unavailable 不阻塞基础流程。
- provider warning 必须被 review / QA / audit 解释。
- 未解释的核心风险可阻塞。
- meta-cc 首批只读取已有摘要文件或记录 unavailable。
