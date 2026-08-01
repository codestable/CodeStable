---
epic: ../epics/cs-continuous-learning-lifecycle.md
phase: executing
approved_revision: 4b0b8e8e0596e7ee42611864843512ecd9402970bb3682b5605f0dc0f8dcf01a
current_item: LEARN-3
next_action: squash and publish the reviewed source, then run real target probes
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
- LEARN-3 tests-first：新增 sequence、oracle、harness、fixture/config/cost 契约；实现 paired A / fresh
  `cs-keep` / treatment-control B、phase checkpoint、Git/manifest 隔离、成本聚合与 fail-closed freeze gate。
- LEARN-3 专项审计发现并修复：fixture/skill/seed/pipeline 输入漂移、截断 checkpoint 与 preflight cache、
  历史 retry integrity、candidate delta、adapter 异常成本、不同 `--out` 隔离、local Git include 预读取及
  Claude 临时 HOME 认证。新增三条回归先得到 `3 failed`，实现后转为 `3 passed`。
- LEARN-3 离线验证：sequence `37 passed`，oracle/adapter/既有 eval 回归通过；全量
  `252 passed, 1 skipped`，分发 `3 passed, 1 skipped`，plugin package check 与 `git diff --check` 通过。
- 六个冻结 fixture 逐个重建 seed 后均为 golden hidden/regression `1.0/1.0`、naive `0.0/1.0`；seed
  verify `4 passed`。dry-run 为 240 次 agent invocation、20 次 hook、`$3.41 [soft]`，低于 `$50` 预算。
- model target 离线探针：Claude/Codex CLI 与 adapter flags 均存在，隔离后的 provider auth 均可用；
  探针只执行 help/version/auth status，未发起模型请求。`freeze.json` 仍为
  `prepared-awaiting-commit`，真实 LLM 尚未运行。
- LEARN-3 frozen input checkpoint：commit
  `3022df55b4aca50e38d289558793db3ddd2205ac`，初始 attestation commit `715c831`；两者均未用于模型
  调用。提交后专项审计补入 Git 隔离修复，freeze gate 因 source bytes 漂移正确阻断，初始 attestation
  随即废弃并等待新 source checkpoint。
- LEARN-3 checkpoint 后加固：Git snapshot 额外隔离宿主 global/system/env config 注入；同一 `--out`
  使用非阻塞进程锁，`--fresh` 同时清除 checkpoint、preflight 与 cell state；在首个 Git 进程前拒绝
  `config.worktree`、`commondir` 及 object alternates；freeze schema、hash algorithm、aggregation 和
  family guard 均由契约测试锁定。
- LEARN-3 加固后验证：四份定向套件 `169 passed`、全量 `263 passed, 1 skipped`、分发
  `3 passed, 1 skipped`，plugin package check 与 `git diff --check` 通过；seed verify `4 passed`，
  六 fixture preflight 与 `$3.41 [soft]` dry-run 结果保持不变；未发起真实模型调用。
- LEARN-3 hardened source checkpoint：commit
  `9fb5d0fae63e308cfd7b7375295f65c53a202ef6`；纠正后的 manifest 保持 33 个实验输入与 25 个外部
  输入，仅替换 source SHA 与加固后的 `e2e_env.py` 哈希。
- 后续审计发现 UTF-8 BOM 可让 Git 接受 local include 而绕过首进程前检测；现改用 `utf-8-sig`
  解码并以回归测试锁定，sequence `45 passed`。此前 `fe635f1` 未执行协议要求的最小真实 target
  probe，因此不作为有效 attestation；候选 manifest 已恢复 `prepared-awaiting-commit` / `pending`。
- LEARN-3 晶化候选：无。输入冻结与 promotion fail-closed 已由既有反馈管线经验、sequence 契约测试和
  freeze manifest 共同承接，不另建重复 lesson。
- LEARN-3 diff review round 1：fresh Paseo `814fd85a-2a72-459e-adda-d23512a80a2a`，
  `claude-fable-5` / `high`，冻结 base `1d78fdd` 到 index patch SHA-256 `4a047d71...d362f0`；
  `0 blocking / 3 important / 6 nit`。important 指向宿主 Claude env 测试泄漏、retry history 与
  structural integrity 混合、Codex 读隔离无真实探针，均在任何真实模型调用前处理。
- LEARN-3 review 修复：Claude settings 测试清理完整 provider key；operational error 与 deterministic
  failure 分流；Claude/Codex 统一采用外层 Seatbelt，Codex 保留内层 `workspace-write`；新增逐 target
  真实模型探针，只允许输出布尔 oracle，不落 prompt、模型回答、sentinel 或 session id。
