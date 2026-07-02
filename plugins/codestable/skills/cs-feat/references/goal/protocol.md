# Feature Goal Package Protocol

## 目标

把一个已通过 design-review、并由用户确认的单个 feature 变成可恢复、可长程执行的 goal 包。

流程：

1. 确认 `{slug}-design.md` 已 `status: approved`，且 `{slug}-design-review.md` 为 `passed`。
2. 写 `goal-plan.md`、`goal-state.yaml`、`goal-protocol.md`。
3. 生成一条可粘贴 `/goal` 指令。
4. 按 `.codestable/reference/execution-conventions.md` 的 Goal driver 派发规则，优先用可见 Task agent 自动执行；派发失败就把 `/goal` 指令交给用户。

---

## 目录

在 feature 目录下新增：

```text
.codestable/features/YYYY-MM-DD-{slug}/
├── {slug}-design.md
├── {slug}-checklist.yaml
├── {slug}-design-review.md
├── goal-plan.md
├── goal-state.yaml
├── goal-protocol.md
├── {slug}-review.md
├── {slug}-qa.md
└── {slug}-acceptance.md
```

---

## 生成文件

`goal-plan.md` 必须包含：

- feature、design、checklist、design-review 路径
- 用户已确认 design 的时间和依据
- 必跑验证命令
- 核心验收路径；非功能性 feature 写替代证据
- DoD / gate policy 摘要
- handoff 条件

`goal-state.yaml`：

```yaml
feature: "{slug}"
status: ready-to-dispatch
baseline_ref: "{git rev-parse HEAD 或 no-git}"
stage: implementation
design: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-design.md"
checklist: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-checklist.yaml"
review: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-review.md"
qa: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-qa.md"
acceptance: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-acceptance.md"
```

合法状态机：

| stage | status | 何时写入 | 下一步 |
|---|---|---|---|
| implementation | ready-to-dispatch | goal 包生成后 | 派发 driver 或打印 `/goal` |
| implementation | running | driver 开始实现时 | 完成 checklist steps |
| review | ready | implementation gates 通过，evidence 已生成 | 运行 `cs-code-review` |
| review | fixing | review 有 blocking，进入 review-fix | 修完回 `review: ready` |
| qa | ready | review passed | 运行 `cs-feat` QA |
| qa | fixing | QA failed / blocked，进入 qa-fix | 修完回 `review: ready`，重跑 review 和 QA |
| acceptance | ready | QA passed | 运行 `cs-feat` acceptance |
| complete | passed | acceptance passed 且无 handoff | 打印 `CS_FEATURE_GOAL_COMPLETE` |
| handoff | blocked | 命中 handoff 条件 | 打印 `CS_FEATURE_GOAL_HANDOFF` |

每次 stage / status 变化都要立即写回 `goal-state.yaml`。driver 中断后，后续 agent 先读 `goal-state.yaml`，再按仓库事实核验对应产物是否存在且状态匹配；不一致时以仓库事实为准并修正 state。

`goal-protocol.md` 必须写明执行 loop：

1. 读取 design、checklist、goal-plan、goal-state。
2. 进入 `cs-feat` implementation 阶段完成 checklist steps。
3. 运行 implementation gates，生成 evidence pack / gate results / DoD results。
4. 进入 `cs-code-review`；有 blocking 就 review-fix 后重跑 review。
5. review passed 后进入 `cs-feat` QA；QA failed / blocked 就 qa-fix 后重跑 review 和 QA。
6. QA passed 后进入 `cs-feat` acceptance，更新 checklist checks 和必要长期文档。
7. 全部通过后打印 `CS_FEATURE_GOAL_COMPLETE`。

`goal-protocol.md` 还必须写明：

- Goal 模式接管：普通流程中各阶段停等用户确认的 checkpoint，在 goal 模式下改为写入报告、状态和证据记录；只有命中 handoff 条件才停。
- 每个阶段 gate 通过后按上表更新 `goal-state.yaml` 的 `stage` / `status`，保证 driver 中断后可按仓库事实重派续跑。
- handoff 输出格式：

```text
CS_FEATURE_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```

handoff 条件：

- 需要改变 approved design、feature 范围、公开契约或 roadmap item。
- 独立 Task agent reviewer pending / failed / blocked，且没有用户明确降级。
- 同一失败项三轮修复仍不通过。
- 外部凭证或环境缺失导致核心行为无法判断。
- 用户主动要求暂停、改方向或终止。

---

## Goal 指令

输出：

```text
/goal "执行 CodeStable feature 目录 .codestable/features/YYYY-MM-DD-{slug} 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md、{slug}-design.md、{slug}-checklist.yaml；这是已由用户确认 design 后的 goal 模式。按 goal-protocol.md 连续执行 cs-feat implementation、cs-code-review、cs-feat QA、cs-feat acceptance；review blocking 时做 review-fix 并重跑 review；QA failed / blocked 时做 qa-fix 并重跑 review 和 QA。只有当 CS_FEATURE_GOAL_COMPLETE 出现在 transcript 中，且 review passed、QA passed、acceptance passed、没有 CS_FEATURE_GOAL_HANDOFF，本 goal 才算完成。"
```

---

## 派发

生成 goal 包后，按 `.codestable/reference/execution-conventions.md` 的 Goal driver 派发规则执行：

- 有可见 Paseo subagent 或可见 native Task/Agent 时，启动 driver 并把 agent id / run id / 查看方式告诉用户。
- driver 不可见、不可追踪、缺授权或启动失败时，不启动后台任务，只打印 fenced `/goal`。
- 主 agent 不能仅凭“已派发”宣布完成；完成必须由 goal 产物和 transcript 标记证明。

---

## 完成判据

- goal 包已落盘。
- 已尝试可见 Goal driver 派发，或已明确回退为用户手动粘贴 `/goal`。
- 长程执行完成后应存在 review、QA、acceptance，且最终 transcript 有 `CS_FEATURE_GOAL_COMPLETE`。
