# Task Agent 与 Goal Driver 约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/agent-conventions.md`。
需要独立 review、QA runner、acceptance auditor、功能验收或 goal driver 时读取。

## Task Agent 选择规则

`Task agent` 指为隔离 review、QA、audit、acceptance 或功能验收而启动的工作
agent。选择顺序：

1. Paseo subagent：首选；用户可见 agent id、状态、日志、权限和取消入口。
2. 当前宿主原生 Codex / Claude Task / Agent：只有宿主暴露可查看的 run id / 状态 /
   transcript 时使用。
3. 都不可用或未获授权：记录限制，按对应 gate 的 fallback / owner-stop 处理。

只给 Task agent 原始产物、审查范围和期望输出；不要泄露主 agent 的结论。主 agent 负责核验
返回 findings，并负责最终状态写入。

review gate（roadmap review、feature design review、implementation code review）在
Task agent 可用时必须启动。赶时间、批量处理、主 agent 已自查或认为风险低，都不是
local-only 降级理由。local-only 只在确无 Task agent 能力、provider 不可用且无法配置，
或 owner 明确批准降级时有效；否则报告 `blocked` / `independent-review-pending`，
不要写 `passed`。

## Task Agent 生命周期

主 agent 启动 Task agent 后记录 `agent_id` / `run_id`、用途和查看方式。Task agent 返回
final result 后，先消费并落盘结果，再调用宿主提供的 `close_agent` 或等价关闭动作。关闭失败
不改变已核验 verdict，但必须在报告里记录 warning、agent 标识和人工清理提示。

不要关闭 still-running、pending、permission-needed、结果尚未消费、或仍需用户查看权限请求的
Task agent。用户取消、owner-stop 或 handoff 时，按宿主取消 / 关闭语义处理，并在报告写明
哪些 agent 仍保留给用户接管。

不要预先批量清理旧 agent。只有 create / spawn 因 `agent thread limit reached`、capacity
exhausted 或等价容量错误失败时，才执行容量恢复：列出当前会话中已完成且结果已消费或不再需要的
旧 Task agent，按最老优先关闭一小批，再重试本次 create / spawn 一次。仍失败时才进入该
gate 的 `blocked` / owner-stop，并报告已关闭哪些 agent、仍保留哪些 agent 和重试结果。

## Goal Driver 派发

`Goal driver` 是一个可见 Task agent，用来执行已生成、已过用户 gate 的 goal 包。它不是
reviewer，不批准 design；它只按 goal 包协议执行 implementation / review / QA /
acceptance，并把证据写回仓库。

启动前置：

- goal 包已落盘，含 goal-plan、goal-state、goal-protocol 和可粘贴 `/goal` 指令。
- 用户已确认对应 design gate：单 feature 是 feature design；epic 是 roadmap 和全部子
  feature design。
- 当前工作区基线可追踪；goal-state 记录 baseline，协议写明 complete / handoff 标记。

选择顺序：

1. Paseo subagent：首选，用户能看见并接管长程执行。
2. 宿主原生 Task / Agent：只有同时满足两条才可用：
   - 宿主显式暴露用户可见的 run id、状态、日志、取消或最终 transcript。
   - 宿主显式支持 driver 在其运行环境内再启动独立 Task agent reviewer；review gate
     必须能跑，不能靠 driver 自审。
3. 任一条件不能确认、driver 不可见或派发失败：不要静默后台运行，直接回退打印 fenced
   `/goal`，让用户粘贴到新 agent 会话。

派发 prompt 必须使用 goal 包协议生成的同一条 literal `/goal` 指令作为 driver 初始任务。
不要改写成普通“执行/实现这个 feature”的自然语言任务；那会绕开 goal 模式接管语义，导致
driver 在 implementation / review / QA / acceptance 普通 checkpoint 被截停。除 `/goal`
指令本身外，只能附加查看方式、agent id 写回要求和 complete / handoff 标记说明。

派发成功后立即把 driver 形态与标识写回对应 `goal-state.yaml`（`driver_kind:
paseo|native`、`driver_id`）。重入时先读 goal-state：状态为 running 且该 driver 仍可见时，
汇报进度和查看方式，不重复派发；driver 已不可见时，以仓库事实修正 state，再续跑或重派。
driver 完成或 handoff 且结果已被主流程消费后，按 Task Agent 生命周期关闭。

## Task Agent 实现选择

review 在 Task agent 可用时必须使用。implementation Task agent 是可选项；当工作跨越三个以上
子系统、需要并行切片、触及高风险 migration / concurrency / runtime contract，或超过单线程
上下文容量时，应主动提出。主线程保留集成、验证和最终 review 责任。
