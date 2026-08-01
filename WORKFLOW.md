# CodeStable v2 工作流与项目结构

## 工作流

CodeStable v2 是 8 个独立安装的 thin-harness skill，加一个项目记忆闭环。`cs` 判别用户
此刻要什么：明确行动诉求**同轮直转**对应 skill 并继续执行；咨询只给推荐；无诉求时介绍体系。

```text
不确定入口       -> cs
仓库接入 / v1 升级 -> cs-onboard
新功能           -> cs-feat ---------\
bug / 行为异常    -> cs-issue ----------> cs-review（高风险或按需）
行为等价重构      -> cs-refactor ------/
大需求拆解        -> cs-epic -> cs-feat / cs-issue / cs-refactor
经验与项目记忆    -> cs-keep
```

执行强度与风险相称：

- `cs-feat` 默认直接理解、实现、验证；公开契约、数据、权限、并发或真实方案取舍先经用户确认。
- `cs-issue` 先建立能明确变红的验证，再修复并证明它变绿。
- `cs-refactor` 先建立等价性证据，分步改动并持续保持验证为绿。
- `cs-epic` 用一个 work 文档维护子项、依赖和验收；拆解与边界变更由用户确认。
- 需要独立审查时由外层主流程创建 reviewer；reviewer 单轮执行 `cs-review`，返回结果前不再创建子 agent。
- 当前主流程创建 reviewer 前，先发现当前会话可调用的 subagent 创建与管理能力。项目上下文有显式创建方式/model 约束时先遵守。达到审查质量基线后，优先选择与实现者异构的 agent，并显式指定最强稳定 model；创建方式依次使用受管理的结构化委派能力、宿主 subagent、本机有界 agent CLI 回退，不得只扫 PATH。没有合格异构候选时回退同构最强模型。把最终创建方式、agent/model 与回退原因写入 task packet，禁止依赖默认模型。具体后端与 model 约束属于项目上下文，不进入 shipped skill。
- 外层主流程派发前冻结一个明确的审查目标（diff review 优先 staged diff，也可用明确 range/patch；design review 冻结对应文档版本；audit 冻结 commit + 范围标识），reviewer 返回前不移动目标或对应工作树；目标变化则本轮失效。
- `cs-review` 是只读叶子执行器，也承接模块或全仓 audit；修复与复审由外层主流程负责。
- 有 blocking 或未被用户明确接受的 important 时不提交当前候选，也不创建正式里程碑；修复后重新验证、冻结目标并创建 fresh reviewer。只有审查门槛通过且已有 commit 授权时才形成语义原子里程碑；WIP/checkpoint 只作恢复或隔离基线，不代表通过。
- Epic 每次只推进一个已确认子项；子项达到里程碑后再进入下一个。未获 commit 授权时先交付 checkpoint 等用户决定，不把多个子项堆进同一 diff。
- 健康运行中的 reviewer 与原 run/target 绑定；running，或 Awaiting 携带同一可查询 run identity 且仍为活动态时继续等待，不因后来发现更优创建方式而取消、重复创建或并行补发。只有终止无报告、run identity 不可恢复、能力不满足或目标失效时，本轮才失败且不计审查轮次；外层主流程先诊断再决定有界重试、更换创建方式或上交，不盲目重发。
- `cs-keep` 把高频事实压进 attention，把可复用经验写成 lesson。

普通任务不生成阶段文档。diff、测试输出和交付说明就是证据；只有跨会话、多人交接或用户
要求留痕时，才维护一个 work 文档，完成后删除或按用户要求保留。

## 项目记忆

`/cs-onboard` 为新项目创建最小骨架：

```text
.codestable/
├── attention.md    # 每次会话需要的少量项目事实，最多 25 条
├── lessons/        # 一条经验一个 Markdown 文件，按关键词检索
└── work/           # 活动中的跨会话任务，文件名带类型前缀 feat-/issue-/refactor-/epic-，完成即清
```

skill 专属 context 与 helper 分别由 owning skill 的 `references/` 和 `scripts/` 提供。项目
事实放在上述目录或项目既有文档与 ADR 中。skill 不读取 sibling skill 文件，也不依赖集中式
onboard runtime；worktree、branch 和 agent backend 策略由宿主或 owner 决定。

## v1 升级边界

v2 不迁移或清理 v1 项目的历史目录。已有 `requirements/`、`roadmap/`、`features/`、
`issues/`、`compound/`、tool、gate、hook 和 manifest 原样保留；新 skill 可以按任务关键词
检索其中的项目知识，但不会执行旧 runtime，也不会继续生成 v1 阶段产物。

v1.0.4 的 32 个 skill 在 v2 收敛为 8 个；其余 24 个入口已退役且不随 v2 安装。完整映射见
[SKILL_CATALOG.md](./SKILL_CATALOG.md)。
