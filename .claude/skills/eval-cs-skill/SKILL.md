---
name: eval-cs-skill
description: CodeStable skill 工程化闭环入口。触发：写/改一个 cs skill、评测 skill 效果、跨 model/agent 量化、优化 skill 提示词、把收敛结论固化回 skill。内部推进 author、eval、optimize、release。
argument-hint: "[--stage author|eval|optimize|release] [--experiment <dir>] <skill-or-request>"
---

# eval-cs-skill

## 启动必读

动作前读取仓库 agent 规则；存在 `.codestable/attention.md` 时再读项目事实。评测 context 以
被测 skill 的实际声明为准，不要求集中式 onboard runtime 或共享 reference。

`eval-cs-skill` 是「造 skill 的 skill」：把 CodeStable 各 skill 的 **编写 → 评测 → 优化 → 再评测** 做成一条可复现、跨 model/agent 的迭代闭环。它编排的对象是 **skill 自身的生命周期**，不是业务代码 feature。它**自指**——同一套 harness 也能评测并优化 `eval-cs-skill` 自己。

评测执行引擎（runner / scorers / harness 适配器）由本 skill 自带于 `scripts/`；实验纪律、双层价值函数、收敛判据、知识回写复用 BAIME 引擎（`run-quantitative-experiment`、`methodology-bootstrapping`、`knowledge-extractor`）——以**文本判据**内联，运行时不跨插件读 BAIME 文件。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源优先级：调用参数 flag > 用户话术。参数为空或仍是字面 `$ARGUMENTS` 时跳过该来源。`--stage` 表示阶段意图，`--experiment <dir>` 指定实验目录，其余文本作为被测 skill 名或诉求。

| 参数 | 入口意图 |
|---|---|
| `--stage author` | 编写/重构一个 cs skill（提示词工程 + 包结构） |
| `--stage eval` | 对某 skill 跑 fixtures×models×harnesses 评测，产出 measured 分数 |
| `--stage optimize` | autoresearch：hypothesis→变体→评测→留/杀→收敛 |
| `--stage release` | 收敛结论固化回 SKILL.md + 打版本 + 回归电池 |

无参数默认：不猜阶段；扫描 `experiments/` 与被测 skill 现状，用状态机恢复下一步；仍不确定就问用户要处理哪个 skill、想到哪一步。

入口意图只是偏好，仓库事实优先。

---

## 闭环是什么（速读）

```text
regression fixtures ────┐
planted-defect fixtures ┼─▶ runner.py（多 harness/model 执行被测 skill，隔离宿主）
golden 任务 ────────────┘        │
                                 ▼
        scorers：确定性(planted_defect 召回 / dod_gate) + llm_judge 两轴(照做没/质量)
                                 │ 指标 token/$/wall/turns（带 [measured]/[soft] tag）
                                 ▼
     optimize.py：预注册 hypothesis → 生成变体 → 评测 → keep/kill → 收敛(V_instance∧V_meta)
                                 │ 持久 experiments/<skill>-NNN/iteration-N.md
                                 ▼
     release：knowledge-extractor 草稿 → 适配成 CS 合规结构 → 打版本 → 回归 N 次电池
```

---

## 文件放哪儿

```text
experiments/{skill}-{NNN}/
├── hypotheses.md          # 预注册，冻结后先 git commit 再跑任何 LLM（provenance）
├── config.json            # ExperimentConfig 声明
├── fixtures/{planted-defect,golden,sanity,regression}/*.json
├── calibration.md         # judge 校准 F1（oracle 校准证据）
├── iteration-0..N.md      # 每轮观测，[measured]/[soft] 标注
├── results.md             # 人读摘要 + evidence_pointer + 收敛模式
└── artifacts/
    ├── runs/              # gitignored 原始响应
    └── analysis/{exp-NNN-results.json,baseline.json}
```

被测 skill 与本 skill 的执行代码在包内 `scripts/`；被测 SKILL.md 以**快照文本**注入 prompt（不读宿主已装版本，避免测成旧版）。

---

## Stage 状态机

按仓库事实恢复：

| 仓库事实 | 下一步 |
|---|---|
| 无 `experiments/{skill}-NNN/` 或要新写 skill | author：读 `references/author/protocol.md` |
| 有 fixtures 但无 `artifacts/analysis/*-results.json` | eval：读 `references/eval/protocol.md` |
| 有 baseline 结果，要提升分数 | optimize：读 `references/optimize/protocol.md` |
| optimize 已收敛（V_instance∧V_meta 达标） | release：读 `references/release/protocol.md` |
| release 落盘后 | 汇报版本、回归结论与后续候选 skill |

用户说「下一步」时，按仓库事实而非聊天历史判断。

---

## Reference 加载（渐进）

只在进入对应阶段时加载厚规则：

- author：`references/author/protocol.md`（skill 编写契约：frontmatter、渐进披露、model/harness 无关措辞、包结构、≤300 行）
- eval：`references/eval/protocol.md`
- optimize：`references/optimize/protocol.md`，模板见 `references/optimize/support/`
- release：`references/release/protocol.md`
- 自治：`references/autonomy/protocol.md`

