---
adr: "006"
title: "CodeStable 项目内持续学习生命周期"
status: Accepted
date: 2026-08-01
applies-to:
  - "plugins/codestable/skills/cs-feat/"
  - "plugins/codestable/skills/cs-issue/"
  - "plugins/codestable/skills/cs-refactor/"
  - "plugins/codestable/skills/cs-epic/"
  - "plugins/codestable/skills/cs-keep/"
  - ".codestable/lessons/"
  - ".codestable/work/"
enforcement: test
stage: [author, execute, keep, review]
lint: "python3 -m pytest tests/test_skill_contracts.py tests/test_v2_architecture_contract.py tests/test_v2_documentation_contract.py"
---

# ADR-006: CodeStable 项目内持续学习生命周期

## Context

四个 task skill 已会检索项目 lesson，`cs-keep` 也有证据、查重与合并门槛，但现有闭环只保证
“读过”和“写下”。任务中不会稳定识别值得复用的晶化时刻；lesson 再次命中后没有统一的核验、
纠偏与退役规则；命中次数和模型自评也无法证明旧经验真实改善了后续任务。

与此同时，自动保存对话、每次任务都询问是否记录，或把所有经验长期留在 lesson，会制造隐私、
噪声、双重真相和流程中断。项目需要一个低打扰、证据驱动且最终收敛到更强 owner 的学习周期，
而不是新的 feedback runtime、后台采集系统或全局知识库。

## Decision

### 生命周期对象与唯一 owner

项目内学习采用以下分层：

| 对象 | 生命周期与 owner |
|---|---|
| Learning signal | 当前任务内的可核实事件；未过门槛即丢弃 |
| Crystallization candidate | 会话内有界候选；不是项目事实，也不自动获得写入授权 |
| Lesson | 项目级 staging，一条一文件；只保留尚未被更强 owner 完整承接的经验 |
| Canonical guard | 测试、checker、lint、类型或 deterministic helper，机械阻止同类错误 |
| Canonical knowledge | `attention.md`、项目既有文档、glossary 或 ADR 中的唯一事实 owner |
| Transfer evidence | fresh 后续任务在有、无 lesson 条件下产生的 paired 结果；实验机制归 ADR-003 |

检索次数、“讨论过”和模型自评置信度都不是学习证据。lesson 是可删除、可纠偏的暂存层；同一事实
不得同时把 lesson 与 canonical guard/knowledge 当作并列真相。

### 强信号与晶化候选

四个 task skill 在任务中静默观察，内存中最多保留 3 条候选，并用新证据替换较低价值项，不为
候选创建 work、transcript 或状态文件。强信号只包括：

- owner 纠正真实改变了方案、代码、术语或验证；
- 可复现证据推翻根因，或同一路径失败两次后更换假设；
- blocking/important finding 暴露尚未编码的不变量；
- 新 red -> green 验证捕获了可复发失败；
- 已有 lesson 真实改变本次行为，或被当前事实反证；
- workaround 重复出现，或某方法显著降低重试、成本或风险。

候选还必须同时具备可追溯证据、可写成未来动作、适用于本次精确 diff 之外，且尚无现成
canonical owner。网络波动、拼写、活动记录、泛化口号和已被机械 owner 完整覆盖的事实直接丢弃。
排序先看失败后果，再看证据与复发可能，最后优先低成本机械化；不得生成伪精确分数。

普通任务仅在强信号成立时，于收尾展示最高价值的一条，首行固定为
`晶化候选：{rule}`，并给出证据、范围和建议归宿；无强信号时不显示空模板。候选不暂停任务，
没有记忆写入授权就随会话结束消失。用户已明确要求“记住 / 更新 / 退役”时，同轮按 `cs-keep`
处理，不重复确认。

### Lesson 三态

新 lesson 必须声明 `status`、`scope` 与 `date`，正文只保留可执行规则、适用/停止应用边界、最多
三个代表性证据指针和候选归宿。状态只允许：

| status | 判据 |
|---|---|
| `observed` | 单次任务有证据，尚未在独立后续任务验证 |
| `validated` | 非创建该 lesson 的后续任务和 agent invocation 中有效命中，真实改善行为并验证成功 |
| `retired` | 被仓库事实反证、范围完全失效，或已被更强 owner 替代；不得再应用 |

旧 lesson 缺少 `status` 时按 `observed` 读取，不批量迁移；只有真实状态变化或 `cs-keep` 本来就要
更新时才补字段。`retired` 结论不得复活并继承 `validated` 身份；新结论必须重新从 `observed` 开始。

### Read-repair 与窄维护授权

task skill 应用 lesson 前必须 read-repair：`retired` 不应用；`observed` / `validated` 先用当前代码、
测试或 canonical 文档核实。只有条目 scope 符合、事实仍成立且真实改变计划或验证时，才报告
`经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}`；纯关键词碰撞或只是读过不算
有效命中。

