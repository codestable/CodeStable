---
name: cs-feat
description: "Feature 主入口。用于新功能或功能改造，从需求恢复并推进 design、design-review、goal package、implementation、code review、QA、acceptance。不要用于单纯 bug 修复(cs-issue)、行为等价重构(cs-refactor)、对外文档(cs-docs)、大需求拆解(cs-epic)。"
argument-hint: "[--stage design|design-review|impl|qa|accept|goal-package] [--mode fastforward] <feature>"
contracts:
  - grep: "restoreFeatureStage"
  - grep: "progressive reference loading"
  - grep: "must not auto-approve design"
  - grep: "design-review passed"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-feat

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-feat` 是 feature 的唯一推荐入口，是一个 workflow skill：从仓库事实恢复当前阶段、加载对应阶段协议、在人工 checkpoint 停下。用户只需持续调用本技能；本技能在 design gate 停下来等用户确认。确认 design 后默认生成单 feature goal 包，并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。真正的 design/QA/acceptance 怎么做由各阶段 protocol 负责（见下方 Progressive Reference Loading）。

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；`--stage <stage>` 表示阶段意图，`--mode <mode>` 表示执行模式，其余文本作为需求描述。

| 参数 | 入口意图 |
|---|---|
| `--stage design` | `requested_stage: design` |
| `--stage design-review` | `requested_stage: design-review` |
| `--stage impl` | `requested_stage: implementation` |
| `--stage qa` | `requested_stage: qa` |
| `--stage accept` | `requested_stage: acceptance` |
| `--stage goal-package` | `requested_stage: goal-package` |
| `--mode fastforward` | `requested_mode: fastforward` |

入口意图只是偏好；**仓库事实优先**（`restoreFeatureStage`），也优先于聊天历史。

无参数默认行为：没有 flag / 需求描述时，不猜阶段；扫描 `.codestable/features/`、目标产物与当前 git diff，用状态机恢复下一步。没有可恢复 feature 且用户原话也无新功能目标时，返回 `NeedsHuman` 问处理哪个 feature。

## Spec

```haskell
csFeat :: FeatureRequest -> FeatureOutcome

