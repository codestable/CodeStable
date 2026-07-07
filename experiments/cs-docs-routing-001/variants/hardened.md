---
name: cs-docs
description: "Docs 主入口。触发：写/更新开发者指南、用户指南、API 参考；不包含 docs-neat 收尾整理。不要用于新功能实现(cs-feat)、修 bug / 诊断报错(cs-issue)、大需求拆解(cs-epic)、领域建模(cs-domain)、ADR 决策记录(best-adr)。"
argument-hint: "[--mode tutorial|api] <topic>"
contracts:
  - grep: "DocsState"
  - grep: "DocsOutcome"
  - grep: "restoreDocsStage"
  - grep: "HumanCheckpoint"
  - grep: "progressive reference loading"
  - grep: "manifest.yaml"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-docs

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-docs` 是对外文档写作的唯一推荐入口，只覆盖开发者/用户指南和 API 参考。阶段收尾、知识库卫生、agent 入口同步仍走独立的 `cs-docs-neat`。

旧技能 `cs-doc-tutorial`、`cs-doc-api` 长期保留为兼容入口，只传入 `requested_mode`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--mode tutorial|api` 表示文档模式，其余文本作为文档主题。旧裸 token（如 `api`）只作为历史提示词兼容识别；新文档和新调用一律用 `--mode`。

无参数默认行为：没有 mode / topic 时，先扫既有文档和公开表面，按状态机找 pending / draft / outdated 文档；若没有可恢复文档目标，再根据用户原话判断目标读者，不清楚就问用户选择。

用户没有明确文档类型时先判断目标读者和使用场景；仍不清楚就问用户选择。

---

## 模式边界

| 模式 | 产物 | 适用 |
|---|---|---|
| tutorial | 开发者指南 / 用户指南 | 教读者怎么完成一个任务 |
| api | API / 组件 / 命令参考 | 给读者查公开表面、参数、返回值、示例 |

`cs-docs` 不做全局同步、不整理 `.codestable/`、不毕业 agent memory。发现这些需求时提示 `cs-docs-neat`。

---

## Spec

```haskell
csDocs :: DocsRequest -> DocsOutcome

data DocsRequest = DocsRequest
  { requestedMode : Maybe Mode           -- tutorial | api
  , userTopic     : Maybe Text
  , repoFacts     : RepoFacts            -- 优先于 args / 聊天历史
  }

data Mode = Tutorial | Api

data Stage = TutorialStage | ApiStage | FocusedEdit | NeatHandoff

data DocsState = DocsState              -- 全部从 docs/ + manifest.yaml + 源码公开表面恢复
  { targetDoc   : Maybe Path
  , docStatus   : Missing | Draft | Current | Outdated  -- frontmatter status
  , manifest    : NoManifest | HasManifest             -- docs/api/manifest.yaml
  , entryStatus : Pending | Draft | Current | Outdated | Skipped
  , codeDrift   : InSync | Drifted       -- 相关源码/spec 是否已变
  }

data DocsOutcome
  = RoutedTo Stage
  | HumanCheckpoint CheckpointReason
  | Completed DocsSummary
  | NeedsHuman Reason

data CheckpointReason = ConfirmNewDoc | ConfirmOverwrite | ConfirmContractWording | AmbiguousReader
```

`restoreDocsStage` 从仓库事实选下一步（全局同步 / 记忆整理 → 路由 `cs-docs-neat`）：

```haskell
restoreDocsStage :: DocsState -> EntryIntent -> DocsOutcome
restoreDocsStage(s, intent)
  | needsGlobalSync(intent)                              -> RoutedTo NeatHandoff   -- 转 cs-docs-neat
  | ambiguousReader(s, intent)                           -> NeedsHuman "which reader?"
  | intent.mode == Api || wantsReference(intent)         -> RoutedTo ApiStage
  | wantsTaskGuide(intent) && s.docStatus == Missing     -> RoutedTo TutorialStage -- 新建
  | s.docStatus == Current && s.codeDrift == Drifted     -> RoutedTo TutorialStage -- 更新
  | s.docStatus == Outdated                              -> RoutedTo TutorialStage -- 更新
  | s.docStatus == Current && smallEdit(intent)          -> RoutedTo FocusedEdit   -- 聚焦编辑
  | otherwise                                            -> RoutedTo TutorialStage
```

