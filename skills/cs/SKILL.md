---
name: cs
description: CodeStable 用 project spec、epic spec 与 issue 组织软件的当前真相、受控变化和可关闭行动，并负责接入、讨论规划、规格维护、系统探索、bug 诊断修复、issue 设计执行关闭、知识沉淀和未知流程学习。用户明确说 cs/CodeStable，或项目已有 `.cs/` 且正在处理需求、规格、bug、issue、实现、关闭或沉淀时使用；只有用户明确要求接入时才初始化 `.cs/`。
---

# cs — CodeStable

CodeStable 不是任务管理流程，也不是 Agent 编排器。它是一套软件演化结构：**project spec 保存当前稳定真相，epic spec 承载有边界但仍在变化的未来，issue 把已经足够明确的部分变成可实现、可验证、可关闭的改变。**

先理解这套结构，再决定当前要做什么。行动名称只是内部模式，不要求用户记住或调用更多技能。

## 为什么这样组织

软件开发中的信息并不具有同样的稳定度。当前有效的项目认知、仍在演化的大需求、一次具体实现的证据如果混在一起，会出现三种问题：

- 只有 issue：需求、架构取舍和长期方向被切碎在任务里，事项关闭后就难以找回。
- 所有东西都写进 project spec：提案和未确认变化污染当前真相，读者分不清“现在如此”还是“以后可能如此”。
- 大需求都塞进巨型 issue：探索、规格、设计、实现和验证纠缠在一起，事项长期无法关闭。

因此 CodeStable 按**认知成熟度**分层，而不是按 Agent、团队角色或固定流水线分层。人和 AI 都通过 `.cs/` 读取同一份显式状态；聊天上下文可以丢，项目结构不能丢。

## 三个核心实体

```text
Project Spec ──小而明确的变化──> Issue ──关闭回写──> Project Spec
     │
     └──大而不稳定的变化──> Epic Spec ──分批推进──> Issues
                                  ↑                    │
                                  └──验证与新认知──────┘

Epic 关闭 ──稳定结论毕业──> Project Spec
```

### Project Spec：当前稳定真相

Project spec 位于 `.cs/spec/`，回答：这个项目现在是什么、为什么这样、服务谁、有哪些能力和边界、开发者如何理解与修改它。

它面向第一次进入项目的开发者，按使用场景、能力、流程、概念、边界和架构考量组织，而不是按代码目录写成索引。它是一棵可递归展开的知识树：简单内容写在一篇里，复杂子域由该层 `index.md` 建立地图并指向下一层。

Project spec 只收当前仍然成立的结论，不记录实现流水，不提前收纳尚未稳定的 epic 方案。它是项目主线真相，但不是永远不变；变化经过 issue 或 epic 验证、关闭后，会重新写回这里。

### Epic Spec：有边界的活规格

Epic spec 位于 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`，回答：一个大变化准备怎样改变 project spec、为什么这样考虑、哪些已经确定、哪些仍在变化、当前哪部分足够清楚可以推进。

Epic 的价值是**隔离不确定性**。只有跨模块、会经历多轮反馈、需要分批 issue，或规格会在一个可圈住范围内反复演化的变化才进入 epic。它不是任务桶，也不是 project spec 的缩小副本。

每个 epic 只有一个权威 `spec.md`。状态、当前方案、架构考量、统一语言、当前推进、issue 列表、阻碍、关闭条件和毕业候选都在其中维护；材料复杂时可以增加按内容命名的相邻文档，但不能形成第二份状态或计划，并要由 `spec.md` 清楚指过去。

### Issue：可关闭的改变

Issue 位于 `.cs/issues/YYYY/MM/DD/{status}-{短语}.md`；需要多篇候选文章的探索型 issue 使用同名目录和 `index.md`。

Issue 回答：下一项可以被实现、验证和关闭的具体改变是什么。它必须有可观察目标、明确范围、归属和验证方式。实现设计、执行记录、证据与关闭结论属于 issue，因为它们解释一次改变怎样发生；整个项目或 epic 的长期真相不属于 issue。

Issue 不一定隶属 epic。小 bug、小功能、局部 chore 可以直接依据 project spec 成为独立 issue；只有大而不稳定的变化才先进入 epic，再从 epic spec 分批切 issue。

## 真相与回写规则

发生冲突时按以下优先级判断：

```text
用户最新确认
  > 当前 epic spec（仅在该 epic 范围内）
  > project spec
  > issue 中的旧设计、执行记录或历史证据
