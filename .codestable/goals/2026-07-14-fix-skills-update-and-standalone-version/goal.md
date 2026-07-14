---
doc_type: goal
goal: fix-skills-update-and-standalone-version
status: active
---

# 修复多 Skill 更新与 Standalone 版本发现

## Objective

修复 GitHub Issues #45 和 #47：正常更新 CodeStable 多 skill package 时保留 sibling `cs*` skills；以 standalone 形式安装 `cs-onboard` 时，runtime manifest 仍能写入真实 CodeStable 版本。完成自动化回归、独立审查、功能验收并创建独立 PR。

## Starting Point

PR #48 已合并到 `main`，本 goal 从 merge commit `c2572f4` 建立分支 `fix/issues-45-47-install-runtime`。当前安装文档推荐裸 `npx skills@latest update`；standalone skill 单元缺少可供 runtime sync 稳定读取的版本元数据。

## Acceptance Criteria

- 完整 CodeStable multi-skill install/update 场景有可执行回归，更新不能删除仍属于 package 的 sibling skills。
- standalone `cs-onboard` 安装能发现实际版本，生成的 `plugin_version` 与 `runtime_version` 不为 `unknown`。
- release bump、package checker 与 runtime sync 共同校验版本一致性。
- focused、相关与全量测试，以及 diff、Markdown 和 runtime sync 门禁全部通过。
- 提交 PR 前必须显式运行固定 `skills@1.5.17` 的真实 CLI E2E，覆盖第三方 skill 与 CodeStable sibling skills 的重复安装保留行为。
- 独立 code review 和功能验收均通过；变更推送到独立分支并创建关联 #45/#47 的 PR。

## Non-Goals

- 不修改或发布外部 `skills` CLI 本身；仓库侧通过 package 布局、元数据、测试与升级指引解决可控范围。
- 不自行合并 PR，不扩展到 #45/#47 之外的安装器功能。

## Decisions And Assumptions

- 用户已明确验收终点和交付方式，无需额外 grill。
- #45 与 #47 共享安装包与 runtime 元数据边界，在同一分支和 PR 内修复，但各自保留独立问题证据与回归。
- GitHub 通信优先使用已验证可用的 SSH rewrite 与 `gh`；不更改用户全局 Git 配置。

## Current State

Goal 已激活，尚未修改生产实现。

## Next Action

检查 package discovery、安装/更新测试、版本发现、release bump 与 plugin checker 的现有实现，先建立能复现两项问题的 RED 测试。
