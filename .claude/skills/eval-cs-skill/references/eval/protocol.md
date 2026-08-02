# eval stage 协议

对某个 cs skill 跑「fixtures × models × harnesses」评测，产出带 tag 的 measured 分数与证据。评测执行引擎在 `scripts/`，被测 SKILL.md 以快照文本注入 prompt（隔离宿主已装版本）。

## 评测效度（validity）：三条铁律（campaign 血泪教训）

要测的是「skill 在其**设计环境**下的真实能力」，不是「skill 在残缺环境下的反应」。一轮真实模型 campaign 里，每个看似的「模型/skill gap」核查后都是**评测缺陷**：

1. **复现被测 skill 的实际 context contract**：fixture 提供任务/diff，并按声明补可选 attention、相关 lessons、项目文档或 ADR；不注入集中式 runtime。缺失必要输入会让模型正确拒绝，形成假 gap（历史 cs-code-review campaign：haiku bare 0.31 → 补上下文 0.92）。
2. **散文 answer 用语义 oracle**：token 重叠对「`>=` 改成 `>`」「删掉早返回守卫」这类符号/散文 answer 会误判漏检（cs-refactor 两模型满分被打成 0.62/0.75）。用 `recall_judge`（judge 语义判定）+ `planted_defect`（机械兜底）。
3. **fixture 必须内嵌 subject matter**：转换/文档型任务需要被操作的对象。v1 `cs-docs` 历史 campaign 中，给「写配置文档」却不给配置时模型会正确要材料而非捏造（sonnet 0.75）。review 需要 diff，文档任务需要 code/config/API，design/plan 可只从需求推导。

核查纪律：**分模型看**（合计数掩盖 haiku↔sonnet 差异）、**手工读原始输出**（token 数字会骗人）、**k=1 有 variance**（同一 fixture 会抖，发布级结论 k≥5）。

## 何时进入

- 已有 `experiments/{skill}-{NNN}/fixtures/`，但缺 `artifacts/analysis/*-results.json`。
- optimize 生成新变体后需要复测。
- release 前跑回归 baseline。

## 1. 声明实验

`experiments/{skill}-{NNN}/config.json`：

```json
{
  "name": "cs-code-review-001",
  "skill_under_test": "cs-code-review",
  "variants": ["baseline"],
  "model_list": ["claude-opus-4-8", "claude-sonnet-4-6"],
  "k": 5,
  "harnesses": ["claude-headless"],
  "scorers": ["planted_defect", "recall_judge"],
  "fixture_classes": ["planted-defect", "golden"],
  "budget_usd": 50.0,
  "judge_model": "claude-sonnet-4-6"
}
```

- `variants`：`baseline`=当前仓库被测 skill 的 SKILL.md；其余=optimize 产出的 `experiments/{name}/variants/<v>.md`。
- `inject_context`（**效度关键，默认 true**）：按被测 skill 的真实 context contract 补任务、diff、可选 attention、相关 lessons 与项目文档，不假设统一 onboard runtime。设 `false` 只用于专门测「bare-input/ad-hoc 健壮性」。
- `model_list` ≥2（跨模型一致性，BAIME 硬约束）。`judge_model` 须独立于被测 model。

## 2. 作 fixtures

`fixtures/<class>/<id>.json`，字段 `id / answerType / answer / task`：

- `answerType: findings-recall`：`answer` 是应被发现/覆盖的要点列表。**散文/符号 answer 必须配 `recall_judge`**（语义判定）；`planted_defect`（token）只对关键词型可靠、对 prose 会低估。
- `answerType: dod-gate`：给 `checklist_path`，scorer=`dod_gate` 跑 checklist 命令判 pass/fail。
- `answerType: dimensions-judge`：scorer=`llm_judge` 按 8 维 rubric 两轴打分。
- `task`：`{kind: review|fix|audit|design|docs, diff, spec}`；`kind` 决定 buildprompt 分派。**铁律 3**：转换/文档型 skill 的 `task` 必须内嵌被操作对象——review/fix/audit/docs 把代码/配置/API 放进 `diff`，design/plan 可只给 `spec` 需求。否则模型没东西可做，会（正确地）要材料 → 假 gap。

每类 `n ≥ 8` 才有统计功效；否则结论标 `[underpowered]`。planted-defect 应含**关键词可检**与**需推理**两种缺陷，避免只测到关键词匹配。

## 3. 预注册与冻结

写 `hypotheses.md`（`H-<id>: metric ≥ threshold`），**先 git commit 再跑任何 LLM**——provenance 由
`.claude/skills/eval-cs-skill/tests/test_cs_skill_convergence.py` 校验。

