# cs-feedback 报告模板

## `{slug}-report.md`

```markdown
---
doc_type: codestable-feedback
feedback: {YYYY-MM-DD}-{slug}
status: draft
created: {YYYY-MM-DD}
source_providers: [codex, claude]
privacy: local-private
github_issue: ""
---

# CodeStable Feedback: {title}

## 用户原始反馈

{user_feedback}

## 自动采集范围

- mode: {current | selected-session | since-days}
- session_filter: {current_or_selected_or_none}
- since_days_ignored: {true_or_false}
- local_private_evidence: `evidence.json`
- local_private_triage: `triage.json`
- public_preview: `public-issue-context.json`
- incidents: {count}
- primary_incident: {incident_id_or_unknown}

## 反馈事件包

| Incident | Kind | Target / Stage | Cutoff | Observation refs |
|---|---|---|---|---|
| `incident-01` | {incident_kind} | `{skill}` / `{stage}` | `{record_or_unknown}` | `obs-0001`, `obs-0002` |

## 客观观察

| Ref | Role / Type | 事实摘要 |
|---|---|---|
| `obs-0001` | assistant / message | {只摘要脱敏事实，不写根因} |
| `obs-0002` | tool / tool_result | {工具结果摘要} |

## 分析判断

| 字段 | 值 | Source | Confidence | Evidence refs |
|---|---|---|---|---|
| expected_behavior | {value_or_unknown} | {user_or_unknown} | - | {refs} |
| actual_behavior | {value_or_unknown} | {transcript_or_unknown} | - | {refs} |
| impact | {value_or_unknown} | {inferred_or_unknown} | {confidence_or_dash} | {refs} |
| proposed_fix | {value_or_unknown} | {source_or_unknown} | {confidence_or_dash} | {refs} |

`cause_status` 默认 `unclassified`。Observation 不写疑似根因；Assessment 无依据时保持
`unknown`，`source=inferred` 必须同时有 confidence 和 evidence refs。

## 质量门

- triage_ready: {true_or_false}
- regression_ready: {true_or_false}
- incident_fingerprint: {sha256_or_unknown}
- previous_incident: {id_or_none}
- pending_incident: {id_or_none}
- missing_fields: {list}
- next_questions: {最多当前最高优先级一项}
- reasons: {list}

`pending_incident` 非空时，先让用户核对 previous/pending。只有用户明确采纳，才用同一组采集
参数追加 `--accept-incident {pending-id}`；采纳后重新检查 assessment 与 public preview。

## 本机环境

- provider / model / host: {values_or_unknown}
- runtime: {version_and_status_or_unknown}
- related_artifacts: {仅 repo-relative path + status}
- git_status: {仅 status + repo-relative filename，不贴 diff 或文件内容}

## 隐私说明

- `evidence.json`、`triage.json`、`regression-candidate.json` 是 local-private。
- evidence 已 best-effort 脱敏，仍可能含业务上下文，不得上传。
- GitHub 只使用用户确认后的 `github-issue.md`，且该正文只从 public allowlist 渲染。
- 不公开完整 transcript、绝对路径、remote/env、secret、原始工具参数或代码块。

## Regression 交接

- candidate: {path_or_not_requested}
- promotion_blockers: {list}
- 正式 fixture: {repo_local_promotion_result_or_not_ready}

## 上报状态

- Public preview confirmed: {yes_or_no}
- GitHub issue: {url_or_pending}
- Manual fallback: {command_or_none}
```

## `github-issue.md`

该正文只从 `public-issue-context.json` 的 allowlist 字段渲染；不要复制用户原话、报告路径或
local-private 文件正文。

```markdown
## Summary

{sanitized one-line incident summary}

## Incident

- Kind: {incident_kind}
- Target skill: {target_skill}
- Stage hint: {stage_hint}

## Expected Behavior

{public expected_behavior or unknown}

## Actual Behavior

{public actual_behavior or unknown}

## Impact

{public impact or unknown}

## Proposed Fix

{public proposed_fix or unknown}

## Evidence

- Matched public events: {count}
- Public evidence fields: provider, session_label, timestamp_bucket, failure_type, match_type,
  tool_name, skill_or_reference, sanitized_excerpt, incident_kind, target_skill, stage_hint,
  expected_behavior, actual_behavior, impact, proposed_fix
- Local private evidence remains on the user's machine and is not uploaded.
```

生成后再次确认：正文不含完整 transcript、本机绝对路径、repo/remote、环境变量、secret、
原始 MCP/tool JSON 参数、代码块或大段业务代码。
