# Independent Review Protocol

code review 是**双环节 review**，两个环节互补：

| 环节 | 目的 | 是否 gate 必需 |
|---|---|---|
| A 独立 Task agent review | spec 视角整体审查，用独立上下文避免主 agent 确认偏误 | 是（gate 放行靠它） |
| B OCR 行级扫描 | 行级 bug / 安全 / 代码模式扫描，补 A 的盲区 | 否（装了就跑，缺了降级） |

检测由主 agent 在运行时自检自己的工具，不靠脚本猜环境。主 agent 最清楚自己手上有哪些工具。

---

## 环节 A：独立 Task agent review（gate 必需）

主 agent 按 Task agent 选择规则启动独立 reviewer（优先 Paseo subagent，否则当前宿主原生 Codex/Claude Task/Agent；都不可用时按 local-only fallback 处理）：

1. **有 `mcp__paseo__create_agent` 工具** → 用 Paseo subagent（首选：能换 provider，做到真正异构审查）。
   先加载 / 读取 `paseo` skill 的当前说明并遵守其规则：读取 `~/.paseo/orchestration-preferences.json`，使用 `providers.audit`，不要硬编码 provider；文件缺失时用合理默认并在报告说明。
2. **否则有当前宿主原生 Codex/Claude Task/Agent 工具** → 启动原生 Task agent。独立上下文同样达成；若同模型，在报告里记录降级和残余风险。
3. **两者都没有** → 记 `local-only`，不能伪装启动。gate 默认不放行，需用户明确降级（见 `reviewer` 字段）。

独立 Task agent reviewer prompt（只给原始材料，不透露主 agent 的任何 review 结论）：

```text
你是 CodeStable 本次改动的独立代码审查 agent。只读，不修改文件，不更新 checklist/design。

请读取：
- .codestable/attention.md
- {design_path}
- {checklist_path}
- {evidence_pack_path}、{gate_results_path}、{dod_results_path}（存在时）
- 当前 git status / git diff / staged diff
- diff 涉及的人写代码和相邻关键调用点

按严重度输出：blocking / important / nit / suggestion / learning / praise / residual-risk。
每条 finding 必须有 file:line 或仓库事实证据、影响、建议修复边界。
执行一次对抗式审查：假设本次实现里一定藏着一个生产 bug，主动构造反例，优先攻击 design 不一致、边界值、错误路径、状态转换、并发/时序、权限/数据隔离、持久化/回滚和测试假阳性。
额外输出 Test And QA Focus：QA 必须重点复核的场景、建议新增或加强的测试、review 无法确认的点。
不要写 {slug}-review.md；只把审查结果回传给主 agent。
```

---

## 环节 B：OCR 行级扫描（装了就跑）

主 agent 自检 `ocr` CLI 是否可用：

```bash
which ocr && ocr llm test
```

可用则自动调用（不需要用户显式要求），用 `--background` 传入 spec 摘要提升质量：

```bash
ocr review --audience agent --background "{feature slug / 目标 / 本次改动范围}"
```

**OCR 只能审本轮 scope，不能用裸 workspace 模式发现 scope。**`ocr review` 默认会审 staged + unstaged + untracked；Roadmap 多 feature 连续执行时，历史 dirty/untracked 会让 OCR 越扫越大。调用规则：

1. 先建立 `current_scope_files`：优先取 scope-gate / evidence pack 的 `changed_files`，否则取 `{feature-base}..HEAD` 或实现汇报中的本轮文件。
2. 已提交 diff → 用 `ocr review --audience agent --from {feature-base} --to HEAD`。
3. 未提交 diff → 只有 `git status --short` 的所有非 ignored 路径都属于 `current_scope_files`，才可裸跑 `ocr review`；否则记 `skipped-scope-ambiguous`，改为本地行级审查 `current_scope_files`。
4. 合并 OCR finding 前，**丢弃**命中以下路径的 finding，无论 OCR 是否扫到：
   - `.codestable/`（CodeStable 自己的 spec / 工具产物，永远不是行级代码审查对象）
   - 任何 `.` 开头的目录（`.git/`、`.claude/`、`.venv/` 等）
   - `.gitignore` 命中的文件（`git check-ignore <path>` 为真）
   未被 `.gitignore` 忽略、且属于 `current_scope_files` 的 untracked 新增文件必须被本轮 review 覆盖。

OCR 的 High / Medium / Low 映射到 cs-code-review 严重度后合并：

| OCR 优先级 | 映射规则 |
|---|---|
| High | 有仓库事实支撑 → `blocking`/`important`；证据不足 → `residual-risk` |
| Medium | `nit` 或 `suggestion` |
| Low | 丢弃（视为噪音），不进入报告 |

OCR 不做 spec-fit 判断；mapping 后的 finding 必须经主 agent 本地事实核验才能升级为 `blocking`。`ocr` 未安装 / `ocr llm test` 失败 → 记 `not-available`，提示用户走 `cs-onboard` 的 open-code-review 段安装并配置；不阻塞本轮。注意 `ocr llm test` 超时（`context deadline exceeded`）多半是配置用了旧 `llm.*` 块：ocr v1.x 需用 `provider`/`providers` 体系，详见 onboard 段或 `codestable-doctor.py` 的 OCR 体检。

---

## 合并与 reviewer 字段

A、B 两环节可并行启动。一旦某环节已启动，主 agent **不能在其返回前定稿 `{slug}-review.md`、给出 `passed` 或进入通过后去向**。

- 已启动的 reviewer 返回 → 逐条本地事实核验，去重，合并进报告，保留来源标注（`paseo` / `native-agent` / `ocr` / `local`）。
- reviewer 失败 / 卡住 / 权限阻塞 → 报告 `status: blocked`，记录 `pending|failed|blocked` 和原因，让用户决定：重试、等待或明确降级。
- 不要无限轮询；等通知或用户带回结果。
- 环节 A reviewer 结果被核验并合并进报告后，按 `.codestable/reference/execution-conventions.md`
  的 Task agent 生命周期关闭该 reviewer。遇到 `agent thread limit reached` 等容量失败时，
  只在失败后按最老已完成 agent 清理并重试一次。

未经本地仓库事实核验的外部结论只能写 `residual-risk` 或忽略，不能直接升级为 `blocking`。

`reviewer` 字段按本轮实际完成的环节写：

| 值 | 含义 | gate |
|---|---|---|
| `subagent+ocr` | 环节 A（Task agent）+ 环节 B 都完成（理想） | 放行 |
| `subagent` | 环节 A 完成，OCR 不可用 / 跳过 | 放行 |
| `ocr` | 仅 OCR，缺 Task agent review | 需 override |
| `self` | 两环节都缺 | 需 override |

gate 默认要求 `subagent` 或 `subagent+ocr`；`ocr` 和 `self` 需配 `CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1` 才放行。OCR 不能替代环节 A：目的不同（A 是 spec 隔离审查，B 是行级扫描）。
