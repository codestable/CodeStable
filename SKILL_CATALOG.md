# CodeStable v2 技能目录

v2 只交付 8 个 skill。每个 skill 是独立安装单元，不依赖 sibling skill 文件或集中式 onboard
runtime。

## 当前入口

| 分组 | Skill | 责任 |
|---|---|---|
| 导航 | `cs` | 明确行动同轮直转；先讨论的请求在当前会话收敛后同轮移交；咨询只推荐；导览不写文件 |
| 接入 | `cs-onboard` | 创建最小项目记忆骨架；无损说明 v1 升级边界 |
| 功能 | `cs-feat` | 实现新功能；按风险决定是否先确认设计或做独立 review |
| 问题 | `cs-issue` | 诊断问题；获授权后用红到绿证据修复 |
| 重构 | `cs-refactor` | 在可核验的行为等价约束下调整结构或性能 |
| 大需求 | `cs-epic` | 用永久 Epic 文档与临时 work 游标拆解、确认并串行连续推进多个可交付子项；owner 批准 `parallel` 策略时并行推进依赖互不阻塞的子项 |
| 审查 | `cs-review` | 只读叶子执行器；单轮审查，不创建子 agent |
| 记忆 | `cs-keep` | 管理有证据的项目事实、lesson 生命周期与 canonical 归宿 |

`cs-code-review` 作为 `cs-review` 的唯一兼容别名随包交付（v1 沿用名，只转发、不含独立规则）。

讨论本身只存在于当前会话，不创建 work 游标或 transcript；稳定资产由 owning skill 按 canonical 归宿毕业，未收敛讨论不承诺跨会话恢复。

共享语言只在术语歧义会改变行为或契约时触发：Feature 收敛局部语义，Epic 收敛概念体系；普通改动不新增 glossary 或 gate。

task skill 静默识别强信号，普通任务最多展示一条晶化候选，Epic 子项统一在最终毕业清单处理。
`cs-keep` 让 lesson 按 observed / validated / retired 演化；机械 guard 优先，新建与跨项目分享仍需显式授权。

任务类型只决定工程方法，实际风险决定保障强度：

```text
执行流程 = 最小闭环 + 每个未排除风险所要求的最少保障
```

独立 review 不是默认步骤。一个风险只增加与它直接对应的保障，不自动打开整套流程。

## 项目知识与 Epic 边界

新项目仍只预建 `.codestable/attention.md`、`lessons/` 与 `work/`。Epic 优先沿用项目已有归宿，否则首次需要时才创建 `.codestable/epics/`：永久文档保存目标、范围、已批准子项、决策、交付索引与终态验收，`work/epic-{slug}.md` 只作批准 revision、执行进度与 `item_progression` / `milestone_commit` / `remote_publish` 策略的临时游标，终态删除游标但保留永久档案。

路线尚不清晰时，永久 Epic 文档本身就是路线地图：决策依赖派生 frontier，agent 解决事实，产品判断
与真实取舍进入 HITL。路线清晰、可审查、可执行后才送审和执行，不增加独立 map、issue 或平行生命周期。

Epic 保留三道 owner gate：独立 design review 后确认拆解；目标、范围、非目标、验收、子项或重大风险变化时重新确认；全部子项完成并由 fresh reviewer 按最新 owner 已批准标准做终态整体验收后，由 owner 最终接受。连续策略在普通子项边界不新增人工 gate。

v1 的 `roadmap/`、`features/`、`issues/`、`refactors/`、`goals/`、`compound/`、`audits/`、`brainstorms/` 与 `feedback/` 九个历史知识目录只按任务关键词只读检索和引用，不生成、不原地改写、不批量迁移，也不写回。

既有 `.codestable/requirements/` 只有经 `.codestable/attention.md` 显式登记为 canonical requirement 位置才可维护，否则只读；新项目不默认创建该目录。`cs-epic` 承接有价值的 goal 契约、恢复游标与验收，但不恢复 `cs-goal` runtime、goal package、`state.yaml`、逐轮 iteration 报告或 runtime gate。

## v1.0.4 退役入口

以下 24 个名称已退役，不随 v2 交付，也不会保留兼容 shim。升级不会删除项目里的历史
产物；只是新的 skill 安装包不再暴露这些触发入口。

| v1 名称 | v2 做法 |
|---|---|
| `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff` | 统一进入 `cs-feat`，由风险与仓库事实决定执行强度 |
| `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix` | 统一进入 `cs-issue` |
| `cs-refactor-ff` | 进入 `cs-refactor` |
| `cs-audit` | 使用 `cs-review` 的 audit 模式 |
| `cs-goal`, `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal` | 大需求进入 `cs-epic`；不恢复 goal package、`state.yaml`、逐轮报告或 runtime gate |
| `cs-brainstorm`, `cs-domain`, `cs-req` | 先由 `cs` 在当前会话对齐；收敛后同轮进入 `cs-feat` / `cs-issue` / `cs-epic`，稳定资产由 owning skill 进入 canonical 项目文档、ADR 或永久 Epic |
| `cs-docs`, `cs-docs-neat`, `cs-doc-api`, `cs-doc-tutorial` | 在对应开发任务中同步文档，或直接提出独立文档请求 |
| `cs-note` | 进入 `cs-keep` |
| `cs-feedback` | 项目经验进入 `cs-keep`；产品反馈按仓库 issue 流程提交 |

不知道如何映射时调用 `cs` 获取推荐。v1 项目资产的保留规则见
[WORKFLOW.md](./WORKFLOW.md#v1-升级边界)。
