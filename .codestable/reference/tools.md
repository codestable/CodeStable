# CodeStable 工具用法参考

本文件由 `cs-onboard` 复制到项目的 `.codestable/reference/tools.md`，所有 CodeStable 子技能用项目相对路径 `.codestable/reference/tools.md` 引用。

当前 `cs-onboard` skill 包 `tools/` 下共享脚本的完整用法参考。子技能里只写本技能特有的 1-2 行典型查询；完整语法和示例看这里。

命令里的 `<cs-onboard skill 目录>` 是当前加载的 `cs-onboard/SKILL.md` 所在目录。新版 CodeStable 从这个全局 skill 包运行工具；旧项目已有 `.codestable/tools/` 只作兼容副本，不作为新版技能入口。

---

## 1. search-yaml.py

通用 YAML frontmatter 搜索工具。从项目根目录运行，无需安装额外依赖（PyYAML 可选，有则用，无则内建 fallback parser）。

### 基本语法

```bash
python3 <cs-onboard skill 目录>/tools/search-yaml.py --dir {目录} [--filter key=value]... [--query "全文关键词"] [--sort-by FIELD [--order asc|desc]] [--full] [--json]
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
python3 <cs-onboard skill 目录>/tools/search-yaml.py --dir .codestable/features --filter doc_type=feature-design --filter status=approved

# 按时间排序
python <cs-onboard skill 目录>/tools/search-yaml.py --dir .codestable/library-docs --sort-by last_reviewed --order asc
python <cs-onboard skill 目录>/tools/search-yaml.py --dir .codestable/guides --filter status=current --sort-by last_reviewed --order asc

# 输出控制
python <cs-onboard skill 目录>/tools/search-yaml.py --dir .codestable/features --filter status=approved --full
python <cs-onboard skill 目录>/tools/search-yaml.py --dir .codestable/features --filter tags~=llm --json
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
# 纯 YAML：checklist/items/goal-state 等逐文件校验
python3 <cs-onboard skill 目录>/tools/validate-yaml.py --file {文件路径}.yaml --yaml-only

# Markdown frontmatter：单文件或目录校验必填字段
python3 <cs-onboard skill 目录>/tools/validate-yaml.py --file {文件路径}.md --require doc_type --require status
python3 <cs-onboard skill 目录>/tools/validate-yaml.py --dir .codestable/features --require doc_type --require status
```

目录模式默认只校验 `.md` frontmatter；要批量校验纯 YAML 目录必须显式加 `--yaml-only`。不要对混有 checklist/items/goal-state 的目录直接加 `--require doc_type --require status`；纯 YAML 没有 Markdown frontmatter 字段，会造成假失败。

---

## 3. Roadmap Goal Gates

`cs-onboard` 会把技能包里的 `gates/` 释放到项目 `.codestable/`；gate 脚本从当前 `cs-onboard` skill 包的 `tools/` 目录运行。这些 gate 不是全局 PreToolUse 拦截器，而是由 `cs-epic` / `cs-feat` 等主入口在阶段边界显式调用。

```bash
python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py epic --roadmap .codestable/roadmap/{slug} --json
python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py feature --feature .codestable/features/YYYY-MM-DD-{slug} --epic-child-batch --json
python3 <cs-onboard skill 目录>/tools/validate-yaml.py --file .codestable/gates/roadmap-goal-gates.yaml --yaml-only
python3 <cs-onboard skill 目录>/tools/codestable-dod-contract-gate.py --design .codestable/features/YYYY-MM-DD-{slug}/{slug}-design.md
python3 <cs-onboard skill 目录>/tools/codestable-dod-runner.py --checklist .codestable/features/YYYY-MM-DD-{slug}/{slug}-checklist.yaml
python3 <cs-onboard skill 目录>/tools/codestable-evidence-pack.py --feature {slug} --design {design} --checklist {checklist} --out {slug}-evidence-pack.md
python3 <cs-onboard skill 目录>/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/{slug}
```

