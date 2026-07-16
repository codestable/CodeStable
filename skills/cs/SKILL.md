---
name: cs
description: CodeStable 用 vision spec、project spec、epic spec 与 issue 组织软件的目标世界、当前真相、受控变化和可关闭行动，并根据用户当下意图选择讨论、提问、直接修改或持续管理。用户明确说 cs/CodeStable，询问系统如何工作或改动影响，或项目已有 `.cs/` 且正在处理愿景、需求、规格、bug、issue、实现、关闭或沉淀时使用；只有用户明确要求接入时才初始化 `.cs/`。
---

# cs — CodeStable

CodeStable 不是强制任务流程，也不是 Agent 编排器。它是一套供 AI 参考的软件演化结构：**vision spec 保存用户想要的应用全景，project spec 保存当前稳定真相，epic spec 承载一段有边界但仍在变化的未来，issue 记录值得持续管理的可关闭行动。** 简单明确的改变可以直接实现和验证，不必为了使用 CodeStable 创建 issue。

先理解这套结构，再决定当前要做什么。行动名称只是内部模式，不要求用户记住或调用更多技能。

## 为什么这样组织

软件开发中的信息并不具有同样的范围、成熟度和稳定度。目标应用全景、当前有效认知、仍在演化的大需求、一次具体实现的证据如果混在一起，会出现四种问题：

- 只有 issue：需求、架构取舍和长期方向被切碎在任务里，事项关闭后就难以找回。
- 只有当前 spec：个人开发者的奇思妙想、互斥方向和跨 Epic 产品全景没有位置，只能污染当前真相或散落在聊天里。
- 所有东西都写进 project spec：提案和未确认变化污染当前真相，读者分不清“现在如此”还是“以后可能如此”。
- 大需求都塞进巨型 issue：探索、规格、设计、实现和验证纠缠在一起，事项长期无法关闭。

因此 CodeStable 按**信息责任与认知成熟度**分层，而不是按 Agent、团队角色或固定流水线分层。它改变 AI 的判断，但不凌驾于用户当前意图：该讨论就讨论，该回答就回答，用户明确要直接改就直接行动。只有信息值得跨会话持续管理时，才把它写入 `.cs/` 的对应实体。

## 四个核心实体

```text
Vision Spec ──摘取目标切片──> Epic Spec ──分批推进──> Issues
     │                         │                        │
     │                         └──关闭毕业──────────────┤
     │                                                  ↓
     └──目标世界                         Project Spec（当前现实）

简单明确的改变 ──直接实现与验证──> Project Spec（仅在当前真相需要更新时）
```

### Vision Spec：目标中的应用世界

Vision spec 位于 `.cs/vision/`，回答：用户希望应用最终长成什么样、用户怎样获得结果、有哪些能力区域、哪些方向仍是候选或互斥实验、哪些部分已经进入建设或成为现实。

它面向需要把脑内产品世界逐渐外化的个人开发者，以用户旅程为主阅读路径、能力版图为辅助视角，由每层 `index.md` 建立地图并按需要递归展开。AI 不只是记录原话，还要帮助用户定位、分层、建立关联、指出断层与冲突；不能为了整齐把不同性质的旅程、概念和实验强塞进统一卡片。

Vision 允许目标、候选和互斥方案并存，也可以适度标记意图成熟度与实现程度；它不是 roadmap、Epic backlog 或详细进度表。用户可以直接讨论并确认 Vision 变化；开发中的普通 issue 不更新 Vision，Epic 经用户确认关闭时才检查并同步实现状态、链接和仍然成立的目标表述。

### Project Spec：当前稳定真相

Project spec 位于 `.cs/spec/`，回答：这个项目现在是什么、为什么这样、服务谁、当前有哪些能力和边界、开发者如何理解与修改它。

它面向第一次进入项目的开发者，按使用场景、能力、流程、概念、边界和架构考量组织，而不是按代码目录写成索引。它是一棵可递归展开的知识树：简单内容写在一篇里，复杂子域由该层 `index.md` 建立地图并指向下一层。

Project spec 只收当前仍然成立的结论，不记录实现流水，不提前收纳尚未稳定的 epic 方案。它是项目主线真相，但不是永远不变；直接改变完成后或受管理变化关闭时，相关稳定事实会重新写回这里。

