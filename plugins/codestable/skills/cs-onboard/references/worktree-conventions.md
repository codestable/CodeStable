# Worktree 与 Finish 约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/worktree-conventions.md`。
需要代码编辑、执行 worktree、commit gate、finish 或 handoff context 时读取。

## 主协调检出与执行 Worktree

CodeStable 把讨论 / 规划和代码编辑分开：

- 主协调检出：owner 讨论需求、编写 design / analysis / roadmap / checklist 的位置，通常是
  `main` 检出。
- 执行 worktree：代码改动发生的位置。每个 feature / issue / refactor 默认使用自己的
  git worktree 和类型化分支（`feat/{slug}` / `fix/{slug}` / `refactor/{slug}`），除非
  owner 明确批准在当前检出直接编辑。

Goal 可以用 `.codestable/goals/YYYY-MM-DD-{slug}` 包装；但代码编辑落入 feature / issue /
refactor 流程时，仍遵守对应 worktree 规则。

## 最短正确用法

1. Start：`cs {goal}`，路由到 feature / issue / refactor / explore / goal。
2. Implement：开执行 worktree，并运行 start gate。
3. Review：完成的代码批次经过独立 review。
4. Commit：运行验证、commit planner 和 commit gate。
5. Finish：运行 finish gate，记录 merge readiness。
6. 固化 finish 产物：提交生成的 finish report 文件。
7. Merge：只能在 owner 明确批准后执行。

## 共享规划表面

worktree 不能读取兄弟 worktree 尚未合并的代码 diff。共享意图只通过这些位置流转：

- `.codestable/goals/**`
- `.codestable/features/**`、`.codestable/issues/**`、`.codestable/refactors/**`
- `.codestable/roadmap/**`
- `.codestable/compound/**`
- owner-designated temporary coordination docs

如果执行 worktree 发现计划必须改变，要把计划变化同步回共享规划表面，或停下来交给 owner 判断。

## 创建执行 Worktree 前

先确认：

1. 当前检出是协调检出还是执行 worktree。
2. spec / checklist / analysis / goal state 可读。
3. worktree 路径、分支、范围和兄弟 worktree 边界清楚。
4. worktree 从目标 baseline 创建；除非明确采用 stacked development，不从另一个 feature
   worktree 创建。

实现前运行 start gate：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-{slug}
```

goal 包装的工作如果已有子 feature / issue / refactor unit，gate unit 指向子 unit。若 goal
还没有子 unit，在 goal iteration 中记录原因，并采用最轻的适用执行路径。

## Worktree 规则

- 只读取共享规划表面和本 worktree 的代码。
- 兄弟 worktree 的意图只有同步进共享文档后才能读取。
- 出现计划冲突时停下，交给 owner 判断。
- 缺 env / secrets 视为环境阻塞，不视为代码失败。

## 独立代码 Review

每个执行 worktree 在汇报一批实现完成前，必须触发独立 review。review 是完成 gate，不是
commit 前的事后补票。详细 review 流程由 `cs-code-review` 负责；需要输入包时运行：

```bash
python3 .codestable/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md --validation "{验证命令} -> {结果}"
```

不要包含 `.env`、token、secret 或本地凭证。reviewer 结果被核验并合并进报告后，按
`.codestable/reference/agent-conventions.md` 的 Task Agent 生命周期关闭。

## Context、Finish 与 Commit

context packet、finish gate、inbox、commit planner 和 backlog 工具的完整用法见
`.codestable/reference/tools-context.md`。常用命令：

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience handoff --output /tmp/codestable-handoff.md --decided "{已决定}" --remaining "{下一步}"
python3 .codestable/tools/check-context-sufficiency.py --file /tmp/codestable-human-review.md --strict --json
python3 .codestable/tools/codestable-finish-worktree.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --json --validation "{验证命令} -> {结果}"
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-{slug}
python3 .codestable/tools/codestable-doctor.py --root . --json
python3 .codestable/tools/codestable-backlog.py --root . --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --json
```

Finish gate 会写 learning、context-check、merge-readiness 和 inbox 记录。finish 报告后如果
分支变化，状态变为 `stale-report`，必须重跑 finish。