`learning-transfer` 还要生成 `freeze.json`，冻结 config、fixtures、A/hidden/regression checks、hook、
seed builder、owning skill 快照、完整 pipeline 与显式 execution targets。先提交这些输入，再对每个
target 做不保留输出的最小真实探针；通过后把该输入 commit 写为 `source_commit`，将 manifest 置为
`frozen` 并单独提交逐 target 布尔 attestation。探针必须确认宿主配置与已知会话状态不变；attestation
只接受注册字段，不记录 prompt、回答、路径、sentinel 或 session id。真实
sequence 会同时核对当前字节、source commit blob 与 HEAD 中的
manifest，prepared/pending 状态不能调用模型。checkpoint header 以这些
输入、`k` 和 run identity 计算 fingerprint；失配直接拒绝恢复。`k=2` 校准和 `k>=5` 最终运行必须
使用不同 run identity，不能合并 checkpoint 或结果；校准必须保留完整 fixtures 和 model families，
只按比例缩小 `k`。

## 4. 跑评测

```bash
# 先估成本（多模型必做）
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN} --dry-run
# 正式跑（超预算需 --confirm）
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN}
# 快速探路：单 harness/model、低 k
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN} --harness mock --k 1
```

分层省钱：确定性 scorer（planted_defect / dod_gate）先跑，`llm_judge` 只在候选变体上跑；cheap model 探路，贵 model 只做终判。

### learning-transfer sequence

项目 lesson 的跨会话迁移使用 `answerType/task.kind: learning-transfer`。每个 pair 从同一 post-A repo
重建 treatment/control，只在 treatment 注入 fresh `cs-keep` 生成且严格校验的 observed lesson；
可选 hook 对两侧对称执行。A、curation、B 两侧都是 fresh invocation，B prompt hash 必须相同。

模型调用前必须通过 fixture schema、seed Epic 授权状态、golden/naive 可解性、资产 containment、repo
symlink、外部 sandbox 与 target 探针；探针必须验证当前 cell 可写、宿主与 sibling cell 不可读、宿主
不可写。A/B 变化同时检查业务 manifest 和 Git HEAD/index/config/hooks；deterministic subprocess 使用
最小环境、有界超时，只保留状态与输出哈希。候选按 A 前后 delta 提取，lesson parser 要拒绝额外字段、
重复字段、非法日期/slug/归宿和超过三条 evidence；窄迁移只允许 status 与一条代表性 evidence 变化。

完整 campaign 至少覆盖四个 task skills、unrelated 与 stale guard、两个 model family、每 fixture 每
family `k>=5`。25pp 作用于两个 family 与四个正向 fixture 的总体 paired delta，且每个 family 必须
为正、losses 不多于 wins、两 guard 无回退、所有隔离/schema/mutation oracle 100% 通过。
Deterministic failure 永久阻断 structural integrity；retryable adapter/transport error 保留尝试与成本，
只有后续同 cell 形成完整 pair 才单列为 resolved，未解决时保持 incomplete / `[underpowered]`。
provider 前须以新 invocation ID durable append start 与 soft fallback，terminal metrics 只追加不覆盖；
中断或半写 terminal 仍保留一次尝试与 fallback 成本。`--fresh` 只允许 header-only journal；任何
invocation、score、error、fixture-invalid 或已有结果都要求新的 `--out`。半 pair 不进入效果均值；
cell repo 在 oracle 后销毁。

## 5. 读结果

`artifacts/analysis/exp-{name}-results.json`：

- `aggregate.<variant>.scores.<name>`：`{value, tag, evidence}`，tag=`measured` 表示 oracle 可验。
- `aggregate.<variant>.metrics`：`wall_ms/turns`=`[measured]`，`*_tokens/cost_usd` 视 harness 是否回传 usage 定 `measured`/`soft`。
- `runs[]`：逐 cell 的 `scores/evidence/status`，`evidence` 含 `matched/missed`。

把人读摘要写 `results.md`，给出 `evidence_pointer` 指向该 json。

## 退出条件

- [ ] config.json、fixtures、hypotheses.md 落盘且 hypotheses 已 git commit。
- [ ] `--dry-run` 成本在预算内（或已 `--confirm`）。
- [ ] `artifacts/analysis/*-results.json` 产出，分数带 tag。
- [ ] `results.md` 有摘要与 evidence_pointer。
- [ ] 跨模型跑了 ≥2 model，或明确标注为 `[underpowered]` 探路。
