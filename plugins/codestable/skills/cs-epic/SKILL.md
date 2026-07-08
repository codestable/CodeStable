---
name: cs-epic
description: "Epic 主入口。用于大需求或系统级能力的端到端拆解与长程执行：planning、review、子 feature design（批量）、goal 包。不要用于单个功能(cs-feat)、bug 修复(cs-issue)、行为等价重构(cs-refactor)、对外文档(cs-docs)。"
argument-hint: "[--stage planning|review|goal-package] <epic>"
contracts:
  - grep: "restoreEpicStage"
  - grep: "epic_child_batch: true"
  - grep: "codestable-workflow-next.py epic"
  - grep: "统一确认所有 design"
  - grep: "独立 Task agent reviewer"
  - grep: "final_answer_allowed: false"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-epic

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-epic` 是大需求端到端入口。用户文档统一叫 epic；为兼容历史产物，第一版内部目录、frontmatter 和工具仍使用 `roadmap`。用户确认 roadmap 和所有子 feature design 后，默认生成 goal 包并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。

旧技能 `cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal` 长期保留为兼容入口，只传入 `requested_stage`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage planning|review|goal-package` 表示阶段意图，其余文本作为大需求描述。旧裸 token（如 `review`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

无参数默认行为：没有 stage / epic 描述时，扫描 `.codestable/roadmap/`、子 feature design 和 goal 包状态，用状态机恢复；若没有可恢复 epic 且用户原话也没有大需求目标，先问用户要规划哪个 epic。

入口意图不覆盖仓库事实。已有 roadmap review 未通过时先修规划；已有 feature design 未确认时不生成 goal 包。

---

## Spec

```haskell
csEpic :: EpicRequest -> EpicOutcome

data EpicRequest = EpicRequest
  { requestedStage : Maybe Stage         -- planning | review | goal-package
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Planning | Review | ChildDesignBatch | GoalPackage

data EpicState = EpicState               -- 从 .codestable/roadmap/{slug}/ 与子 features/ 恢复
  { roadmapStatus     : Missing | Draft | ReviewPassed | Confirmed
  , reviewStatus      : Missing | Passed | Blocking | Blocked
  , childrenDesign    : AllPassed | Pending   -- items.yaml 里所有未 dropped child 是否都有 design+checklist+passed review
  , allDesignApproved : Bool
  , hasGoalPackage    : Bool
  }

data EpicOutcome
  = RoutedTo Stage
  | ChildDesignBatch                     -- 逐项进入 cs-feat（epic_child_batch: true），不逐个停用户
  | HumanCheckpoint CheckpointReason
  | GoalHandoff Command
  | Completed EpicSummary
  | NeedsHuman Reason

data CheckpointReason = ConfirmRoadmap | ConfirmAllChildDesign | GoalDriverUnavailable | AmbiguousEpicTarget
```

```haskell
restoreEpicStage :: EpicState -> Intent -> EpicOutcome
restoreEpicStage(s, intent)
  | ambiguousTarget(s, intent)                              -> NeedsHuman "which epic?"
  | s.roadmapStatus == Missing                              -> RoutedTo Planning      -- 大需求未拆解
  | s.roadmapStatus == Draft && s.reviewStatus == Missing   -> RoutedTo Review        -- roadmap draft 无 passed review
  | s.reviewStatus in [Blocking, Blocked]                   -> RoutedTo Planning      -- 修订后重跑 review
  | s.reviewStatus == Passed && s.roadmapStatus /= Confirmed
      -> HumanCheckpoint ConfirmRoadmap        -- roadmap review passed 但用户未确认：停下让用户确认 epic 规划
  | s.roadmapStatus == Confirmed && s.childrenDesign == Pending
      -> ChildDesignBatch                      -- 逐项进 cs-feat（epic_child_batch: true）；design 保持 `draft`，不逐个让用户确认
                                               -- 仍有子 feature 未完成 design-review 就继续下一个，不停用户
  | s.childrenDesign == AllPassed && not s.allDesignApproved
      -> HumanCheckpoint ConfirmAllChildDesign -- 停下让用户统一确认所有 design，确认后逐份标 approved
  | s.allDesignApproved && not s.hasGoalPackage             -> RoutedTo GoalPackage
  | s.hasGoalPackage                                        -> GoalHandoff "/goal"    -- 派发失败输出可粘贴 /goal 并停止
```

`restoreEpicStage` 是唯一路由真相：扫 `.codestable/roadmap/{slug}/` 与子 features/ 恢复 `EpicState`，按上方分支选下一步；各 stage 加载哪个 protocol 见「Reference 加载」。子 design 阶段是连续 `ChildDesignBatch` loop（见「Child design batch loop」），在 `ConfirmAllChildDesign`（统一确认所有 design）之前不得 final answer。`HumanCheckpoint` 三点见下方「人工 checkpoint」。

`cs-epic` 不在主线程直接执行长程 goal；只能通过可见 Task agent goal driver 派发。没有可见 driver 或派发失败时，回退为用户手动粘贴 `/goal`。

