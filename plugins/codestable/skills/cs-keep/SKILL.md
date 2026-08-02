---
name: cs-keep
description: 管理有证据的项目事实、lesson 生命周期与 canonical 归宿。触发：记录踩坑、教训、调研结论、纠偏，或用户说"记住这个"。
argument-hint: "[要沉淀的内容]"
---

# cs-keep

把这次学到的东西沉淀成下次能被检索到的项目记忆。落点由你判断，不追问用户分类。

## 开工与授权

- 有 `.codestable/attention.md` 就先读；写前检索 `.codestable/lessons/` 与 v1 只读
  `.codestable/compound/`，核实证据、scope、重复项与已有 canonical owner。
- 用户明确要求“记住 / 更新 / 退役”、接受普通 owning task 给出的晶化候选，或在 Epic 最终毕业
  gate 批准候选，就是本次精确内容的写入授权，不追问分类。新建、改写规则/scope、晋升、删除或
  跨项目分享仍需用户显式授权，不能从历史操作或“这可能有用”推断。
- 没有可追溯证据不写；不编造，不从模型记忆、命中次数或自评置信度泛化。

## 落点判断

按单一 owner 和以下顺序路由：

1. **机械 guard 优先**：能由测试、checker、lint、类型或 deterministic helper 阻止的重复错误，
   在 owning task 已有实现授权且不扩大 scope 时直接机械化，不另写重复 lesson；否则只建议进入
   对应 owning task，不把记忆写入授权扩成代码修改授权。
2. **高频必读事实进入 `attention.md`**：全文保持 ≤25 条，保留存量分节；超限先合并再新增。
3. **结构性决定进入 ADR**：必须同时满足难回退、缺少上下文会令人意外、源于真实取舍；沿用项目
   惯例位置，不用 lesson 复制决定。
4. **其他稳定方法进入项目既有文档**；目标不存在时请 owner 选择，不发明目录。
5. 其余尚未被更强 owner 承接的可复用经验，进入
   `.codestable/lessons/YYYY-MM-DD-{slug}.md`，作为可纠偏、可删除的 staging。

`.codestable/`、`attention.md` 或 `lessons/` 不存在时可按需创建，不要求先跑 cs-onboard。临时状态、
本周计划或 git 已完整表达的事实不沉淀。`codestable-eval` 只标记未来上游候选；本轮不导出、不上传、
不改 skill，也不恢复 `cs-feedback`。

## lesson 格式

一条一文件，slug 用小写连字符、≤30 字符：

```markdown
---
status: observed
scope: 模块 / 命令 / 场景关键词
date: YYYY-MM-DD
---
规则：未来可执行的结论。
适用 / 不适用：边界与停止应用信号。
证据：最多三个代表性路径、测试、diff 或任务指针。
候选归宿：test | checker | attention | project-doc | adr | codestable-eval
```

## 生命周期

| status | 判据 |
|---|---|
| `observed` | 单次任务已有证据，尚未在独立后续任务验证 |
| `validated` | 非创建该 lesson 的任务和 agent invocation 中有效命中，真实改善行为并验证成功；具体表现为改变计划或验证，或明确排除一个具体且合理的错误路径 |
| `retired` | 被仓库事实反证、scope 完全失效或已有更强 canonical owner；不得应用且不再复活原结论 |

- 新 lesson 一律从 `observed` 开始；不能把创建该 lesson 的同一任务自证为 validated，也不因命中
  次数或模型自评晋级。
- 旧 lesson 缺 `status` 按 `observed` 读取，不批量迁移；只在真实状态变化或本来就要更新时补字段。
- `observed -> validated` 只在独立后续任务确实采用并验证成功时发生，并只补一次代表性证据；必须记录 lesson 实际改变的计划或验证，或明确排除的具体且合理错误路径，以及本次通过的验收证据。
- `observed|validated -> retired` 只写反证/替代原因与指针。retired 条目上的新结论必须另建 observed
  lesson，不继承旧条目的 validated 身份。
- 稳定 validated 命中不产生文件 churn。不得保存原始对话、逐次命中日志或无限 evidence history。

## 写入纪律（硬门槛）

- 命中同域 lesson 时查重、合并到原条目，不新增重复；继续维持约 50 条预算，达到预算先整理、
  晋升、合并或删除，不简单扩容。
- `.codestable/compound/` 是只读历史知识源：命中且结论完整时只引用来源、不新建；有增量时只合并进现有 lesson 或新建 lesson，并引用旧 compound 来源，绝不更新 compound。
- 晋升前先验证新 owner 已写入且能承接完整事实，再在同一更新中删除重复 lesson；若 task skill
  只发现已有 owner，则先标 retired，删除留待显式 `cs-keep` 整理。
- 一次只写用户拍板过的内容，不顺手多写。

## 检索约定

日后找回：`grep -ri "关键词" .codestable/lessons/ .codestable/compound/`。应用前以当前代码、测试或
canonical 文档核实；`retired` 不应用，`compound/` 命中仍按只读规则处理。

## 完成

报告写入、更新或删除的文件路径与一句话摘要即可，不设写后确认。
