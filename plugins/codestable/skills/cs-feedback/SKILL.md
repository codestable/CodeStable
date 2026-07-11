---
name: cs-feedback
description: CodeStable 使用反馈闭环。触发：用户反馈 cs skill 跑偏、工具失败、规则没讲清、agent 被用户纠正；显式调用后采集本机证据并准备可确认的公开 issue。
argument-hint: "[--since-days N | --session current|<id-or-path>] [--accept-incident <id>] [--github] <feedback>"
---

# cs-feedback

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-feedback` 只在用户显式调用后收集 CodeStable 自身的规则、工具或流程问题。它生成
local-private evidence 与 triage，不修业务代码、不自动改目标 skill、不后台采集、不自动上传。
GitHub 上报必须先展示 public preview 并得到用户逐次确认。

## 入口意图

本次调用参数：$ARGUMENTS

无参数默认行为：参数为空或仍是字面 `$ARGUMENTS` 时，只问一句“这次是哪类失败：工具失败、规则不清、
阶段跑偏、安装上报问题，还是其他？”有反馈文本但没有范围参数时，skill 默认当前会话：
传 `--session current --cwd "$(pwd)"`，不传 `--since-days`。

| 参数 | 行为 |
|---|---|
| `--session current` | metadata-only 定位当前 cwd 的唯一会话；弱匹配或多候选必须让用户选择 |
| `--session <id-or-path>` | 只采集用户选定的 Codex / Claude 会话 |
| `--since-days N` | 用户显式要求时跨会话扫描最近 N 天；不再传 `--session current` |
| `--accept-incident <id>` | 只在 triage 已记录同一 pending incident 时显式采纳；不得由 agent 自行推断 |
| `--github` | 生成 public preview；不是上传授权 |

collector 直接调用仍保留 v1 的 `session=None + since_days=3` 默认。若调用方同时传 current
和 since-days，current 只绕过 `time_cutoff`，输出 `since_days_ignored=true`；最后 user
record 的 `trigger_cutoff` 始终生效。

## 文件布局

```text
.codestable/feedback/YYYY-MM-DD-{slug}/
├── {slug}-report.md
├── evidence.json                 # local-private observations
├── triage.json                   # local-private assessments + quality
├── public-issue-context.json     # public allowlist projection，可选
├── github-issue.md               # 用户确认的公开正文，可选
└── regression-candidate.json     # local-private eval 交接，可选
```

未 onboard 时先提示 `cs-onboard`；仍需保留现场时可写
`/tmp/codestable-feedback-{slug}/`，但继续按 local-private 处理。

## 工作流

### 1. 定位并冻结会话

默认运行：

```bash
python3 {skill_dir}/scripts/collect_feedback_context.py --session current --cwd "$(pwd)" --feedback "{用户原话}" --output {feedback-dir}/evidence.json --triage-output {feedback-dir}/triage.json --public-output {feedback-dir}/public-issue-context.json
```

显式 `--since-days N` 时去掉 current/cwd。`ambiguity.candidates` 非空时，metadata-only
路径不得 flatten、匹配或持久化 message/tool 正文；只让用户选择 session，再用
`--session <id-or-path>` 重跑。

采集器对选定输入只读一次 snapshot：JSONL 记录完整 record EOF，单 JSON 使用不可变 byte
snapshot；`trigger_cutoff` 后的 assistant/tool record 不进入 evidence。没有 user anchor 时仍可
保存 incident，但 triage 保持未就绪。

### 2. 检查 incident 与 triage

`evidence.json` schema v2 以有序 `incidents` 为 canonical 单元，保留 role、tool pairing、
用户纠正、observation ids、runtime/artifact/git 文件级上下文；旧 `matched_events` 继续作为 v1
兼容投影。provider id 精确配对标 `provider`，唯一无 id 紧邻配对标 `adjacency`，其他均为
`unpaired`。

`triage.json` 把 Observation 与 Assessment 分开。判断字段必须带 `source` 和
`evidence_refs`；`source=inferred` 还必须有 `confidence`。未知就写 `unknown`，不猜根因。

canonical `incident_kind`：`wrong-route / skipped-gate / missing-artifact / tool-failure /
goal-driver / unnecessary-detour / install-version / privacy-reporting / unclear-rule / unknown`。
v1 public `events[].failure_type` 只保留原 6 值域，不写 v2 枚举。

### 3. Ask User（缺口驱动）

不要固定三问。按 `quality.next_questions` 每次只问最高优先级缺口：

1. session / primary incident 仍歧义：只让用户选择。若 triage 已有
   `pending_incident_id`，展示 previous/pending 值；用户明确采纳后，用原采集参数加
   `--accept-incident <pending-id>` 重跑。采纳必须匹配当前 primary 的 fingerprint，保留
   reproduction，归档旧 assessment/privacy，并把 active privacy review 重置为 `pending`。
2. target skill、expected、actual 或 observation ref 缺失：只补当前第一项。
3. triage 已就绪但 regression 缺 input/oracle：只在用户要做回归样本时追问。
4. 用户要求 GitHub：只问 public preview 是否可以公开。

`triage_ready` 要求唯一 incident、trigger cutoff、target skill、expected/actual 和 observation
refs；`regression_ready` 还要求兼容 profile、最小可重放 input 与 oracle。quality 表示证据完备性，
不表示问题严重度，也不证明一定是 skill 缺陷。重复采集不得覆盖用户手工补充字段；位置编号
相同但 fingerprint 不同也必须重新选择。

### 4. 写本地报告与公开投影

按 `references/report-template.md` 写 `{slug}-report.md`。报告引用 observation ids 与 triage
quality，不贴完整 transcript。`evidence.json`、`triage.json`、`regression-candidate.json` 永远
local-private。
local evidence 只做 best-effort 脱敏，不能因此视为可公开文件。

public preview 只能从结构化 allowlist 构建：

- v1 event 精确 8 字段：provider、session_label、timestamp_bucket、failure_type、match_type、
  tool_name、skill_or_reference、sanitized_excerpt。
- v2 incident 精确 7 字段：incident_kind、target_skill、stage_hint、expected_behavior、
  actual_behavior、impact、proposed_fix。

禁止公开：完整 transcript、本机绝对路径、repo/remote、环境变量、secret、原始 tool JSON、
代码块或业务代码。不要从人写报告反向抓字段生成 preview。

### 5. 可选 regression candidate

shipped skill 只产同目录 local-private candidate：

```bash
python3 {skill_dir}/scripts/feedback_to_fixture.py --triage {feedback-dir}/triage.json
```

兼容 `--evidence <v1-public-context>` 也只生成未就绪 candidate。旧 `--failure --experiment`
/ shipped `--experiment` 直写正式 fixture 必须非零。正式 promotion
只由 CodeStable 维护仓库的 repo-local `eval-cs-skill` 工具消费 JSON artifact；普通用户仓库
没有该工具时保留 candidate，不形成运行时跨 skill 依赖。

### 6. GitHub 上报

即使用户传 `--github`，也必须先让用户确认 preview；未确认不调用 GitHub。确认后只上传
`github-issue.md`：

```bash
python3 {skill_dir}/scripts/report_feedback_issue.py --repo liuzhengdongfortest/CodeStable --title "{title}" --body-file {feedback-dir}/github-issue.md --confirm-public-preview
```

reporter 按文件名硬拒 evidence、triage、candidate，按 `privacy=local-private` 二次拒绝，并在
网络边界再次扫描 public body。`gh` 缺失、未登录或网络失败时只返回 manual fallback；若需要
访问 GitHub，按宿主规则检测本机代理后重试。

## 退出条件

- [ ] report、evidence、triage 已落盘，或报告说明采集不可用。
- [ ] primary incident 与 `quality.triage_ready` 状态明确；未知字段未编造。
- [ ] public preview（如生成）只含 allowlist，用户未确认时没有网络上报。
- [ ] candidate（如生成）仍在 feedback 目录，未就绪输入未进入正式 fixtures。
- [ ] 没有后台采集、自动上传、自动修改目标 skill 或默认全历史扫描。

## 相关文档

- `references/report-template.md` — 本地报告、triage 补充和 GitHub body 模板。
- `scripts/collect_feedback_context.py` — evidence / triage / public projection 编排。
- `scripts/feedback_to_fixture.py` — candidate-only 转换。
- `scripts/report_feedback_issue.py` — 确认后的 GitHub 创建 / fallback。
