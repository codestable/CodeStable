---
doc_type: issue-fix
issue: standalone-runtime-version-unknown
path: standard
fix_date: 2026-07-14
related: [standalone-runtime-version-unknown-analysis.md]
tags: [runtime, versioning, standalone-install]
---

# Standalone Runtime 版本 Unknown 修复记录

## 1. 实际采用方案

采用分析方案 A：`cs-onboard` standalone 单元携带与仓库版本一致的 `VERSION`，现有版本发现逻辑无需新增 schema 即可读取。release bump 和 package checker 共同保证该副本不漂移；runtime sync 在版本仍不可发现时返回 `version-unavailable`，不再写入 `unknown` manifest。

## 2. 改动文件清单

- `plugins/codestable/skills/cs-onboard/VERSION`：standalone 版本载体。
- `plugins/codestable/skills/cs-onboard/tools/codestable_runtime.py`：版本缺失结构化 fail-closed；保留 onboarding 和 dirty managed paths 的既有错误优先级。
- `.claude/skills/eval-cs-skill/scripts/bump_version.py`：release bump 同步 standalone 版本。
- `tools/check-plugin-package.py`：校验 standalone、Codex/Claude plugin 与 marketplace 版本全部等于根 `VERSION`。
- `tests/test_codestable_doctor.py`、`tests/test_cs_skill_release.py`、`tests/test_plugin_package.py`：覆盖 standalone refresh、缺版本阻断、发布与 checker 一致性。

## 3. 验证结果

- standalone `cs-onboard` 临时副本运行 sync 后，manifest 的 `plugin_version` 与 `runtime_version` 均为 `1.0.3`。
- 删除 standalone `VERSION` 后，无论默认还是 `force=True` 都返回 `version-unavailable`，原 manifest 保持不变。
- runtime sync check：`status: ok`，expected/installed 均为 `1.0.3`，missing 为空。
- 相关测试 `45 passed, 1 skipped`；全量 `443 passed, 1 skipped`。
- ruff 与 `git diff --check` 通过。

## 4. 遗留事项

无 blocking/important 遗留；独立 code review 与 goal 功能验收仍需执行。
