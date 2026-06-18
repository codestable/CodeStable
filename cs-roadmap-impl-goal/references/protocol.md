# CodeStable Roadmap Goal 执行协议

本文件复制到 `.codestable/roadmap/{slug}/goal-protocol.md` 后，由 `/goal` 会话读取。它描述如何按一个已确认的 roadmap 执行包，逐个完成 feature 的实现、代码审查与验收。

## 先读文件

进入 goal 会话后先读取：

- `.codestable/roadmap/{slug}/goal-state.yaml`
- `.codestable/roadmap/{slug}/goal-plan.md`
- `.codestable/roadmap/{slug}/{slug}-roadmap.md`
- `.codestable/roadmap/{slug}/{slug}-items.yaml`
- `.codestable/roadmap/{slug}/goal-features/*.md`

`goal-state.yaml` 是断点恢复唯一依据。每个 feature 边界都要更新它。

开始执行前确认所有 feature design 的 frontmatter 都是 `status: approved`。发现 draft design 时停止，要求回到 design review 确认阶段；不要把未批准设计推进到实现。

---

## 启动标记

打印：

```text
CS_ROADMAP_GOAL_START
Roadmap: <slug>
Features: <数量>
Baseline ref: <sha|no-git>
Plan: .codestable/roadmap/<slug>/goal-plan.md
Protocol: .codestable/roadmap/<slug>/goal-protocol.md
```

然后做预检：

1. 汇总所有 goal-features 中的必跑命令。
2. 成本可接受时先跑一遍。
3. 记录每条命令 green / red。
4. red 时判断：既有问题 / 阻塞问题 / 无法归因。
5. 阻塞或无法归因时不要盲目继续；如果 roadmap 明确有 safety net feature，则先执行对应 feature，否则交还用户。

---

## Feature 循环

按 `goal-state.yaml` 的 features 顺序循环。

### 1. 进入 feature

读取：

- goal-features/{feature-slug}.md
- feature design
- feature checklist
- roadmap item
- 当前代码上下文

进入实现前核验：

- feature design `status: approved`
- checklist `steps` 非空且未完成项只使用 `pending`
- checklist `checks` 非空且验收前只使用 `pending`
- roadmap item 与 goal-state 中的 `roadmap_item` / `feature_dir` 一致

把当前 feature 状态改为 `implementing`，然后打印：

```text
CS_ROADMAP_GOAL_FEATURE_START
Feature: <N>/<总数> <slug>
Design: <路径>
Checklist: <路径>
Depends on: <依赖|none>
Mandatory commands: <命令列表>
Evidence required: <证据列表>
```

### 2. 执行 cs-feat-impl

按 `cs-feat-impl` 规则执行：

- 做基线预检。
- 按 checklist steps 顺序执行。
- 每步完成立刻把对应 step 的状态从 `pending` 改为 `done`。
- 实现阶段不要修改 `checks`；checks 只由 acceptance 阶段从 `pending` 改为 `passed` 或 `failed`。
- 每步留下证据：命令 / 手工 / 浏览器 / API / diff。
- 每步做清洁度检查。
- 失败时走本文“失败恢复”。

### 3. 执行 cs-feat-review

按 `cs-feat-review` 规则执行：

- 读取 design、checklist、实现证据、`git status --short`、`git diff` 和相关代码。
- 只读审查；不要在 review 阶段直接修代码。
- 写 `{feature-slug}-review.md`。
- 输出 blocking / important / nit / suggestion / learning / praise / residual-risk 分级。
- 把 review 的 Test And QA Focus 留给 acceptance 复核。

如果有 blocking findings，打印：

```text
CS_ROADMAP_GOAL_REVIEW_FIX
Feature: <slug>
Findings: <REV 编号列表>
Next: cs-feat-impl review-fix then rerun cs-feat-review
```

然后按 `cs-feat-impl` 的 review-fix 模式只修 blocking findings，修完回到本节重跑 `cs-feat-review`。review 未 passed 时不能进入 acceptance。

### 4. 执行 cs-feat-accept

按 `cs-feat-accept` 规则执行：

- 先确认 `{feature-slug}-review.md` 存在、`status=passed`，且没有 unresolved blocking findings。
- 填 acceptance 报告。
- 把 checklist checks 从 `pending` 更新为 `passed`；失败项先标 `failed`，修复并重验后再改 `passed`。
- 更新 checklist 时只改目标 `steps` 或 `checks` 块，避免用全文件批量替换把 `steps.status` 和 `checks.status` 混在一起。
- 按 design 第 4 节更新 architecture。
- 按 requirement 字段回写 requirement。
- 按 roadmap / roadmap_item 回写 items.yaml 和 roadmap 主文档。
- 做 feature 级最终审计。

### 5. Feature 验证标记

打印：

```text
CS_ROADMAP_GOAL_FEATURE_VERIFY
Feature: <slug>
Implementation: pass|fail
Review: pass|fail
Acceptance: pass|fail
Commands: <命令退出码摘要>
Deliverables: <present|missing 摘要>
Cleanliness: pass|fail
Roadmap item: done|not-done
Knowledge candidates: <候选|none>
```

全部通过后：

1. 把 goal-state 当前 feature 状态改为 `accepted`。
2. 把 current_feature 指向下一条。
3. 确认 feature review 报告存在且 `status=passed`，没有 unresolved blocking findings。
4. 确认 feature checklist 中所有 steps 都是 `done`、所有 checks 都是 `passed`。
5. 打印：

```text
CS_ROADMAP_GOAL_FEATURE_DONE
Feature <slug> accepted. State updated.
```

