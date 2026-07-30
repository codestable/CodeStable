---
adr: "001"
title: "CodeStable 工具从已安装的 skill 包运行"
status: Superseded
superseded-by: "004"
date: 2026-07-06
applies-to:
  - "plugins/codestable/skills/cs-onboard/tools/"
  - "plugins/codestable/skills/cs-onboard/references/"
  - ".codestable/reference/"
  - ".codestable/runtime-manifest.json"
enforcement: test
stage: [design, review, check, runtime]
lint: "python3 -m pytest tests/test_codestable_doctor.py tests/test_skill_entry_simplification.py tests/test_codestable_workflow_next.py"
---

# ADR-001: CodeStable 工具从已安装的 skill 包运行

> 本决策已被 [ADR-004](004-project-knowledge-not-runtime-distribution.md) 取代。以下内容保留为
> v1 架构记录。

## Context

CodeStable 过去会把共享 Python 工具复制到每个仓库的 `.codestable/tools/`。这让每个已
onboard 的仓库都携带一份可能过期的工具 runtime。新版 skill 行为可能被旧的 repo-local
脚本挡住，runtime refresh 也必须判断是否覆盖或删除 `.codestable/tools/` 里的用户文件。

当前重构把 repo-local policy/config 和工具执行分开。仓库仍需要稳定资产，例如
`.codestable/gates/`、`.codestable/reference/`、`.codestable/.gitignore` 和
`.codestable/runtime-manifest.json`，但可执行工具应来自已安装的 CodeStable skill 包。

## Decision

CodeStable 工具必须从当前 `cs-onboard` skill 包目录运行：

```bash
python3 <cs-onboard skill directory>/tools/<tool>.py ...
```

runtime sync 不得为了新版 skill 行为安装、刷新、删除或要求 `.codestable/tools/`。已有
`.codestable/tools/` 目录只作为兼容副本保留。runtime manifest 用
`tool_runtime: skill-global` 记录这一点，runtime health 将 repo-owned paths 和
`skill_tool_paths` 分开报告。

## Consequences

- skill 升级从已安装包生效，不再依赖每个仓库刷新可执行脚本。
- runtime sync 只管理 repo-local 资产：gates、共享 reference 文档、`.gitignore` 和 manifest。
- 老项目可以继续保留 `.codestable/tools/`，不会被删除或覆盖。
- 缺少工具现在是 CodeStable 安装问题，不是仓库骨架问题。
- 任何 skill 文本、README 或工具帮助如果继续提示用户运行 `python .codestable/tools/...`，
  都属于回归。

## Rejected alternatives

- 继续把 `.codestable/tools/` 复制到每个 repo。拒绝原因：过期脚本会让不同仓库行为分叉，
  并迫使 refresh 逻辑覆盖用户可见文件。
- refresh 时删除 legacy `.codestable/tools/`。拒绝原因：老项目可能包含本地兼容文件或用户
  编辑，本次变更不应破坏性清理历史。
- 保留 repo-local tools 作为主入口，并增加版本检查。拒绝原因：这仍然让每个仓库成为可执行
  runtime 分发路径的一部分。
