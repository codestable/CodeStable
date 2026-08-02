---
epic: ../epics/cs-continuous-learning-lifecycle.md
phase: executing
approved_revision: 4b0b8e8e0596e7ee42611864843512ecd9402970bb3682b5605f0dc0f8dcf01a
current_item: LEARN-3
next_action: publish the A pipeline correction; wait for fresh owner authorization before any real probe
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

- 初始调研确认 task skills 只有 lesson 检索与笼统收尾，旧 eval 也不能证明跨会话迁移；设计只借鉴
  晶化、证据晋级、机械化优先与 read-repair，不引入外部 skill 的默认目录或全局状态。
- Epic design review 共三轮：Paseo `ceb5d5d6`、`50bf355c`、`00358ef1`；前两轮 findings 已处理，
  末轮为 `0 blocking / 0 important / 3 nit`。owner 于 2026-08-01 确认永久 Epic，并选择
  `continuous` / `authorized` / `each-milestone`；批准 hash 即 frontmatter `approved_revision`。
- LEARN-1 tests-first 为 `4 failed, 2 passed`；修复与兼容收口后契约 `37 passed`、全量
  `130 passed, 1 skipped`。reviews：Paseo `8a20cd70`（1 important 已处理）、`76255cc7`
  （`0 blocking / 0 important`）；milestone `45521f9` 已发布。
- LEARN-2 tests-first 为 `3 failed`；三态 lifecycle、canonical owner 与双语文档收口后契约
  `40 passed`、全量 `133 passed, 1 skipped`。reviews：Paseo `c50ee628`、`ad9fd5a7`、`a8bfa9c3`，
  末轮 `0 blocking / 0 important`；milestone `1d78fdd` 已发布。
- LEARN-1/2 晶化候选均为无：换行锚点、lifecycle 与 owner 路由已由 helper、契约测试和 ADR-006 承接。
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
- owner 确认 shell 同时配置 `OPENAI_API_KEY` 与 `OPENAI_BASE_URL`；只读核验又确认本机 Codex 的
  `config.toml` 已选 `sub2api`、`auth.json` 与 `codex login status` 一致。根因不是凭证失效，而是 harness
  让 ambient key 优先，拆散 selected provider 与 stored auth，并把无关 key 发往错误 endpoint。
- provider/auth 原子性回归先红：期望 `gateway.example.invalid`，实际取 ambient route；实现改为 selected
  provider 存在时只配对同一 `CODEX_HOME/auth.json`，仅无 selected provider 时才采用完整 ambient fallback。
  缺失 stored auth 时也禁止回退到 ambient。修复后聚焦 `5 passed`、四份 eval
  `258 passed, 3 skipped`、全量 `352 passed, 4 skipped`；分发 `3 passed, 1 skipped`、seed verify `4 passed`、package checker 与
  `git diff --check` 通过，dry-run 保持 240 invocation / 20 hook / `$3.41 [soft]`，freeze 33/26 全匹配。
- provider/auth 原子性 fresh review：Paseo `74f5b8ef-8a33-41fb-b79f-703c872cd2ec`，
  `claude-fable-5` / `plan-high`，冻结 staged patch `2e03b9af...f9ce`、tree `80919f9e...2512`；
  `0 blocking / 0 important / 3 nit`，结论可合。reviewer 未运行真实 CLI、模型调用或进程扫描。
- provider/auth 原子性里程碑已提交并发布：`92b12babe359b836e003cbe232358a1330c09a92`。提交后首轮
  双 target probe 只返回 `RuntimeError`，未形成 attestation；清理核验无 sentinel、sandbox 或进程残留。
  随后逐 target 诊断与官方双 target 复跑均通过：`claude-haiku`、`codex-terra` 的 cell write、
  host/sibling read block、host write block、config unchanged、runtime removed 六项全部为 true。
- `freeze.json` 已据官方闭集输出切换为 `frozen`，source commit 绑定 `92b12ba`，probe status 为 passed，
  `real_llm_runs_started=true`；未启动 calibration 或 final campaign，也未持久化 prompt、模型输出或凭证。
- `92b12ba` 的 `k=2` calibration 使用独立 `calibration-k2-92b12ba.json`，实际软成本 `$1.886275`：
  Claude 12/12 为 `pipeline-failed`，Codex 12/12 为未解决 operational error（外层
  `RetryableSequenceError`，根因 `HarnessError`），0 个可聚合完成 pair，verdict 为 `REJECTED /
  underpowered`。结果与 append-only checkpoint 均保留，不删除、不改样本，也不进入 final。
- Codex error 均在 76–91ms 内发生；等价深层 artifacts workdir 复现 Seatbelt 无法 canonicalize 临时
  `CODEX_HOME`。新增非 real-CLI `/bin/sh` 回归先红后绿：逐级放行受保护祖先的 metadata 后 runtime 可
  canonicalize，sibling 内容仍不可读；同路径真实 Codex 短诊断通过。Claude 额外诊断在 600s 超时，
  未据此改 prompt、fixture、hypothesis 或 metric，原负结果照实保留。
- 因 `base.py` 是 frozen pipeline input，新候选 manifest 已用其新 hash 重新置为
  `prepared-awaiting-commit` / pending / `real_llm_runs_started=false`；该字段只描述尚未运行的新 source。
