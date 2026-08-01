# cs-learning-transfer-001 预注册假设

## 实验问题

任务 A 产生的项目 lesson，在不传递聊天上下文、不向任务 B 泄露候选内容时，是否能提高 fresh agent
完成同项目 sibling 任务的正确率，同时避免无关应用，并在 canonical 事实变化后及时退役？

## 冻结总体

- 实验单位：同一 `target × fixture × k_index` 下，共享 post-A 基线的 treatment/control pair。
- 正向样本：`cs-feat`、`cs-issue`、`cs-refactor`、`cs-epic` 各一个。
- Guard：一个 unrelated、一个 stale；每个 model family、每个 fixture 均运行 `k=5`。
- 模型族：Claude 与 Codex，各绑定一个显式 harness/model target，不做笛卡尔积。
- treatment 唯一额外输入是经 fresh `cs-keep` 写入的 observed lesson；B prompt hash 必须相同。
- 校准允许 `k=2`，但校准结果不得作为 Epic 接受证据。

## H-LT-1：项目 lesson 产生正向迁移

Primary metric 是四个正向 fixture 全部完成 pair 的 hidden pass rate 差值：

```text
overall paired delta = mean(treatment_hidden - control_hidden)
```

H-LT-1 仅在以下条件同时成立时确认：

- overall paired delta `>= 0.25`；25pp 门槛只作用于跨两个 family 的总体正向聚合；
- Claude 与 Codex 两个 family 的各自 paired delta 都 `> 0`；
- paired losses 不多于 wins；
- 每个 family 有四个 owning skill × `k=5`，即至少 20 个完成正向 pair；
- 所有结构、隔离、schema、mutation、prompt equality 与 regression oracle 100% 通过。

## H-LT-2：无关 lesson 不制造回退

Unrelated fixture 中 treatment hidden pass rate 不低于 control，双方 regression 全绿，observed lesson
保持字节不变且不产生状态 churn。该 guard 不参与 H-LT-1 的 25pp 聚合。

## H-LT-3：失效 lesson 会被 read-repair

Stale fixture 中对 treatment/control 同时施加 `opaque-v2` canonical reference policy hook。hook 先把
A 侧 `find_job` 与公开测试迁移为精确匹配，保留尚未迁移的 sibling `find_route` 作为 B 任务；大小写、
外围空白与 `_` / `-` 都不再等价。双方 hidden 与 regression 不回退，treatment 的旧 lesson 必须
`observed -> retired`，退役率必须为 100%。

## 机械 oracle 与失败判据

- A checks、候选唯一性、lesson schema、lesson-only curation、post-A 同源、B prompt equality、B mutation
  allowlist、hidden/regression、lesson transition 与 stale retirement 均标 `[measured]`。
- 任何 fixture preflight 未满足 golden hidden/regression 全绿、naive hidden 红且 regression 绿，fixture
  直接 invalid；不得进入模型运行，也不得从结果集中删除来改善指标。
- Deterministic pipeline / fixture / oracle 失败是当前冻结输入下的终态，永久阻断 structural
  integrity，不得重试或从结果中删除。
- Adapter / transport 故障记为 operational error：所有尝试与实际成本保留；后续同 cell 成功时标
  resolved 并与 structural integrity 分列，不永久污染 acceptance；未解决时该 cell 不完整，整体
  `[underpowered]`。每次调用前以新 invocation ID durable append start 与 `[soft]` fallback，terminal
  metrics 只追加；中断或半写 terminal 仍计一次 unresolved attempt 与 fallback 成本。只有完整 pair 才
  resolved；`--fresh` 仅允许 header-only journal，任何运行证据或已有结果都必须换新 `--out`。
- 任一 family/skill/guard 少于五个完成 repeat，存在未解决 operational error，或任一 primary aggregate
  仍不足，verdict 为 `[underpowered]`，不得接受 Epic。
- 语义质量只作 `[soft]` 观察，不得覆盖机械 verdict。

## 成本与冻结纪律

- `budget_usd = 50`；dry-run 必须累加 A、curation、B treatment、B control 与两侧 hook 实际次数。
- `config.json`、本文件、fixtures、checks、hidden/regression、preflight 与 hook 的 SHA-256 记录在
  `freeze.json`；先提交冻结版本，再运行任何真实 LLM。
- model/harness 探针若证明 target 不可用，允许在首个真实 LLM 前修改配置，但必须重新生成
  `freeze.json` 并提交；首个结果产生后不得按观测改 hypothesis、metric、预算或失败判据。
