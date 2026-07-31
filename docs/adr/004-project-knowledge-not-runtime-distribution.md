---
adr: "004"
title: "CodeStable v2 项目目录只承载项目知识"
status: Accepted
date: 2026-07-30
supersedes: ["001"]
applies-to:
  - "plugins/codestable/skills/"
  - ".codestable/"
  - ".claude/skills/build-cs-skill/"
enforcement: test
stage: [author, onboard, review, release]
lint: "python3 -m pytest tests/test_v2_architecture_contract.py tests/test_skill_contracts.py tests/test_skills_cli_distribution.py"
---

# ADR-004: CodeStable v2 项目目录只承载项目知识

## Context

v1 通过 `cs-onboard` 分发共享 reference、gate、Python runtime 和 manifest，并交付大量阶段
skill。升级时，项目副本、已安装 runtime 与 skill 文本可能处于不同版本；简单任务也要恢复并
维护与实际工作无关的状态。v2 已收敛为 8 个独立 skill 和最小项目记忆闭环，继续保留 v1
ownership 会重新引入已经删除的耦合。

## Decision

- v2 只交付 `cs`、`cs-onboard`、`cs-feat`、`cs-issue`、`cs-refactor`、
  `cs-review`、`cs-epic`、`cs-keep`；另随包交付 `cs-code-review` 作为 `cs-review` 的唯一
  兼容别名（v1 沿用名，只含 canonical route 与 shim 边界，不含审查规则）——这是“不保留
  兼容 shim”的唯一显式例外。
- 新项目的 `.codestable/` 只包含 `attention.md`、`lessons/` 与 `work/`。项目文档和 ADR
  继续由项目自己的目录结构管理。
- skill 必须独立安装。skill 专属 context 和确定性 helper 分别放在 owning skill 的
  `references/` 与 `scripts/`；不得读取 sibling skill，也不得依赖集中式 onboard runtime。
- 不再向项目复制或刷新通用 reference、gate、tool、hook、gitignore 或 runtime manifest，
  v2 skill 也不调用这些旧 runtime 入口。
- v1 项目中的历史目录与产物原样保留。新 skill 可以按任务关键词检索其中的项目知识，但不得
  删除、覆盖、迁移格式或执行其中的 legacy runtime。

## Consequences

- 安装包升级即可更新行为，不再要求逐仓库 runtime refresh。
- 普通任务以 diff、测试和交付说明为证据；只有跨会话工作维护一个 work 文档。
- 跨 skill 的通用规则不能藏在 sibling reference 中；必须成为宿主策略、项目事实、owning
  skill 的小型 hard guard，或有明确接口的独立安装单元。
- 从 v1 升级会退役 24 个旧 skill 名称，是需要 major version 和升级测试的 breaking change。

## Rejected alternatives

- **恢复 `cs-onboard` 的共享 runtime**。拒绝：重新制造版本分叉，并违反独立安装边界。
- **保留 24 个兼容 shim**。拒绝：扩大触发表面，让旧阶段模型继续影响 v2 决策。
- **升级时删除 v1 项目资产**。拒绝：历史知识和用户 hook 可能仍有价值，破坏性清理无必要。
- **把所有 context 复制进每个 skill**。拒绝：增加 always-loaded token 与规则漂移；只保留每次
  调用确实需要的小型 guard。