- retry/隔离专项审计进一步补齐 append-only write-ahead journal：每次 provider 前用新 invocation ID
  `flush + fsync` start 与 soft fallback，terminal 只追加；单 reducer 统一成本、interrupted/retry history、
  fixture-invalid、pipeline/score 与 fresh eligibility。只有完整 pair 才把 operational error 标 resolved，
  `--fresh` 仅允许 header-only journal，终态或已有结果必须使用新 `--out`。
- journal 与输出保全新增回归先得到 `8 failed`，实现后 sequence/oracle `96 passed`；探针显式
  `BLOCKED` marker 与宿主 `~/.claude.json` 快照先得到 `2 failed` 后转绿。四份 eval 定向套件当前
  `203 passed`，`git diff --check` 干净；freeze 机械比对为 33 inputs / 26 external inputs 全部一致，
  仍保持 `prepared-awaiting-commit`、`source_commit: pending`、probe pending、无真实 LLM run。
- 隔离审计 follow-up 发现并修复 attestation 未拒绝额外字段、宿主状态快照漏掉 session/rollout、首次
  snapshot 失败残留 sentinel：probe/target 字段改为闭集，快照递归覆盖已知持久状态但不读取 transcript，
  sentinel 从创建起受 `finally` 清理；相关用例均先红后绿。
- 六 fixture 复跑时发现 `python -I` 忽略 `PYTHONDONTWRITEBYTECODE` 环境变量并污染冻结资产；seed、
  injector、hook 与 deterministic pytest 现均显式使用 `-B`，五个回归先红后绿，实验目录复跑后无
  `__pycache__`。该错误已机械化，不另建 lesson。
- LEARN-3 最新验证：四份 eval 定向 `214 passed`，全量 `308 passed, 1 skipped`，seed verify
  `4 passed`；六 fixture 继续满足 golden `1.0/1.0`、naive `0.0/1.0`，dry-run 仍为 240 invocation、
  20 hook、`$3.41 [soft]`。freeze 为 33 inputs / 26 external inputs 全匹配，保持 prepared/pending，
  未执行真实模型。
- LEARN-3 隔离专项终态复核：内建只读 agent 对最新四个实现文件给出
  `0 blocking / 0 important / 0 nit`；独立确认 snapshot 异常无 sentinel 残留、四条 `-I -B` 路径均由
  真实 sibling import 测试锁定，freeze external inputs 匹配且无 bytecode 资产。
- LEARN-3 full diff review round 2：fresh Paseo `cbf5e71d-0d79-4620-8cb9-a9b75be9bb72`，
  `claude-fable-5` / `high`，冻结 base `1d78fdd` 到 index patch SHA-256 `955845cd...b70245c`、
  tree `39e5d475...864e2b`；`0 blocking / 1 important / 5 nit`。唯一 important 指出截断 journal tail
  修复仍以非原子整文件重写，二次崩溃窗口可能丢失 append-only 证据。
- LEARN-3 atomic repair tests-first：故障注入先复现 `os.replace` 失败时的保全要求；实现同目录临时文件、
  `flush + fsync + os.replace` 的 `_atomic_write_text`，checkpoint tail 与 preflight cache 共用该 helper。
  红态 `1 failed`，修复后聚焦 `5 passed`；四份 eval 定向 `215 passed`、全量
  `309 passed, 1 skipped`、分发 `3 passed, 1 skipped`，package checker、seed verify 与
  `git diff --check` 通过。dry-run 保持 240 invocation / 20 hook / `$3.41 [soft]`，freeze 的 33 inputs
  与 26 external inputs 全匹配，仍为 prepared/pending 且未运行真实模型。
- LEARN-3 atomic repair 晶化候选：无。该崩溃窗口已由故障注入回归和原子写 helper 机械承接。
- LEARN-3 final prepared diff review round 3：fresh Paseo
  `c95eeb1c-ba20-41b0-88d7-5c69c2927243`，`claude-fable-5` / `high`，冻结 base `1d78fdd` 到 index
  patch SHA-256 `7e43904b...c022`、tree `39429368...edf4f`；`0 blocking / 0 important / 4 nit`，
  结论可合。上一轮 atomic tail repair important 经字节级故障注入与全候选复核确认闭合；保留 nit 仅为
  父目录 fsync、探针错误诊断、锁文件和 kill -9 临时文件清理等可选加固，不影响本轮证据完整性。
