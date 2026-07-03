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

- since_days: {N}
- session_filter: {session_filter_or_none}
- local_private_evidence: `evidence.json`
- public_preview: `github-issue.md`
- matched_events: {count}

## 失败点清单

| # | 类型 | 相关 skill | 现象 | 证据 |
|---|---|---|---|---|
| 1 | tool-failure / unclear-rule / agent-detour / goal-driver / install-distribution / privacy-reporting | `cs-feat` | {一句话} | {provider/session_label/timestamp_bucket} |

## 关键上下文

{按失败点摘要 evidence 里的 context，不贴完整 transcript。}

## 隐私说明

- `evidence.json` 是本机私有证据，`public_upload_allowed=false`。
- GitHub issue 只使用 `github-issue.md` public preview，不上传 `evidence.json` 原文。
- 虽然 evidence 已 best-effort 脱敏，仍可能含业务上下文，应按私有文件处理。

## 用户纠正信号

{用户指出 agent 绕路、做错阶段、没有按 skill 行为执行的原话和前后动作。}

## 疑似根因

{规则缺口 / 脚本缺口 / 分发缓存 / agent 执行偏差 / 需要更多样本。}

## 建议修改

- {改哪个 skill / reference / script / test}

## 上报状态

- GitHub issue: {url_or_pending}
- Manual fallback: {command_or_none}
```

## `github-issue.md`

```markdown
## Summary

{一句话说明 CodeStable skill 使用问题。}

## User Feedback

{用户原始反馈}

## Evidence

- Report: `{report_path}`
- Local private evidence: kept on the user's machine, not uploaded
- Matched events: {count}
- Public evidence fields: provider, session_label, timestamp_bucket, failure_type, match_type, tool_name, skill_or_reference, sanitized_excerpt

## Suspected Area

- Skill/reference/script/test: {paths_or_unknown}
- Failure type: {tool-failure|unclear-rule|agent-detour|goal-driver|install-distribution|privacy-reporting|unknown}

## Context

{只放 public allowlist 摘要；不贴完整 transcript、本机绝对路径、私有 repo 名、remote URL、环境变量、token、MCP/tool 原始 JSON 参数或大段业务代码。}

## Expected Behavior

{用户期望或报告推断出的正确行为。}

## Proposed Fix

{建议补规则、脚本或测试。}
```
