---
doc_type: refactor-dogfood-report
refactor: 2026-07-01-skill-entry-simplification
status: passed
tested: 2026-07-02
summary: Real isolated toy repo dogfood for the skill entry simplification refactor.
---

# Skill Entry Simplification Dogfood Report

## 1. 测试目标

这份报告补充真实隔离开发仓库 dogfood，弥补状态机场景测试没有实际改代码的问题。

目标：用当前分支改动后的 CodeStable skill 文档，实际推进一个小型 Python toy repo 的 feature、issue、refactor、docs、epic 和 code-review 工作流，并模拟 `cs-feat` / `cs-epic` 的人工确认点继续执行。

## 2. 隔离仓库

路径：`/tmp/codestable-skill-dogfood.Xk4s5v/toyapp`

仓库内容：

- Python package：`src/toycalc`
- 测试：`tests/test_core.py`
- CodeStable 骨架：`.codestable/attention.md`、`.codestable/reference/execution-conventions.md`
- 验证命令：`pytest -q`

baseline 后发现并修复了一个真实卫生问题：第一次跑 pytest 后 `__pycache__` 被提交。处理方式是添加 `.gitignore` 并从 git index 移除 `.pyc` 生成物。

## 3. 实际提交记录

toy repo 最终提交历史：

```text
fdfeb0a feat: add multiply support epic
ae1ebec docs: document calculation api
901bd35 refactor: extract format normalization helper
71f3b2b fix: normalize integer result formatting
9d2d968 feat: add safe divide api
ee41cee chore: ignore generated python caches
e591aea baseline toycalc app
```

最终验证：

```bash
pytest -q
# 8 passed in 0.00s
```

## 4. 覆盖的 workflow

| Workflow | 实际动作 | 关键产物 |
|---|---|---|
| `cs-feat` | 新增 `safe_divide` API；先 design/design-review/checklist，再模拟用户确认，生成 goal 包，实际实现、review、QA、acceptance | `.codestable/features/2026-07-02-safe-divide/*` |
| `cs-code-review` | 为 `safe_divide` 和 `multiply-core` 写 review 报告，作为 QA 前 gate | `safe-divide-review.md`、`multiply-core-review.md` |
| `cs-issue` | 修复 `format_result(4.0)` 输出 `Result: 4.0` 的问题，走 report → analysis → fix-note → review | `.codestable/issues/2026-07-02-integer-format/*` |
| `cs-refactor` | 标准模式扫描并提取 `_normalize_value` helper；模拟 scan 勾选和 design 确认，执行 apply，保留 apply-notes 和 review | `.codestable/refactors/2026-07-02-format-helper/*` |
| `cs-docs` | 为计算 API 写 API reference 和 dev guide | `docs/api/toycalc-api.md`、`docs/dev/calculation-guide.md` |
| `cs-docs-neat` | 将稳定学习沉淀进 `.codestable/compound/` | `.codestable/compound/safe-divide-learning.md` |
| `cs-epic` | 规划 `multiply-support` roadmap；review passed 后模拟 roadmap 确认；生成 child feature design，design-review passed 后批量确认；生成 goal 包并执行 child feature | `.codestable/roadmap/multiply-support/*`、`.codestable/features/2026-07-02-multiply-core/*` |

兼容入口没有逐个真实调用宿主 skill runtime；它们由自动化场景测试验证委托语义，不在这份 dogfood 中重复模拟。

## 5. 人工确认模拟

`cs-feat`：

1. `safe-divide-design.md` 初始 `status: draft`。
2. `safe-divide-design-review.md` 写入 `status: passed`。
3. 模拟用户确认：将 design frontmatter 改为 `status: approved`。
4. 生成 `goal-plan.md`、`goal-state.yaml`、`goal-protocol.md`。
5. `goal-state.yaml` 记录 `driver_kind: native`、`driver_id: dogfood-visible-driver-safe-divide`，表示可见 driver simulation。
6. 实际实现、review、QA、acceptance 后，`goal-state.yaml` 更新为 `stage: complete`、`status: passed`，acceptance 打印 `CS_FEATURE_GOAL_COMPLETE`。

`cs-epic`：

1. `multiply-support-roadmap.md` 初始 `status: draft`。
2. `multiply-support-roadmap-review.md` 写入 `status: passed`。
3. 模拟用户确认 roadmap：将 roadmap 改为 `status: active`。
4. 生成 child feature `multiply-core` 的 design/checklist/design-review。
5. 模拟用户统一确认所有 child design：将 child design 改为 `status: approved`。
6. 生成 epic goal 包，`goal-state.yaml` 记录 `driver_kind: native`、`driver_id: dogfood-visible-driver-multiply-support`。
7. 实际实现 child feature、review、QA、acceptance，更新 items.yaml 和 goal-state。
8. `goal-audit.md` 记录 `CS_ROADMAP_GOAL_COMPLETE`。

## 6. 产物证据

最终 toy repo 关键产物：

```text
.codestable/features/2026-07-02-safe-divide/goal-state.yaml
.codestable/features/2026-07-02-safe-divide/safe-divide-acceptance.md
.codestable/issues/2026-07-02-integer-format/integer-format-fix-note.md
.codestable/refactors/2026-07-02-format-helper/format-helper-apply-notes.md
.codestable/roadmap/multiply-support/goal-audit.md
docs/api/toycalc-api.md
docs/dev/calculation-guide.md
```

状态核验摘录：

```text
safe-divide design: status approved
safe-divide review/QA/acceptance: status passed
safe-divide completion marker: CS_FEATURE_GOAL_COMPLETE
multiply-core design: status approved
multiply-core review/QA/acceptance: status passed
multiply-support goal-state: status complete
multiply-support audit marker: CS_ROADMAP_GOAL_COMPLETE
```

## 7. 发现的问题

本轮 dogfood 发现 1 个真实隔离 repo 工程卫生问题：

- 问题：初始 toy repo 没有 `.gitignore`，pytest 生成的 `__pycache__` / `.pyc` 被提交。
- 修复：添加 `.gitignore`，从 git index 移除缓存文件，提交 `ee41cee chore: ignore generated python caches`。
- 归因：测试环境搭建问题，不是 CodeStable skill 协议问题。

没有发现本次 skill entry simplification 在真实 toy repo 推进中出现 blocking / important 协议缺陷。

## 8. 结论

当前证据比状态机场景测试更强：改动后的 skill 流程不仅能从仓库事实恢复下一步，也能在真实隔离开发仓库中推进小型工程任务。

已验证：

- `cs-feat` 长程：design gate 确认后能继续 implementation → review → QA → acceptance。
- `cs-epic` 长程：roadmap gate 和 child design gate 确认后能继续 goal package → child feature loop → audit。
- `cs-issue`、`cs-refactor`、`cs-docs`、`cs-docs-neat` 能与 feature/epic 产物协同，而不是依赖旧 stage skill。
- 最终 toy repo 测试通过：`pytest -q` 8 passed。