---

## Workflow

主执行主线（每次调用按序走；各 stage "怎么做" 的厚规则见对应 protocol，本节只定顺序与边界）：

1. **`preflight`** — 读 `.codestable/attention.md`；缺失则 `route to cs-onboard`；不得用 `AGENTS.md`/`CLAUDE.md` 代替 CodeStable attention。
2. **`parseEntryIntent`** — 优先级 `flag > compat-preset > utterance`；`repoFacts override requestedMode`；空参不推断 mode，先按仓库事实恢复。
3. **`restoreDocsStage`** — 扫 `docs/`、`README*`、`manifest.yaml` + 相关源码公开表面恢复 `DocsState`，选 next stage；全局同步 / 记忆整理（非对外文档）→ `route to cs-docs-neat`。
4. **`loadStageProtocol`** — progressive reference loading：进某 stage 才加载该 stage 一个 protocol，禁止 eager 读全部 references。
5. **`executeOrRoute`** — 先读代码和既有文档再落盘；tutorial/api 生成或增量更新，`status` 落到合法值；遇 `HumanCheckpoint` 必停。
6. **`exitRecoverable`** — 文档 `status` / manifest 状态明确、可从源码追溯，next stage 或 checkpoint reason 明确。

---

## 状态机

启动后先扫既有文档和公开表面：`docs/`、`README*`、用户点名路径、相关源码导出/API/命令。按仓库事实恢复：

| 仓库事实 | 下一步 |
|---|---|
| 用户要任务教程/使用指南，且没有对应 guide | 读取 `references/tutorial/protocol.md` 新建 |
| 已有 guide，但相关代码/spec 已变或 status 为 `outdated` | 读取 `references/tutorial/protocol.md` 更新 |
| 用户要 API/组件/命令参考，且无 manifest 或条目缺失 | 读取 `references/api/protocol.md` 初始化或补条目 |
| API manifest / 条目存在且有 `pending`、`draft` 或 `outdated` | 读取 `references/api/protocol.md` 生成或增量更新 |
| 目标文档已 `current` 且用户只要小改 | 做聚焦编辑，保持事实可追溯 |
| 诉求是全局同步、README/agent 入口/记忆整理 | 转 `cs-docs-neat` |

用户说“继续写文档”时，也按文件和 frontmatter / manifest 状态判断，不靠聊天历史。

---

## Reference 加载

- tutorial：`references/tutorial/protocol.md`
- api：`references/api/protocol.md`，必要时 `references/api/reference.md`

先读代码和既有文档，再按对应模式生成或更新文档。不要凭记忆写 API。

---

## 人工 checkpoint

必须停下等用户明确确认的点：

1. 新建文档前：目标读者、文档类型（tutorial / api）和落点路径。
2. 覆盖或重写已有 `current` 文档前：确认旧内容确实过期，不是并行有效版本。
3. 文档表述会改变 user-facing 契约或公开理解时：让用户确认口径后再落盘。

---

## Failure Behavior

返回 `NeedsHuman` 当：`.codestable/attention.md` 缺失（→ `cs-onboard`）；无法识别目标文档或落点路径；目标读者/文档类型模糊无法从仓库事实判定；requested mode 与仓库事实冲突；文档表述会改变 user-facing 契约或公开理解而用户未确认口径；诉求实为全局同步 / 记忆整理（→ `cs-docs-neat`）；写 API 时源码事实源不足只能靠猜。报告：当前目标文档、阻塞原因、下一步用户动作、已写文件、是否可安全重试。

---

## 退出条件

- 文档目标读者、入口路径和状态已明确。
- 新增/更新文档的 `status` 或 manifest 状态已落到 `draft` / `current` / `outdated` / `pending` / `skipped` 中的合法值。
- 新增/更新的文档能从源码或现有项目事实追溯。
- 需要同步 README、agent 入口或记忆时，明确提示后续运行 `cs-docs-neat`。
