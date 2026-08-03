---
adr: "007"
title: "CodeStable 最小充分保障"
status: Accepted
date: 2026-08-03
applies-to:
  - "plugins/codestable/skills/cs/"
  - "plugins/codestable/skills/cs-feat/"
  - "plugins/codestable/skills/cs-issue/"
  - "plugins/codestable/skills/cs-refactor/"
  - "plugins/codestable/skills/cs-epic/"
  - "plugins/codestable/skills/cs-review/"
  - "README.md"
  - "README.en.md"
  - "WORKFLOW.md"
  - "WORKFLOW.en.md"
  - "SKILL_CATALOG.md"
  - "SKILL_CATALOG.en.md"
  - "docs/why-codestable.md"
  - "docs/why-codestable.en.md"
enforcement: test
stage: [design, execute, review, release]
lint: "python3 -m pytest tests/test_skill_contracts.py tests/test_v2_architecture_contract.py tests/test_v2_documentation_contract.py"
---

# ADR-007: CodeStable 最小充分保障

## Context

CodeStable 的 task skill 已按功能、问题、重构和 Epic 区分工程方法，但普通功能与修复曾把独立
change review 设为默认步骤，再用“文案级”或“单行级”例外降级。这个结构把任务类型和语法规模
当成风险代理：给一个低风险参数增加 `query` 也可能依次产生 design、work、全量验证和独立 review，
而一行权限绕过、schema 变化或不可逆外部操作却可能因为规模小而进入例外。

问题不在于某个例外阈值不够宽，而在于流程强度的决定因素错了。小问题需要成本最低但完整、可交付的
闭环；大问题或高失败代价问题可以支付更高保障成本。两者之间不能靠文件数、行数、文案/代码分类，
也不能靠任务名称预选流程档位。

## Decision

### 单一模型

普通 task skill 统一采用：

```text
执行流程 = 最小闭环 + 每个未排除风险所要求的最少保障
```

最小闭环是理解相关事实、完成最小完整改动、运行最窄权威验证、交付可核验证据。非平凡行为变化
至少留下一个能复发失败的检查；纯说明性变更也应运行与声明相称的最低成本校验。

选择最小闭环前，agent 基于目标及预计/实际触及的路径、符号、信任边界和代码外副作用，对风险做
一次静默、有界核对。核对不生成清单、文档或新的用户 gate；一次最低成本定向核实后仍不能排除时先按风险存在处理，
或继续定向诊断到能够判定。不得以“没有注意到风险”作为降级依据。
“未排除风险”包括已经证实存在的风险，以及完成一次最低成本定向核实后仍不能合理排除的风险；不要求
先证明失败已经发生才增加对应保障。

语义风险高于语法规模。行数、文件数或文案/代码类型、task kind 只可作为影响面证据，不能替代
兼容性、信任边界、数据、并发、副作用、性能与传播风险的事实判断。

### 风险事实到保障

每个新增门槛必须能写成“风险事实 → 增加的保障”。一个风险只增加与它直接对应的保障，不自动
启用整套 design、全量回归、独立 review、work 文档或 Epic final acceptance 路径。

| 风险事实 | 最少增加的保障 |
|---|---|
| 目标、根因、实现方向仍不确定，或有改变结果的真实取舍 | 定向诊断、提问或 design；需要 owner 选择时确认 |
| 破坏兼容性或改变多消费者依赖的公开契约 | 契约确认、对应契约测试与 canonical 文档；兼容范围或消费者影响仍不确定时独立 review |
| 改变权限、安全、隐私或其他信任边界 | 定向威胁/安全证据与独立 review；改变 owner 授权边界时确认 |
| 改变持久化数据、schema 或迁移路径 | 兼容/迁移验证、适用的备份与回滚/恢复证据、独立 review；破坏性或不可逆时确认 |
| 改变并发、顺序或一致性语义 | 对应竞态/顺序验证与独立 review；存在语义取舍时确认 |
| 产生不可恢复的代码外副作用 | 执行前确认，适用的 dry-run、幂等、补偿或恢复证据，以及独立 review |
| 性能回退或性能敏感路径变化 | 定向 profile、基线或前后对比；SLO、成本或传播范围重大/不确定时独立 review |
| 影响面广或失败可跨模块传播 | 扩大到受影响回归；消费者或失败范围仍不确定、失败代价重大时才做全量验证或独立 review |

