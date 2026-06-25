# CodeStable 工具用法参考

本文件由 `cs-onboard` 复制到项目的 `.codestable/reference/tools.md`，所有 CodeStable 子技能用项目相对路径 `.codestable/reference/tools.md` 引用。

`.codestable/tools/` 下共享脚本的完整用法参考。子技能里只写本技能特有的 1-2 行典型查询；完整语法和示例看这里。

---

## 1. search-yaml.py

通用 YAML frontmatter 搜索工具。从项目根目录运行，无需安装额外依赖（PyYAML 可选，有则用，无则内建 fallback parser）。

### 基本语法

```bash
python3 .codestable/tools/search-yaml.py --dir {目录} [--filter key=value]... [--query "全文关键词"] [--sort-by FIELD [--order asc|desc]] [--full] [--json]
```

### filter 语法

- `key=value`：字段精确匹配（大小写不敏感）
- `key~=value`：字符串字段子串匹配；列表字段元素包含匹配
- `key=a|b|c` / `key~=a|b|c`：同一字段多个候选值，候选之间是 OR；在 PowerShell / Bash 中请给整个 filter 加引号，例如 `--filter "status=approved|draft"`

### 排序语法

- `--sort-by FIELD`：按 frontmatter 字段排序（典型字段：`last_reviewed`、`date`、`updated_at`）
- `--order desc|asc`：`desc` 默认，新的在前；`asc` 老的在前（查"谁最久没更新"用这个）
- 字段缺失 / 值为空的文档一律排到最后，不干扰前排结论

### 常用命令

`search-yaml.py` 用于扫**带 frontmatter 的产物**——feature spec / issue spec / requirements / adrs / guides / library-docs。

`.codestable/compound/` 由 `cs-keep` 写纯 markdown（无 frontmatter），**不用 search-yaml**，直接 grep：

```bash
grep -r "关键词" .codestable/compound/
grep -rl "prisma" .codestable/compound/   # 只列文件名
ls -lt .codestable/compound/ | head        # 看最近沉淀
```

带 frontmatter 的目录用 search-yaml：

```bash
# 搜索 feature 方案 doc
python3 .codestable/tools/search-yaml.py --dir .codestable/features --filter doc_type=feature-design --filter status=approved

# 按时间排序
python .codestable/tools/search-yaml.py --dir .codestable/library-docs --sort-by last_reviewed --order asc         # 最久没 review 的在前（找陈旧文档）
python .codestable/tools/search-yaml.py --dir .codestable/guides --filter status=current --sort-by last_reviewed --order asc

# 输出控制
python .codestable/tools/search-yaml.py --dir .codestable/features --filter status=approved --full
python .codestable/tools/search-yaml.py --dir .codestable/features --filter tags~=llm --json
```

### 典型使用场景

| 场景 | 命令建议 |
|---|---|
| feature-design 开始前查 compound 已有沉淀 | `grep -r "{关键词}" .codestable/compound/` |
| issue-analyze 根因分析前查历史 | `grep -rl "{关键词}" .codestable/compound/` 再人工挑相关的看 |
| cs-keep 落盘前查重叠 | `grep -rl "{关键词}" .codestable/compound/`，命中就先看那条决定更新还是新写 |
| 找最久没 review 的库文档 / 指南 | `--dir {目录} --filter status=current --sort-by last_reviewed --order asc` |

---

## 2. validate-yaml.py

YAML 语法校验工具。用于验证 frontmatter 语法和必填字段。

```bash
# 校验单个文件的 YAML 语法
python3 .codestable/tools/validate-yaml.py --file {文件路径} --yaml-only

# 校验必填字段
python3 .codestable/tools/validate-yaml.py --file {文件路径} --require doc_type --require status

# 批量校验目录下所有文件
python3 .codestable/tools/validate-yaml.py --dir {目录} --require doc_type --require status
```

---

## 3. validate-implementation-review.py

实现完成门禁。用于 Stop hook 或手动检查：有实现代码变更时应在 linked worktree 内执行；已完成的 feature / issue / refactor 要有 `{slug}-review.md`，且默认必须声明 subagent reviewer。

```bash
python3 .codestable/tools/validate-implementation-review.py --root . --json
```

若用户明确要求直接在主 checkout 改代码，可临时显式 override：

```bash
CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION=1 python3 .codestable/tools/validate-implementation-review.py --root .

# 只有平台确实没有 subagent 能力时，才允许 self-review fallback
CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1 python3 .codestable/tools/validate-implementation-review.py --root .
```

配到 Codex / Claude Stop hook 时，可调用 `.codestable/tools/codestable-implementation-gate.sh`。

---

## 4. codestable-doctor.py

CodeStable 生命周期状态检查工具。只读，不修改文件。用于开始工作、恢复上下文、最终汇报前判断当前仓库是否还有阻塞项。

```bash
python3 .codestable/tools/codestable-doctor.py --root . --json
```

