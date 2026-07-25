# Close：关闭与沉淀

关闭 issue 或 epic，把仍成立的结论**毕业**到正确层级；Epic 关闭时检查来源 Vision 的实现状态与链接。

**关闭 ≠ 完成。** 完成指实现与验证已达成目标；关闭须用户授权收尾（“关闭 / 收尾 / 做完并沉淀”等）。Git 契约见下与 `SKILL.md`。

**关闭 ≠ 整理进 `done/`。** 关闭只做 `o`→`x` 与毕业回写；把已完成项挪到 `issues/done/` 或 `epics/done/` 仅在用户主动要求整理时进行（见 `SKILL.md`「完成 · 关闭 · done」）。

## 背景

复利在关闭时的回写：issue 留执行历史；epic spec 留活规格边界内的当前理解；project spec 留主线真相。回写层级见 `SKILL.md` 毕业规则与下文。

## 原则

**先确认可以关闭。** 目标达成、范围未暗扩、已选质量目标均有相称证据。Epic 必须由人确认关闭，不能因 issue 看起来都完成就自行关闭。

**只沉淀仍然有效的东西。** 不把事项全文搬进 spec；流水与中间判断留原事项。

**回写到正确层级。** 独立 issue → project spec；epic issue → epic spec；epic 关闭 → project spec 并检查 Vision。普通 issue 不更新 Vision。notes / Agent 指令 / tools 按复用价值分流。

**只按事实更新 Vision 状态。** 实现程度与链接可更新；目标内容或候选关系要变时须用户确认，否则记录偏差。

**spec 写当前为什么这样。** 不写“某天从 A 改到 B”的流水。

**只按承诺检查质量。** 不重开九项清单。关键遗漏 → 回 Design 补目标与响应，再 Do；不能在关闭结论里临时降级。见 [quality](quality.md)。

**有界简化必须仍有界。** 检查上限、触发未发生、未削弱目标与承诺。稳定产品边界 → spec；维护坑点 → notes；触发已发生且阻碍目标 → 回 Design/Do，不能以“后续再做”关闭。见 [economy](economy.md)。

**UI 按真相层级毕业。** 见 [ui-spec](ui-spec.md)。

**核心理解不引用代码。** 代码路径与命令留 issue/notes/证据索引。见 [docs](docs.md)。

**先守组织再写内容。** 从 `.cs/spec/index.md` 找路径；缺位置先补入口，不散落平级文件。

**探索文章按渐进式披露毕业。** 不是原样搬家；稳定现状机制说明按 Spec 结构安置。

## 行动指南

### 读取关闭上下文

- issue：用户给路径则读该文件/目录；否则在 `.cs/issues/` 按 `NNN-o-…` / 名称搜索
- epic：读权威 `spec.md`、明确引用的相邻材料与相关 issue

写入或暂存前确认目标事项、将回写的 spec/notes/Agent 指令/tools、以及要提交代码的当前版本。

### 关闭 issue

路径规则：把文件名或目录名中的 **`-o-` 改为 `-x-`**，保留 `NNN`、可选的 `ff`、名称不变。例如 `012-o-fix-login.md` → `012-x-fix-login.md`；`015-o-ff-toolbar.md` → `015-x-ff-toolbar.md`；Explore 目录 `003-o-auth-flow/` → `003-x-auth-flow/`。

- **普通 issue**：检查目标、范围、质量目标、执行记录与验证；有界简化则检查上限/触发/方向。缺记录或证据 → 回 Design/Do。
- **ff issue**：检查四节是否齐全（做了什么 / 改了哪些 / 验证 / 对 `.cs/` 的影响）。真相失效须已同步 spec 或明确标漂移；不要求完整质量清单与实现设计。同会话快改已直接落 `x-ff` 的，无需再关一次。
- **Explore issue**：不要求业务代码执行记录。须能讲清触发—过程—结果，相关责任/数据/状态有证据，未知显式标出；有具体变化时影响已分层。未达“足够行动” → 继续探索，不进 Do。

按 `epic` frontmatter / 归属回写：

- `type: ff`：默认不强制大段毕业；按「对 `.cs/` 的影响」执行或确认；坑点可进 notes
- `epic` 空且非 ff：稳定结论 → project spec
- `type: explore`：用户认可后，稳定现状机制说明 → `.cs/spec/` 并更新 `index.md`；影响分析留 `related_issue`；证据与已排除理解留 Explore issue；在 Explore `## 关闭回写` 记录迁入位置
- `epic` 有目录：结果、验证、仍有效约束、推进变化与毕业候选 → 该 epic `spec.md`

坑点 → notes；启动短规则 → `AGENTS.md` / `CLAUDE.md`；稳定工具 → tools。

### 关闭 epic

仅用户明确要求时。确认：关闭条件满足；epic 内直接推进已有足够验证；相关 issue 已关或明确废弃/移出；质量约束有证据或保留为后续约束；毕业候选足够稳定。

合并进 `.cs/spec/` 合适层级后，epic `spec.md` 标 `closed` 并记录合并位置；目录名 `-o-` → `-x-`（序号与名称不变）。有来源 Vision 则按事实更新实现程度与链接；改目标内容须确认。

### 提交关闭变更

若在 git 仓库：关闭结论与长期实体回写完成后，**相关变更同一 commit**（业务代码、目标 issue/epic、project/epic spec、notes/Agent 指令/tools）。

提交前 `git status --short`，只暂存相关文件。无关脏改不碰；同文件混有无关变更则停下说明。不 amend / rebase / reset；不 push，除非用户明确要求。

## 产物契约

关闭 issue：

- 更新 `## 关闭结论`（常规 issue）：判断、验证摘要（含质量证据）、回写位置、遗留事项；ff 以「对 `.cs/` 的影响」为准，可无长关闭结论
- `status: closed`；路径 `-o-` → `-x-`（序号与名称不变）

关闭 Explore issue：另更新 spec 阅读路径与 Explore `## 关闭回写`。

关闭 epic：

- `spec.md` 状态 `closed`；记录合并到 project spec 的位置与已检查/更新的 Vision
- 目录 `{NNN}-o-{名称}/` → `{NNN}-x-{名称}/`；不删除目录

遗留事项应成新 issue 或留在 epic 当前推进/阻碍中，不藏在关闭结论里；仅用户明确要求时建新 issue。

## 收尾汇报

先讲为何可关、质量证据、沉淀到哪一层、Epic 时如何同步或保留 Vision、是否已 commit。路径与 commit 作证据。

## 应用场景

实现验证完成后关闭 issue；Explore 经确认合并 project spec；bug/feature 关闭沉淀；用户确认后关 epic。

不适用：代码未完成 → Do；设计缺口 → Design；规格仍变 → Spec；默认不推送不部署。
