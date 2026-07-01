# CodeStable 工作流与运行结构

## 工作流层次

CodeStable 的技能是分层 + 事件驱动的：

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-roadmap
    │   ├── cs-roadmap-review
    │   └── cs-roadmap-impl-goal
    ├── cs-goal
    ├── cs-feat-design -> cs-feat-design-review -> cs-feat-impl -> cs-code-review -> cs-feat-qa -> cs-feat-accept
    ├── cs-issue-report -> cs-issue-analyze -> cs-issue-fix -> cs-code-review
    ├── cs-refactor / cs-refactor-ff -> cs-code-review
    └── cs-keep / cs-note / cs-docs-neat
```

纵向是层次，不是严格时间顺序。长效档案层会反复刷新，规划层只在大需求时进入；`cs-goal` 是目标驱动的自主迭代入口，给定起点与期望终态后自动迭代到验收。第 3 层是事件入口：新需求走 feature，bug 走 issue，腐化走 refactor；`cs-code-review` 是横切代码审查 gate，feature / issue / refactor 链路都经它产 `{slug}-review.md`。横切层是知识飞轮：任何流程都可以把值得复用的经验经 `cs-keep` 沉淀到 compound。
`cs-docs-neat` 是阶段收尾整理器，负责同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆，不新增沉淀文档类型。

## 运行时结构

`/cs-onboard` 后，项目根下会出现 `.codestable/`：

```text
.codestable/
├── requirements/        # 需求文档 + 领域模型：CONTEXT.md 术语表 + adrs/ ADR
├── roadmap/
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

- `requirements/` 是长效档案，记现状：既存需求/能力文档，也存 cs-domain 的领域模型——`CONTEXT.md` 术语表与 `adrs/` 决策记录（多 context 时再拆 `CONTEXT-MAP.md` + 各子 context 子目录）。
- `roadmap/` 是规划层，描述大需求接下来怎么走；`goals/` 存 cs-goal 的目标启动 / 迭代 / 验收产物。
- `features/`、`issues/`、`refactors/` 用 `YYYY-MM-DD-{slug}/` 聚合单次流程产物；`audits/`、`brainstorms/` 同理存审计与头脑风暴产物。
- `compound/` 是唯一知识沉淀目录，由 `cs-keep` 把坑 / 技巧 / 决策 / 调研统一写成纯 markdown 文件，靠 grep 检索。
- `reference/` 由 `cs-onboard` 释放共享口径；跨 skill 共享文档必须通过项目内 `.codestable/reference/`，不能从一个 skill 直接引用另一个 skill 包内文件。
