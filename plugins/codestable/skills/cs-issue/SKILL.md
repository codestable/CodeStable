---
name: cs-issue
description: "Issue 主入口。用于修复 bug / 诊断报错 / 定位既有行为异常，从问题恢复并推进 report、analyze、fix、review。不要用于新增功能(cs-feat)、行为等价重构(cs-refactor)、对外文档(cs-docs)、大需求拆解(cs-epic)。"
argument-hint: "[--stage report|analyze|fix] <issue>"
contracts:
  - grep: "restoreIssueStage"
  - grep: "progressive reference loading"
  - grep: "fix-note"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-issue

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-issue` 是问题修复的唯一推荐入口，是一个 workflow skill：从仓库事实恢复当前阶段、加载对应阶段协议、在人工 checkpoint 停下。它把问题从记录、根因分析、定点修复、验证、fix-note 和 code review 衔接到闭环。真正的 report/analyze/fix 怎么做由各阶段 protocol 负责（见下方 Progressive Reference Loading）。

旧阶段技能 `cs-issue-report`、`cs-issue-analyze`、`cs-issue-fix` 长期保留为兼容入口，只传入 `requested_stage`。

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage report|analyze|fix` 表示阶段意图，其余文本作为问题描述。旧裸 token（如 `fix`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

无参数默认行为：没有 flag / 问题描述时，不猜阶段；扫描 `.codestable/issues/`、目标产物和当前 git diff，用状态机恢复下一步。若没有可恢复 issue 且用户原话也没有问题目标，返回 `NeedsHuman` 问处理哪个 issue。

入口意图不覆盖仓库事实。若 report 已存在但用户从 report 兼容入口进来，继续 analyze；若代码已改但无 fix-note，进入 fix 验证/记录。

## Spec

```haskell
csIssue :: IssueRequest -> IssueOutcome

data IssueRequest = IssueRequest
  { requestedStage : Maybe Stage         -- report | analyze | fix
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Report | Analyze | Fix | CodeReview | FastPath

data IssueState = IssueState             -- 全部从 .codestable/issues/{slug}/ 恢复
  { issueDir     : Maybe Path
  , hasReport    : Bool
  , rootCause    : Unknown | Clear       -- 读代码后根因是否明确
  , hasAnalysis  : Bool
  , codeStatus   : NotStarted | Changed  -- 当前 git diff
  , hasFixNote   : Bool
  , reviewStatus : Missing | Passed | Blocking
  }

data IssueOutcome
  = RoutedTo Stage
  | HumanCheckpoint CheckpointReason
  | Completed IssueSummary
  | NeedsHuman Reason

data CheckpointReason = ConfirmReport | ConfirmFixPlan | ConfirmFastPath | AmbiguousIssueTarget
```

`restoreIssueStage` 从仓库事实选下一步（新增能力而非坏掉的既有行为 → 路由 `cs-feat`）：

```haskell
restoreIssueStage :: IssueState -> EntryIntent -> IssueOutcome
restoreIssueStage(s, intent)
  | ambiguousTarget(s, intent)                          -> NeedsHuman "which issue?"
  | isNewCapability(intent)                             -> RoutedTo <cs-feat>   -- 非 bug
  | not s.hasReport                                     -> RoutedTo Report
  | s.hasReport && s.rootCause == Clear && smallFix(s) && not crossModule(s)
      -> HumanCheckpoint ConfirmFastPath                                        -- 确认后直接 fix，仍写 fix-note
  | s.hasReport && s.rootCause == Unknown && not s.hasAnalysis -> RoutedTo Analyze
  | s.hasAnalysis && s.codeStatus == NotStarted        -> RoutedTo Fix
  | s.codeStatus == Changed && not s.hasFixNote        -> RoutedTo Fix          -- 验证/记录部分
  | s.hasFixNote && s.reviewStatus == Missing          -> RoutedTo CodeReview
  | s.reviewStatus == Blocking                         -> RoutedTo Fix          -- 窄修复，修完重跑 review
  | s.reviewStatus == Passed                           -> Completed summary     -- 汇报完成，提示 docs/neat 候选
```

