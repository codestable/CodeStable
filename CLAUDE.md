# Claude Rules

## 核心原则

言简意赅。先读仓库事实、现有 skill 文档和 ADR，再修改规则；只把可复用且能验证的做法写进规则文件。

## 语言与文档

- 默认用中文写面向人的回复、报告和文档；代码、命令、路径、协议字段、YAML/JSON key 保持原格式。
- 单个 Markdown 文件不得超过 300 行；超过必须拆分（经 owner 明确豁免的设计章程除外）。
- 增加或更新 skill 时，同步检查相关 skill、SKILL_CATALOG、WORKFLOW、README、测试和 ADR 中的表述。
- `AGENTS.md`/`CLAUDE.md` 只写 agent 行为规则；不要替代 `.codestable/attention.md`、work 文档、ADR 等项目事实载体。

## Skill 边界（v2：thin harness, thick context）

- 交付 skill 共 8 个，位于 `plugins/codestable/skills/`；每个 SKILL.md 是薄责任契约（约 30–60 行正文），不写流程状态机、不写 Haskell spec。
- 不同 skill 之间不相互耦合：公共纪律（开工检索、沉淀推荐、授权边界）以两三行内联进各 SKILL.md，不建跨 skill 共享 reference 机制。
- 上下文按需检索：skill 只写"去哪取"（attention、`lessons/` grep、项目文档），不把材料复制进 skill 包或项目。
- 交付 skill 不带 contracts frontmatter；硬门槛锚由 `tests/test_skill_contracts.py` 直接对 SKILL.md 正文断言（改硬门槛措辞须同步更新锚清单）。

## CodeStable 项目数据

- 项目侧只有 `.codestable/{attention.md, lessons/, work/}`；普通任务零产物，跨会话任务一个 work 文档。
- v1 存量（`reference/`、`tools/`、`gates/`、`hooks/`、`compound/`、`features/` 等）只读保留，不迁移、不删除、不覆盖；旧沉淀由 grep 检索继续生效。
- 不再有 skill 调用的 gate / runtime 工具与 runtime-manifest 机制；不要新增此类入口。
- CodeStable skills 不拥有默认 worktree/branch 策略；是否创建 worktree、如何命名分支、如何 merge，由宿主与 owner 决定。

## 验证

- skill 改动完成前至少运行 `python3 -m pytest tests/` 与 `git diff --check`。
- skill 行为的量化验证按需使用 `eval-cs-skill`（仅在明确要做测量实验时）。
