---
doc_type: feature-design-review
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: passed
reviewed: 2026-07-10
round: 8
---

# cs-feedback-evidence-pipeline feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-10-cs-feedback-evidence-pipeline/cs-feedback-evidence-pipeline-design.md`
- Checklist: `.codestable/features/2026-07-10-cs-feedback-evidence-pipeline/cs-feedback-evidence-pipeline-checklist.yaml`
- Intent / brainstorm / roadmap / requirement: none
- Related docs: `docs/adr/003-cs-skill-evaluation-loop.md`、`.codestable/reference/shared-conventions.md`、execution conventions
- Code facts checked: cs-feedback collector/reporter/candidate converter、feedback/bootstrap/eval tests、eval config/fixtures/buildPrompt/scorers

### Independent Review

- Status: completed
- Detection: paseo
- Provider / agent: `providers.audit=claude/opus` / `54019950-31f5-4544-93b2-3bf1b9ce96a3`
- Raw output: 第八轮最终审查明确“建议通过”，无 blocking/important；前七轮 reviewer 发现的契约缺口均已修订并重审
- Merge policy: 主 agent 已逐条用 design、checklist、ADR、代码和测试事实核验；所有完成 reviewer 均已归档
- Gate effect: none；进入用户整体 design review checkpoint

## 2. Design Summary

- Goal: 把一次 CS skill 使用问题整理成可分诊、可复现、可安全进入优化评测的本地证据包。
- Key contracts: incident canonical model、Observation/Assessment 分层、`time_cutoff`/`trigger_cutoff`、private/public 投影、candidate artifact 与 repo-local promotion 边界。
- Steps: 6；先行为等价拆分，再完成采集、分诊、评测交接、入口同步和验证闭环。
- Checks: 21；覆盖跨 provider、隐私、v1/v2 兼容、profile/config gate、运行时 skill 独立性和 ADR-003 消费侧。
- Baseline / validation: targeted/full pytest、ADR-003 lint、package baseline、runtime sync、YAML 和 diff check。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- feedback-to-fixture 的稳定边界是 artifact handoff：shipped skill 只产 local-private candidate，repo-local eval skill 才拥有 experiment config、validator、scorer 和正式 promotion。
- `validate_fixture_dict` 只覆盖部分结构；profile 最小 input、task kind、scorer、harness、judge 和 commit-safe 必须由 promotion 工具独立 fail closed。

### praise

- Observation/Assessment 分层、`cause_status=unclassified` 与 evidence refs 把认知诚实落实到数据结构。
- current-session metadata-only reader、public allowlist、candidate/promotion 分离共同形成清晰的隐私边界。

## 4. User Review Focus

- 用户需要重点拍板：显式触发且无遥测；默认 current session；不唯一时让用户选择。
- 用户需要重点拍板：candidate 默认只留 feedback 目录；正式 fixture 仅由 repo-local eval 工具显式 promotion。
- implement 需要遵守：shipped 脚本运行时不得 import eval 工具；两者只通过 candidate artifact 交接。
- code review / QA / acceptance 需要复核：cutoff、provider 同构、commit-safe、v1 8 字段/6 值域、config/judge/harness gate。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | 16 个场景逐项映射 S2-S6 和证据动作 | acceptance 逐项核对 |
| DoD Contract | pass | E | Design/Implementation/Review/QA/Acceptance DoD 与 required artifacts 完整 | none |
| Steps and checks traceability | pass | E | 6 steps、21 checks 均能回到名词/编排/范围/挂载点/场景 | implementation 留 step 证据 |
| Roadmap contract compliance | n/a | E | 本 feature 非 roadmap 起头 | none |
| Module interface design | pass | C | 代码证实 metadata reader、candidate artifact、repo-local promotion 是真实 seam | code review 查运行时 import |
| Validation and artifacts | pass | C | 命令路径、ADR lint、runtime sync、package baseline 与仓库事实一致 | QA 运行完整命令 |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- current-session 仍依赖 provider 的 cwd/session metadata；弱匹配必须让用户选择，不能静默自动选。
- commit-safe 扫描只能覆盖已知敏感模式；正式 promotion 仍需人工 privacy approval 和合成复现纪律。
- `recall_judge` 结论是 `[soft]` 且有 k=1 variance；acceptance 必须记录模型分布并人工读原始输出。
- candidate→promotion 兼容测试只允许在 repo-local ADR lint 测试中连接两个安装单元，不能演化为 shipped runtime import。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review；用户确认前 design 保持 `draft`，不得进入 goal package 或 implementation。
