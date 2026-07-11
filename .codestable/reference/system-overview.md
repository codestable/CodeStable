# CodeStable 体系总览

本文档介绍 CodeStable 工作流家族整体：有哪些推荐主入口、各管什么场景、产物怎么组织。

CodeStable 把常见开发活动各配一套流程，产物放进统一的 `.codestable/` 目录结构，带统一命名和状态，方便人和 AI 在后续会话里检索复用。

## 技能分成四部分

**根入口**

- `cs` — 先判入口模式；行动请求同轮直转，咨询请求只给建议；介绍与歧义请求不误启动下游流程。

**做事主入口**

- `cs-feat` — 新功能端到端：design → design-review → implementation → code-review → QA → acceptance。想法模糊时先走 `cs-brainstorm`。
- `cs-issue` — 修 bug 端到端：report → analyze → fix → code-review。
- `cs-refactor` — 行为不变的结构/性能/可读性优化：标准模式或 fastforward mode。
- `cs-epic` — 大需求端到端：规划、规划审查、子 feature design、goal 执行包。用户叫 epic；内部第一版仍用 roadmap 目录/doc_type。
- `cs-goal` — 限定起点/终点后自主迭代实现、验证，完成前做 Task agent 功能验收。
- `cs-code-review` — 各执行流末端、commit 前的横切独立 diff 评审。

**沉淀**

- `cs-keep` — 把坑点、技巧、决策、调研沉淀到 `.codestable/compound/`。
- `cs-note` — 把一两行启动必读项目注意事项追加到 `.codestable/attention.md`。

**讨论与辅助**

- `cs-brainstorm` — 想法模糊时分诊到 feature、epic 或 brainstorm note。
- `cs-onboard` — 把新仓库接入 CodeStable 目录结构。
- `cs-req` — 起草或刷新 `.codestable/requirements/` 下的需求文档。
- `cs-domain` — 维护 CONTEXT.md 术语、ADR 决策和单/多 context 拓扑。
- `cs-audit` — 主动扫描 bug、安全、性能、可维护性和架构偏离。
- `cs-feedback` — 显式调用后把当前会话整理为 local-private incident/triage；公开预览经用户确认后才可上报。
- `cs-docs` — 写给外部读者的开发者指南、用户指南或 API 参考。
- `cs-docs-neat` — 阶段/里程碑收尾时整理 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆。

旧阶段技能仍长期可用，但只是兼容入口；共享文档只写主入口和阶段，不把旧入口作为推荐路径。

## 场景路由

仓库还没有 `.codestable/` 目录时，明确行动请求由 `cs` 串行进入 `cs-onboard` gate，完成后继续原目标；只咨询时不自动搭骨架。

| 场景 | 主入口 |
|---|---|
| 想法还模糊 / 先聊聊 | `cs-brainstorm` |
| 新功能 / 新能力 | `cs-feat` |
| 限定起点/终点的目标达成 | `cs-goal` |
| BUG / 异常 / 文档错误 | `cs-issue` |
| 代码优化 / 重构 / 重写，且行为不变 | `cs-refactor` |
| 大需求拆解 / 系统级能力 / 执行整个 roadmap | `cs-epic` |
| 合并前代码评审 / 准备 PR | `cs-code-review` |
| CodeStable skill 跑偏 / 规则没讲清 / 工具失败 | `cs-feedback` |
| 摸代码、踩坑回顾、技术选型、可复用模式 | `cs-keep` |
| 补 / 更新需求文档 | `cs-req` |
| 拍板技术决策 / 加术语 / 分 context | `cs-domain` |
| 开发者指南 / 用户指南 / API 参考 | `cs-docs` |
| 阶段收尾 / 同步 agent 入口 / 新人交接 | `cs-docs-neat` |

## 档案分层

- **愿景档案**（requirements）：用户需要什么、系统提供什么能力。
- **领域档案**（CONTEXT.md / adrs）：项目术语和结构性决策。
- **规划档案**（roadmap）：`cs-epic` 的内部存储模型，描述大需求分步实现。
- **单次动作**（feature / issue / refactor）：本次要做的一件具体事情的 spec 和验证记录。

用户说“我想要一个 X 系统”这种大需求，走 `cs-epic` 拆成若干子 feature，再逐条走 `cs-feat`。直接起 feature 容易变成巨型 design。

## 阶段不可跳

主入口会自动判断阶段，但不会跳过 gate：

- feature：design → design-review → implementation → code-review → QA → acceptance。
- issue：report → analyze → fix → code-review；简单问题可走快速通道但仍写 fix-note。
- refactor：标准模式必须 scan → design → apply → code-review；fastforward 必须行为不变、范围小、可自证。
- epic：planning → review → 用户确认 → 子 feature design/review → 用户确认 → goal 包。

每个 checkpoint 的详细规则在对应主入口及其 `references/` 中。

## 进一步参考

- `.codestable/reference/shared-conventions.md` — 目录结构、frontmatter 口径、checklist 生命周期和收尾约定。
- `.codestable/reference/execution-conventions.md` — CodeStable preflight、runtime 恢复和按需规则索引。
- `.codestable/reference/agent-conventions.md` — Task agent 选择、生命周期和 Goal driver 派发。
- `.codestable/reference/tools.md` — `search-yaml.py`、`validate-yaml.py` 和 workflow gate 工具用法。
- `.codestable/reference/tools-context.md` — context packet、commit planning 和 backlog 工具用法。
- `.codestable/reference/maintainer-notes.md` — 断点恢复和新增子工作流登记。

目录结构权威定义在 `shared-conventions.md`。要改目录先改 `plugins/codestable/skills/cs-onboard/references/shared-conventions.md` 模板，新项目 onboard 时会带上新版本。