`roadmap-goal-gates.yaml` 是阶段配置入口；`codestable-scope-gate.py`、`codestable-dod-runner.py` 和 `codestable-evidence-pack.py` 是 implementation.before_review 的最小 runtime。`status: protocol-only` 的 gate 只表示协议占位，由 review / QA / acceptance / audit 技能读取证据后执行，不代表已有独立脚本。
`codestable-goal-consistency-gate.py` 是 roadmap_audit.before_complete 的 runtime，检查 goal-state、items、每个 feature 的 review/QA/acceptance/evidence/gate/DoD 产物和 checklist 状态，防止 goal-state 早于证据推进。
`codestable-workflow-next.py` 是只读下一步解析器，输出 `next_action`、`must_continue` 和 `final_answer_allowed`；`cs-epic` / `cs-feat` 在 child design batch 边界必须按它的 JSON 继续或停 gate。单 feature 按仓库事实恢复：feature goal-state 优先为 Goal；design 的完整 roadmap metadata 经 parent items 唯一证明，或被 parent items / roadmap goal-state 反向唯一认领的 child 交回 Epic；显式 feature 指针具有权威性，目录回退按精确 feature slug，多 claim 与错误 owner 结构/路径 fail-closed；ff-note 或 design 的 `execution_lane: quick` 恢复 Quick；旧 design 缺 lane 时恢复 Standard。Quick/Standard 的 passed review 必须有独立 reviewer 锚点，Quick 不得吞掉既有非 passed QA/acceptance；损坏的 YAML/frontmatter 或合法 YAML 中错误的路径/容器在 `--json` 下返回含具体路径的结构化 `blocked`，不得输出 traceback。
如果 skill 包缺少这些 runtime 脚本，说明本机 CodeStable 安装不完整；先更新 / 重装 CodeStable。项目缺少 `gates/` 或 `reference/` 时运行 runtime sync。

---

## 4. codestable-doctor.py

CodeStable 生命周期状态检查工具。只读，不修改文件。用于开始工作、恢复上下文、最终汇报前判断当前仓库是否还有阻塞项。

```bash
python3 <cs-onboard skill 目录>/tools/codestable-doctor.py --root . --json
```

JSON 关键字段：

- `status`：`idle` / `planning-safe` / `dirty` / `implementation-active` / `attention-needed` / `blocked`
- `tooling.runtime`：repo-local runtime 与 skill-global tool 静态体检；`version-mismatch` 时运行 runtime sync，`version-unavailable` 时先重装或更新 `cs-onboard`
- `tooling.runtime.capabilities`：`base` / `workflow-next` / `goal-gates` 的 `repo_paths`、`skill_tool_paths` 和缺失列表
- `checkout`：当前分支、默认分支
- `dirty_buckets`：按 `code` / `tests` / `docs` / `migrations` / `data` / `logs` / `codestable` / `unknown` 分组的 dirty paths
- `implementation_changes`：当前 dirty tree 中的实现文件
- `backlog`：`needs-human-review`、`Follow-up`、accepted/deferred P2、`attention.md` candidates 等待处理项；canonical lifecycle 文件里 `status: canceled/cancelled/abandoned` 的 feature / issue / refactor 单元会被当作历史记录跳过
- `findings`：按严重度列出的阻塞或待处理问题
- `next_action`：下一步建议

典型用法：

```bash
# 汇报前确认没有遗漏的人审 / follow-up / runtime 阻塞
python3 <cs-onboard skill 目录>/tools/codestable-doctor.py --root . --json
```

---

## 5. build-review-packet.py

独立 Task agent review 的输入包生成器。它把本次 unit 文档、diff stat、聚焦 diff、验证结果和风险提示整理成一份可发给 reviewer 的 Markdown，并自动隐藏 `.env` / token / secret 类路径和值。`--stage` 用来区分 review 目的，默认 `implementation` 兼容旧调用。

```bash
python3 <cs-onboard skill 目录>/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md \
  --validation "uv run pytest -> passed" \
  --validation "CLI smoke -> passed"
```

可选 stage：

- `implementation`：旧默认值，综合实现 review。
- `spec`：检查是否严格满足 requirement / report / analysis / design / checklist，重点抓缺失需求、额外行为和范围漂移。
- `quality`：检查可维护性、安全、边界条件、测试缺口、幂等和 crash-resume 等工程质量。
- `verification`：只看 fresh validation evidence；必须传 `--validation` 或 `--validation-file`，不能接受记忆里的“已跑过”。

适用时机：feature / issue / refactor 代码写完、owner 验证命令跑完之后，触发 Task agent reviewer 之前。reviewer 只审查，不修改代码。review 结果仍要落到 `{slug}-review.md`，packet 只是输入材料。

输出内容：

- unit 下的 `.md` / `.yaml` 关键文档；
- unstaged / staged `git diff --stat`；
- 排除 secret-like 路径后的 focused diff；
- owner 传入的验证命令和结果；
- 数据库 / 迁移 / 并发 / 幂等 / crash-resume / provider cost / deterministic LLM boundary 风险提示。

---

## 6. Context / Commit Tools

For these tools, see `.codestable/reference/tools-context.md`:

- `build-context-packet.py`
- `check-context-sufficiency.py`
- `plan-commits.py`
- `codestable-backlog.py`

Owner approval checkpoints are not context packets. When the owner must choose,
approve, authorize, accept risk, merge, deploy, or answer a grill / interview
decision, follow `.codestable/reference/approval-conventions.md` and write the
relevant unit's `approval-report.md`. Context packets may be supporting
evidence, not the approval surface.
