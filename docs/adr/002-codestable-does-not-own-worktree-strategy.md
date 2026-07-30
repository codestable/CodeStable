---
adr: "002"
title: "CodeStable skills 不拥有 worktree 或分支策略"
status: Accepted
date: 2026-07-06
applies-to:
  - "plugins/codestable/skills/"
  - ".codestable/work/"
enforcement: test
stage: [design, review, check]
lint: "python3 -m pytest tests/test_v2_architecture_contract.py tests/test_skill_contracts.py"
---

# ADR-002: CodeStable skills 不拥有 worktree 或分支策略

## Context

早期 CodeStable skills 把工作流指导和 branch/worktree policy 混在一起。这会让 agent 把
worktree 创建、branch guard、finish-worktree 步骤和相关 hooks 当作 feature / issue /
refactor 的默认执行内容。实际使用中，有些 agent 已经拥有有效的 design 或执行上下文，并不
需要 CodeStable 决定是否切换或创建 worktree。

worktree 和分支决策属于执行环境和 owner policy。把它们内建到每个 CS skill，会制造不必要的
耦合，也会让未来的 worktree 能力难以独立演进。

## Decision

CodeStable 的 feature、issue、refactor、epic 和 review skills 不得规定默认 worktree、
branch guard、finish-worktree 或 merge-inbox 流程。它们应在宿主或 owner 已选择的 checkout
环境中推进。

如果项目后续需要自动创建 worktree 或分支保护，该能力应作为独立 skill 或宿主策略提供，而
不是嵌入每个 CS workflow。

legacy worktree / branch 文件可以继续留在已接入的仓库中，但新的 CS skill 文本不得把它们
作为默认契约，也不得执行相关 legacy runtime。

## Consequences

- CS workflows 聚焦任务边界、验证证据、review 和可恢复 work 文档，而不是 checkout 管理。
- worktree policy 可以独立演进，不需要修改每个 CS skill。
- 现有项目不需要强制删除历史 worktree 文档或 hooks。
- review 和测试守卫必须监控当前 skill 文档中的默认 worktree/branch 契约残留。

## Rejected alternatives

- 继续把 worktree gates 放在每个 CS skill 内。拒绝原因：这会把 workflow correctness 绑定到
  本应属于宿主或 owner 的 checkout strategy。
- v2 升级时删除旧 worktree 和 branch-guard artifacts。拒绝原因：当前迁移目标是非破坏性兼容。
- 立刻用新的内建 worktree policy 替代旧 policy。拒绝原因：目标边界是未来独立 skill，而不是
  另一个嵌入式默认策略。
