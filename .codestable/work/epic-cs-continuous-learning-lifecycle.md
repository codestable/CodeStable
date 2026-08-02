---
epic: ../epics/cs-continuous-learning-lifecycle.md
phase: executing
approved_revision: 4b0b8e8e0596e7ee42611864843512ecd9402970bb3682b5605f0dc0f8dcf01a
current_item: LEARN-3
next_action: obtain a valid Codex CLI provider credential, then rerun both target probes
blocked_by: "codex-terra target probe fails at provider invocation; previous classified response was INVALID_API_KEY"
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
- LEARN-3 reviewed source milestone：4 个未发布 checkpoint 已压缩为 commit `eed9f55`，父提交为远端
  `1d78fdd`、tree `8b81cc0a...8c60`，已发布到 `origin/refactor-v2`；旧 attestation 从未用于真实模型。
- LEARN-3 真实 probe 首轮未形成 attestation：Claude 复杂安全 prompt 被模型自身拒绝，且宿主
  `.codex/logs_2.sqlite*` 的并发更新让全量 mtime snapshot 假失败；Codex runtime 又因 Seatbelt 父目录
  metadata 与 `/var` canonical 路径错配在模型前退出。三项均用 red -> green 回归收口：既有 state 内容
  变化不算 probe mutation、但新路径仍阻断；模型只验证 cell 写入，越界读写改由同一 Seatbelt profile
  的确定性 shell 验证；runtime env 全部 canonical，并只开放父目录本身、不开放 sibling 子树。
- LEARN-3 probe correction 证据：snapshot/prompt 回归先 `5 failed` 后 `8 passed`；分层 probe 回归先
  `2 failed` 后通过；Codex canonical runtime 与真实 Seatbelt `CODEX_HOME` 遍历测试均先红后绿。
  修复后的 Claude target 六个布尔 oracle 全部通过。Codex 已通过路径与 sandbox gate 并到达配置的
  provider API，但宿主 Codex CLI 自身同样返回 `INVALID_API_KEY`；当前没有可安全复用的 API/Paseo
  隔离替代，待有效 CLI credential 后重跑。freeze 保持 prepared/pending，未写失败 attestation，
  未运行 calibration/final campaign。
- LEARN-3 probe correction 晶化候选：无。三类可复发错误均已由契约测试和 frozen input 哈希机械承接。
- LEARN-3 probe correction 深化审计发现三条安全/效度断点：provider 配置解析可能静默退回默认 route；
  POSIX `read` 会把无换行 secret 的 EOF 误判为阻断；父进程会跟随模型控制的输出 symlink。新增
  fail-closed route/auth、allow-all sandbox 负控、模型/确定性 cell 分离、no-follow/大小上限与 symlink
  配置快照测试，红态为 `29 failed, 16 passed`，实现后 harness 为 `45 passed`。
- Codex host auth 只接受当前 uid、`0600`、普通非 symlink 的 `apikey` JSON；只把最小 key 放入隔离 env
  与临时最小 auth，不复制其他字段。selected provider 必须是 CLI `-c` 可表达的 bare id，四个 route
  字段完整且无额外字段；config 派生 route 不继承 ambient `OPENAI_BASE_URL`，任何解析失败均在调用前阻断。
- probe correction 修复后专项语义复核：内建只读 agent 冻结四文件 patch SHA-256
  `e53f5c5a...105d`，独立复现 allow-all 泄漏、真实 profile 三项阻断、symlink 输出拒绝与配置内容变化；
  `0 blocking / 0 important / 2 nit`。nit 仅为进一步锁定 >4 KiB 输出与更多异常清理分支。
- probe correction 完整验证：四份 eval 定向 `246 passed`、全量 `340 passed, 1 skipped`、分发
  `3 passed, 1 skipped`、seed verify `4 passed`，plugin package checker 与 `git diff --check` 通过；
  dry-run 保持 240 invocation / 20 hook / `$3.41 [soft]`。freeze 的 33 inputs / 26 external inputs 已重新
  匹配，仍为 prepared/pending，未运行 calibration/final campaign。
