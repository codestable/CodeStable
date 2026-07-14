---
doc_type: issue-fix
issue: skills-update-removes-cs-skills
path: standard
fix_date: 2026-07-14
related: [skills-update-removes-cs-skills-analysis.md]
tags: [installation, skills-cli, regression]
---

# Skills Update 删除 CodeStable Skills 修复记录

## 1. 实际采用方案

采用分析方案 A：不复制 skill 或改变 canonical package 布局，而是把 `skills` 安装与升级都限定到 `codestable/CodeStable/plugins/codestable` package root。中英文 README 不再推荐存在破坏风险的裸 `update`，package checker 将安全命令设为发布契约。

默认离线回归固定 `skills@1.5.17` 的 discovery 与删除判定：仓库根只发现 2 个维护者 skills，32 个 plugin lock 路径会全部进入删除差集；package subpath 能精确发现完整 32 个，删除差集为空。迁移前 29 个 sibling inventory 也被固定；真实 CLI E2E 另行预装第三方 skill，验证完整 package 重装不会误删它。

## 2. 改动文件清单

- `README.md`、`README.en.md`：安装和升级改用 plugin package root；解释裸 update 风险与 project scope 用法。
- `tools/check-plugin-package.py`：要求安全安装/升级命令并拒绝裸 update。
- `tests/test_plugin_package.py`：锁定双语命令契约。
- `tests/test_skills_cli_distribution.py`：增加离线 discovery/reconciliation 与可选真实 CLI E2E。
- `tests/fixtures/skills-cli/legacy-cs-inventory.json`：记录 package 化前的 29 个 sibling skills。

## 3. 验证结果

- RED：focused 初始 5 类 package/release/runtime 契约均按预期失败。
- GREEN：四个相关测试文件 `45 passed, 1 skipped`。
- 真实 `skills@1.5.17` 隔离重复安装：`1 passed`，预装第三方 probe 与 32 个 CodeStable sibling 全部保留。
- 全量：`443 passed, 1 skipped`；默认 skip 为需显式 CLI 的网络/缓存边界测试。
- `check-plugin-package.py --json`：`ok: true`，无 findings。

## 4. 遗留事项

- 上游 `vercel-labs/skills#1298` 尚未关闭；package-root `add` 是安全完整重装入口，不能重新宣称裸 `update` 已安全。
- 上游修复 install/update discovery 同源后，可另行评估是否恢复更简短的升级命令。
