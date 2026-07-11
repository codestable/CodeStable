# CS Feedback Evidence Pipeline Goal Plan

## 1. Inputs

- Feature: `2026-07-10-cs-feedback-evidence-pipeline`
- Design: `.codestable/features/2026-07-10-cs-feedback-evidence-pipeline/cs-feedback-evidence-pipeline-design.md`
- Checklist: `.codestable/features/2026-07-10-cs-feedback-evidence-pipeline/cs-feedback-evidence-pipeline-checklist.yaml`
- Design review: `.codestable/features/2026-07-10-cs-feedback-evidence-pipeline/cs-feedback-evidence-pipeline-design-review.md`
- Baseline ref: `30fecaae5e747dbad1f0e599d592d7c04cc7f0c4`
- User approval: 用户于 `2026-07-10T19:07:38+08:00` 明确回复“确认”。
- Existing worktree changes: `.codestable/attention.md` 与本 feature 目录属于本 goal，driver 不得回滚；其他新增变化视为用户资产，先核验来源。

## 2. Objective

把显式 `cs-feedback` 调用升级为本地证据管线：默认安全定位当前会话，生成可追溯 incident、evidence、triage 与 public preview；shipped skill 只产 local-private regression candidate，repo-local eval skill 负责正式 fail-closed promotion。

## 3. Execution Steps

按 checklist 六步顺序推进，每完成一步立即更新 checklist status 与 `goal-state.yaml.ledger`：

1. 行为等价拆分 collector、privacy/models 和 reporter tests。
2. 完成 metadata-only current session、双 cutoff、normalized record、tool pairing、incident 聚合与 repo context。
3. 完成 triage、字段来源、quality gate 和 public allowlist projection。
4. 完成 shipped candidate-only converter 与 repo-local promotion 工具的 artifact handoff。
5. 更新 cs-feedback 协议、report template、shared/execution runtime 模板与公开文档。
6. 补齐 provider/隐私/profile/兼容 decision fixtures，运行全量 gate。

## 4. TDD Policy

- 所有行为代码 step 默认使用 RED → GREEN → VERIFY micro-loop；每个 step 的 evidence 记录失败测试、最小实现和通过命令。
- 纯移动的微重构先锁定既有 9 个 feedback tests，再移动、再验证；不得在同一 diff 混入行为变化。
- 文档投影或纯声明无法合理先写失败测试时，记录 `TDD exception`，并提供 static contract test、diff review 或 schema validation 作为替代证据。
- 缺 RED/GREEN/VERIFY 且无 `TDD exception` 的 step 不得进入 review。

## 5. Review Agent Constraint

- 所有 design/code/re-review gate 必须使用 Paseo `provider=claude`、`model=claude-fable-5`、
  `thinkingOptionId=high`，只读等价 mode。
- Fable 因额度或 provider 异常无法完成时必须 handoff；用户没有授权任何 reviewer 模型降级。
- code review 结论必须分别覆盖 spec 合规与代码质量；blocking/important 全部解决后才能 passed。

## 6. Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_cs_feedback*.py tests/test_cs_skill_bootstrap.py tests/test_skill_entry_simplification.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_cs_skill_eval.py tests/test_cs_skill_convergence.py tests/test_cs_skill_release.py tests/test_cs_skill_bootstrap.py tests/test_cs_skill_selfref.py
python3 tools/check-plugin-package.py --root . --json
python3 plugins/codestable/skills/cs-onboard/tools/codestable-runtime-sync.py --root . --source-skill-dir plugins/codestable/skills/cs-onboard --check --json
git diff --check
```

`check-plugin-package.py` 当前允许记录 ignored 根 `cs-onboard/` legacy 目录的既有非 core finding，但 findings 数量/类型不得新增。其余 core 命令失败必须修复或 handoff。

## 7. Core Acceptance Path

- 逐项证明 design 的 16 个场景，尤其 current session ambiguity 不读正文、Codex/Claude 同构 incident、v1 public 8 字段/6 值域、三类 local-private 上传拒绝。
- shipped runtime 不得 import repo-local eval skill；candidate→promotion 只通过 JSON artifact，跨单元连接只允许存在于 repo-local tests。
- promotion 对缺 eval/config、空/占位/敏感 input、不兼容 scorer/harness/judge 全部非零且不落盘。
- runtime template 与 repo-local copy 同步，`codestable-runtime-sync.py --check --json` 为 `status=ok`。

## 8. DoD And Handoff

- Implementation：六个 steps done，TDD evidence 与 gate outputs 落盘。
- Review：Fable 5 high reviewer 无 unresolved blocking/important。
- QA：隐私、聚合、quality、promotion、兼容与全量测试通过。
- Acceptance：16 个场景与 required artifacts 从仓库事实核验通过。
- 需要改变 approved design/公开契约、同一失败三轮未过、Fable 5/high reviewer 不可用、外部环境阻止核心判断或用户要求暂停时，立即 handoff，不扩大范围。
