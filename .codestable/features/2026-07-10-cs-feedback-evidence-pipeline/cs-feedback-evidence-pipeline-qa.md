---
doc_type: feature-qa
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: passed
tested: 2026-07-11
round: 2
---

# cs-feedback-evidence-pipeline QA 报告

## 1. Scope And Inputs

- Design/checklist：approved；6 steps done，21 checks 留给 acceptance。
- Review：Round 17 `passed`，`reviewer: subagent`，无 unresolved blocking/important。
- Evidence/gates：DoD、scope、evidence pack 均 passed；package 仅既有根 `cs-onboard/` baseline。
- Diff basis：baseline `30fecaae5e747dbad1f0e599d592d7c04cc7f0c4` 加完整 tracked/untracked
  工作区；scope gate 证明全部可归因本 feature。
- Feature type：functional。核心证据门覆盖 current/session CLI、snapshot/incident/triage 持久化、
  public privacy、candidate/promotion、v1/v2 兼容与 reporter 上传确认边界。
- 真实 smoke 只读本机 transcript snapshot，输出落随机 `/tmp` 目录；未改 session、未联网、
  未上传 GitHub。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 结果 |
|---|---|---|---|---|---|
| QA-001 | S1-2 | core-functional | current 唯一/多候选、metadata-only、time cutoff | unit + 真实 CLI | pass |
| QA-002 | S3-4 | core-functional | provider/adjacency/unpaired、窗口合并与问题分离 | unit/integration | pass |
| QA-003 | S5-6,9 | core-functional | Observation/Assessment、source/ref/confidence、缺口单问 | unit | pass |
| QA-004 | S7 | supporting | runtime/artifact/git 文件级 context 与 unknown | integration | pass |
| QA-005 | S8 | core-functional | secret/path/remote/env/raw JSON/code 隔离与私有文件拒绝 | adversarial + CLI | pass |
| QA-006 | S10 | core-functional | triage-ready 可报告、未就绪不可 promotion | integration + CLI | pass |
| QA-007 | S11 | core-functional | candidate-only、config/profile/privacy/judge/harness fail-closed | integration | pass |
| QA-008 | S12 | core-functional | v1 events 8 字段/6 值域与 v2 incident 分区 | unit | pass |
| QA-009 | S13-14 | core-functional | 显式触发、未确认零网络、确认后 body/title 二次扫描 | contract + CLI | pass |
| QA-010 | S15 | core-functional | trigger cutoff、无 anchor、anchor 后排除 | unit | pass |
| QA-011 | S16 | core-functional | Codex/Claude JSON/JSONL 同构与真实 provider schema | unit + 真实 CLI | pass |
| QA-012 | review/gates | supporting | pending/accept/fingerprint、原子回滚、全量 gate | integration + command | pass |

## 3. Command Results

- 会话/incident 聚焦组 → `10 passed`；quality/privacy 聚焦组 → `15 passed`。
- candidate/promotion 组 → `66 passed`；reporter/协议组 → `64 passed`。
- targeted → `171 passed`；全量 → `341 passed`；eval/ADR lint → `65 passed`。
- runtime sync → `status=ok`；三组 template/runtime `cmp` → exit 0；`git diff --check` → exit 0。
- package → 仅既有根 `cs-onboard/` finding；无新增 cache/package finding。
- 真实 `--session current --cwd` → exit 0，5 个 Codex/Claude metadata-only candidates；候选
  精确只有 `cwd/mtime/path/provider/score/session`，无 message/tool/content 字段；triage 未就绪，
  public events/incidents 为空。
- 显式真实 Codex/Claude snapshot → 均 exit 0，生成 local-private evidence/triage 与有效
  `trigger_cutoff`；不完整 assessment 保持 fail-closed，public 字符串无隐私命中。
- 真实 triage → candidate exit 0，只写同目录 local-private candidate、无 fixture；缺 config
  promotion exit 2，目标目录未创建。
- reporter 未确认 → exit 0/manual，reason 为 confirmation required；三类 local-private 文件即使
  带确认也均在网络前 exit 1 拒绝。

## 4. Scenario Results

- [x] QA-001：真实 current ambiguity 与 metadata-only 正文隔离均成立。
- [x] QA-002：三态配对、歧义不猜、连通窗口 source order 与跨 user-turn 分离成立。
- [x] QA-003：用户 expected、actual observation ref、unknown 单问及非法 source/ref fail-closed。
- [x] QA-004：隔离 repo 的 runtime/artifact/git context 与 metadata 来源资格通过。
- [x] QA-005：短/长/quoted/multiline/shell secret、JSON、路径和代码双层负向矩阵通过。
- [x] QA-006：未就绪真实 candidate 保留缺口且不含 fixture；public 只在唯一 ready primary 生成。
- [x] QA-007：routing/findings 正向 promotion 与全部 no-write 负向 gate 通过。
- [x] QA-008：v1 精确字段和值域冻结，v2 `incident_kind` 不污染 events。
- [x] QA-009：共享提示不自动采集；真实未确认 CLI 不触网，confirmed 调用边界由 subprocess
  断言锁定。
- [x] QA-010：无 user anchor 未就绪；有 anchor 时 post-anchor assistant/tool 不进入 evidence。
- [x] QA-011：三种 provider 容器同构测试与真实 Codex/Claude schema smoke 通过。
- [x] QA-012：用户字段保留、same-id fingerprint 重选、三文件 rollback 与完整 gates 通过。

## 5. Findings

### failed

none。

### blocked

none。

### residual-risk

- CJK 直接粘 `.`+合法扩展名的句末/换行形状、假名/谚文粘连会落向隐私侧并损失正文；
  与真实文件名机械同形，不泄露绝对根路径，需继续依赖人工 preview 评估保真。
- 混合脚本真实路径组件、CJK 相对路径重启、伪 Windows 多字母盘符与未闭合引号存在窄幅
  过脱敏/尾段残留；本轮探针未发现可公开绝对根路径。
- ENV_NAME 对普通全大写词过脱敏；方向 fail-closed。
- 未真实创建 GitHub issue：真实上传需要用户逐次确认，本 QA 只执行未确认零网络 CLI、私有
  文件真实拒绝，以及 confirmed `gh auth/issue create` 参数级集成测试。
- recall_judge `[soft]` 与 k=1 variance、candidate 语义真实性留给 acceptance 记录。

## 6. Cleanliness

- Debug output：pass。
- Temporary TODO/FIXME/XXX：pass；scope 的两条 TODO warning 仅来自 placeholder 拒绝规则及其
  负向测试字面量。
- Commented-out code：pass。
- Unused imports / dead code from this feature：pass。
- Out-of-scope files：pass。
- Cache/generated artifacts：pass；review/QA import 后无 `__pycache__`。
- Markdown 300 行上限：pass；最长 design/implementation 各 297 行。

## 7. Verdict

- Status：`passed`。16 个功能场景均有运行证据，核心隐私/聚合/quality/promotion/compatibility
  路径无 failed/blocked item。
- Next：进入 `cs-feat` acceptance 阶段，逐项核验 21 checks、required artifacts、ADR/runtime
  投影和 residual-risk 记录。
