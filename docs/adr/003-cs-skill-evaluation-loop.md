---
adr: "003"
title: "eval-cs-skill：skill 评测与自研迭代闭环，复用 BAIME 引擎"
status: Accepted
date: 2026-07-06
applies-to:
  - ".claude/skills/eval-cs-skill/"
  - "experiments/"
  - ".claude/skills/eval-cs-skill/scripts/promote_feedback_fixture.py"
enforcement: test
stage: [author, eval, optimize, release]
lint: "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --strict-markers -q .claude/skills/eval-cs-skill/tests -rs"
---

# ADR-003: eval-cs-skill 评测与自研迭代闭环

## Context

CodeStable 原有 `tests/test_skill_*` 只验证 skill **写得对不对**（路由表、reference 路径、兼容入口），没有任何东西验证 skill **跑得好不好**。要让这套 skills 在不同 agent/model 下持续改进，需要一条「编写→评测→优化→再评测」的闭环，且能自治、自举、自指。

参考 Superpowers 6：evals 套件是一切基础，autoresearch loop 用预注册 hypothesis + 硬 verdict + 认知诚实纪律驱动改进。本环境已有 BAIME 方法论插件（run-quantitative-experiment / methodology-bootstrapping / knowledge-extractor / loop-backlog），提供实验纪律、双层价值函数、收敛判据、知识回写与自治 worker——但**不发货执行 runner**（消费方自带）。

## Decision

新增 skill `eval-cs-skill`（stage：author/eval/optimize/release）。它是**项目级开发 skill**——「开发 cs skill 的 skill」，是维护者工具，**放 repo 根 `.claude/skills/eval-cs-skill/`，不随 `codestable` 插件交付给用户**，因此也不出现在 `cs` 路由表与 `SKILL_CATALOG`。并：

1. **CS 自研执行引擎**：`scripts/runner.py` + harness 适配器注册表（claude-headless/codex-cli/paseo/api + 离线 mock/mock-weak）+ scorers（planted_defect/dod_gate/llm_judge）+ metrics。被测 SKILL.md 以**快照文本**经 `buildPrompt` 注入，绕开「skill 无法无头执行」，并隔离宿主已装版本（Superpowers 教训）。
2. **复用 BAIME 的判据与编排**（以文本内联，运行时不跨插件读）：双层价值函数 V_instance∧V_meta≥0.80、四机械分量 V_meta、三收敛模式；`optimize.py` 自实现 OCA（因 `iteration-executor` agent 调不到本地 runner）。
3. **认知诚实为硬约束**：一切数值带 `[measured]/[soft]/[underpowered]`；hypotheses 冻结须先 git commit（provenance）；`.claude/skills/eval-cs-skill/tests/test_cs_skill_convergence.py` 机械校验。
4. **experiments/ 布局**：hypotheses/fixtures/config/analysis/iteration 入库，`artifacts/runs/` 与 `.queue.jsonl` gitignore。
5. **release 两步走**：`knowledge-extractor` 产草稿 → `adapt_extracted_skill.py` 翻译成 CS 合规结构（禁止 extractor 直写 plugins/），再 `regression.py` + `bump_version.py`。
6. **自治默认轻量 cron**（`enqueue_experiment.py`），BAIME `loop-backlog` 为可选宿主。
7. **自指**：`experiments/eval-cs-skill-001/` 用同一 runner/scorer 评 `eval-cs-skill` 自身。
8. **v2 输入边界**：评测 fixture 是 repo-local 维护者资产，不依赖任何 shipped runtime
   skill。`promote_feedback_fixture.py` 只保留为 v1 `cs-feedback` candidate 的 legacy-only
   导入器，不构成 v2 production feedback 入口。
9. **项目 lesson 的 paired sequence**：`answerType/task.kind: learning-transfer` 由独立
   `sequence.py` / `learning_transfer` scorer 承载 A -> fresh `cs-keep` -> treatment/control fresh B。
   它只用于维护者验证项目内跨会话迁移，不在用户使用 CodeStable 时构造实验。post-A 同源、B prompt
   equality、严格 lesson schema/窄迁移、Git 与文件 mutation、hidden/regression、stale retirement
   都是机械 oracle。Deterministic failure 永久阻断 structural integrity；adapter/transport error 单列
   operational history，成功重试仍计成本但不永久污染 integrity，未解决则保持 underpowered。调用前
   durable append start 与 soft fallback，terminal 只追加；仅完整 pair 能把历史 operational error 标为
   resolved，`--fresh` 只允许 header-only journal，其他 campaign 必须使用新的输出身份。
10. **冻结与隔离是接受前提**：真实调用前提交 hypothesis 与完整 campaign 输入，checkpoint fingerprint
    绑定 config、fixtures、skill snapshots、runner/scorer、seed、target、`k` 与 run identity，校准不得
    混入最终结果。每个 harness 必须通过宿主与 sibling cell 读取、宿主写入隔离探针；deterministic
    子进程只获最小环境且不保留原始输出。cell repo 在 oracle 后销毁，只保留结构化指标和哈希，不保留
    transcript 或完整 treatment/control 仓库。

## Consequences

- skill 效果可跨 model/harness 量化，改进有硬 verdict 而非直觉。
- 新 skill 接入只需加 `experiments/` 数据（自举）；加 harness 只需加一个 adapter。
- 冻结的 v1 feedback candidate 仍可显式导入历史 experiment；v2 不承诺 production feedback promotion。
- eval-cs-skill 自身可被同一闭环评测优化（自指）。
- 真实多模型运行需 API/CLI 鉴权并产生成本，受 `--dry-run` + `budget_usd` 护栏约束。
- paired learning-transfer 的结论要求至少两个 model family、每 fixture 每 family `k>=5`；校准可用
  `k=2` 但只能标探路证据，任何 primary aggregate 仍为 `[underpowered]` 时不得接受。
- **评测效度是头等风险**（首轮真实 campaign 教训）：必须复现被测 skill 实际声明的 context contract，而不是注入统一 onboard runtime；同时用语义 oracle（`recall_judge`）判散文 answer，并让 fixture 内嵌被操作的 subject matter。否则测到的是「skill 在残缺环境下的反应」而非真实能力。核查须分模型看 + 手工读原始输出 + 认 k=1 variance。细则见 `references/eval/protocol.md` 效度三铁律。

## Rejected alternatives

- **从另一个 shipped skill import runtime**。拒绝：违反 skill 独立性；确定性检查必须自包含或通过明确 CLI 边界调用。
- **BAIME loop-backlog 作默认自治**。拒绝：绑 Node/backlog/独立 checkout，跨不了 harness，且与 ADR-002 有张力；改为可选宿主。
- **knowledge-extractor 直接写 plugins/**。拒绝：单数 `reference/`、`inventory/`、`README.md`、超 300 行会被 check-plugin-package fail；必经适配层翻译。
- **只扩展现有结构测试**。拒绝：结构测试测不了运行效果；eval 是独立新层。
