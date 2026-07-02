# 执行约定

本文件会由 `cs-onboard` 复制到
`.codestable/reference/execution-conventions.md`。它负责共享的执行、
worktree、review、finish 和 handoff 规则。

## CodeStable Preflight

任何 CodeStable skill 在判断或动作前先执行 preflight：

1. 读取 `.codestable/attention.md`。
2. 缺 `.codestable/attention.md` 时视为骨架不完整，提示补齐或运行 `cs-onboard`。
3. 不回退读取 `AGENTS.md` / `CLAUDE.md` / `.cursorrules` 等外部 AI 入口文件。
4. 正文报告语言按 `.codestable/attention.md` 的报告语言策略执行；默认中文，若草稿用了英文，落盘前先改写为项目语言。frontmatter / yaml 字段不翻译。

`cs-note` 是唯一例外：`.codestable/` 存在但 `attention.md` 缺失时，它可以创建最小分节骨架后写入。

## 主协调检出与执行 worktree

CodeStable 把讨论 / 规划和代码编辑分开：

- **主协调检出**：owner 讨论需求、编写 design / analysis / roadmap / checklist
  的位置，通常是 `main` 检出。
- **执行 worktree**：代码改动发生的位置。每个 feature / issue / refactor
  默认使用自己的 git worktree 和类型化分支（`feat/{slug}` / `fix/{slug}` /
  `refactor/{slug}`），除非 owner 明确批准在当前检出直接编辑。

Goal 工作可以用 `.codestable/goals/YYYY-MM-DD-{slug}` 作为包装单元；但只要
代码编辑落入 feature / issue / refactor 流程，仍必须遵守对应 worktree 规则。

## 最短正确用法

1. Start：`cs {goal}`。agent 路由到 feature / issue / refactor / explore /
   goal。
2. Implement：`开 worktree 实现`。agent 进入执行 worktree 并运行 start gate。
3. Review：`允许 Task agent`。完成的代码批次必须经过独立 review。
4. Commit：`提交这批实现`。运行验证、commit planner 和 commit gate。
5. Finish：`finish worktree`。运行 finish gate 并记录 merge readiness。
6. 固化 finish 产物：提交生成的 finish report 文件。
7. Merge：只能在 owner 明确批准后执行。

## 共享规划表面

worktree 不能读取兄弟 worktree 尚未合并的代码 diff。共享意图只通过以下位置流转：

- `.codestable/goals/**`
- `.codestable/features/**`, `.codestable/issues/**`, `.codestable/refactors/**`
- `.codestable/roadmap/**`
- `.codestable/compound/**`
- owner-designated temporary coordination docs

如果执行 worktree 发现计划必须改变，要把计划变化同步回共享规划表面，或停下来交给
owner 判断。

## 创建执行 worktree 前

先确认：

1. 当前检出是协调检出还是执行 worktree；
2. spec / checklist / analysis / goal state 可读；
3. worktree 路径、分支、范围和兄弟 worktree 边界清楚；
4. worktree 从目标 baseline 创建，而不是从另一个 feature worktree 创建，除非明确采用
   stacked development。

