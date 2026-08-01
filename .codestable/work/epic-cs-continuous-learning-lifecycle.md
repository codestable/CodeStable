---
epic: ../epics/cs-continuous-learning-lifecycle.md
phase: executing
approved_revision: 4b0b8e8e0596e7ee42611864843512ecd9402970bb3682b5605f0dc0f8dcf01a
current_item: LEARN-3
next_action: implement LEARN-3 with tests first
blocked_by: null
item_progression: continuous
milestone_commit: authorized
remote_publish: each-milestone
---

## 子项进度

- [x] LEARN-1
- [x] LEARN-2
- [ ] LEARN-3

## 临时决策与证据

- 现有四个 task skill 只有 lesson 检索与笼统收尾推荐，没有 read-repair 或强信号筛选。
- 现有 eval runner 每个 cell 只有一次 invocation，无法证明跨会话迁移。
- 设计调研已核对 domain-modeling、teach、diagnosing-bugs、prototype、neat-freak 与现有 ADR-003；
  只借鉴晶化、证据晋级、机械化优先与 read-repair，不引入它们的默认目录或全局状态。
- design review round 1：Paseo `ceb5d5d6-4c74-4825-b600-64d5111b2f48`，
  `claude-fable-5` / `plan-high`，冻结 SHA-256 `a660265a...e7ffd`；1 blocking / 4 important 已处理。
- revised proposed Epic SHA-256：`a0107b6da2079556024c1a4807365e93a365149d37bedbbed7987188af45aa45`。
- design review round 2：Paseo `50bf355c-fbbb-4ef0-a9fd-ec3d9c560e9f`，
  `claude-fable-5` / `plan-high`，冻结 SHA-256 `a0107b6d...aa45`；0 blocking / 3 important 已处理。
- final design review round 3：Paseo `00358ef1-46a8-4976-abe6-8a2d4b783a07`，
  `claude-fable-5` / `plan-high`，冻结 SHA-256 `2c023c22...62cd`；0 blocking / 0 important / 3 nit，
  结论可交 owner 确认。
- accepted nit interpretation：Epic 游标候选沿用 `晶化候选：` marker；25pp 是总体聚合阈值且每个
  model family 方向必须为正；“等集测试”指四 task skills 的一致契约断言。
- owner 于 2026-08-01 确认 proposed Epic，并选择 `continuous` / `authorized` /
  `each-milestone`；激活后批准版本 SHA-256 为
  `4b0b8e8e0596e7ee42611864843512ecd9402970bb3682b5605f0dc0f8dcf01a`。
- LEARN-1 tests-first：新增契约测试先得到 `4 failed, 2 passed`，实现后定向契约
  `25 passed`、全量 `130 passed, 1 skipped`、分发 `3 passed, 1 skipped`，plugin package check 与
  `git diff --check` 通过；四个 task skill 与 ADR-006 均未超过 300 行。
- LEARN-1 晶化候选：无。Markdown 换行造成的锚点误判已通过空白归一化 helper 机械化，不另写
  重复 lesson。
- LEARN-1 diff review round 1：Paseo `8a20cd70-9f55-4331-9b69-90e63bed4913`，
  `claude-fable-5` / `plan-high`，冻结 staged patch SHA-256 `eff4faae...5d02`；
  `0 blocking / 1 important / 3 nit`。已补齐 canonical-owner 退役、候选证据/范围/归宿、显式记忆
  诉求同轮处理、窄维护报告，并加入旧 lesson 缺 `status` 的独立安装兼容；新增锚点先红后绿。
- LEARN-1 修复后验证：三份契约套件 `37 passed`、全量 `130 passed, 1 skipped`、分发
  `3 passed, 1 skipped`，plugin package check 与 `git diff --check` 通过。
- LEARN-1 diff review round 2：fresh Paseo `76255cc7-43b3-44d7-86af-90a2fffd3284`，
  `claude-fable-5` / `plan-high`，冻结 staged patch SHA-256 `e3490e44...7deb`；
  `0 blocking / 0 important / 4 nit`，结论可合。保留的 nit 仅为排版、授权来源概括、测试冗余和
  范围外 cs-review 旧推荐句，不影响行为或授权边界。
- LEARN-1 milestone：commit `45521f9`（`feat: add project learning lifecycle`），已发布到
  `origin/refactor-v2`。
- LEARN-2 tests-first：新增 `cs-keep` 三态生命周期、单一 owner 路由和双语低打扰文档契约，初始
  `3 failed`；实现 schema、独立后续验证、退役不复活、机械 guard 优先、晋升清理与公开文档同步后
  新增测试 `3 passed`，三份相关契约套件 `40 passed`。
- LEARN-2 完整验证：全量 `133 passed, 1 skipped`、分发 `3 passed, 1 skipped`，plugin package
  check 与 `git diff --check` 通过；所有相关 Markdown 均未超过 300 行。
- LEARN-2 晶化候选：无。本轮没有出现超出 ADR-006 且尚未被测试或 canonical 文档承接的强信号。
- LEARN-2 diff review round 1：Paseo `c50ee628-8fa6-4a1e-95cc-917b1c007de5`，
  `claude-fable-5` / `plan-high`，冻结 staged patch SHA-256 `29e97d73...24d51`；
  `0 blocking / 0 important / 5 nit`，结论可合。
- 主流程独立预检补充发现并修复三处 reviewer 漏检的契约漂移：`cs-keep` 补入 Epic 最终毕业 gate
  授权来源；WORKFLOW 命中报告补齐 status / 核验 / 影响；公开文档把 lesson 从经验终点纠正为无更强
  owner 时的 staging。同步处理 reviewer 的负断言归属、空白归一化、中英措辞等 nit。
- LEARN-2 review 修复后验证：三份相关契约套件 `40 passed`、全量 `133 passed, 1 skipped`、分发
  `3 passed, 1 skipped`，plugin package check 与 `git diff --check` 通过。
- LEARN-2 diff review round 2：fresh Paseo `ad9fd5a7-88b0-448a-88d0-5fe9a36d5739`，
  `claude-fable-5` / `plan-high`，冻结 staged patch SHA-256 `5f8e4f5b...09b18`；
  `0 blocking / 0 important / 3 nit`，结论可合，三处主流程补强均经独立核验成立。
- LEARN-2 nit 收口：负向旧路由断言改为跨换行归一化；README 与 `cs-keep` metadata 对齐为管理
  lesson 生命周期和 canonical 归宿；validated 统一使用“有效命中”。metadata 锚点初始 `1 failed`，
  改为通过 frontmatter 接口断言后相关契约 `40 passed`，全量 `133 passed, 1 skipped`，分发与 package
  checker 继续通过。
- LEARN-2 final diff review round 3：fresh Paseo `a8bfa9c3-627f-4a7b-b0b4-5438ca32f3f5`，
  `claude-fable-5` / `plan-high`，冻结 staged patch SHA-256 `6a04b044...50bdf`；
  `0 blocking / 0 important / 2 nit`，结论可合。保留的 nit 仅为英文 validated 术语精度和两套测试
  各自保留同名空白归一化 helper，不影响行为、授权或契约真实性。