- LEARN-3 probe correction 晶化候选：无。新增三类断点均已由确定性 helper 和 red -> green 回归承接。
- LEARN-3 probe correction diff review round 1：fresh Paseo
  `1b129156-e9c2-4a55-a10a-9e1ef63158a1`，`claude-fable-5` / `high`，冻结 staged patch
  `7eebbd42...c96c`、tree `c7943d9d...a94f7f3a440`；`0 blocking / 2 important / 3 nit`。
  important 指向 auth 派生 key 的 ambient route 歧义和稳定指令文件未做内容 hash，均已处理。
- 同轮专项安全审计发现 `1 blocking / 3 important`：模型工具可读取临时 auth 与继承的 provider env；
  当前 Codex 只认 `CODEX_API_KEY`；host config 缺 owner/写权限校验；失败 stderr 可能回显 key。新增测试先得
  `10 failed, 42 deselected`，实现 owner/mode、route 与 stderr gate 后聚焦 `11 passed`。
- 真实 Codex + 仅本机假 provider 回归进一步推翻两个假设：外层 Seatbelt 中的内层 `workspace-write`
  会因嵌套 `sandbox_apply` 失败；仅用 `shell_environment_policy.inherit=core` 仍可从父进程信息读取 key。
  现由外层 Seatbelt 独占 cell/sibling 文件边界，Codex 内层设 `danger-full-access` 避免嵌套，并禁用默认
  `plugins` 后台 clone；本地 credential proxy 在内存中向上游注入 Bearer，Codex argv/env/home/父进程均无 key。
- 真实 CLI 安全 oracle 已机械证明：两次请求只到 `127.0.0.1` 假 provider、Authorization 使用受控 dummy、
  请求体不含 key、工具实际执行且其 env/父 PID/进程枚举均看不到 key、sibling read 仍被阻断；跨域 redirect
  不携带 Authorization，local proxy 强制 `NO_PROXY`，非法 key 与不可信 route/config 均在调用前失败。
- 正式 review 的 snapshot nits 同批收口：`CLAUDE.md` / `AGENTS.md` 纳入稳定内容 hash，未知顶层状态目录新增
  会改变 snapshot，probe result 读取增加 `O_NONBLOCK`，Seatbelt listing 用例不再空验。
- LEARN-3 hardened correction 验证：harness `58 passed`；四份 eval 定向 `259 passed`；全量
  `353 passed, 1 skipped`；分发 `3 passed, 1 skipped`、seed verify `4 passed`，plugin package checker 与
  `git diff --check` 通过；dry-run 仍为 240 invocation / 20 hook / `$3.41 [soft]`。
- freeze 再次机械核对为 33 inputs / 26 external inputs 全匹配，保持 `prepared-awaiting-commit`、
  `source_commit: pending`、probe pending、`real_llm_runs_started=false`；本轮没有运行真实 campaign。
- LEARN-3 hardened correction 晶化候选：无。凭证穿透、route 歧义、snapshot 与 FIFO 风险均已有确定性
  helper、真实 CLI 攻击回归或 freeze hash 承接，不另建 lesson。
- LEARN-3 hardened correction diff review round 2：fresh Paseo
  `f6a0b030-3fba-4fa0-81a3-7c7bf949d479`，`claude-fable-5` / `high`，冻结 staged patch
  `5b658fa3...deeef4`、tree `71de77e1...c4d4`；`1 blocking / 0 important / 2 nit`。blocking 证实
  `process-info-listpids` 只阻断枚举，工具仍可沿已知 PPID 读取祖先环境。
