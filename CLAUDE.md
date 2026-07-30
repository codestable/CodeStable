# Claude Rules

## 核心原则

言简意赅。先读仓库事实、现有 skill 文档和 ADR，再修改规则；只把可复用且能验证的做法写进规则文件。

## 语言与文档

- 默认用中文写面向人的回复、报告和文档；代码、命令、路径、协议字段、YAML/JSON key 保持原格式。
- 单个 Markdown 文件不得超过 300 行；超过必须拆分。
- 增加或更新 skill 时，同步检查相关 skill、README/reference、测试和 ADR 中的表述。
- `AGENTS.md`/`CLAUDE.md` 只写 agent 行为规则；不要替代 `.codestable/attention.md`、项目文档、work 文档或 ADR 等项目事实载体。

## Skill 边界

- 不同 skill 之间不要相互耦合；A skill 在非必须情况下不要读取或依赖 B skill 的内部文件。
- skill 是独立安装单元，运行时每个 skill 只能稳定看到自己包内文件；不要在 SKILL.md 中写 `B-skill/reference/xxx.md` 这类 sibling 引用。
- v2 项目知识放在项目文档、ADR 以及 `.codestable/attention.md`、`lessons/`、`work/`；不通过 onboard 分发通用 reference。
- skill 专属 context 和确定性 helper 分别放在 owning skill 的 `references/` 与 `scripts/`；跨 skill 通用规则应归宿主策略、项目事实或独立安装单元。

## v1 兼容边界

- v1 的 `.codestable/reference/`、`tools/`、`gates/`、`hooks/`、`runtime-manifest.json` 原样保留，但 v2 skill 不把它们作为入口或执行其中的 legacy runtime。
- 不要新增、同步或刷新 repo-local CodeStable runtime；确定性行为由 owning skill 自己的 helper 或项目已有工具负责。
- CodeStable skills 不拥有默认 worktree/branch 策略；是否创建 worktree、如何命名分支、如何 merge，应由宿主、owner 或未来独立 skill 决定。

## 验证

- skill/runtime 改动完成前至少运行相关 pytest 与 `git diff --check`。
- plugin 分发或退役清单变更还要运行 `tests/test_skills_cli_distribution.py` 与 `tools/check-plugin-package.py`。