独立 review 不是默认步骤。review 实际触发后，现有 fresh reviewer、冻结目标、finding-driven
lineage、最多三轮以及 blocking/important 门槛才生效。没有对应风险事实时，不得为了遵守仪式而
增加 review；发现一个风险时，也不得顺带启用与它无关的保障。

用户指出“流程太重 / 只是小改动 / 文档比代码多”时，这是重新核对风险和保障的触发信号，
不是无条件跳过安全门槛。agent 停止继续增加产物并重算；若仍需保留门槛，只说明阻止降级的具体风险。

### 连续性与冻结目标

连续性需要不是风险门槛。跨会话、多人交接或用户要求留痕，只增加一个临时 work 游标；高风险本身
不自动创建 work。普通任务的 diff、验证输出和交付说明就是执行证据。

design review 可冻结两种等价目标：仓库内已有 design 文档版本，或 task packet 内原样设计全文
加 SHA-256。packet 首轮必须把全文与 hash 原样交给 reviewer，reviewer 审查的就是该文本；
finding-driven follow-up 携带最新全文、前后 hash 与修复摘要。hash 用于跨轮身份和增量比对，
不能代替 reviewer 可读的目标文本。

### Task 路由与 Epic 边界

`cs` 只选择 owning skill，不预选保障强度。`cs-feat`、`cs-issue` 与 `cs-refactor` 采用相同保障模型，
但继续分别拥有功能交付、失败信号红到绿和行为等价的方法。`cs-epic` 仍用于真正的大需求与系统级
能力；Epic 保留三道 owner gate：拆解确认、重大契约变化确认、final acceptance 后最终接受。
本决定不声称每个旧步骤原样保留：旧规则按任务形态要求 owner 预确认公开契约、持久化数据、权限或
并发语义；新规则先要求与风险直接对应的定向证据，在信任边界、数据与并发风险上保持独立 review，
只在破坏性/不可逆、授权边界变化或真实语义取舍等 owner 决策存在时确认。
这是有意用可核验证据与独立审查替代无条件预确认，不是删除权限、安全、数据保护或不可逆操作护栏，
也不把普通任务模型带入 Epic。

### 可验证边界

本次 skill/文档契约改动只增加少量静态测试，验证 shipped skills 与中英文文档是否发布同一规则；
不新建模型行为 experiment，也不扩 eval harness。静态锚点不观测 reviewer 是否被创建、是否实际
运行 full suite，或 work 是否缺席，因此这些行为仍是明确证据缺口，不能冒充已验证。只有后续出现
真实行为回退，或发布声明需要模型级证据时，才另行设计最小行为样例。

本决定不新增 lane、状态机或 runtime helper。它通过 thin-harness 契约、双语文档、ADR 与测试约束
现有 skill，不引入集中调度器。

## Consequences

- 低风险小改动可以在最小闭环内完成，不再为得到“例外”而先进入完整流程。
- 高风险小 diff 仍按语义风险获得安全、迁移、恢复、并发或独立 review 保障。
- 大范围但可证明低风险的机械改动只扩大受影响验证，不因文件数自动叠加全部门槛。
- agent 必须先做有界风险核对，并能为每个新增门槛给出事实依据；这增加少量判断责任，但不新增产物。
- 流程强度不再由固定模板提供表面一致性，回退防线转为契约测试和明确证据边界。

## Rejected alternatives

- **所有普通任务走固定全流程**。拒绝：把低成本问题变成高成本仪式，且与真实失败代价无关。
- **用行数、文件数或文案/代码类型设置例外**。拒绝：语法规模会同时漏掉小而危险的变更，并误伤
  大而机械的低风险变更。
- **给风险维度加权并计算伪精确风险分数**。拒绝：权重缺少可校准数据，分数掩盖了应逐项说明的
  风险事实与对应保障。
- **新增 Quick / Standard / Goal 三条 lane**。拒绝：固定档位会重新捆绑无关保障，形成新的命名、
  状态迁移和兼容成本。
- **新增集中 runtime 或 helper 自动编排门槛**。拒绝：现阶段规则可由独立 skill 契约表达；集中实现
  会破坏 thin-harness 安装边界，并使一个流程减负改动重新变成系统级工程。
