# CodeStable 工作流与运行结构

## 工作流层次

CodeStable 的技能是分层 + 事件驱动的。日常使用主入口，不需要记阶段技能名。

根入口 `cs` 先判断入口模式：行动请求同轮直转，咨询请求只给建议；介绍体系不启动下游流程，歧义请求只停一个聚焦问题。

主入口关系如下：

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-epic
    │   └── 内部使用 roadmap 存储模型和 goal 执行包
    ├── cs-goal
    ├── cs-brainstorm
    ├── cs-feat -> cs-code-review
    ├── cs-issue -> cs-code-review
    ├── cs-refactor -> cs-code-review
    ├── cs-docs
    ├── cs-feedback
    └── cs-keep / cs-note / cs-docs-neat
```

纵向是层次，不是严格时间顺序。长效档案层会反复刷新；`cs-epic` 只在大需求时进入，第一版内部仍写 `.codestable/roadmap/`；`cs-goal` 是目标驱动自主迭代入口。

第 3 层是事件入口：新需求走 `cs-feat`，bug 走 `cs-issue`，腐化走 `cs-refactor`，对外文档走 `cs-docs`。`cs-code-review` 是横切代码审查 gate，feature / issue / refactor 链路都经它产 `{slug}-review.md`。

横切层是知识与反馈飞轮：任何流程都可以把值得复用的经验经 `cs-keep` 沉淀到 compound；`cs-feedback` 收集 skill 使用失败和规则缺口，准备上报 issue；`cs-docs-neat` 在里程碑收尾时同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆。

旧阶段技能仍是长期兼容入口，但不再作为主路径展示：

- Feature：`cs-feat-design` / `cs-feat-design-review` / `cs-feat-impl` / `cs-feat-qa` / `cs-feat-accept` / `cs-feat-ff`
- Issue：`cs-issue-report` / `cs-issue-analyze` / `cs-issue-fix`
- Refactor：`cs-refactor-ff`
- Docs：`cs-doc-tutorial` / `cs-doc-api`
- Epic：`cs-roadmap` / `cs-roadmap-review` / `cs-roadmap-impl-goal`

## 运行时结构

`/cs-onboard` 后，项目根下会出现 `.codestable/`：

```text
.codestable/
├── requirements/        # 需求文档 + 领域模型：CONTEXT.md 术语表 + adrs/ ADR
├── roadmap/             # epic 的内部历史存储模型
├── goals/
├── features/
├── issues/
├── refactors/
├── audits/
├── brainstorms/
├── compound/
├── tools/
└── reference/
```

关键约束：

- `requirements/` 是长效档案，记现状：既存需求/能力文档，也存 cs-domain 的领域模型。
- `roadmap/` 是 `cs-epic` 第一版继续复用的内部规划层；用户文档叫 epic，历史路径/doc_type 暂不迁移。
- `features/`、`issues/`、`refactors/` 用 `YYYY-MM-DD-{slug}/` 聚合单次流程产物。
- `compound/` 是唯一知识沉淀目录，由 `cs-keep` 写纯 markdown 文件，靠 grep 检索。
- `reference/` 由 `cs-onboard` 释放共享口径；跨工作流共享约定优先读项目内 `.codestable/reference/`。
