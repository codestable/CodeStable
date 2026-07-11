---
adr: "003"
title: "eval-cs-skill：skill 评测与自研迭代闭环，复用 BAIME 引擎"
status: Accepted
date: 2026-07-06
applies-to:
  - ".claude/skills/eval-cs-skill/"
  - "experiments/"
  - "plugins/codestable/skills/cs-feedback/scripts/feedback_to_fixture.py"
  - ".claude/skills/eval-cs-skill/scripts/promote_feedback_fixture.py"
enforcement: test
stage: [author, eval, optimize, release]
lint: "python3 -m pytest tests/test_cs_skill_eval.py tests/test_cs_skill_convergence.py tests/test_cs_skill_release.py tests/test_cs_skill_bootstrap.py tests/test_cs_skill_selfref.py"
---

# ADR-003: eval-cs-skill 评测与自研迭代闭环

## Context

CodeStable 原有 `tests/test_skill_*` 只验证 skill **写得对不对**（路由表、reference 路径、兼容入口），没有任何东西验证 skill **跑得好不好**。要让这套 skills 在不同 agent/model 下持续改进，需要一条「编写→评测→优化→再评测」的闭环，且能自治、自举、自指。

参考 Superpowers 6：evals 套件是一切基础，autoresearch loop 用预注册 hypothesis + 硬 verdict + 认知诚实纪律驱动改进。本环境已有 BAIME 方法论插件（run-quantitative-experiment / methodology-bootstrapping / knowledge-extractor / loop-backlog），提供实验纪律、双层价值函数、收敛判据、知识回写与自治 worker——但**不发货执行 runner**（消费方自带）。

## Decision

新增 skill `eval-cs-skill`（stage：author/eval/optimize/release）。它是**项目级开发 skill**——「开发 cs skill 的 skill」，是维护者工具，**放 repo 根 `.claude/skills/eval-cs-skill/`，不随 `codestable` 插件交付给用户**，因此也不出现在 `cs` 路由表与 `SKILL_CATALOG`。并：

1. **CS 自研执行引擎**：`scripts/runner.py` + harness 适配器注册表（claude-headless/codex-cli/paseo/api + 离线 mock/mock-weak）+ scorers（planted_defect/dod_gate/llm_judge）+ metrics。被测 SKILL.md 以**快照文本**经 `buildPrompt` 注入，绕开「skill 无法无头执行」，并隔离宿主已装版本（Superpowers 教训）。
2. **复用 BAIME 的判据与编排**（以文本内联，运行时不跨插件读）：双层价值函数 V_instance∧V_meta≥0.80、四机械分量 V_meta、三收敛模式；`optimize.py` 自实现 OCA（因 `iteration-executor` agent 调不到本地 runner）。
3. **认知诚实为硬约束**：一切数值带 `[measured]/[soft]/[underpowered]`；hypotheses 冻结须先 git commit（provenance）；`tests/test_cs_skill_convergence.py` 机械校验。
4. **experiments/ 布局**：hypotheses/fixtures/config/analysis/iteration 入库，`artifacts/runs/` 与 `.queue.jsonl` gitignore。
5. **release 两步走**：`knowledge-extractor` 产草稿 → `adapt_extracted_skill.py` 翻译成 CS 合规结构（禁止 extractor 直写 plugins/），再 `regression.py` + `bump_version.py`。
6. **自治默认轻量 cron**（`enqueue_experiment.py`），BAIME `loop-backlog` 为可选宿主。
7. **自指**：`experiments/eval-cs-skill-001/` 用同一 runner/scorer 评 `eval-cs-skill` 自身。
8. **反馈交接边界**：shipped `cs-feedback` 只把 local-private `triage.json` 转成同目录 candidate；正式 fixture 由 repo-local promotion 工具读取 experiment config，校验 profile/input/privacy/scorer/harness/judge 后 fail-closed 落盘。两单元只通过 JSON artifact 连接，运行时互不 import。

## Consequences

- skill 效果可跨 model/harness 量化，改进有硬 verdict 而非直觉。
- 新 skill 接入只需加 `experiments/` 数据（自举）；加 harness 只需加一个 adapter。
- 生产失败先经 `cs-feedback/feedback_to_fixture.py` 形成未入库 candidate；只有 readiness、隐私与目标 experiment gates 全过，repo-local promotion 才写 regression fixture。
- eval-cs-skill 自身可被同一闭环评测优化（自指）。
- 真实多模型运行需 API/CLI 鉴权并产生成本，受 `--dry-run` + `budget_usd` 护栏约束。
- **评测效度是头等风险**（首轮真实 campaign 教训）：必须复现 skill 的设计运行环境（`inject_context` 补 onboard 上下文）、用语义 oracle（`recall_judge`）判散文 answer、fixture 内嵌被操作的 subject matter；否则测到的是「skill 在残缺环境下的反应」而非真实能力。核查须分模型看 + 手工读原始输出 + 认 k=1 variance。细则见 `references/eval/protocol.md` 效度三铁律。

## Rejected alternatives

- **import cs-onboard/tools 到 eval-cs-skill**。拒绝：违反 skill 独立性（CLAUDE.md）；dod_gate 改为自包含 + CLI 边界。
- **BAIME loop-backlog 作默认自治**。拒绝：绑 Node/backlog/独立 checkout，跨不了 harness，且与 ADR-002 有张力；改为可选宿主。
- **knowledge-extractor 直接写 plugins/**。拒绝：单数 `reference/`、`inventory/`、`README.md`、超 300 行会被 check-plugin-package fail；必经适配层翻译。
- **只扩展现有结构测试**。拒绝：结构测试测不了运行效果；eval 是独立新层。