如果用户中途发新消息，在 feature 边界停下，询问是继续、修改后续 feature specs，还是停止。

---

## 失败恢复

适用于实现标准、review blocking 修复、验收 checks、必跑命令、交付物、清洁度。

### 第一次失败：诊断并重试

打印：

```text
CS_ROADMAP_GOAL_FAILURE_DIAGNOSE
Feature: <slug>
Failed item: <失败项>
Tried: <已尝试>
Hypothesis: <根因假设>
Next: retry same item once
```

只重试失败项，不推进下一步。

### 第二次失败：窄范围修复说明

写：

```text
.codestable/roadmap/{slug}/goal-features/{feature-slug}-repair.md
```

内容包含：

- 失败项
- 根因
- 允许修改的文件 / 文档
- 必跑验证
- 禁止扩大范围

执行这份修复说明，然后回到原检查项重验。

### 第三次失败：交还用户

打印：

```text
CS_ROADMAP_GOAL_HANDOFF
Feature: <slug>
Failed item: <失败项>
Attempts: <三次尝试摘要>
Suggested next move: <建议>
State: blocked
```

把 goal-state 改为 `blocked`，停止。不要打印完成。

---

## 清洁度检查

每个 feature 都检查完整工作区（有 baseline_ref 就看相对 baseline 的变化，否则看当前 diff）：

- 新增调试输出：`console.log` / `print` / `fmt.Println` / 临时 logger
- 新增临时 `TODO` / `FIXME` / `XXX`
- 注释掉的代码
- 未使用 import
- 超出本 feature 范围的文件改动

未解释命中 = 验证失败。确实是功能本身需要的日志 / debug 能力，必须在 design 或 goal-feature spec 中写明例外范围。

---

## 知识回写候选

每个 feature accept 后，列出但不要擅自写入：

- 环境 / 命令 / 工作流事实 → `cs-note`
- 可复用坑点 / 调试经验 → `cs-learn`
- 稳定 convention / 架构决定 → `cs-decide`
- 用户或开发指南变化 → `cs-guide`
- 公开 API / 组件 / 命令参考变化 → `cs-libdoc`

architecture / requirement / roadmap 回写是 acceptance 必做动作，不需要额外征求；其他知识沉淀按用户确认执行。

---

## 最终 Roadmap 审计

最后一个 feature accepted 后，不能直接完成。先打印：

```text
CS_ROADMAP_GOAL_AUDIT_START
Roadmap: <slug>
Features to verify: <数量>
Commands to re-run: <去重命令列表>
```

审计步骤：

1. 重读 roadmap 主文档和 items.yaml。
2. 确认每个 item 都是 `done`，或有理由 `dropped`。
3. 重读每个 feature 的 design / checklist / review / acceptance。
4. 去重重跑必跑命令（成本过高时说明跳过原因）。
5. 从仓库事实核验交付物：文件、配置 key、schema、路由、文档、roadmap 状态。
6. 检查完整工作区：tracked / staged / unstaged / untracked。
7. 检查全 run 清洁度。
8. 统计 `re-verified` 和 `trust-prior-verify`；截图 / 手工项不能重跑时记为 trust-prior。
9. 确认每个 review 报告都 passed，且没有 unresolved blocking findings。
10. 确认 architecture / requirement / roadmap 回写存在。
11. 确认知识候选已处理、明确延后或列给用户。
12. 做 learning reflection：从整个 goal 的失败恢复、最终审计补强、设计/实现/review 反复、跨 feature 约束中筛选可复用经验。

打印：

```text
CS_ROADMAP_GOAL_AUDIT_VERIFY
Roadmap items: <done>/<total>
Commands: <摘要>
Deliverables: <present>/<total> present
Cleanliness: pass|fail
Writebacks: pass|fail
Knowledge exits: handled|deferred|none
Coverage: <re-verified> re-verified / <trust-prior> trust-prior
```

如果有缺口：

1. 写 `.codestable/roadmap/{slug}/audit-repair-<round>.md`。
2. 只修审计失败项，不扩大范围。
3. 重跑审计。
4. 三轮仍失败则打印 `CS_ROADMAP_GOAL_HANDOFF`，把 state 改为 `blocked`，停止。

如果无缺口：

先打印 learning reflection，不直接写知识库：

```text
CS_ROADMAP_GOAL_LEARNING_REVIEW
Pitfall candidates:
- <候选|none>
Knowledge candidates:
- <候选|none>
Not worth archiving:
- <一次性上下文|none>
Recommended next step: <run cs-learn after user confirmation|none>
```

筛选规则：

- pitfall：失败恢复、误判、测试假设、环境/工具坑，后续任务可能重复踩。
- knowledge：更好的默认做法、工作流改进、可复用设计/验证模式。
- not worth archiving：只属于本次业务、不会复用、已被 architecture / requirement / roadmap 回写覆盖的事实。
- 有候选时只建议用户确认后运行 `cs-learn`；不要自动创建或修改 `.codestable/compound/`。

```text
CS_ROADMAP_GOAL_AUDIT_COMPLETE
Roadmap: <slug>
Audit rounds: <轮数>
Coverage: <re-verified> re-verified / <trust-prior> trust-prior
```

然后打印：

```text
CS_ROADMAP_GOAL_COMPLETE
Roadmap <slug> complete.
Features accepted: <数量>
Final audit passed.
Manual follow-up: <事项|none>
```

只有 `CS_ROADMAP_GOAL_COMPLETE` 出现，`/goal` 才算满足。