---

## Workflow

主执行主线（每次调用按序走；planning/review/goal 的厚规则见对应 protocol，本节只定顺序与边界）：

1. **`preflight`** — 读 `.codestable/attention.md`；缺失则 `route to cs-onboard`；不得用 `AGENTS.md`/`CLAUDE.md` 代替 CodeStable attention。
2. **`parseEntryIntent`** — 优先级 `flag > compat-preset > utterance`；`repoFacts override requestedStage`；空参不推断 stage。
3. **`restoreEpicStage`** — 扫 `.codestable/roadmap/` + 子 features/ + goal 包恢复 `EpicState`，选 next stage。
4. **`loadStageProtocol`** — progressive reference loading：进某 stage 才加载该 stage 一个 protocol，禁止 eager 读全部 references。
5. **`ChildDesignBatch` loop** — roadmap 确认后，逐个子 feature 经 `cs-feat`（`epic_child_batch: true`）连续推进 design/design-review；每轮先跑 `codestable-workflow-next.py epic`，输出 `final_answer_allowed: false` 时不得结束本轮；单个 child 完成只是内部进度，不停用户、不 final answer。
6. **`HumanCheckpoint` / `GoalHandoff`** — 所有 child design-review passed 后停下让用户统一确认所有 design，确认后逐份标 approved；再生成 goal 包，经可见 Task agent goal driver 派发，派发失败则输出可粘贴 `/goal`。
7. **`exitRecoverable`** — artifact 已落盘、next stage 明确、或 checkpoint reason 明确，任一即可让下次调用从 `repoFacts` 恢复。

---

## 文件放哪儿

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── {slug}-roadmap-review.md
├── goal-plan.md
├── goal-state.yaml
├── goal-protocol*.md
├── goal-audit.md
└── goal-features/
```

普通子 feature 仍放 `.codestable/features/YYYY-MM-DD-{feature-slug}/`。

---

## Child design batch loop

roadmap 已确认后，子 feature design 阶段是一个连续 batch loop，不是单次子任务：

- 每轮开始、每个 child design-review 后、以及准备 final answer 前，先运行
  `python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py epic --roadmap .codestable/roadmap/{slug} --json`。
- hook 输出 `must_continue: true` 或 `final_answer_allowed: false` 时，必须按 `next_action` 继续；不得结束本轮。
- 每轮先扫描 `{slug}-items.yaml`，找出下一个 `planned` / `in-progress` 且缺 design、checklist 或 `passed` design-review 的 item。
- 完成某一个 child 的 design + design-review `passed` 只是内部进度；不得 final answer、不得要求用户确认该 child、不得进入实现。
- 只有 items.yaml 里所有未 dropped child 都已有 design + checklist + `passed` design-review，才允许触发“所有 design 统一确认”的人工 checkpoint。
- 若下一条 child 可继续推进，本轮必须继续调用 `cs-feat`，而不是用“下一步继续处理下一个 child”作为结束汇报。

---

## Reference 加载

- planning：`references/planning/protocol.md`，必要时 `references/planning/reference.md`、`references/planning/support/codebase-design.md`
- review：`references/review/protocol.md`。**gate 必需独立 Task agent reviewer**：主 agent 本地
  审查不得定稿、不得给 `passed`；roadmap 修订后的**每一轮重审同样适用**，降级须
  approval-report + 用户明确授权（细则见 protocol）。子 feature design-review 经 `cs-feat`
  同受此约束。
- goal-package：`references/goal/protocol.md`，并复制 `references/goal/support/protocol*.md` 和 `references/goal/support/goal-command-template.md`
- goal driver：`.codestable/reference/agent-conventions.md` 的 Goal driver 派发规则
- child feature：通过 `cs-feat` 主入口推进，不直接调用旧阶段技能；调用时带内部上下文 `epic_child_batch: true`，让单 feature 人工 checkpoint 推迟到 `cs-epic` 的批量确认

---

## 人工 checkpoint

1. roadmap/epic planning review passed 后，用户确认规划。
2. 所有子 feature design-review passed 后，用户统一确认 design。
3. goal driver 不可见、派发失败或返回 `CS_ROADMAP_GOAL_HANDOFF` 时，把 `/goal` 指令或 handoff 原因交给用户。

不要在第一个或任一单独子 feature design-review passed 后停下来要求用户确认执行；那是
`cs-feat` 普通单 feature 行为，在 `cs-epic` 子流程里必须延后到所有子 feature 都完成
design-review 后统一处理。

---

## 退出条件

- child design batch loop 只在全部 child design-review passed、遇到 blocking / pending / 授权问题、或用户明确要求停止时才可结束。
- 若 `codestable-workflow-next.py` 返回 `final_answer_allowed: false`，当前 run 不能退出。
- 规划、审查、子 feature design 和 goal 包状态能从仓库事实恢复。
- 历史 `roadmap` 命名只作为内部兼容说明出现；用户主路径称为 epic。
- 需要同步文档或记忆时提示 `cs-docs-neat`。