- 进程隔离修复采用系统 profile 同类规则：`deny process-info*` 后只允许 `target self`；修复前已用真实
  Codex + 本机 fake provider 的良性工具调用验证不会破坏执行。随后撤回会触发宿主安全拦截的 PPID 遍历
  测试，仅保留严格 profile 文本契约与既有真实 CLI 行为证据，不再执行祖先凭证扫描。
- 主流程另行复现并修复两条 proxy 边界：Codex 子进程不再继承可能含凭证的宿主 proxy env，只保留固定
  loopback `NO_PROXY`；credential proxy 退出时先撤销 forwarding、停止接入并关闭存量连接，半请求不能在
  invocation 结束后继续携带 Bearer。新增回归红态 `3 failed, 1 passed`，修复后纯本地聚焦 `4 passed`、
  harness 非真实 CLI 子集 `56 passed, 3 deselected`、四份 eval `257 passed, 3 deselected`、全量
  `351 passed, 1 skipped, 3 deselected`；分发 `3 passed, 1 skipped`、seed verify `4 passed`、package
  checker 与 `git diff --check` 通过，dry-run 保持 240 invocation / 20 hook / `$3.41 [soft]`。
- LEARN-3 process/proxy hardening 晶化候选：无。三条风险均由 Seatbelt 契约、proxy 生命周期 helper 和
  确定性回归机械承接，不另建 lesson。
- LEARN-3 process/proxy hardening diff review round 3：fresh Paseo
  `65f7052b-2f2f-46fd-9985-4d7f7c9a40ea`，`claude-fable-5` / `high`，冻结 staged patch
  `06ae07a8...b4b67`、tree `77dade41...c8607`；`0 blocking / 0 important / 4 nit`，结论可合。
- owner 随后复现默认 pytest 节点会启动真实 Codex 并触发挂起/宿主安全拦截，故上一冻结结论不作为最终
  提交依据。静态红态确认三项真实 CLI 用例没有 opt-in，且 Codex 用例仍含进程枚举与父进程环境探测。
- 修复后 `real_cli` 测试默认 skip，仅显式 `--run-real-cli` 才执行；同时删除进程枚举和父进程环境读取。
  owner 原命令为 `3 passed, 1 skipped`，harness `56 passed, 3 skipped`，四份 eval
  `257 passed, 3 skipped`，全量 `351 passed, 4 skipped`；分发 `3 passed, 1 skipped`、seed verify
  `4 passed`、package checker 与 `git diff --check` 通过，dry-run 仍为 240 invocation / 20 hook /
  `$3.41 [soft]`，freeze 33 inputs / 26 external inputs 零漂移。
- LEARN-3 real-CLI opt-in 修复晶化候选：无。默认禁跑由 pytest collection policy 与三处 marker
  机械承接，不另建 lesson。
- LEARN-3 real-CLI opt-in fresh review：Paseo `0667d2cf-d27c-4800-b048-fd6e1413a9d6`，
  `claude-fable-5` / `high`，冻结 staged patch `f63d6476...f4f27`、tree `7ec517ac...e1f0`；
  `0 blocking / 0 important / 3 nit`，结论可合。reviewer 未执行任何真实 CLI、模型调用或进程环境探测，
  并独立复现三项 real-CLI node 默认全部 skipped、marker 覆盖完整及 freeze 33/26 零漂移。
- LEARN-3 reviewed probe-hardening milestone：commit `54785f7`（`fix: harden learning transfer target
  probes`），已发布到 `origin/refactor-v2`。
- commit 后正式 target probe 保持 fail-closed：Claude `claude-haiku` 的 cell write、host/sibling read
  block、host write block、config unchanged、runtime removed 六项全部通过；Codex `codex-terra` 在 provider
  invocation 返回 `HarnessError`。同一 provider 的上次可诊断响应为 `INVALID_API_KEY`，本轮未修改宿主认证，
  不再盲目重试。freeze 与 attestation 继续保持 prepared/pending，未启动 calibration/final campaign；
  probe sentinel、sandbox 与进程均已清理。
