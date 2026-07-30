# CodeStable 工作流与运行结构

## 设计原则：thin harness, thick context

规则点到为止：skill 只传递研发经验（何时该做什么、为什么）与少数硬门槛，不复刻流程状态机；执行路线交给模型，状态从仓库事实恢复。上下文按需检索：每次动手前按任务关键词 grep 项目沉淀，命中报告来源。

## 工作流

```text
cs（导览）
cs-onboard（骨架）
cs-feat / cs-issue / cs-refactor（事件入口）──> cs-code-review（独立审查，高风险或用户要求时）
cs-epic（大需求拆解，逐子项走事件入口）
cs-keep（收尾沉淀，所有入口内置推荐时机）
```

每个入口共用同一执行主线：**理解相关事实 → 行动 → 相称的验证 → 交付结果**。风险每次按当前事实重判，不写入持久 lane；触发升级信号（公开契约 / 数据 / 权限 / 真实取舍 / 大范围 diff / 用户要求）时先对齐设计再动手。design 与整体验收的确认不可被模型自主跳过；声称完成必须附可核验证据。

## 持久化

普通任务零 CodeStable 产物——git diff、测试输出与交付说明就是证据。

```text
.codestable/
├── attention.md    # 每次会话必读的项目事实，≤25 条
├── lessons/        # 沉淀经验，一条一 markdown 文件，grep 检索
└── work/           # 仅活动中的跨会话任务，一任务一文档（目标/现场/边界/证据/验收五节），完成即压缩删除
```

lesson 写入纪律：没有可追溯证据不写；写前 grep 同域旧条目，能合并不新增；约 50 条上限触发先合并。

## v1 兼容

存量项目的 v1 产物（`requirements/`、`roadmap/`、`features/`、`issues/`、`compound/`、`reference/`、`tools/` 等）一律只读保留、不迁移不删除；旧沉淀继续被各 skill 的 grep 检索覆盖。v1 的 gate 与 runtime 工具不再被 skill 调用。