实现前运行 start gate：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-{slug}
```

goal 包装的工作如果已有子 feature / issue / refactor unit，gate unit 应指向子
unit。若 goal 还没有子 unit，在 goal iteration 中记录原因，并采用最轻的适用执行路径。

## Worktree 规则

- 只读取共享规划表面和本 worktree 的代码。
- 兄弟 worktree 的意图只有同步进共享文档后才能读取。
- 出现计划冲突时停下，交给 owner 判断。
- 缺 env / secrets 视为环境阻塞，不视为代码失败。

## Task agent 选择规则

`Task agent` 指为隔离 review、QA、audit 或功能验收而启动的工作 agent。选择顺序：
优先使用 Paseo subagent（在 Paseo 内运行，或存在 `mcp__paseo__create_agent`
工具时）；否则使用当前宿主平台的原生 Codex/Claude Task/Agent 能力。两者都不可用或
未获授权时，记录限制，并按该 gate 的显式 fallback / owner-stop 路径处理。

凡涉及只读独立审查、QA runner、acceptance auditor 或实现协作时，统一按这条规则启动。
不要把主 agent 的结论泄露进 Task agent prompt。只提供原始产物、审查范围和期望输出。
主 agent 仍负责核验返回 findings，并负责所有最终状态写入。

对 review gate（roadmap-review、feature design-review、implementation code-review），
Task agent 可用时必须启动。批量处理、赶时间、主 agent 已做本地 review 或认为风险低，
都不是 local-only 降级理由。local-only 只在确无 Task agent 能力、provider 不可用且无法
配置，或 owner 明确批准降级时有效；否则报告 `blocked` / `independent-review-pending`，
不要写 `passed`。

## Goal driver 派发

`Goal driver` 指启动一个可见 Task agent 执行已经生成、已经过用户 gate 的 goal 包。它不是
reviewer，不批准 design；它只按 goal 包里的协议执行 implementation / review / QA /
acceptance，并把证据写回仓库。

启动前置：

- goal 包已落盘，且包含 goal-plan / goal-state / goal-protocol / 可粘贴 `/goal` 指令。
- 用户已经确认对应 design gate：单 feature 是 feature design，epic 是 roadmap 和全部子
  feature design。
- 当前工作区基线可追踪；goal-state 记录 baseline，协议写明完成 / handoff 标记。

选择顺序：

1. **Paseo subagent**：首选。Paseo 有 agent id、activity、status、permission 和 cancel
   表面，用户能看见并接管长程执行。
2. **宿主原生 Task/Agent**：只有同时满足下面两条才可用：
   - 宿主显式暴露用户可见的 run id / 状态 / 日志 / 取消或最终 transcript，且主 agent
     能告诉用户如何查看。
   - 宿主显式支持 driver 在其运行环境内再启动独立 Task agent reviewer；review gate
     必须能跑，不能靠 driver 自审。

   任一条不能确认时，不要猜测可用；不要用原生子 agent 当 driver，直接回退打印 `/goal`，
   避免 driver 在第一个 review gate 就 handoff。
3. **不可见或派发失败**：不要静默后台运行。打印 fenced `/goal` 指令，让用户粘贴到新的
   agent 会话执行，并说明没有自动 driver 在跑。

派发 prompt 只给 goal 包路径、协议文件和完成 / handoff 标记，不塞主 agent 的本地推断。
主 agent 不能因为 driver 已启动就宣称 goal 完成；完成只能由 goal 产物和 transcript 标记证明。

派发成功后立即把 driver 形态与标识写回对应 goal-state.yaml（`driver_kind: paseo|native`、
`driver_id`）。重入（用户再次调用主入口）时先读 goal-state：状态为 running 且该 driver
仍可见时，汇报进度和查看方式，不重复派发；driver 已不可见时，以仓库事实修正 state，
再续跑或重派，并把新 driver 标识写回。

## 独立代码 review

每个执行 worktree 在汇报一批实现完成前，必须触发独立 review。review 是完成 gate，
不是 commit 前的事后补票。

如果当前对话没有 Task agent / delegation 授权，implementation review 前要在相关 unit
写 `approval-report.md`。报告必须包含这些审批上下文字段：

```markdown
Context: CodeStable 要求实现完成前经过独立 implementation review。
Term: Task agent review = 单独的 Task agent 执行只读 review。
Why it matters: 否则 P0/P1 问题可能在完成后才暴露。
Options:
1. Task agent review（推荐）- 完成前启动 reviewer。
2. Inline review - 仅当平台没有 Task agent 能力时有效。
Default: Task agent review.
Non-automatic: 这不会自动 commit、merge、push 或接受 finding。
Question: CodeStable 应使用哪种 review 授权？
```

生成尽量小但有用的 review packet：

```bash
python3 .codestable/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md --validation "{验证命令} -> {结果}"
```

不要包含 `.env`、token、secret 或本地凭证。

风险默认值：

- 极小文档 / typo：owner self-check 足够。
- 小型局部代码：一次 quality review。
- 普通 feature / fix：quality review + owner evidence；scope 可能漂移时加 spec review。
- schema / security / core runtime：spec、quality、verification review。
- 大型多模块工作：分阶段执行，并写 handoff context。

review 结果写入 `{slug}-review.md`，frontmatter 使用 `reviewer: subagent` 或
`reviewer: subagent+ocr`。只有平台确实没有 Task agent 能力且设置
`CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1` 时，才使用 `reviewer: ocr` / `self`。
即使具体 Task agent 是 Paseo、Codex 或 Claude，也必须保留这些 frontmatter 值以兼容 gate。

## Context Packets

多阶段 handoff：

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience handoff --output /tmp/codestable-handoff.md --decided "{已决定}" --remaining "{下一步}"
```

面向人的报告：

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience human-reviewer --language {en-or-zh} --output /tmp/codestable-human-review.md --decided "{decided}" --remaining "{next step}" --evidence "{verification evidence}"
```

根据 `.codestable/attention.md` 映射出工具支持的 `{en-or-zh}`。如果项目报告语言不在
工具 `--language` 选项内，就用项目语言改写或适配面向人的报告，不要把 attention 原文
当 CLI 值传入。

发送前运行 sufficiency gate：

```bash
python3 .codestable/tools/check-context-sufficiency.py --file /tmp/codestable-human-review.md --strict --json
```

## Finish 与 Commit Gates

finish / merge 前：

```bash
python3 .codestable/tools/codestable-finish-worktree.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --json --validation "{验证命令} -> {结果}"
```

Finish gate 会写 learning、context-check、merge-readiness 和 inbox 记录。finish
报告后如果分支变化，状态变为 `stale-report`，必须重跑 finish。

gate 通过后，把 finish 产物作为一个小的最终 commit 提交：

```bash
git add .codestable/features/YYYY-MM-DD-{slug}/{slug}-learning-report.md \
  .codestable/features/YYYY-MM-DD-{slug}/{slug}-learning-context-check.json \
  .codestable/features/YYYY-MM-DD-{slug}/{slug}-merge-readiness.json
git commit -m "docs: add {slug} finish report"
```

commit 或最终汇报前：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-{slug}
```

常用状态工具：

```bash
python3 .codestable/tools/codestable-doctor.py --root . --json
python3 .codestable/tools/codestable-backlog.py --root . --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --json
```

延后已接受的 merge 提醒：

```bash
python3 .codestable/tools/codestable-worktree-inbox.py --root . --snooze codex_slug --until 2026-06-12T00:00:00Z --json
```

## Task agent 实现选择

review 在 Task agent 可用时必须使用。implementation Task agent 是可选项；当工作跨越
三个以上子系统、需要并行切片、触及高风险 migration / concurrency / runtime contract，
或超过单线程上下文容量时，应主动提出。主线程保留集成、验证和最终 review 责任。
