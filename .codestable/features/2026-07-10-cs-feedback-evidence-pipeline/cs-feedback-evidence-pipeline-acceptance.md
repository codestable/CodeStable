---
doc_type: feature-acceptance
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: passed
accepted: 2026-07-11
round: 1
---

# CS Feedback Evidence Pipeline 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-11
> 关联方案：`cs-feedback-evidence-pipeline-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：

- [x] collector：current/显式 session 输入生成 local-private evidence、triage 与条件性 public
  projection；真实 Codex/Claude CLI 与结构化 integration tests 一致。
- [x] triage：单一 incident、assessment source/ref/confidence、双 readiness 与缺口字段均按
  design schema 输出；非法 identity/ref fail-closed。
- [x] candidate：canonical triage 只在同目录生成 local-private candidate；v1 public context
  只生成未就绪 candidate，旧直写入口非零。
- [x] promotion：repo-local 工具消费 candidate/config，完成 profile/input/privacy/judge/harness/
  commit-safe 校验后才落正式 fixture。

**名词层与流程图核对**：

- [x] `NormalizedRecord`、`FeedbackIncident` 有明确类型；Observation/Assessment/Quality 作为
  schema 与机械计算边界落在 incidents/triage 模块。
- [x] schema v2 incidents 为 canonical，v1 matched_events/public events 保持兼容投影。
- [x] “显式调用 → metadata-only 定位 → normalize/incident → repo enrich → evidence/triage →
  quality → public/candidate”各节点均有代码与测试落点。

## 2. 行为与决策核对

**需求与关键决策**：

- [x] 仅显式调用采集；current 优先且歧义时只让用户选，不扩大扫描。
- [x] snapshot 与 trigger cutoff 分离；无 user anchor 未就绪，post-anchor 记录排除。
- [x] provider/adjacency/unpaired 三态配对，跨 user-turn incident 不误合并。
- [x] Observation 与 Assessment 分层，推断必须带来源、置信度和 evidence refs。
- [x] public projection 只从 8+7 allowlist 构建；local-private 文件永不作为公开正文。
- [x] quality gap 驱动单问；triage readiness 不等于 regression readiness。
- [x] shipped candidate 与 repo-local promotion 只通过 JSON artifact 交接，无运行时 import。
- [x] 共享提示集中在 execution conventions，未复制到每个 skill。

**明确不做与流程级约束**：

- [x] 无后台 telemetry、自动上传、默认全历史扫描、自动修改目标 skill 或自动付费评测。
- [x] 重采集保留用户补充；incident/fingerprint 漂移进入 pending/accept 状态，不静默覆盖。
- [x] evidence/triage/public 三文件 staged+rollback；candidate/promotion 失败均诊断且 no-write。

**挂载点与可卸载性**：

- [x] M1：`cs-feedback/SKILL.md` + report template 承载用户协议与报告格式。
- [x] M2：collector + feedback modules 承载 schema v2、current、incident、triage 与 privacy。
- [x] M3：shipped converter + repo-local promotion 承载评测交接。
- [x] M4：onboard execution/shared/system templates 与 runtime copy 承载共享提示和布局。
- [x] M5：tests、`rt-c17`、ADR-003 与公开 docs 承载 gate 和对外投影。
- [x] 反向核查：scope-gate changed files 除 workflow/requirement/验收产物外均落在 M1-M5；
  无清单外运行入口。按 M1-M5 逆序拔除后只剩 feature/requirement 历史，不留可执行路径。

## 3. 验收场景核对

- [x] S1：current 唯一候选自动选择；skill 不传 since-days，collector 报 ignored。
- [x] S2：真实 current 产生 5 个 metadata-only 候选，候选无 message/tool/content 字段。
- [x] S3：provider id、唯一相邻 fallback、歧义 unpaired 与 source order 均通过。
- [x] S4：两个不重叠 user-turn 生成两个 incident，不因相同 skill 名合并。
- [x] S5：用户纠正进入 expected source=user，actual 引用此前 observation。
- [x] S6：expected unknown 时保存反馈、quality 只优先追问该缺口。
- [x] S7：runtime/artifact/git file-level context 存在时记录，缺失为 unknown 而不失败。
- [x] S8：secret/path/remote/env/raw JSON/code 双层负向矩阵及三类私有文件真实拒绝通过。
- [x] S9：assessment 缺 ref、source 或 inferred confidence 时 triage_ready=false。
- [x] S10：triage-ready 但缺 reproduction/oracle 时可报告，不可形成正式 fixture。
- [x] S11：routing/findings 正向 promotion 与 config/profile/privacy/judge/harness/no-write 负向通过。
- [x] S12：v1 context 仍可读；events 精确 8 字段/6 值域，v2 incident_kind 只进 incidents。
- [x] S13：共享约定只提示显式调用，不采集、不上传。
- [x] S14：真实未确认 reporter 返回 manual；confirmed body/title 与私有文件边界由集成测试锁定。
- [x] S15：无 anchor capture_cutoff unknown 且未就绪；有 anchor 时后续记录不进 evidence。
- [x] S16：Codex JSONL 与 Claude JSON/JSONL 合成同构，真实两 provider snapshot 均解析成功。

**review/QA/gate 复核**：

- [x] Round 17 Fable 5/high review `passed`，无 blocking/important。
- [x] Round 2 QA `passed`，功能性核心路径均有 unit/integration/真实 CLI 证据。
- [x] QA residual 仅为隐私侧过脱敏、窄路径边界和需用户授权的真实上传，不承载核心缺口。
- [x] evidence pack、scope gate、DoD 均 passed；CMD-004 仅既有根 `cs-onboard/` baseline。

## 4. 术语一致性

- `Feedback Incident`：design、model、incident builder、skill 文案与 schema 使用一致。
- `Observation` / `Assessment`：分别归 evidence 与 triage；无反向混写。
- `Feedback Quality Gate`：实现为 `triage_ready/regression_ready/missing_fields/reasons` 机械结果。
- `Optimization Handoff`：shipped candidate 与 repo-local promotion 的 artifact 边界一致。
- canonical `incident_kind` 与 v1 `failure_type` 分区明确，无同名异义。

## 5. 领域影响盘点

- 新术语候选：Feedback Incident、Observation/Assessment 分层、Feedback Quality Gate。仓库目前
  无 CONTEXT.md；建议后续通过 `cs-domain` 将三者纳入领域术语，不在 acceptance 代写。
- 结构性决策：candidate artifact 边界已机械回写现有 ADR-003 applies-to/Decision/
  Consequences/lint；design 明确“不新增 ADR”，实现与之相符。
- 流程约束：显式触发、public 逐次确认、skill 运行时独立性已进入 shared/execution conventions
  与测试，不需另开 ADR。

## 6. requirement 回写

- [x] Owner 在 `approval-report.md` 选择 Option A，并确认完整 backfill 初稿“可以了”。
- [x] 新建 `.codestable/requirements/feedback-evidence-pipeline.md`，`status: current`，用户故事、
  pitch 与边界来自 approved design 和实际 QA，无新增实现范围。
- [x] 新建 `VISION.md`，按 Current/Draft/Outdated 分组索引现有两份 requirement。
- [x] design frontmatter 机械关联 `requirement: feedback-evidence-pipeline`。

## 7. roadmap 回写

- design frontmatter 的 `roadmap` / `roadmap_item` 均为空；本 feature 非 roadmap 起头，按协议跳过。

## 8. attention.md 候选盘点

- 本 feature 未暴露新的全局启动硬约束；Fable 5/high review 约束已在 attention.md。
- compound 候选：隐私 matcher 必须同时测试“漏脱敏”和“过脱敏”，并覆盖词位、定界符后的
  语言环境与真实 transcript 形态。建议收尾时询问是否走 `cs-keep`。
- 用户指南/API 变化已在本 feature 内同步 README/WORKFLOW/catalog/SKILL，无额外 docs 缺口。

## 9. 遗留

- CJK/假名粘连、混合脚本路径、伪盘符、未闭合引号存在隐私侧过脱敏或窄尾段残留；公开前
  人工 preview 仍是最终防线。
- ENV_NAME 对普通全大写词可能过脱敏；方向 fail-closed。
- converter/candidate 单文件写原子性、session id fallback、promotion temp/fsync 等 review nits
  未扩成核心正确性问题，后续按 issue/refactor 处理。
- recall_judge `[soft]`、k=1 variance 与 candidate 语义真实性属于 eval 有效性残余；正式 campaign
  仍需分模型手读原始输出。
- 未真实创建 GitHub issue；实际上传必须由用户逐次确认，不能为验收越过授权。

## 10. 最终审计

- 验证证据来源：Round 2 `cs-feedback-evidence-pipeline-qa.md`（functional / passed）。
- Evidence sources：acceptance 阶段 fresh evidence pack、DoD results 与 scope gate，均 `passed`。
- 聚合命令：targeted `171 passed`、full `341 passed`、eval/ADR lint `65 passed`；runtime
  `status=ok`；`git diff --check` exit 0；package 仅既有根 `cs-onboard/` baseline。
- 场景复核：re-verified 16 / trust-prior-verify 0；全部 design 场景由最终 targeted/integration
  suite 重跑，真实 provider/reporter CLI 证据由同一最终代码状态的 QA 补强。
- 交付物复核：collector/modules、candidate converter、repo-local promotion、reporter、schema/fixture、
  tests、skill/runtime templates、ADR/docs、current requirement 与 VISION 均存在；roadmap 不适用。
- 完整工作区复核：tracked、untracked、machine artifacts 全部纳入 scope-gate；新增 requirement
  路径来自 owner-approved Option A，无未授权文件。
- diff 清洁度：无新增 debug、cache、注释死代码或方案外文件；两条 TODO warning 仅为 placeholder
  拒绝规则/负向测试字面量；所有 Markdown ≤300 行。
- 知识沉淀出口：无新 attention 候选；双向隐私 matcher 测试经验列为可选 `cs-keep`；领域术语
  列为可选 `cs-domain`；用户指南/API 投影已在本 feature 内同步。
- 结论：通过。21 checks 全部 `passed`，review/QA/DoD 无 failed/blocked，required artifacts 完整。
