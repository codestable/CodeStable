---
adr: "008"
title: "CodeStable 设计前的条件式共享语言"
status: Accepted
date: 2026-08-03
applies-to:
  - "plugins/codestable/skills/cs/"
  - "plugins/codestable/skills/cs-feat/"
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
stage: [discuss, design, review]
lint: "python3 -m pytest tests/test_skill_contracts.py tests/test_v2_architecture_contract.py tests/test_v2_documentation_contract.py"
---

# ADR-008: CodeStable 设计前的条件式共享语言

## Context

实际 Epic 反馈表明，可审查不等于 owner 可理解。一份方案可以通过多轮技术 design review，却仍因
产品名词、事实权威、存储职责或相邻概念没有先对齐，在 owner confirmation 时才暴露不同理解；后续
澄清若改变架构与验收，已经收敛的设计和审查都需要重来。

现有 `cs` 会话讨论已经要求精确术语、具体场景和边界案例，但直接调用 `cs-feat` 或 `cs-epic` 时，
缺少对等的共享语言完成判据。只要求“归属与命名”能避免代码同义词，不能保证 owner、reviewer 和
执行者对领域概念、架构角色及其关系理解一致。

## Decision

### 条件式共享语言

共享语言只在新词、重载词或相邻概念边界会改变目标、行为、归属、事实权威、生命周期、公开契约、
验收或子项边界时触发。普通改动零新增产物：沿用已有单义词汇时不增加 glossary、问题、design 章节
或 review。

`cs` 在显式讨论中发现歧义并把 owner 已确认术语交给 owning skill。直接调用 owning skill 时语义
相同，不能因跳过 `cs` 而跳过必要的对齐。

### 不同任务的完成标准

- **Feature 局部语义清晰**：当前行为或契约涉及的术语有 canonical 名称、紧凑定义、排除含义与至少
  一个能区分边界的场景；实现、API、schema、文档与测试使用同一含义。没有歧义时立即继续最小闭环。
- **Epic 概念体系清晰**：所有会改变路线的术语已经定义或链接，概念责任、事实权威、关系与不变量
  一致，子项契约沿用同一词汇；产品含义与概念边界作为既有 HITL 收敛，并纳入 Route Clear。
- **Review 检查可理解性**：design / contract review 检查先定义后使用、全文同义及场景一致，但 reviewer 不能
  替 owner 证明理解或决定产品语义。

共享语言不新增 owner gate。仓库与 canonical 文档可唯一确定的事实由 agent 核实；只有真实产品
含义、命名偏好或概念边界需要既有 owner 确认。owner 在 review 后的术语问题若揭示契约级不同理解，
说明候选尚未清晰；只解释不进入 owner 契约的实现细节时不重开设计。

### 归属与持久化

领域术语与架构角色分开归属。领域术语定义业务概念本身，跨任务稳定后进入项目已有 canonical
领域文档；架构角色说明当前设计中的责任、权威、输入输出与不变量，留在 Feature/Epic 设计，难回退
且来自真实取舍时才进入 ADR。

项目没有术语归宿时，当前 Feature design/task packet、当前会话交付摘要或永久 Epic 暂存本次必要
定义，并请 owner 选择毕业位置；未选择不阻塞当前交付。不强制创建 `CONTEXT.md`，也不创建独立 issue、
术语状态机或平行真相。

`cs-issue` 与 `cs-refactor` 不新增共享语言设计分支：前者恢复既有行为，后者保持行为等价；若工作需要
定义新的产品含义或改变概念边界，则转 `cs-feat`。理解既有术语时直接沿用 canonical 定义。

shipped skills 不依赖外部 domain-modeling skill。CodeStable 内化主动消歧、代码事实核验、具体场景
与及时 canonical 化这些方法，同时保持每个 skill 独立安装。

### 可验证边界

静态测试只验证 shipped skill、ADR 与双语文档发布同一条件式契约，并机械保证 Epic 共享语言不复制
进临时游标。静态测试不冒充 owner 理解或模型行为证据；真实模型是否会及时发现歧义、提出有效边界
场景并正确区分事实与产品选择，留给本机试用与后续有证据的最小行为评测。

## Consequences

- 小改动继续走零产物最小闭环，领域建模不会成为固定阶段。
- Feature 在代码命名之前先对齐会改变行为的局部语义，减少实现正确但产品含义错误的返工。
- Epic 的技术 review 与 owner confirmation 共享同一概念模型，减少在审查完成后才推翻路线。
- 永久 Epic 条件式多一个共享语言小节；只在真实歧义存在时付出文档成本。
- reviewer 可以发现未定义或重载术语，但 owner 仍拥有产品语义，独立审查不会越权成为理解证明。

## Rejected alternatives

- **每个任务强制 glossary 或领域建模阶段**。拒绝：多数小改动沿用已有语言，会重新制造固定重流程。
- **只在 `cs` 讨论入口对齐术语**。拒绝：直接调用 `cs-feat` / `cs-epic` 会获得不同语义，并且跨会话
  执行者无法读取只存在于聊天中的定义。
- **把完整词典写进每份 Feature/Epic**。拒绝：复制项目 canonical 定义会产生漂移；任务只链接已有
  定义并补局部边界。
- **自动创建 `CONTEXT.md`**。拒绝：项目可能已有 glossary、domain 文档或 requirement 归宿，自动
  新建会制造平行真相。
- **运行时调用外部 domain-modeling skill**。拒绝：破坏独立安装边界，并让核心设计语义取决于宿主
  是否安装第三方 skill。
- **让 design reviewer 代替 owner 判断是否理解**。拒绝：reviewer 能检查文本自洽，不能证明 owner
  对产品词义和边界已经形成同一理解。
