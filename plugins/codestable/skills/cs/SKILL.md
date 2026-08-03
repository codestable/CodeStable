---
name: cs
description: CodeStable 入口。触发：用户调用 cs、想先讨论或对齐、想了解体系、问该用哪个 skill，或带着诉求未选入口。明确行动同轮直转；先讨论的请求收敛后同轮移交。
argument-hint: "[诉求]"
---

# cs

判断用户此刻要执行、先讨论、咨询还是了解体系。**明确行动默认直接执行，不先加讨论 gate。**
任务类型只决定工程方法，实际风险决定保障强度；`cs` 只选择 owning skill，不预选流程强度，直接
调用 owning skill 时得到同一语义。

## 判别与行为

| 用户输入 | 行为 |
|---|---|
| 明确行动诉求（修这个 bug、排查这个报错为什么发生、实现 X、重构 Y、审一下、记住这个…） | **同轮直转**：报一句"按 `cs-xxx` 处理：{一句理由}"，随即在当前回合按该 skill 的纪律继续执行，不要求用户重新调用或再次确认 |
| 用户显式要求先讨论，或调查仓库事实后仍无法安全判断行动类型 / owning skill，且产品决策会实质改变建档或改代码路径 | 在当前会话对齐；用户没有要求先讨论且 owning skill 已可判定时，直接转入，不在入口层细化目标或验收 |
| 咨询（该用哪个 / 流程怎么走 / 你建议怎么做） | 只推荐入口并说明理由，不启动执行 |
| 只说 cs、想了解体系、无具体诉求 | 输出体系速读 |
| 诉求含糊但一个分类问题即可判断 | 先调查可核实事实，只问一个聚焦问题，不默认重流程 |

## 会话内讨论与 handoff

- Execute 默认优先级最高；明确行动仍同轮直转。用户显式要求先讨论时才覆盖该默认；owning skill 已可判定时，目标与验收细化留给该 skill。
- 讨论只存在于当前会话。仓库可核实的事实由 agent 自行调查；一次只问一个真正需要 owner 决定的问题，给出建议与理由，并用精确术语、具体场景和边界案例检验理解。共享语言只在歧义会改变目标、行为、归属、契约或验收时收敛；已有单义术语不增加提问或产物。
- handoff-ready 时形成内存 packet：目标入口、原始诉求、目标或期望行为、范围、非目标、验收口径、已核实仓库事实及来源、owner 已确认的术语与决策、未决风险、canonical 资产指针或资产候选。
- 已有执行授权时同轮移交给三个已确认出口 `cs-feat` / `cs-issue` / `cs-epic`，不再询问“是否继续”；只授权讨论时返回已确认结论，并推荐由 `cs-keep` 或对应 owning skill 完成资产毕业。
- 讨论过程本身不产生授权；handoff 不扩大实现、commit、发布或写入授权，也不替代目标 skill 的硬门槛。收敛到其他入口时按既有 Execute / Advise 规则处理，不附带 handoff 的不重复确认契约。
- 不创建 `.codestable/work/discussion-*`、transcript 或新状态；未收敛讨论不跨会话恢复，原始问答、未决讨论和候选分支不落盘。
- 稳定术语交给项目已有 canonical 术语归宿；难逆转、缺少上下文会令人意外且源于真实取舍的决定才进入 ADR；任务契约、永久 Epic 文档、`attention.md` 与 `lessons/` 由 owning skill 按各自规则毕业。

## 入口表

| 诉求 | 入口 |
|---|---|
| 新功能、功能改造 | `cs-feat` |
| 排查、诊断、bug、报错、性能回退、行为异常 | `cs-issue` |
| 行为等价的重构、主动性能优化 | `cs-refactor` |
| 审查 diff 或按需审计代码 | `cs-review` |
| 大需求拆解与长程推进 | `cs-epic` |
| 沉淀经验、教训、"记住这个" | `cs-keep` |
| 仓库接入 / v1 升级 | `cs-onboard` |

大而路线仍不清晰时也只交给 `cs-epic`；是否需要批准前路线发现由 `cs-epic` 根据路线级迷雾判断，
`cs` 不创建地图、issue 或平行设计状态。

一次只转一个入口；用户同时给出两个独立诉求时，问先做哪个。转入不扩大授权：目标 skill 的硬门槛、checkpoint 与写入规则照常生效。

## 体系速读

CodeStable 是一层薄研发纪律加一个项目记忆闭环。项目记忆在 `.codestable/`：attention.md（每次必读）、lessons/（按关键词检索的经验）、work/（活动中的跨会话任务）。普通任务零产物，证据是 diff 与测试。

Epic 采用职责互斥的双层文档：永久 Epic 上下文优先沿用项目已有 Epic / RFC / initiative 归宿，否则首次使用时按需创建 `.codestable/epics/`；临时 `.codestable/work/epic-{slug}.md` 只保存执行游标，完成后清理。`cs-goal` 中有价值的目标契约、恢复、人工门槛和终态验收已并入 `cs-epic`，但不恢复 `cs-goal` 入口、goal package、`state.yaml`、逐轮 iteration 报告或 runtime gate。

v1 的 24 个旧入口（cs-feat-design、cs-goal、cs-audit、cs-note、cs-feedback、cs-roadmap 系等）已并入
上表：设计与需求澄清是按风险或 Epic 契约触发的可用保障，审计是 cs-review 的模式，沉淀统一走
cs-keep。

导览与推荐本身不写任何文件。