### Epic Spec：有边界的活规格

Epic spec 位于 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`，回答：一个大变化准备怎样改变 project spec、为什么这样考虑、哪些已经确定、哪些仍在变化、当前哪部分足够清楚可以推进。

Epic 的价值是**隔离不确定性**。只有跨模块、会经历多轮反馈、需要分批推进，或规格会在一个可圈住范围内反复演化的变化才进入 epic。它不是任务桶，也不是 project spec 的缩小副本。

每个 epic 只有一个权威 `spec.md`。状态、当前方案、架构考量、统一语言、当前推进、直接切片与 issue 链接、阻碍、关闭条件和毕业候选都在其中维护；材料复杂时可以增加按内容命名的相邻文档，但不能形成第二份状态或计划。

### Issue：可关闭的行动

Issue 位于 `.cs/issues/YYYY/MM/DD/{status}-{短语}.md`；完整 Explore 使用同名目录和 `index.md`，以多篇“触发如何产生结果”的路径文章渐进解释系统现状。

Issue 回答：哪一项改变值得被持续追踪、验证和关闭。它适合存在范围与取舍、需要多轮或跨会话推进、需要交接留痕，或用户明确希望管理的工作；不是每次代码修改的必经步骤。大多数 issue 是可实现的改变，必须有可观察目标、明确范围、归属和验证方式；完整 Explore issue 则是一项有边界的系统理解行动，必须有探索问题、停止条件、证据和关闭结论。

Issue 不一定隶属 epic。需要留痕的小 bug、小功能、局部 chore 可以依据 project spec 成为独立 issue；大而不稳定的变化先进入 epic，再按需要从 epic spec 分批切 issue。简单、明确且没有持续管理价值的改变可以跳过 issue，直接实现并留下与风险相称的验证证据。

## 信息归属与回写规则

Vision 和 Project Spec 可以有意不同：前者描述目标世界，后者描述当前现实，不能用一条线性优先级互相覆盖。发生冲突时先判断正在回答哪类问题：

```text
目标方向：用户最新确认 > 相关 vision 分支
当前现实：代码与验证证据 > project spec 中疑似过时的表述
Epic 范围内的交付判断：用户最新确认 > 当前 epic spec > 来源 vision 的旧表述
具体行动：用户最新确认 > 当前 issue（如有）> 旧设计与历史证据
```

不要静默绕过冲突。Epic 解释与 Vision 不一致时，先指出它是在收窄实现还是改变目标；只有用户确认目标变化后才改 Vision。Project Spec 与代码证据不一致时，先确认事实，再维护当前真相。

关闭不是改一个状态，而是知识提升：

- 独立 issue 关闭：稳定结论回写 project spec。
- Epic issue 关闭：稳定结论先回写所属 epic spec。
- 探索型 issue 关闭：经用户确认的稳定 How it works 理解按 project spec 结构毕业；与具体改动绑定的影响分析留在目标 issue，错误理解和证据流水留在 Explore issue。
- Epic 关闭：必须由用户明确确认，再把已稳定结论合并回 project spec。
- Epic 关闭后：检查来源 Vision，按事实更新实现程度和链接；若要改变目标内容，必须得到用户确认。
- 直接改变：不补造 issue；只有它改变了已记录的当前真相时才同步 project spec，Vision 不自动随普通直接改变更新。

实现产生证据；有 issue 时由它收束一次行动，没有时由直接验证完成轻量闭环；epic 把多轮结论收敛，project spec 接收最终仍然有效的项目真相。

## 质量承诺链

CodeStable 使用 ISO/IEC 25010:2023 的九项产品质量特征作为统一质量语言，但不把它做成九项必填表，也不宣称 ISO 合规。Vision 可以保存目标质量方向，Project / Epic Spec 保存长期有效的质量约束；Talk、Explore 和 Complain 帮助发现当前变化的质量风险；受管理 issue 选择具体质量目标，直接改变守住必要边界并留下相称证据。

选中即承诺。受管理事项的质量目标必须说明具体结果、来源和预期证据，并落实到 Design、Do 和 Close。直接改变不生成形式清单，但不免除 spec 约束、用户要求、安全、数据保护、可访问性和必要验证。

## 辅助实体

这些实体服务核心结构，但不与四个核心实体争夺信息责任：

- `.cs/talks/`：局部讨论收束稿。它可以导向直接改变、Vision、issue 或 epic，不是当前规格。
- `.cs/notes/`：跨事项可复用的坑点、调查结论和操作经验。
- `.cs/tools/`：已经跑通、稳定、重复且适合自动化的项目工具。

几乎每次 Agent 启动都必须知道的短规则不再另建 `.cs/facts.md`，直接写入项目根已有的 `AGENTS.md` 或 `CLAUDE.md`。Agent 框架会自动注入这些指令，`cs` 不把它们建模成实体，也不要求行动模式主动读取。跨 Agent 规则优先放 `AGENTS.md`，只对 Claude 生效的规则放 `CLAUDE.md`，不要在两处重复。复杂背景、证据和操作步骤仍写 `.cs/notes/`，Agent 指令里只保留简短结论或阅读指针。

## 工作原则

**先判断用户此刻要什么。** 明确的提问先回答，系统理解进入 Explore，目标世界的构想进入 Vision 整理，局部模糊需求进入 Talk，明确行动则直接设计或实现。内容规模只是线索，不能盖过用户当前授权和正在进行的上下文。

**流程必须证明自己的价值。** CodeStable 提供判断框架，不要求用户完成固定流水线。用户明确要求直接修改时不要用建档阻塞；意图不清且“直接改还是持续管理”会影响结果时，说明推荐与理由，再让用户选择。复杂度、风险、跨会话推进、交接留痕或长期质量承诺足以受益时，才建议 issue 或 epic。

**先解释现状，再提出改变。** 修改代码前，先沿“触发如何穿过系统并产生结果”顺清相关逻辑。能在当前上下文或目标 issue 中紧凑说明就做轻量 Explore；现状解释不清、横跨多个边界或理解值得复用时，再升级为完整 Explore issue。影响分析只在存在具体变化时展开。

**复用上下文，但写前确认当前版本。** 当前会话已经掌握且没有变化迹象的 spec 和代码不机械重读；目标 issue、准备回写的 `.cs` 文件、Agent 指令文件和准备提交的代码在修改前必须确认当前内容。

**能查就先查，不明白就问。** 先查 `.cs/`、README、代码、测试、配置和历史。查不到、冲突、代价过高，或属于业务取舍、用户偏好、成功标准和不可破坏边界时，带着已确认事实与影响向用户提问。不要把推测写成真相。

**沿根因和责任举一反三。** 暴露一个约束或根因后，在同一职责、接口、数据形状和用户故事附近看一圈；能在当前范围安全处理就一起处理，会扩大范围或改变需求就记录并请求判断。不要借机主动审计。

**先走最小实现梯子。** 理解真实路径以后，先判断是否真的需要改，能否删除或收窄，能否复用正确归属的现有能力、标准库、平台原生能力或已安装依赖；最后才写新的最小代码。最小改动要落在正确责任边界，并为非平凡逻辑留下最小可运行检查；不能省略根因、输入校验、安全、数据保护、可访问性和已选质量目标。有意采用受约束的简单方案时，记录已知上限和升级触发，不为想象中的未来提前造抽象。

**按风险选择质量目标。** 从相关 spec 继承质量约束，再按影响范围和失败代价主动识别候选目标；受管理工作写入 issue，直接改变保留必要判断与验证结果。指标阈值、显著成本、兼容策略或目标冲突交给用户决定。

**UI 关系优先可视化。** 界面变化涉及空间关系、信息层级或多状态交互时，用可版本化的线框图与标注共同表达规格；ASCII 负责布局，Mermaid 负责流程和状态。Vision 画目标应用体验，Project Spec 只画当前稳定界面，Epic 画本次目标变化，Issue 只画局部，Design 映射到实现而不重定义需求。

**结构改进长在具体变化里。** 没有单独的重构流水线，也不主动扫全仓库找错。当前 feature 或 bug 被错误责任边界阻碍时，先做服务于当前目标的最小结构调整，再完成行为变化。

## 行动与授权边界

一个技能不等于一次跑完整个生命周期。根据用户当前授权推进：

- “讨论、规划”可以调查和给出口草案；用户确认前不落盘、不创建 vision、issue 或 epic。
- “整理 Vision”可以组织目标世界并在用户确认后写入 `.cs/vision/`；不强迫产生开发事项。
- “设计”不写代码；有目标 issue 时写回，没有时在当前对话中交付，不补造事项。
- “实现、修复”可以直接改代码和验证；有目标 issue 时回写执行记录，没有时不补造事项。实现不自动关闭、提交、推送或发布。
- “关闭、收尾”才更新状态、沉淀长期实体；git 仓库中按关闭契约提交相关变更。
- 初始化 `.cs/`、覆盖文件、关闭 epic、危险操作、推送、部署和共享状态修改都需要用户明确授权；破坏性操作执行前再次确认。

方向已经确认且用户要求执行时，持续推进到完成或真正阻塞，不在正常步骤之间反复请求确认。只有用户尚未授权改动，或是否建立持续管理实体会实质改变后续工作时，才询问“直接做还是先建档”。

## 按需读取行动规则

确定当前意图后，**在行动前完整读取对应 reference**；只读取当前模式和真正相关的原则文件，不把所有资源一次塞进上下文。模式切换仍在同一个 `cs` 技能内完成。扫描、选择、继承、落实、验证或关闭质量目标时同时读取 [quality](references/quality.md)：具体变化的 Talk、质量回归的 Complain、带质量目标的 Design / Do / Close 必须读取；Vision 记录目标质量方向、Spec 记录质量约束、Explore 服务具体变化时按需读取；纯 How it works 探索不需要。Design、Do 和 Complain 作实现取舍时同时读取 [economy](references/economy.md)；Close 发现 issue 记录了有界简化时再读取。Talk、Vision、Spec、Design、Do 或 Close 涉及 UI 空间关系、信息层级或多状态交互时，同时读取 [ui-spec](references/ui-spec.md)。

| 当前意图 | 必读资源 | 同时读取 |
|---|---|---|
| 初始化或补齐 `.cs/` | [onboard](references/onboard.md) | — |
| 构想或整理目标应用全景 | [vision](references/vision.md) | [docs](references/docs.md)；涉及目标质量方向再读 [quality](references/quality.md)；涉及 UI 关系再读 [ui-spec](references/ui-spec.md) |
| 想法模糊、讨论、初步规划 | [talk](references/talk.md) | [docs](references/docs.md)；具体变化再读 [quality](references/quality.md)；涉及 UI 关系再读 [ui-spec](references/ui-spec.md) |
| 维护 project / epic spec | [spec](references/spec.md) | [docs](references/docs.md)；涉及质量约束再读 [quality](references/quality.md)；涉及 UI 关系再读 [ui-spec](references/ui-spec.md) |
| 理解系统如何工作、修改前顺逻辑或分析影响范围 | [explore](references/explore.md) | [docs](references/docs.md)；服务具体变化再读 [quality](references/quality.md) |
| 行为不符合预期、debug、修 bug | [complain](references/complain.md) | [debug](references/debug.md)、[economy](references/economy.md)、[quality](references/quality.md)；根因涉及结构时再读 [code-design](references/code-design.md) |
| 为明确改变做实现设计（有无 issue 均可） | [design](references/design.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；涉及 UI 关系再读 [ui-spec](references/ui-spec.md) |
| 实现明确改变（有无 issue 均可） | [do](references/do.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；bug 还需 [debug](references/debug.md)，涉及 UI 关系再读 [ui-spec](references/ui-spec.md) |
| 关闭 issue 或 epic | [close](references/close.md) | [docs](references/docs.md)、[quality](references/quality.md)；存在有界简化时再读 [economy](references/economy.md)，回写 UI 关系时再读 [ui-spec](references/ui-spec.md) |
| 记录可复用知识 | [note](references/note.md) | [docs](references/docs.md) |
| 用户带路跑通未知流程 | [maketools](references/maketools.md) | [docs](references/docs.md) |
| 写、改或审视技能 | [great-skills](references/great-skills.md) | [docs](references/docs.md) |

模板位于 `templates/entities/`，初始化脚本位于 `scripts/init_codestable.py`。Reference 里的产物契约决定何时使用哪个模板；不要凭文件名猜格式。