不要一次读完；按阶段加载。

---

## 工具入口（从本 skill 包运行）

```bash
# 评测（--dry-run 先估成本；超预算需 --confirm）
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN} [--harness H --model M --k N] [--dry-run]
# 优化收敛循环
python3 {skill_dir}/scripts/optimize.py --experiment experiments/{skill}-{NNN} --max-iterations N
# 固化回写 + 打版本 + 回归
python3 {skill_dir}/scripts/adapt_extracted_skill.py --draft .claude/skills/{name} --target {skill}
python3 {skill_dir}/scripts/regression.py --experiment experiments/{skill}-{NNN} --n 5
python3 {skill_dir}/scripts/bump_version.py --to X.Y.Z
```

`{skill_dir}` = 本 SKILL.md 所在目录。工具随 skill 包分发，不复制到 `.codestable/tools/`。

### 项目内学习迁移实验

`execution_mode: learning-transfer` 是维护者侧实验，不在用户任务中构造样本或运行模型。它用独立
`sequence.py` 执行 A -> fresh `cs-keep` -> treatment/control fresh B；每次 invocation 只注入 owning
skill 的冻结快照，B 两侧 prompt 相同，唯一处理变量必须是经 schema 校验的项目 lesson。

真实运行前必须同时满足：实验输入与 hypothesis 已提交；checkpoint fingerprint 绑定 config、fixture、
skill 快照、seed、完整 pipeline、target、`k` 与 run identity；golden/naive preflight 成立；显式
`family/harness/model` target 至少覆盖两个 model family；每个 target 的外部 sandbox 已通过宿主与
sibling cell 读取、宿主写入隔离探针，且宿主配置与已知会话状态快照保持不变。
输入 commit 后先做最小真实 target 探针，再提交含 `source_commit` 和逐 target 布尔 oracle 的 frozen
attestation；attestation 只接受注册字段，不得记录 prompt、输出、路径、sentinel 或 session id。
prepared manifest 不能运行真实 sequence。
失配的 checkpoint 拒绝恢复；校准保留完整 fixtures/model families，只缩小
`k`，并与最终运行使用不同 run identity；`learning_transfer` scorer 不可替换。

Deterministic pipeline / fixture / oracle 失败永久阻断 structural integrity；adapter / transport 故障
单列为 operational error。成功重试保留尝试与成本但不永久污染 integrity，未解决时保持
`[underpowered]`；只有完整 pair 才能把历史 operational error 标为 resolved。

每次 provider 调用前，append-only checkpoint 必须用新的 invocation ID 先 `flush + fsync` start 与
`[soft]` fallback，再追加同 ID terminal metrics；中断时 reducer 保留 fallback、成本和 unresolved
attempt。`--fresh` 只允许删除 header-only journal，其他运行证据与已有结果都必须换新 `--out`。每个
cell repo 在 oracle 后销毁；checkpoint 只保留结构化 phase、指标与哈希，不保留原始子进程输出，
也不得持久化 transcript、完整 treatment/control repo，或自动导出、上传、改写 skill。

---

## 认知诚实纪律（硬约束）

- 一切数值必带 tag：`[measured]`（oracle/机械可验）/ `[soft]`（自评估算）/ `[underpowered]`（k<5 或 n<8）。
- `hypotheses.md` 冻结后**先 git commit 再跑任何 LLM**；provenance 由 `tests/test_cs_skill_convergence.py` 机械校验。
- 禁止裸 `V_instance = 0.XX` 自评分；收敛判据见 optimize 协议。
- 跨模型 ≥2；judge 模型须独立于被测模型（避免同源偏差）。
- learning-transfer 校准可用 `k=2`，但接受证据要求每 fixture、每 family `k>=5`；任一 primary
  aggregate 为 `[underpowered]` 时扩大样本后重跑，不得把校准结果混入最终结论。

---

## 成本护栏

多模型运行前用 `--dry-run` 估算 token×pricing；单实验默认预算上限 **$50**，超限阻断需 `--confirm`。分层省钱：确定性 scorer 先跑、llm_judge 只评候选变体、cheap model 探路 + 贵 model 只做终判。

---

## 退出条件

- 当前 stage 产物已落盘，状态可由 `experiments/` 事实恢复。
- eval 产出带 tag 的 measured 分数与 evidence_pointer。
- optimize 产出 iteration-N 与收敛判定；release 产出合规回写 + 版本同步 + 回归结论。
- 需要外部文档时直接更新对应项目文档；需要沉淀坑/决策时提示 `cs-keep`。

---

## 相关入口

- `cs-code-review` / `cs-issue` / `cs-feat`：常见活动被测 skill。
- `cs-onboard`：最小项目记忆骨架；不提供评测 runtime。

`scripts/promote_feedback_fixture.py` 仅用于显式导入冻结的 v1 `cs-feedback` candidate，不是
v2 production feedback 入口；新反馈如何进入 regression 不在当前协议中定义。
