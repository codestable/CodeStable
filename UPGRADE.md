# CodeStable 升级指南

[English](./UPGRADE.en.md) · **中文**

升级前先看 [CHANGELOG.md](./CHANGELOG.md)，再使用最初的安装入口刷新。

不要把 `npx skills@latest update` 当作完整升级方式：外部 CLI 的更新发现与插件安装发现并不等价，可能误删 package 内的 sibling skills。

## Codex Plugin

```bash
codex plugin marketplace upgrade codestable
codex plugin add codestable@codestable
```

Codex 当前没有单独的 `plugin update` 子命令。第一条命令刷新 marketplace Git snapshot，第二条从新 snapshot 安装当前版本。

## Claude Plugin

```text
/plugin marketplace update
/plugin update codestable@codestable
```

更新后重启 Claude Code，使新版插件生效。

## `skills` CLI

同一 major 内升级，重新从 package root 完整安装：

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

项目级安装去掉 `-g`，并在对应项目中执行。不要改用裸 `update`；package-root `add` 才会按插件 manifest 发现完整 skill 集合。

## 从 v1.0.4 升级到 v2

v2 把 32 个入口收敛为 8 个主 skill，并只保留 `cs-code-review` 这一个兼容别名。

当前 `skills` CLI 的 `add` 不会自动删除新版 package 已移除的旧名称，因此首次升级前必须精确删除 24 个退役入口：

```bash
npx skills@latest remove \
  cs-audit cs-brainstorm cs-doc-api cs-doc-tutorial cs-docs cs-docs-neat \
  cs-domain cs-feat-accept cs-feat-design cs-feat-design-review cs-feat-ff \
  cs-feat-impl cs-feat-qa cs-feedback cs-goal cs-issue-analyze cs-issue-fix \
  cs-issue-report cs-note cs-refactor-ff cs-req cs-roadmap \
  cs-roadmap-impl-goal cs-roadmap-review \
  -g -y
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

这条删除命令按名称删除，不校验安装来源。它不会影响列表外的名称；如果你维护了同名自定义或第三方 skill，请先备份，并从命令中移除对应名称。

项目级 v1 安装同样去掉两条命令中的 `-g`，在项目目录执行。

## 项目资产不会被迁移

升级不会删除项目里的 v1 历史资产，也不会批量迁移或原地改写它们。既有需求、feature、issue、复盘与经验仍留在原位置；本指南不重复定义其运行时政策。

旧 tools、gates、hooks、reference 与 manifest 也原样保留，但 v2 不执行或刷新旧 runtime。升级 skill 包不需要逐仓库安装一套新 runtime。

检索与写入政策以 [WORKFLOW.md](./WORKFLOW.md#v1-升级边界) 为准；旧入口到 v2 入口的完整映射见 [SKILL_CATALOG.md](./SKILL_CATALOG.md#v104-退役入口)。

## 升级后检查

- 调用 `/cs`，确认根入口可用。
- 调用 `/cs-onboard` 时应只维护最小项目记忆，不覆盖已有项目文档。
- 使用 `skills` CLI 时，确认 8 个主 skill 与 `cs-code-review` 兼容别名都已安装。
- 遇到安装差异时先记录安装入口和版本，再到仓库 Issue 报告。

返回 [README](./README.md)。
