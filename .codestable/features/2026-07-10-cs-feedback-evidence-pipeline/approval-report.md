---
doc_type: approval-report
unit: 2026-07-10-cs-feedback-evidence-pipeline
status: approved
reason: blocker
created_at: 2026-07-11
decision: option-a
answered_at: 2026-07-11
---

# Approval Report

## Decision History

- 2026-07-11：owner 选择 Option A，批准为反馈证据能力新建 requirement backfill；后续仍按
  `cs-req` 的 ReviewDraft checkpoint 审核完整正文。
- 2026-07-11：owner 确认完整 `feedback-evidence-pipeline` requirement 初稿“可以了”；允许
  落盘 current requirement、刷新 `VISION.md` 并恢复 feature acceptance。

## Decision Needed

决定本 feature 的用户可感能力如何进入长期 requirement 层。当前实现、Round 17 code review 和
Round 2 QA 均已通过，但 acceptance 不能在 requirement 归属为空时直接标记完成。

## Why Now

Design frontmatter 的 `requirement` 为空；仓库现有 `.codestable/requirements/` 只有
`plugin-market-distribution.md`，不覆盖反馈证据能力。本 feature 改变了用户调用方式、反馈
产物、公开确认边界和 regression candidate 交接，命中 acceptance L3 的“新增用户可感能力”
分支，必须先有 owner-approved backfill/delta。

## Context

建议 backfill 的能力边界：

- 用户显式调用 `cs-feedback` 后，系统安全定位当前会话并生成可追溯 evidence/triage。
- 公开 preview 只含 allowlist 字段，GitHub 上传必须逐次确认。
- 未就绪反馈可保存和分诊，但不能进入正式 regression fixture。
- shipped skill 只产 local-private candidate，维护仓库 promotion 工具负责正式 fail-closed 提升。
- 不包含后台遥测、自动上传、默认全历史扫描或自动修改目标 skill。

## Options

### A. 新建反馈证据能力 requirement（推荐）

授权后续通过 `cs-req` backfill 新建一份 current capability requirement，以上述能力边界为
愿景与用户故事，并把本 feature 记录为首个实现变更。随后回到 acceptance，机械关联 requirement、
复核 21 checks 并完成最终审计。

### B. 暂缓 requirement 决策

保留当前实现、passed review 和 passed QA，但 goal 继续停在 handoff/blocked；不创建长期
requirement，也不把 feature 标记 complete。后续 owner 准备好能力命名/边界后再恢复。

## Recommendation

选择 A。现有代码已经形成稳定的用户入口与跨 skill artifact 边界；不落 requirement 会让后续
feature 无法从能力愿景层发现这套约束，容易重新引入自动上传、私有产物越界或 shipped/eval
运行时耦合。

## Risks And Tradeoffs

- A 会新增一份长期 requirement，并需要 `cs-req` 流程落盘；但不会改变已经批准的实现行为。
- B 不引入文档范围，但 feature 不能完成，后续恢复仍需同一决策。
- 不能选择“直接忽略 requirement 影响并完成”：这与 acceptance 的 Global Route Governance
  冲突，也不符合当前用户可见改动事实。

## Non-Automatic Actions

- 不会自动 commit、merge、push、创建 GitHub issue或上传任何反馈。
- 不会在 owner 回答前创建/改写长期 requirement。
- 不会借 requirement backfill 改动已批准 design 的功能范围或重新修改实现代码。

## After You Answer

- 选择 A：将本报告标为 approved，记录回答日期，加载 `cs-req` 完成 backfill，再恢复
  acceptance 的 21 checks 与 final audit。
- 选择 B：将本报告记录为 deferred，保持 goal handoff/blocked，等待后续恢复。