data FeatureRequest = FeatureRequest
  { requestedStage : Maybe Stage
  , requestedMode  : Maybe Mode          -- fastforward
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Design | DesignReview | GoalPackage | Implementation | CodeReview | QA | Acceptance | FastForward

data FeatureState = FeatureState          -- 全部从 .codestable/features/{slug}/ 恢复
  { featureDir       : Maybe Path
  , designStatus     : Missing | Draft | Approved
  , reviewStatus     : Missing | Passed | ChangesRequested | Blocked
  , hasGoalPackage   : Bool
  , codeStatus       : NotStarted | InProgress | Complete
  , qaStatus         : Missing | Passed | Failed | Blocked
  , acceptanceStatus : Missing | Passed
  , epicChildBatch   : Bool               -- cs-epic 批量上下文，非公开参数
  }

data FeatureOutcome
  = RoutedTo Stage
  | HumanCheckpoint CheckpointReason
  | GoalHandoff Command                   -- goal driver 派发 / 可粘贴 `/goal`
  | Completed FeatureSummary
  | NeedsHuman Reason

data CheckpointReason = ConfirmDesign | ConfirmScopeChange | GoalDriverUnavailable | AmbiguousFeatureTarget
```

`restoreFeatureStage` 从仓库事实选下一步（**must not auto-approve design**：design-review passed 后必须停等用户确认）：

```haskell
restoreFeatureStage :: FeatureState -> EntryIntent -> FeatureOutcome
restoreFeatureStage(s, intent)
  | ambiguousTarget(s, intent)                     -> NeedsHuman "which feature?"
  | wantsFastForward(intent) && ffEligible(s)      -> RoutedTo FastForward
  | wantsFastForward(intent) && not ffEligible(s)  -> RoutedTo Design            -- 不合格（含跨公开契约/大范围）：结果是 RoutedTo Design（不是 NeedsHuman、不是 checkpoint），在推进 design 的同时说明降级原因
  | s.designStatus == Missing                      -> RoutedTo Design
  | s.reviewStatus == Missing                      -> RoutedTo DesignReview
  | s.reviewStatus in [ChangesRequested, Blocked]  -> RoutedTo Design
  | s.reviewStatus == Passed && s.designStatus /= Approved
      -> if s.epicChildBatch then RoutedTo <return-to-cs-epic> else HumanCheckpoint ConfirmDesign
  | s.designStatus == Approved && not s.hasGoalPackage       -> RoutedTo GoalPackage
  | s.hasGoalPackage && s.codeStatus /= Complete             -> RoutedTo Implementation   -- 或 GoalHandoff
  | s.codeStatus == Complete && s.reviewStatus /= Passed     -> RoutedTo CodeReview
  | s.reviewStatus == Passed && s.qaStatus == Missing        -> RoutedTo QA
  | s.qaStatus in [Failed, Blocked]                          -> RoutedTo Implementation   -- qa-fix，修完重跑 review+QA
  | s.qaStatus == Passed && s.acceptanceStatus == Missing    -> RoutedTo Acceptance
  | s.acceptanceStatus == Passed                             -> Completed summary
```

## Workflow

主执行主线（每次调用按序走；各 stage "怎么做" 的厚规则见对应 protocol，本节只定顺序与边界）：

1. **`preflight`** — 读 `.codestable/attention.md`；缺失则 `route to cs-onboard`；不得用 `AGENTS.md`/`CLAUDE.md` 代替 CodeStable attention。
2. **`parseEntryIntent`** — 优先级 `flag > compat-preset > utterance`；`repoFacts override requestedStage`；空参不推断 stage。
3. **`restoreFeatureStage`** — 扫 `.codestable/features/` + artifact + `git diff` 恢复 `FeatureState`，选 next stage。
4. **`loadStageProtocol`** — progressive reference loading：进某 stage 才加载该 stage 一个 protocol，禁止 eager 读全部 references。
5. **`executeOrRoute`** — authoring stage（design/design-review/goal-package）落盘 artifact；implementation/QA/review loop 可不打断用户继续；遇 `HumanCheckpoint` 必停。
6. **`exitRecoverable`** — artifact 已落盘、next stage 明确、或 checkpoint reason 明确，任一即可让下次调用从 `repoFacts` 恢复。

## 文件放哪儿

```text
.codestable/features/{YYYY-MM-DD}-{slug}/
├── {slug}-design.md / {slug}-checklist.yaml
├── {slug}-design-review.md
├── goal-plan.md / goal-state.yaml / goal-protocol.md
├── {slug}-review.md / {slug}-qa.md / {slug}-acceptance.md
└── {slug}-ff-note.md          # 仅 fastforward
```

目录命名取首次创建当天，slug 小写字母/数字/连字符。feature 过程发现的 bug 另开 issue，不在 feature 里偷修。

## Progressive Reference Loading

进入某阶段才加载**该阶段一个 protocol**，不在启动时读全部（progressive reference loading）：

- design → `references/design/protocol.md`（必要时 support/intent-template.md、codebase-design.md）
- design-review → `references/design-review/protocol.md`
- goal-package → `references/goal/protocol.md`
- implementation → `references/implementation/protocol.md`（必要时 support/reference.md、tdd.md）
- code review → 公开横切 skill `cs-code-review`
- qa → `references/qa/protocol.md`
- acceptance → `references/acceptance/protocol.md`
- fastforward → `references/fastforward/protocol.md`

禁止：启动即读全部 references；用 implementation 协议做 design；code review 未过就进 QA。

## Human Checkpoints

必须停下等用户明确确认（`HumanCheckpoint`）：

1. `ConfirmDesign`：design-review passed 后的 design 整体确认（**must not auto-approve design**，不得直接进 GoalPackage）。
2. `GoalDriverUnavailable`：goal driver 不可见 / 派发失败 / 返回 handoff 时，把 `/goal` 指令或 handoff 原因交给用户。
3. `ConfirmScopeChange`：仅长程执行中（design 已 approved 后）要改 approved design、feature 范围或公开契约时；入口阶段的 fastforward 不合格 / 大范围需求不触发本 checkpoint，直接 `RoutedTo Design`。

implementation / code review / QA / acceptance 的普通阻塞优先由 goal driver 按协议循环修复，不在每个阶段默认打断用户。

## Failure Behavior

返回 `NeedsHuman` 当：`.codestable/attention.md` 缺失（→ `cs-onboard`）；无可恢复 feature 目标；feature 范围模糊；requested stage 与仓库事实冲突；approved design 需要变更；goal driver 派发失败且无可见 Task agent。报告：当前 feature 目录、阻塞原因、下一步用户动作、已写文件、是否可安全重试。

## Fastforward

`requested_mode: fastforward` 只是模式请求，不是跳过安全的许可。进入前确认范围小、需求清楚、无跨系统术语/契约风险；不合格则解释原因并回标准 design 流程。产物固定 `{slug}-ff-note.md`，不生成标准 design/checklist/QA/acceptance 套件。`cs-feat-ff` 是兼容入口，不再单独维护快速模式规则。

## Epic 子 Feature 批量上下文

`cs-epic` 批量生成子 feature design 时以内部上下文 `epicChildBatch: true` 调用（非公开参数，不写入 argument-hint）。此时：design-review passed 后 design 保持 `draft`、**不执行单 feature 的人工整体 review checkpoint**、不改 approved；design-review passed 但未 approved 时**不在这里停，回到 `cs-epic` 继续下一个子 feature**，等所有 design 统一确认；回写 design/checklist/design-review/items.yaml 后返回 `cs-epic`，**不得用 final answer 要用户确认单个 child**；退出前运行 `python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py feature --feature .codestable/features/YYYY-MM-DD-{slug} --epic-child-batch --json`，若输出 `final_answer_allowed: false` 按 `next_action` 交回 `cs-epic`。单独调用 `cs-feat` 或无该上下文时，仍按普通 checkpoint 停。

## 兼容入口

旧阶段技能保留为兼容入口（`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`）：只传入 `requested_stage` / `requested_mode`，不维护独立规则。新文档与新调用一律用 `--stage` / `--mode`。

## 退出条件

- 当前阶段产物已落盘，状态可由仓库事实恢复（`restoreFeatureStage`）。
- 阻塞项、`HumanCheckpoint` 或下一阶段已明确说明。
- 标准流程最终需 design approved、review passed、QA passed、acceptance passed。
- 需要外部文档提示 `cs-docs`；阶段收尾/记忆同步提示 `cs-docs-neat`。

## 相关入口

- `cs-code-review`：实现后横切只读审查 gate。
- `cs-issue` / `cs-refactor` / `cs-docs` / `cs-epic` / `cs-docs-neat`。
