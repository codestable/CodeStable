---
name: cs-feedback
description: CodeStable 使用反馈闭环。触发：用户反馈 cs skill 跑偏、工具失败、规则没讲清、agent 被用户纠正，自动采集本机 Codex/Claude 历史并生成可上报 issue。
argument-hint: "[--since-days N] [--session current|<id-or-path>] [--github] <feedback>"
---

# cs-feedback

## 启动必读

开始任何判断或动作前，先执行 CodeStable preflight：读 `.codestable/attention.md`；缺失先 `cs-onboard`；不读外部 AI 入口替代（详见 `.codestable/reference/execution-conventions.md`）。

`cs-feedback` 收集用户使用 CodeStable skills 的体验问题，把“这次哪里跑偏”转成可修复的维护 issue。它不修业务代码，也不直接改其他 skill；它只产出反馈报告，并在用户确认后尽量帮忙上报 GitHub。

---

## 入口意图

本次调用参数：$ARGUMENTS

无参数默认行为：参数为空或仍是字面 `$ARGUMENTS` 时，不猜具体问题；先问用户一句“这次是哪类失败：工具失败、规则不清、阶段跑偏、上报安装问题，还是其他？”同时仍可运行自动采集，给用户可选证据。

可用参数：

| 参数 | 行为 |
|---|---|
| `--since-days N` | 扫最近 N 天历史，默认 3 |
| `--session <id-or-path>` | 只扫某个 Codex/Claude session id 或 jsonl 路径 |
| `--session current` | 尝试按 cwd、mtime 和 transcript metadata 推断当前会话；命中多个候选时必须问用户选择 |
| `--github` | 生成 GitHub issue public preview；用户确认后才用 `gh issue create` 上报 |

其余文本作为用户原始反馈，必须原样写入报告。

---

## 文件放哪儿

```text
.codestable/feedback/{YYYY-MM-DD}-{slug}/
├── {slug}-report.md
├── evidence.json                 # local-private，不上传
├── public-issue-context.json     # 可公开证据摘要，可选
└── github-issue.md
```

如果当前仓库还没接入 `.codestable/`，先提示 `cs-onboard`；但仍可把 evidence/report 写到 `/tmp/codestable-feedback-{slug}/`，方便用户手动带走。

---

## 工作流

### 1. 收集线索

先把用户原话分类，不急着定责：

- 工具调用失败：file read、apply patch、MCP、Paseo、git、GitHub、网络、权限、超时。
- 规则不清：skill 没讲清阶段、参数、fallback、handoff、goal driver、review gate。
- 流程绕路：agent 做了不必要步骤，被用户纠正后才回到正确路径。
- 分发安装：Codex / Claude marketplace、版本缓存、branch/ref、插件安装。

### 2. 自动采集

运行：

```bash
python3 {skill_dir}/scripts/collect_feedback_context.py --since-days 3 --feedback "{用户原话}" --output {feedback-dir}/evidence.json --public-output {feedback-dir}/public-issue-context.json
```

如果用户给了 session id/path，加 `--session`。如果用户要“当前会话”，传
`--session current --cwd "$(pwd)"`；这是 best-effort，不是可靠 oracle。脚本会扫：

- Codex：`~/.codex/sessions/**/*.jsonl`
- Claude：`~/.claude/projects/**/*.jsonl` 和 `~/.claude/sessions/*.json`

脚本输出两层证据：`evidence.json` 是 local-private，只留本机；`public-issue-context.json` 是 allowlist 摘要，可用于生成 `github-issue.md`。不要把完整 transcript 或 `evidence.json` 原文贴进 GitHub issue。
当 `evidence.json` 里 `ambiguity.candidates` 非空时，先让用户选 session，不能假装已经定位。

### 3. 归纳报告

读取 `references/report-template.md`，写 `{slug}-report.md`。报告必须包含：

- 用户原始反馈。
- 自动采集范围：provider、时间窗口、命中条数；session 只写短标签或 hash，不写本机路径。
- 失败点清单：每条有现象、上下文、疑似根因、涉及 skill/reference/script。
- 用户纠正信号：用户说了什么，agent 之前做了什么绕路。
- 可执行建议：改哪个 skill / reference / script / test，或标为需要更多样本。
- 隐私说明：`evidence.json` 只保存在本机，best-effort 脱敏后仍按私有文件处理。

没有自动命中时也要写报告：明确“自动采集未命中”，并列出已尝试的历史位置。

### 4. Ask User（缺口驱动）

报告落盘后只问当前阻塞质量或隐私确认的那个问题；不要固定三问。按优先级：

1. `ambiguity.candidates` 非空：只问用户选哪个 session。
2. `github-issue.md` 还没生成：先生成 public preview，不问泛泛问题。
3. preview 缺 expected behavior：问“你期望 agent 当时怎么做？”
4. preview 缺相关 skill/reference：问“最相关的是哪个 skill 或流程入口？”
5. 用户要求上报 GitHub：只问“这个 GitHub issue preview 可以公开上报吗？”

用户已在原始反馈里说清的，不重复问。

### 5. GitHub 上报

先生成 `{slug}/github-issue.md` public preview，列出将公开包含 / 不会公开包含的内容。即使用户传 `--github`，也必须先让用户确认 preview；未确认前不调用 `gh issue create`。

允许公开的内容只来自 allowlist：provider、session_label、timestamp_bucket、failure_type、match_type、tool_name、CodeStable skill/reference/script 相对路径、sanitized_excerpt、expected_behavior、actual_behavior、proposed_fix。

禁止公开：完整 transcript、`evidence.json` 原文、本机绝对路径、私有 repo 名/remote URL、环境变量、token/secret/API key、大段业务代码或用户长对话、MCP/tool 原始 JSON 参数。

用户确认可上报后：

```bash
python3 {skill_dir}/scripts/report_feedback_issue.py --repo liuzhengdongfortest/CodeStable --title "{title}" --body-file {feedback-dir}/github-issue.md
```

脚本检测 `gh`：

- `gh` 可用且已登录：直接 `gh issue create`，回填 issue URL 到报告。
- `gh` 不可用或未登录：不失败，把命令和 issue body 路径交给用户手动执行。

---

## 退出条件

- [ ] `{slug}-report.md` 已落盘，含用户反馈、自动采集范围、失败点和建议。
- [ ] `evidence.json` 已落盘并标记 local-private，或报告说明自动采集为什么不可用。
- [ ] 已生成 `github-issue.md` public preview，且不含禁止公开内容。
- [ ] 用户要求上报时，已创建 GitHub issue 或给出可手动执行的 `gh issue create` 命令。
- [ ] 没有把 token、密钥、完整无关 transcript 写进报告。

---

## 相关文档

- `references/report-template.md` — feedback report 和 GitHub issue 模板。
- `scripts/collect_feedback_context.py` — 本机 Codex / Claude 历史采集。
- `scripts/report_feedback_issue.py` — GitHub issue 创建 / fallback。