`restoreIssueStage` 是唯一路由真相：启动后扫描 `.codestable/issues/`、读取目标 issue 产物、检查当前 git diff 恢复 `IssueState`，按上方分支选下一步；各 stage 加载哪个 protocol 见下方 Progressive Reference Loading。

## Workflow

主执行主线（每次调用按序走；各 stage "怎么做" 的厚规则见对应 protocol，本节只定顺序与边界）：

1. **`preflight`** — 读 `.codestable/attention.md`；缺失则 `route to cs-onboard`；不得用 `AGENTS.md`/`CLAUDE.md` 代替 CodeStable attention。
2. **`parseEntryIntent`** — 优先级 `flag > compat-preset > utterance`；`repoFacts override requestedStage`；空参不推断 stage。
3. **`restoreIssueStage`** — 扫 `.codestable/issues/` + artifact + `git diff` 恢复 `IssueState`，选 next stage；新增能力（非 bug）→ `route to cs-feat`。
4. **`loadStageProtocol`** — progressive reference loading：进某 stage 才加载该 stage 一个 protocol，禁止 eager 读全部 references。
5. **`executeOrRoute`** — report/analyze 落盘 artifact；fix 循环修复+验证+写 `fix-note`；遇 `HumanCheckpoint` 必停。
6. **`exitRecoverable`** — `fix-note` 必出（根因/改动/验证/遗留风险），next stage 或 checkpoint reason 明确。

## 文件放哪儿

```text
.codestable/issues/{YYYY-MM-DD}-{slug}/
├── {slug}-report.md
├── {slug}-analysis.md
└── {slug}-fix-note.md
```

日期取发现/提报问题当天。`fix-note.md` 是必出产物，即使走快速通道也要写。

## Progressive Reference Loading

进入某阶段才加载**该阶段一个 protocol**，不在启动时读全部（progressive reference loading）：

- report → `references/report/protocol.md`
- analyze → `references/analyze/protocol.md`
- fix → `references/fix/protocol.md`，必要时 `references/fix/reference.md`
- code review → 公开横切 skill `cs-code-review`

禁止：启动即读全部 references；用 fix 协议做 report；code review 未过就当修复完成。

## 快速通道

快速通道（`FastPath`）是 `cs-issue` 内部模式，不是单独技能。必须同时满足：

1. 读代码后能指出明确根因。
2. 修复很小，通常 1-2 处。
3. 无跨模块影响风险。

不满足就走标准 report → analyze → fix。进入标准路径后默认不再二次改判，避免阶段之间口径漂移。

## 人工 checkpoint

必须停下等用户明确确认（`HumanCheckpoint`）：

1. `ConfirmReport`：report 阶段确认问题描述、复现、期望/实际、环境、严重度。
2. `ConfirmFixPlan`：analyze 阶段确认推荐修复方案和风险。
3. `ConfirmFastPath`：走快速通道前确认根因明确、改动小、无跨模块风险。

fix 阶段的验证结果和 review blocking 处理按协议循环，不在每步默认打断用户。

## Failure Behavior

返回 `NeedsHuman` 当：`.codestable/attention.md` 缺失（→ `cs-onboard`）；无可恢复 issue 目标；issue 范围模糊；requested stage 与仓库事实冲突；问题实为新增能力（→ `cs-feat`）；修复需产品判断而非定点修复。报告：当前 issue 目录、阻塞原因、下一步用户动作、已写文件、是否可安全重试。

## 退出条件

- `{slug}-fix-note.md` 已写明根因、改动、验证和遗留风险。
- 必要 code review 已通过或阻塞项已清楚交回。
- 修复暴露新 feature 需求时，不在 issue 内偷做，另开 `cs-feat`。