JSON 关键字段：

- `status`：`idle` / `planning-safe` / `dirty` / `implementation-active` / `attention-needed` / `blocked`
- `checkout`：当前分支、默认分支、是否 linked worktree
- `dirty_buckets`：按 `code` / `tests` / `docs` / `migrations` / `data` / `logs` / `codestable` / `unknown` 分组的 dirty paths
- `implementation_changes`：会触发 worktree 约束的实现文件
- `backlog`：`needs-human-review`、`Follow-up`、accepted/deferred P2、`attention.md` candidates 等待处理项；canonical lifecycle 文件里 `status: canceled/cancelled/abandoned` 的 feature / issue / refactor 单元会被当作历史记录跳过
- `post_baseline_blocks`：工作树干净但默认分支在 gate baseline 之后出现实现变更的阻塞项
- `findings`：按严重度列出的阻塞或待处理问题
- `next_action`：下一步建议

典型用法：

```bash
# 汇报前确认没有遗漏的人审 / follow-up / worktree 阻塞
python3 .codestable/tools/codestable-doctor.py --root . --json
```

---

## 5. codestable-worktree-gate.py

CodeStable worktree 生命周期门禁。用于实现开始前、提交前、以及误在协调检出开工后的恢复规划。

### start

实现开始前运行。feature / issue / refactor 这类实现单元必须在 linked execution worktree 中开始；如果用户明确批准在主检出中实现，单元目录下必须有 `worktree-override.md`，并写明 reason、scope、approval。

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-slug
```

通过后 gate 会把 baseline 写入 Git 私有路径，不污染工作树。

### commit

提交或最终汇报前运行。它会阻止：

- 默认分支上 staged implementation changes；
- 工作树干净但默认分支在 start baseline 后已经出现 implementation commits；
- 完成的 implementation unit 缺少 subagent implementation review。

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-slug
```

如果 staged 文件横跨 code / docs / data / logs / migrations 等多个 bucket，命令会给出 P2 warning；它不会替你 stage、unstage 或 commit。

### quarantine

误在主协调检出开始实现时，用 quarantine 先生成恢复计划。默认 dry-run，不创建分支、不创建 worktree、不移动文件、不改 index。

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json quarantine --unit .codestable/features/YYYY-MM-DD-slug
```

只有同时满足以下条件才允许创建 quarantine worktree：

- 显式传 `--apply`
- 单元目录存在带 reason / scope / approval 的 `worktree-override.md`
- 没有未跟踪的 `.env`、token、secret 等敏感文件

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json quarantine --unit .codestable/features/YYYY-MM-DD-slug --apply
```

Phase 1 只创建安全 execution worktree，不自动搬 dirty 文件；文件迁移仍由 owner 显式处理。

---

## 6. build-review-packet.py

独立 subagent review 的输入包生成器。它把本次 unit 文档、diff stat、聚焦 diff、验证结果和风险提示整理成一份可发给 reviewer 的 Markdown，并自动隐藏 `.env` / token / secret 类路径和值。`--stage` 用来区分 review 目的，默认 `implementation` 兼容旧调用。

```bash
python3 .codestable/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md \
  --validation "uv run pytest -> passed" \
  --validation "CLI smoke -> passed"
```

可选 stage：

- `implementation`：旧默认值，综合实现 review。
- `spec`：检查是否严格满足 requirement / report / analysis / design / checklist，重点抓缺失需求、额外行为和范围漂移。
- `quality`：检查可维护性、安全、边界条件、测试缺口、幂等和 crash-resume 等工程质量。
- `verification`：只看 fresh validation evidence；必须传 `--validation` 或 `--validation-file`，不能接受记忆里的“已跑过”。

适用时机：feature / issue / refactor 代码写完、owner 验证命令跑完之后，触发 subagent reviewer 之前。reviewer 只审查，不修改代码。review 结果仍要落到 `{slug}-review.md`，packet 只是输入材料。

输出内容：

- unit 下的 `.md` / `.yaml` 关键文档；
- unstaged / staged `git diff --stat`；
- 排除 secret-like 路径后的 focused diff；
- owner 传入的验证命令和结果；
- 数据库 / 迁移 / 并发 / 幂等 / crash-resume / provider cost / deterministic LLM boundary 风险提示。

---

## 7. Context / Finish / Commit Tools

For these tools, see `.codestable/reference/tools-context.md`:

- `build-context-packet.py`
- `check-context-sufficiency.py`
- `codestable-finish-worktree.py`
- `codestable-worktree-inbox.py`
- `plan-commits.py`
- `codestable-backlog.py`

Owner approval checkpoints are not context packets. When the owner must choose,
approve, authorize, accept risk, merge, deploy, or answer a grill / interview
decision, follow `.codestable/reference/approval-conventions.md` and write the
relevant unit's `approval-report.md`. Context packets may be supporting
evidence, not the approval surface.
