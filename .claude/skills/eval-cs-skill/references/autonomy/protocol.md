# 自治协议（过夜自跑实验）

两条路径，默认 A。皆遵守认知诚实与成本护栏。

## 路径 A：轻量 cron（默认，跨 harness、零重依赖）

`runner.py` / `optimize.py` 是幂等命令；用队列 + 宿主 cron/CI 驱动，不引入 Node/backlog/独立 checkout 隔离（符合 ADR-002）。

```bash
# 入队若干实验
python3 {skill_dir}/scripts/enqueue_experiment.py --experiment experiments/cs-code-review-001 --stage optimize
python3 {skill_dir}/scripts/enqueue_experiment.py --experiment experiments/cs-code-review-001 --stage eval
# 宿主 cron 反复调用 run-next（每次跑一个 queued 项，幂等）
python3 {skill_dir}/scripts/enqueue_experiment.py --run-next
```

宿主 cron 示例（每 30 分钟跑一个队列项，避开整点）：`7,37 * * * * cd <repo> && python3 <skill_dir>/scripts/enqueue_experiment.py --run-next`。

成本：每个 eval 已受 `--dry-run` + `budget_usd` 护栏约束；过夜批量前先对每个实验 `--dry-run` 估总额。

## 路径 B：BAIME loop-backlog（可选宿主，仅 Claude Code）

功能全（事件驱动 worker、并行隔离 checkout、自动 merge），但绑 Node daemon + backlog CLI + 独立 checkout 隔离，跨不了 harness，且与 ADR-002「cs 不拥有 checkout/分支策略」有张力——故为**可选宿主**，不内建。

启用方式（用户自行决定）：
1. `backlog` 项目就绪（见 BAIME `backlog-setup`）。
2. 把每个实验封成 `kind:basic` 任务，DoD = `runner.py`/`optimize.py` 命令。
3. 用户自己 `/loop-backlog` 消费；eval-cs-skill 不 own daemon/checkout/merge。

## 自指（eval-cs-skill 评自己）

`experiments/eval-cs-skill-001/` 用**同一** runner/scorer 指向 `eval-cs-skill/SKILL.md` 自身（把它当被测文本注入，不调用其工具→无递归）。收敛用 meta-focused（V_meta≥0.80 且 V_instance≥0.55）。这让「造 skill 的 skill」也进入同一评测闭环，可被优化——包括优化它自己。

## 边界

- 自治只跑已冻结（hypotheses 已 commit）的实验；未冻结的不入队。
- 任何 harness 调用仍用独立 tmp workdir 隔离宿主；不读宿主已装 skill。
- 队列文件 `experiments/.queue.jsonl` 是运行时状态，不入库。
