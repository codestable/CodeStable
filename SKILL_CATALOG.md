# CodeStable 技能目录

主入口调用时可带 flag 化的阶段 / 模式参数（如 `/cs-feat --stage qa`、`/cs-refactor --mode fastforward`、`/cs-docs --mode api 认证接口`）。参数只是意图提示，仓库事实始终优先；裸参数始终表示任务描述；不传参数时按仓库事实和用户原话恢复或路由。

## 推荐主入口

| 分组 | 技能 | 用途 |
|---|---|---|
| 根入口 | `cs` | 行动请求同轮直转，咨询请求只给建议；介绍与歧义请求不误启动 workflow |
| 接入 | `cs-onboard` | 把 CodeStable 接入新仓库或已有零散文档仓库 |
| 需求与领域 | `cs-req` | 整理和沉淀能力愿景文档 |
| 需求与领域 | `cs-domain` | 维护领域模型、术语表、ADR 和多 context 拓扑 |
| Epic | `cs-epic` | 大需求端到端入口：规划、review、子 feature design、goal 包和可见 driver 派发 |
| 目标驱动 | `cs-goal` | 给定起点与期望终态后自主迭代到验收 |
| 讨论入口 | `cs-brainstorm` | 想法模糊时分诊到 feature、epic 或 brainstorm note |
| 特性流程 | `cs-feat` | 新特性端到端入口：design、review、goal 包、impl、code review、QA、accept |
| 问题流程 | `cs-issue` | 问题修复端到端入口：report、analyze、fix、review |
| 重构流程 | `cs-refactor` | 行为等价重构入口：标准模式或 fastforward mode |
| 横切审查 | `cs-code-review` | 实现完成后的只读代码审查 gate |
| 审计 | `cs-audit` | 主动扫描 bug、安全、性能、可维护性和架构偏离 |
| 反馈 | `cs-feedback` | 显式采集当前会话为 local-private incident/triage；确认 preview 后才可上报 |
| 知识沉淀 | `cs-keep` | 把坑点、技巧、决策、调研沉淀到 `.codestable/compound/` |
| 知识沉淀 | `cs-note` | 把一两行启动必读项目注意事项追加到 `.codestable/attention.md` |
| 对外文档 | `cs-docs` | 写或更新开发者指南、用户指南、API 参考 |
| 文档收尾 | `cs-docs-neat` | 阶段收尾时同步 `.codestable/`、README/docs、agent 入口和记忆 |

## 长期兼容入口

这些技能名继续可用，但只转入对应主入口，不维护独立流程规则。

| 兼容组 | 技能 | 转入 |
|---|---|---|
| Feature | `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff` | `cs-feat` 的对应阶段或模式 |
| Issue | `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix` | `cs-issue` 的对应阶段 |
| Refactor | `cs-refactor-ff` | `cs-refactor` 的 fastforward mode |
| Docs | `cs-doc-tutorial`, `cs-doc-api` | `cs-docs` 的 tutorial / api mode |
| Epic | `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal` | `cs-epic` 的 planning / review / goal-package 阶段 |