```

不要静默绕过冲突。用户改变了规格，或 issue 执行证明上层理解不成立时，先更新正确层级的 spec，再继续依赖该结论的工作。

关闭不是改一个状态，而是知识提升：

- 独立 issue 关闭：稳定结论回写 project spec。
- Epic issue 关闭：稳定结论先回写所属 epic spec。
- 探索型 issue 关闭：经用户确认的候选文章按 project spec 结构毕业，错误理解和证据流水留在 issue。
- Epic 关闭：必须由用户明确确认，再把已稳定结论合并回 project spec。

实现产生证据，issue 把证据收束成结论，epic 把多轮结论收敛，project spec 接收最终仍然有效的项目真相。

## 辅助实体

这些实体服务核心结构，但不与三个核心实体争夺真相来源：

- `.cs/talks/`：讨论收束稿。它是进入 issue 或 epic 前的缓冲，不是当前规格。
- `.cs/notes/`：跨事项可复用的坑点、调查结论和操作经验。
- `.cs/tools/`：已经跑通、稳定、重复且适合自动化的项目工具。

几乎每次 Agent 启动都必须知道的短规则不再另建 `.cs/facts.md`，直接写入项目根已有的 `AGENTS.md` 或 `CLAUDE.md`。Agent 框架会自动注入这些指令，`cs` 不把它们建模成实体，也不要求行动模式主动读取。跨 Agent 规则优先放 `AGENTS.md`，只对 Claude 生效的规则放 `CLAUDE.md`，不要在两处重复。复杂背景、证据和操作步骤仍写 `.cs/notes/`，Agent 指令里只保留简短结论或阅读指针。

## 工作原则

**复用上下文，但写前确认当前版本。** 当前会话已经掌握且没有变化迹象的 spec 和代码不机械重读；目标 issue、准备回写的 `.cs` 文件、Agent 指令文件和准备提交的代码在修改前必须确认当前内容。

**能查就先查，不明白就问。** 先查 `.cs/`、README、代码、测试、配置和历史。查不到、冲突、代价过高，或属于业务取舍、用户偏好、成功标准和不可破坏边界时，带着已确认事实与影响向用户提问。不要把推测写成真相。

**沿根因和责任举一反三。** 暴露一个约束或根因后，在同一职责、接口、数据形状和用户故事附近看一圈；能在当前范围安全处理就一起处理，会扩大范围或改变需求就记录并请求判断。不要借机主动审计。

**先走最小实现梯子。** 先判断是否真的需要改，能否复用现有能力、平台原生能力、标准库或已安装依赖，能否删除或收窄；最后才写新的最小代码。最小不省略根因、输入校验、安全、数据保护、可访问性和必要验证。

**结构改进长在具体变化里。** 没有单独的重构流水线，也不主动扫全仓库找错。当前 feature 或 bug 被错误责任边界阻碍时，先做服务于当前目标的最小结构调整，再完成行为变化。

## 行动与授权边界

一个技能不等于一次跑完整个生命周期。根据用户当前授权推进：

- “讨论、规划”可以调查和给出口草案；用户确认前不落盘、不创建 issue 或 epic。
- “设计”只更新目标 issue 的实现设计，不写代码。
- “实现、修复”可以改代码、验证并回写执行记录，但不自动关闭、提交、推送或发布。
- “关闭、收尾”才更新状态、沉淀长期实体；git 仓库中按关闭契约提交相关变更。
- 初始化 `.cs/`、覆盖文件、关闭 epic、危险操作、推送、部署和共享状态修改都需要用户明确授权；破坏性操作执行前再次确认。

方向已经确认且用户要求执行时，持续推进到完成或真正阻塞，不在正常步骤之间反复请求确认。

## 按需读取行动规则

确定当前意图后，**在行动前完整读取对应 reference**；只读取当前模式和真正相关的原则文件，不把所有资源一次塞进上下文。模式切换仍在同一个 `cs` 技能内完成。

| 当前意图 | 必读资源 | 同时读取 |
|---|---|---|
| 初始化或补齐 `.cs/` | [onboard](references/onboard.md) | — |
| 想法模糊、讨论、初步规划 | [talk](references/talk.md) | [docs](references/docs.md) |
| 维护 project / epic spec | [spec](references/spec.md) | [docs](references/docs.md) |
| 调查 project spec 缺口 | [explore](references/explore.md) | [docs](references/docs.md) |
| 行为不符合预期、debug、修 bug | [complain](references/complain.md) | [debug](references/debug.md)；根因涉及结构时再读 [code-design](references/code-design.md) |
| 为明确 issue 做实现设计 | [design](references/design.md) | [code-design](references/code-design.md) |
| 实现明确 issue | [do](references/do.md) | [code-design](references/code-design.md)；bug 还需 [debug](references/debug.md) |
| 关闭 issue 或 epic | [close](references/close.md) | [docs](references/docs.md) |
| 记录可复用知识 | [note](references/note.md) | [docs](references/docs.md) |
| 用户带路跑通未知流程 | [maketools](references/maketools.md) | [docs](references/docs.md) |
| 写、改或审视技能 | [great-skills](references/great-skills.md) | [docs](references/docs.md) |

模板位于 `templates/entities/`，初始化脚本位于 `scripts/init_codestable.py`。Reference 里的产物契约决定何时使用哪个模板；不要凭文件名猜格式。
