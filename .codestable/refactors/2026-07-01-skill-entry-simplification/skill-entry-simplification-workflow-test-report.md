---
doc_type: refactor-test-report
refactor: 2026-07-01-skill-entry-simplification
status: passed
tested: 2026-07-02
summary: Isolated workflow state-machine scenario tests for the skill entry simplification refactor.
---

# Skill Entry Simplification Workflow Test Report

## 1. 测试目标

本轮测试验证这次 entry simplification refactor 后，CodeStable 的主入口和兼容入口能在隔离仓库事实模型里按 `.codestable` 产物恢复正确下一步。

重点不是检查文案是否存在，而是验证：

- 主入口能按 `.codestable` 产物恢复正确下一步。
- 兼容入口不会保留独立流程，也不会要求用户重跑主入口。
- `cs-feat` / `cs-epic` 的人工 gate 可确认后继续推进长程 goal。
- Goal driver 只在可见且可 review 的条件下派发，失败回退 fenced `/goal`。
- issue / refactor / docs / code review 的阶段恢复不会被旧 stage skill 名称误导。

## 2. 隔离环境与边界

新增测试文件：`tests/test_skill_workflow_scenarios.py`。

每个场景都使用 `tmp_path` 创建独立 git repo，并写入最小 `.codestable` 骨架：

- `.codestable/attention.md`
- `.codestable/reference/execution-conventions.md`
- `src/app.py`
- feature / issue / roadmap / refactor / docs 对应产物

测试不依赖当前仓库真实 `.codestable` 状态，不启动真实长程 AI agent，也不在 toy app 中实际完成代码开发；它用仓库事实 evaluator 模拟 agent 按 skill 状态表做的下一步选择。这样能稳定复现 gate、状态恢复和 driver 派发决策。

真实 toy repo 开发 dogfood 见同目录 `skill-entry-simplification-dogfood-report.md`。

## 3. 场景矩阵

| 场景 | 覆盖 skill | 验证点 |
|---|---|---|
| router | `cs`, `cs-brainstorm`, `cs-req`, `cs-onboard` | 未接入仓库路由到 onboard；bug / refactor / docs / epic / brainstorm / requirement / feature 路由到主入口，不路由旧 stage skill |
| feature long-range | `cs-feat`, `cs-feat-*`, `cs-code-review` | 无 design → design；draft design → design-review；review passed 后停用户确认；模拟确认后生成 goal 包并派发 driver |
| feature goal state machine | `cs-feat`, `cs-code-review` | `implementation/running`、`review/ready`、`review/fixing`、`qa/ready`、`qa/fixing`、`acceptance/ready`、`complete/passed`、`handoff/blocked` 都路由到正确阶段 |
| epic long-range | `cs-epic`, `cs-roadmap*`, `cs-feat`, `cs-code-review` | roadmap review passed 后停用户确认；模拟确认后批量做 child design；child design-review passed 后统一停用户确认；模拟确认后生成 goal 包并派发 driver |
| goal driver | `cs-onboard`, `cs-feat`, `cs-epic` | Paseo 可见 driver 优先；native driver 必须同时具备可见 run surface 和 nested reviewer；否则 fenced `/goal` fallback |
| issue | `cs-issue`, `cs-issue-*`, `cs-code-review` | report → analyze → fix → code review；review blocking 回 fix；review passed 完成 |
| refactor | `cs-refactor`, `cs-refactor-ff`, `cs-code-review` | fastforward 小范围直达；标准流程 scan 用户勾选、design 用户确认、HUMAN 验证 gate、apply、code review |
| docs | `cs-docs`, `cs-doc-*`, `cs-docs-neat` | API docs 走 api protocol；guide 走 tutorial protocol；current 文档小改聚焦编辑；全局同步转 docs-neat |
| code review | `cs-code-review` | feature diff 进入 review；clean worktree 的 `--range` review 可执行；passed 且 diff 不变时进入下游 QA |
| compatibility | 所有旧 stage skills | 每个兼容入口加载主入口、携带 `requested_stage` / `requested_mode`，不使用兄弟目录相对路径，不要求用户重跑 |

覆盖集合由 `AFFECTED_SKILLS` 和 `SCENARIO_COVERAGE` 锁定；测试会失败于任何受影响 skill 没被场景覆盖。

## 4. 人工确认模拟

`cs-feat` 模拟：

1. 写入 draft feature design 和 passed design-review。
2. evaluator 返回 `user-checkpoint: feature-design-confirmation`。
3. 测试把 design frontmatter `status` 从 `draft` 改为 `approved`，模拟用户确认。
4. evaluator 继续进入 `references/goal/protocol.md`，再进入 goal driver 派发。

`cs-epic` 模拟：

1. 写入 draft roadmap 和 passed roadmap-review。
2. evaluator 返回 `user-checkpoint: epic-roadmap-confirmation`。
3. 测试把 roadmap `status` 改为 `active`，模拟用户确认 roadmap。
4. 写入两个 child feature draft design + passed design-review。
5. evaluator 返回 `user-checkpoint: all-feature-designs-confirmation`。
6. 测试把每个 child design `status` 改为 `approved`，模拟用户批量确认。
7. evaluator 继续进入 epic goal package 和 goal driver 派发。

这覆盖了用户特别要求的长程任务确认点：测试不会卡在 gate，而是模拟确认继续推进。

## 5. 运行结果

新增场景测试：

```bash
pytest -q tests/test_skill_workflow_scenarios.py
# 32 passed in 1.40s
```

原 entry simplification 静态约束测试：

```bash
pytest -q tests/test_skill_entry_simplification.py
# 21 passed in 0.06s
```

完整测试：

```bash
pytest -q
# 134 passed in 13.91s
```

包检查：

```bash
python tools/check-plugin-package.py --root . --json
# {"ok": true, "findings": []}
```

其他检查：

```bash
git diff --check
# passed

find plugins/codestable/skills -name '*.md' -print0 | xargs -0 wc -l | awk '$2 != "total" && $1 > 300 {print}'
# no output
```

## 6. 测试期间问题与处理

首次运行新增场景测试时，有 1 个失败：

- 失败点：`test_code_review_scenario_handles_feature_diff_and_ad_hoc_range`
- 原因：测试断言抓了 `cs-feat` 状态表里的短语“进入公开横切 gate”，但被测文件是 `cs-code-review/SKILL.md`，权威表述是“横切代码审查 gate”。
- 处理：修正测试断言为 `cs-code-review` 自身的权威短语。
- 重跑：`tests/test_skill_workflow_scenarios.py` 32 passed，随后完整测试 134 passed。

本轮没有发现需要修改 skill 协议本身的 blocking / important 问题。

## 7. 结论

当前证据证明：这次 skill entry simplification refactor 的核心状态机链路在隔离仓库事实场景下可恢复、可推进、可 gate、可 fallback。真实代码开发执行证据见 dogfood 报告。

尤其是：

- `cs-feat` 和 `cs-epic` 的长程 goal 模式不会被普通阶段 checkpoint 打断。
- 需要人确认的 design / roadmap gate 已有明确停点，确认后能继续推进到 goal package 和 driver。
- 旧 stage skills 保持可用但不再承载独立流程逻辑。
- `cs-code-review` 作为横切 gate 能服务 feature / issue / refactor 和 ad-hoc range。
- docs / issue / refactor 入口按主入口状态机恢复，不回退到旧 stage 路由。