- nested Seatbelt 修复验证：harness `58 passed, 3 skipped`、四份 eval `259 passed, 3 skipped`、全量
  `353 passed, 4 skipped`、分发 `3 passed, 1 skipped`、seed verify `4 passed`；package checker、
  `git diff --check` 通过，dry-run 仍为 240 invocation / 20 hook / `$3.41 [soft]`，freeze 33/26 全匹配。
- nested Seatbelt review 的 Fable 运行 `d48a130d` 在完成确定性核验后两次因 provider `503` 未形成报告；
  owner 指定不可用时回退 Opus。fresh Opus reviewer `c50bd609` 冻结 patch `8b6ee734...271fa`、tree
  `68fab428...21a4`，给出 `0 blocking / 2 important / 5 nit`：Claude binary 祖先 metadata 未覆盖，且新
  metadata 放行缺少 listing/stat/literal 负向契约。
- review 修复先红：同一非 real-CLI `/bin/sh + sandbox-exec` 用例中 runtime 可 canonicalize，但 home 下
  模拟 Claude binary 目录报 `Not a directory`。共享 profile 现只把 binary 加入祖先 metadata 来源，
  不把 binary 目录变成可读 subpath；同时锁住 sibling 内容、listing、stat 与 metadata 段只含 literal。
- 修复后 harness `58 passed, 3 deselected`、全量 `353 passed, 1 skipped, 3 deselected`，命令显式
  `-m 'not real_cli'`；seed verify `4 passed`、package checker、`git diff --check` 均通过，dry-run 仍为
  240 invocation / 20 hook / `$3.41 [soft]`，freeze 33/26 零失配。游标已压缩已发布的 LEARN-1/2 过程
  证据并保留 review/commit 指针；新 `base.py` hash 为 `2e440a7a...e061`。
- nested Seatbelt fresh re-review：Opus Paseo `ab6f7611-adff-41dd-9801-4627652eb65e`，冻结 patch
  `87122d76...cb327`、tree `69a55202...e3333`；`0 blocking / 0 important / 7 nit`，结论可合。两条
  important 均经独立 `/bin/sh + sandbox-exec` 对照闭合，且未执行 real CLI、target probe 或模型调用。
- nested Seatbelt milestone `652949c08d42ee099be404cdc9e6914a69b5439b` 已发布。提交后的官方双 target
  probe 通过：`claude-haiku` 与 `codex-terra` 的 cell write、host/sibling read block、host write block、
  config unchanged、runtime removed 六项均为 true；输出只含闭集布尔 attestation，无 prompt、回答或凭证。
- 双 target attestation commit `70ae347` 已发布。随后 `652949c` 的 `k=2` calibration 按 owner 纠偏中断；
  无最终 JSON 或 verdict，53 行 append-only checkpoint 原样保留（SHA-256 `61efb61b...ac052`），不得恢复、
  删除或 `--fresh` 覆盖。旧 `92b12ba` 的完整负结果亦原样保留。
- 更早的 `9fb5d0f` 完整 calibration 亦补回 tracked 披露：Claude 12/12 pipeline-failed、Codex 12/12
  unresolved operational、0 完成 pair、`$2.003669 [soft]`、`REJECTED / underpowered`；JSON/checkpoint
  SHA-256 为 `afce3136...959e6` / `c72675d0...38ca19`。该 source 后被修正取代，不计当前接受证据。
- 中断时已有 17 个 `A oracle failed` 终态和 1 个 durable start：Claude 8 个 checks-only、4 个
  allowlist/lesson mutation 失败，Codex 5 个 control mutation 失败。旧 journal 只存布尔，无法倒推 4 个
  越界路径；该类不得隐藏或从样本删除，若新 source 重现则用新增有界诊断继续修正。
- A pipeline correction 直接修正三处：A 失败持久化有界 check/mutation 诊断（无模型原文）；Git index 改按
  staged entries/flags 的语义 hash 比较，仍拒绝真实 staged mutation；A/B 同源注入已确认范围与不可用外部
  gate 的执行上下文。聚焦红态 `4 failed`，实现后 `4 passed`；相关 sequence/oracle/eval 为 `202 passed`。
- 首轮 review（Paseo `734e0b9a`，Opus 5）指出共享 context 对 seed attention 的摘要不实，且“流程产物
  照常落盘”可能放大上述 4 个 mutation 失败。sequence 现改用专用 context：要求读取真实 attention，
  不替代仓库事实、不为评测模拟 reviewer/gate 或新建无关流程产物；A/B 对称注入由同一测试锁定。
- 第二轮 review `bdec2b7c` 的唯一 important 指向非空/截断/control diagnostics 缺回归；现有 Git mutation
  用例改为 21 个越界路径 + local config mutation，逐值锁定 20 条上限、截断与 changed control key。
- 第三轮 review `a011c1a7` 的唯一 important 指向 `9fb5d0f` 完整负 calibration 漏披露；结果与双 hash 已
  补回 results/游标。三轮上限已到；末项是现存 artifact 的机械事实补录，无实现分歧，不再创建第 4 轮。
- pipeline 输入已重置为 `prepared-awaiting-commit` / probe pending / `real_llm_runs_started=false`；该字段只
  描述尚未运行的新 source。真实 probe、CLI 或 calibration 均须 owner 重新逐次授权，本流程不自动执行。
