# Agent Rules

## 通用

- 默认用中文写面向人的回复、报告和文档；代码、命令、路径、协议字段、YAML/JSON key 保持原格式。
- 先读仓库事实和已存在的设计/ADR，再改规则或流程；不要只凭记忆改 skill 契约。
- 增加或更新 skill 时，同步检查相关 skill、SKILL_CATALOG、WORKFLOW、README、测试和 ADR 中的表述。
- 保持规则言简意赅，优先写可执行约束，不写口号。

## CodeStable Skill 边界（v2：thin harness, thick context）

- 交付 skill 共 8 个；每个 SKILL.md 是薄责任契约，不写流程状态机。
- skill 之间不相互耦合；公共纪律内联进各 SKILL.md，不建跨 skill 共享 reference 机制。
- 项目侧只有 `.codestable/{attention.md, lessons/, work/}`；v1 存量只读保留，不迁移不删除。
- 不再有 skill 调用的 gate / runtime 工具；不要新增 `python .codestable/tools/...` 类入口。
- CodeStable skills 不决定默认 worktree/branch 策略；该策略由宿主与 owner 决定。
- 不要把 `AGENTS.md`/`CLAUDE.md` 当作 `.codestable/attention.md` 的替代；项目事实沉淀到对应 CodeStable 载体。

## 验证

- skill 改动完成前至少运行 `python3 -m pytest tests/` 与 `git diff --check`。
