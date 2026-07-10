---
doc_type: feature-goal-plan
feature: 2026-07-10-cs-router-direct-dispatch
status: complete
created: 2026-07-10
---

# cs-router-direct-dispatch Goal Plan

## 输入

- Design: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-design.md`
- Checklist: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-checklist.yaml`
- Design review: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-design-review.md`
- 用户确认依据：用户要求“根据建议优化，然后用 Task agent Claude Fable 评审”；design 经三轮 Fable review 后 approved。
- Baseline ref: `ab39a4be5673554336192e3615d2667bdaac893c`

## 执行与验证

- 代码行为 step 默认 RED → GREEN → VERIFY；不能 TDD 时记录 exception 与替代证据。
- 核心路径：四入口模式、current-run dispatch、onboard 串行恢复、二级出口 checkpoint、canonical target。
- 必跑命令：checklist CMD-001..005；package check 的两条发布元数据 finding 是已登记基线。
- DoD：implementation、独立 `subagent+ocr` review、mixed-feature QA、acceptance 均通过；19 个 checks 全 passed。

## 恢复说明

本 goal package 在 implementation/review/QA/acceptance 已完成后由 workflow-next 缺口检查发现并补齐。仓库终态事实优先于缺失的历史派发状态，因此直接恢复为 `complete/passed`；不得再派发 driver 重复实现。

## Handoff 条件

- approved design / 公开契约 / feature 范围需要改变。
- 独立 reviewer 未完成，或核心 QA 环境无法判断。
- 同一失败项三轮仍不通过。
- 用户要求暂停、改方向或终止。

## Literal Goal 指令

```text
/goal "执行 CodeStable feature 目录 .codestable/features/2026-07-10-cs-router-direct-dispatch 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md、cs-router-direct-dispatch-design.md、cs-router-direct-dispatch-checklist.yaml；状态为 complete/passed 时按终态优先，不得重复派发或重做；只有产物不一致时才按 goal-protocol.md 恢复。"
```
