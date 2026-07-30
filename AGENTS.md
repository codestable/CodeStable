# Agent Rules

## 通用

- 默认用中文写面向人的回复、报告和文档；代码、命令、路径、协议字段、YAML/JSON key 保持原格式。
- 先读仓库事实和已存在的设计/ADR，再改规则或流程；不要只凭记忆改 skill 契约。
- 增加或更新 skill 时，同步检查相关 skill、README/reference、测试和 ADR 中的表述。
- 保持规则言简意赅，优先写可执行约束，不写口号。

## CodeStable Skill 边界

- skill 是独立安装单元，运行时不能假设能读取 sibling skill 文件。
- v2 项目知识放在项目文档、ADR 以及 `.codestable/attention.md`、`lessons/`、`work/`；不通过 onboard 分发通用 reference。
- 确定性 helper 放在实际 owning skill 的 `scripts/`，不得隐式调用 sibling skill 或集中式 onboard runtime。
- v1 的 `.codestable/reference/`、`tools/`、`gates/`、`hooks/`、`runtime-manifest.json` 只作 legacy compatibility；不要默认删除、覆盖或作为 v2 入口调用。
- CodeStable skills 不决定默认 worktree/branch 策略；该策略由宿主、owner 或独立 skill 决定。
- 不要把 `AGENTS.md`/`CLAUDE.md` 当作 `.codestable/attention.md` 的替代；项目事实仍应沉淀到对应的 CodeStable artifacts。

## 验证

- skill/runtime 改动完成前至少运行相关 pytest 与 `git diff --check`。
- plugin 分发或退役清单变更还要运行 `tests/test_skills_cli_distribution.py` 与 `tools/check-plugin-package.py`。
