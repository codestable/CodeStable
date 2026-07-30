# CodeStable v2 技能目录

v2 只交付 8 个 skill。每个 skill 是独立安装单元，不依赖 sibling skill 文件或集中式 onboard
runtime。

## 当前入口

| 分组 | Skill | 责任 |
|---|---|---|
| 导航 | `cs` | 明确行动诉求同轮直转对应入口；咨询只推荐；导览不写文件 |
| 接入 | `cs-onboard` | 创建最小项目记忆骨架；无损说明 v1 升级边界 |
| 功能 | `cs-feat` | 实现新功能；按风险决定是否先确认设计或做独立 review |
| 问题 | `cs-issue` | 用红到绿的验证修复 bug 或既有行为异常 |
| 重构 | `cs-refactor` | 在可核验的行为等价约束下调整结构或性能 |
| 大需求 | `cs-epic` | 拆解、确认并长程推进多个可交付子项 |
| 审查 | `cs-code-review` | 独立只读审查；按需做模块或全仓 audit |
| 记忆 | `cs-keep` | 将有证据的高频事实或可复用经验写入项目记忆 |

## v1.0.4 退役入口

以下 24 个名称已退役，不随 v2 交付，也不会保留兼容 shim。升级不会删除项目里的历史
产物；只是新的 skill 安装包不再暴露这些触发入口。

| v1 名称 | v2 做法 |
|---|---|
| `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff` | 统一进入 `cs-feat`，由风险与仓库事实决定执行强度 |
| `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix` | 统一进入 `cs-issue` |
| `cs-refactor-ff` | 进入 `cs-refactor` |
| `cs-audit` | 使用 `cs-code-review` 的 audit 模式 |
| `cs-goal`, `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal` | 大需求进入 `cs-epic`；普通跨会话任务使用一个 work 文档 |
| `cs-brainstorm`, `cs-domain`, `cs-req` | 功能或大需求在 `cs-feat` / `cs-epic` 内澄清；项目事实直接更新到项目文档或 ADR |
| `cs-docs`, `cs-docs-neat`, `cs-doc-api`, `cs-doc-tutorial` | 在对应开发任务中同步文档，或直接提出独立文档请求 |
| `cs-note` | 进入 `cs-keep` |
| `cs-feedback` | 项目经验进入 `cs-keep`；产品反馈按仓库 issue 流程提交 |

不知道如何映射时调用 `cs` 获取推荐。v1 项目资产的保留规则见
[WORKFLOW.md](./WORKFLOW.md#v1-升级边界)。
