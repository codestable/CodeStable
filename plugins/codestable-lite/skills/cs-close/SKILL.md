---
name: cs-close
description: 关闭已实现验证或已确认探索结论的 issue，或人工确认完成的 epic，沉淀到 project/epic spec、notes、facts、tools，并在 git 仓库提交相关变更。触发：关闭 issue、关闭 epic、收尾、沉淀。
---

# cs-close

关闭 issue 或 epic，把这次工作里毕业的东西沉淀到正确层级。

## 背景

CodeStable 的复利不在事项本身，而在关闭时的回写。issue 记录一次执行历史；epic spec 记录一条大需求变更线的当前理解；project spec 记录项目主线真相。

独立 issue 关闭后，可以把稳定结论直接回写 project spec。探索型 issue 关闭时，把用户确认过的候选文章按 spec 规范合并进 project spec。epic issue 关闭后，先回写 epic spec。只有当用户确认整个 epic 完成，AI 才把 epic spec 中毕业的结论合并回 project spec。

## 原则

**先确认可以关闭。** issue 的目标必须达成，范围不能暗中扩大，验证结果要能支撑关闭。epic 必须由人确认关闭，不能由 AI 因为 issue 看起来都完成就自行关闭。

**只沉淀仍然有效的东西。** 不要把 issue 或 epic 全文搬进 spec。历史叙事、实现流水账、一次性中间判断留在原事项里。

**回写到正确层级。** 独立 issue → project spec；epic issue → epic spec；epic 关闭 → project spec。notes、facts、tools 按复用价值分流。

**spec 写当前为什么这样。** 合并 spec 时写需求、架构考量、统一语言、边界和取舍；不要写“某天从 A 改成 B”的流水。

**核心理解不引用代码。** 回写 spec 时只合并人能读懂的稳定结论。代码路径、命令结果和调查证据留在 issue、notes 或证据索引里，不要让 project spec 的正文变成代码导览。

**先守组织，再写内容。** 回写 project spec 时先从 `.cs/spec/index.md` 找阅读路径。缺少合适位置时，先补入口或子层索引，再写内容，不要散落平级文件。

**探索文章按 spec 规范毕业。** explore 工作区里的文章不是原样搬家。关闭时要按 `cs-spec` 调整为使用叙事、统一语言、树状入口和证据分层；再把文章放到合适目录，并更新对应 `index.md` 的阅读路径或结构落点。

## 行动指南

### 读取关闭上下文

必须先判断关闭对象：

- issue：用户给路径就读该文件或目录；没给路径就递归搜索 `.cs/issues/`。
- epic：用户给 `.cs/epics/YYYY/MM/DD/{短语}/`；读取 `index.md`、`spec.md`、`plan.md` 和相关 issue。

开始前复用当前上下文；目标 issue/epic、准备写回的 spec/notes/facts/tools、以及要提交的代码文件，写入或暂存前必须确认当前版本。

### 关闭 issue

检查目标、范围、执行记录和验证。缺少执行记录或验证时，回到 `cs-do`。

按 issue 的 `epic` frontmatter 或“归属”判断回写层级：

- `epic` 为空：把稳定需求、架构考量、统一语言或边界合并回 project spec。
- `type: explore`：读取工作区 `index.md` 和候选文章，先确认用户认可 `ready-for-spec` 的文章；再按 `cs-spec` 规范合并到 `.cs/spec/` 的合适层级，更新对应 `index.md` 引用。错误讨论、代码证据、证据流水、已排除理解和仍未知问题留在 issue 工作区。
- `epic` 指向目录：把完成结果、验证事实、影响到的本轮计划和合并候选写回该 epic 的 `spec.md` / `plan.md`。

再把坑点、操作经验、调试路径写入 notes；极少数启动必读事实写入 facts；稳定工具说明写入 tools。

### 关闭 epic

只在用户明确要求关闭 epic 时执行。先确认：

- `index.md` 的关闭条件已满足。
- 相关 issue 都已关闭，或未关闭 issue 已明确废弃/移出。
- `spec.md` 中“合并回 project spec 的候选”已经足够稳定。

然后把 epic spec 中毕业的需求、架构考量、统一语言、边界和取舍合并回 `.cs/spec/` 的合适层级。合并后更新 epic `index.md` 状态为 closed，并记录合并位置。

### 提交关闭变更

如果项目在 git 仓库里，关闭结论和长期实体回写完成后，把本次关闭相关变更提交在同一个 commit 里：业务代码、目标 issue/epic、project/epic spec、notes/facts/tools 回写都一起提交。

提交前看 `git status --short`，只暂存相关文件。已有无关脏改不要碰；相关和无关变更混在同一文件时，停下来说明风险。不要 amend、rebase、reset；不要 push，除非用户明确要求。

## 产物契约

关闭 issue 时：

- 更新 `## 关闭结论`：关闭判断、验证摘要、回写位置、遗留事项。
- frontmatter 的 `status` 改为 `closed`。
- 普通 issue 文件名改成 `.cs/issues/YYYY/MM/DD/closed-{短语}.md`；探索型 issue 目录名改成 `.cs/issues/YYYY/MM/DD/closed-{短语}/`。

关闭探索型 issue 时还要：

- 把确认过的候选文章合并或迁移到 `.cs/spec/`，必要时改写标题、章节和证据索引以符合 `cs-spec`。
- 更新目标层级的 `index.md`，让新文章进入使用路径、能力地图或结构落点。
- 在 explore `index.md` 的 `## 关闭回写` 记录迁入的 spec 文章、更新的 spec index、留在 issue 的材料。

关闭 epic 时：

- 更新 epic `index.md` 的当前状态为 `closed`。
- 在 epic `index.md` 或 `spec.md` 记录已合并到 project spec 的位置。
- 不删除 epic 目录；它保留变更线历史。

遗留事项应该成为新 issue 或留在 epic `plan.md`，不要藏在关闭结论里；只有用户明确要求时才创建新 issue。

## 收尾汇报

先讲关闭结论：为什么可以关、验证支撑是什么、沉淀到了 project spec 还是 epic spec、是否已提交。涉及 spec 时，要说明更新了哪个入口/子层，以及这样放的组织理由。最后给路径和 commit 作为证据。

## 应用场景

实现和验证完成后关闭 issue；探索型 issue 经用户确认后合并 project spec；bug 修完后沉淀稳定预期；feature 完成后回写边界和取舍；用户确认大 epic 完成后，把 epic spec 合并回 project spec。

不适用：代码没完成回 `cs-do`；设计缺口回 `cs-design`；规格仍在变化回 `cs-spec`；默认不推送、不部署，除非用户明确要求。
