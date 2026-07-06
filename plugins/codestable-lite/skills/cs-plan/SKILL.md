---
name: cs-plan
description: 和用户商量计划草案，确认后再把已聊清的 talk 或 epic spec 本轮范围落成独立 issue、探索型 issue、目录型 epic 或 epic issue。触发：开始计划、拆 issue、创建 epic、从 epic spec 切本轮事项。不写代码。
---

# cs-plan

判断一件事应该是独立 issue，还是需要 epic spec 承载的大需求；先和用户确认拆分方案，再生成对应的可关闭事项。

## 背景

CodeStable 不是所有事情都进 epic。小 bug、小功能、局部 chore、project spec 缺口调查可以直接成为独立 issue；跨模块、会多轮变化、会分批切 issue 的大需求，才需要 epic 和 epic spec。

`cs-plan` 站在 `cs-talk` 和 `cs-spec` 后面：把已经想清楚或已经在 epic spec 中明确的一批范围，先整理成可讨论的计划草案。用户确认后，它才把草案变成后续可以设计、执行和关闭的事项。它不写代码，也不替 spec 继续澄清。

## 原则

**先判断形状，再生成文件。** 计划不是把想法切碎，而是判断它属于独立 issue、新 epic，还是已有 epic 的下一批 issue。

**先商量，再落盘。** 拆分是架构判断和工作节奏判断，不是自动切文件。必须先向用户说明建议拆法、理由、取舍和影响；用户确认前，不创建或修改 issue、epic、talk 下一步、epic plan。

**issue 必须可关闭。** 每个 issue 只承载一条能独立验证的变更。未定范围、可能推翻的内容和需要继续讨论的内容，不塞进 issue 目标。

**epic 承载变化。** 大需求的需求变化、架构考量和统一语言进入 epic spec；issue 只是从 epic spec 某一轮切出来的执行片段。

**主线不被中途污染。** 独立 issue 可以关闭后直接回写 project spec；epic issue 先回写 epic spec。project spec 等 epic 人工关闭后再合并。

**计划阶段不做实现设计。** 可以查看相关代码确认边界和模块归属，但具体功能分工、请求/数据流和实施步骤交给 `cs-design`。

## 行动指南

开始前复用当前上下文。必要时补读：

- `.cs/facts.md`
- `.cs/spec/index.md` 和本次相关的 project spec 子层
- 用户指定或最相关的 `.cs/talks/`
- 用户指定或最相关的 `.cs/epics/YYYY/MM/DD/{短语}/index.md`、`spec.md`、`plan.md`

没有 `.cs/` 时提醒先用 `cs-onboard`。

先形成计划草案，草案必须让用户能判断：

- 建议出口：独立 issue、探索型 issue、新 epic，还是已有 epic 的本轮 issue。
- 建议拆分：每个候选 issue/epic 的标题、目标、范围、验证点和归属。
- 判断理由：目标粒度、变化风险、依赖关系、验证方式和是否需要 epic spec 承载。
- 暂不纳入：哪些内容还不清楚、应该留在 spec/talk、或需要先探索。
- 影响旧事项：是否需要暂停、废弃、修改或迁移已有 issue。

草案只在对话中给出，不写文件。向用户请求确认；用户修改拆法时，先迭代草案。只有用户明确确认本轮拆分方案后，才进入落盘。

判断出口时使用：

- **独立 issue**：目标、范围、验证能说清；不需要长期变更上下文；不依赖一组未定架构取舍。
- **探索型 issue**：目标是摸清 project spec 的某个缺口，在 issue 内形成当前结论、当前理解和证据索引，关闭时由人确认是否合并进 project spec。
- **新 epic**：大需求、跨模块、会分多批 issue、规格可能反复变化、需要一份 epic spec 记录当前方案和架构考量。
- **已有 epic 的本轮 issue**：epic spec 已有“本轮可计划范围”，只需要切出可关闭 issue。

从 talk 创建 epic 时，生成目录 `.cs/epics/YYYY/MM/DD/{短语}/`，写入 `index.md`、`spec.md`、`plan.md`。从 epic spec 切 issue 时，只消费 `spec.md` / `plan.md` 的本轮可计划范围；暂不计划范围继续留在 epic spec。

生成 issue 后，回写来源：talk 的下一步，或 epic `plan.md` 的 issue 列表。若新 plan 使旧 issue 需要修改、暂停或关闭，在 epic `plan.md` 的“暂停或废弃的 issue”记录原因，不直接改旧 issue 内容，除非用户明确要求。

## 产物契约

确认前没有文件产物；计划草案留在对话里。不要为了“先存一下”创建草稿 issue 或半成品 epic。

独立 issue 写入 `.cs/issues/YYYY/MM/DD/open-{短语}.md`，frontmatter 里 `status: open`，`epic: ""`。根据场景选择模板：

- bug：`templates/entities/bug-issue.md`
- feature：`templates/entities/feature-issue.md`
- refactor：`templates/entities/refactor-issue.md`
- chore：`templates/entities/chore-issue.md`

探索型 issue 也写入 `.cs/issues/YYYY/MM/DD/open-{短语}.md`，但模板专用；必须使用 `cs-spec-explore/templates/entities/explore-issue.md`，由 `cs-spec-explore` 执行和补文档。

epic issue 也按其场景选择 bug / feature / refactor / chore 模板，写入 `.cs/issues/YYYY/MM/DD/open-{短语}.md`，frontmatter 的 `epic` 填对应 `.cs/epics/YYYY/MM/DD/{短语}/` 路径，并在“归属”里写相关 epic spec。

`open-`、`closed-` 这类状态前缀保持英文。

新 epic 使用：

- `templates/entities/epic-index.md`
- `templates/entities/epic-spec.md`
- `templates/entities/epic-plan.md`

所有 issue 都必须使用场景模板并保留 YAML frontmatter；不要使用通用 issue 模板，也不要只凭章节名手写一个缺头的 markdown。

## 收尾汇报

确认前的汇报只讲计划草案：建议怎么拆、为什么这样拆、请用户确认或调整。

确认并落盘后的汇报先说明用户确认的最终形状：独立 issue、探索型 issue、新 epic，还是已有 epic 的本轮 issue。再解释依据：目标粒度、变化风险、依赖关系、验证方式和是否需要 epic spec 承载。最后给文件路径和下一步技能。

## 应用场景

- talk 已经整理完，用户要进入落地。
- epic spec 有一批范围已经可计划。
- 用户说“这个太大，帮我拆一下”或“创建 epic”。
- 用户说“直接建个 issue”，但仍需检查是否其实需要 epic。

不适用：想法还模糊时回 `cs-talk`；规格还不足以决定本轮范围时回 `cs-spec`；project spec 缺口需要调查时交给 `cs-spec-explore`；实现设计交给 `cs-design`；代码执行交给 `cs-do`。