创建 lesson、改写规则或 scope、一般晋升、删除及跨项目反馈，仍需用户显式 `cs-keep` 诉求、接受
普通任务候选，或 Epic 最终毕业 gate。为使 read-repair 不中断任务，仅对已有且有效命中的 lesson
开放两种无需新增确认的窄维护：

- `observed -> validated`：独立后续任务确实采用并验证成功，只补一次代表性证据；
- `observed|validated -> retired`：当前仓库事实直接反证，或发现已有 canonical owner，只写退役原因
  与替代/反证指针。

窄维护不得新建事实、改规则、扩 scope 或新增 gate，必须与当次代码、证据和游标组成同一语义原子
milestone，并在最终报告列出文件变化。稳定的 `validated` 命中不写文件。证据不足或需要改写结论时
只形成候选；发现 canonical owner 时 task skill 先 retire，删除与合并仍由 `cs-keep` 负责。

### 机械化优先与 canonical 归宿

当前任务范围内能直接落成 red -> green 测试或 checker 的约束，必须优先机械化，不再写重复
lesson；机械化会扩大任务范围时只给候选，不借学习名义扩权。`cs-keep` 按以下顺序迁移：

1. 能机械阻止的规则进入测试、checker、lint、类型或 owning skill 的 deterministic helper；
2. 高频必读且稳定的项目事实进入 `attention.md`，并维持不超过 25 条的预算；
3. 同时满足难回退、缺少上下文会令人意外、源于真实取舍的结构性决定进入项目 ADR；
4. 其他稳定方法进入项目既有文档；目标不存在时请 owner 选择，不发明目录；
5. `codestable-eval` 仅标记未来上游候选，本轮不导出、不上传，也不修改 shipped skill。

新 owner 写入并验证后，应在同一更新中删除完全重复的 lesson；若由 task skill 发现，则先退役，留待
显式 `cs-keep` 清理。`cs-keep` 继续执行查重、合并和约 50 条 lesson 预算。

### Epic 聚合

Epic 子项不得展示或询问晶化候选。每个子项至多把一条去重候选写入既有 Epic 游标的证据区，
不得为此新建 work；该记录只是临时毕业输入，不是项目事实。全部子项完成后，毕业清单统一处理
lesson、guard、项目文档与 ADR 的归宿，并复用 Epic 最终 owner gate，不新增逐项暂停或确认。

### 隐私与跨项目边界

不得保存原始对话、原始问答、完整思考过程、候选分支、逐次命中日志或无限 evidence history；
不得扫描 transcript 来补召回率。除上述有界 Epic 游标证据外，未获写入授权的候选只存在于当前
会话内。

本 ADR 只建立项目内 session candidate -> lesson -> canonical owner 的闭环。不创建
`.codestable/learning/`、全局 lessons、常驻索引、后台 telemetry、集中 runtime 或第九个 skill，
也不自动跨项目、团队或向 CodeStable 上游分享。未来跨项目路径必须另行获得显式授权，并经过脱敏
packet、fixture、跨模型 eval 与 regression；本 Epic 只保留这一边界，不实现上传或同步。

## Consequences

- task skill 会说明经验如何被当前事实核验、又如何改变行为，避免把检索命中冒充学习效果。
- lesson 可以随新证据晋升、纠偏和退役，最终迁移到单一机械或文档 owner，减少陈旧知识与双重真相。
- 普通任务只有高价值候选才出现一次提示，Epic 则聚合到最终 gate，持续学习不会增加常规暂停点。
- 两种窄维护会让已有 lesson 随任务 diff 一起变化；实现与审查必须核对其证据、状态转换和原子性。
- 不做 transcript 扫描、后台采集和自动跨项目共享会降低召回率，但同时限制隐私、噪声和权限风险。
- thin-harness skills 缺少集中 runtime 强制，契约测试与 ADR-003 的 paired cross-session eval 是主要
  回退防线；未达到跨模型、非 `[underpowered]` 的验收证据时，不得宣称学习迁移有效。

## Rejected alternatives

- **每个任务固定询问是否沉淀**。拒绝：高频仪式会打断主任务，并把弱信号升级成噪声。
- **自动保存候选、对话或反馈流**。拒绝：扩大隐私与持久化边界，并重新引入本 Epic 明确排除的
  feedback runtime、状态机和后台采集。
- **把 lesson 当作永久、只增不减的知识库**。拒绝：事实变化后会继续误导，且与测试、ADR、项目
  文档形成多个 owner。
- **命中一次或模型自评后直接标记 validated**。拒绝：没有独立后续任务的行为与验证证据，无法
  区分复用效果和自我确认。
- **自动同步到全局或其他项目**。拒绝：项目事实、隐私与适用范围尚未经过脱敏和跨模型回归验证。
- **用更醒目的规则文本代替机械 guard**。拒绝：能由测试、checker、类型或 helper 阻止的错误，
  不应继续依赖 agent 记得阅读。
