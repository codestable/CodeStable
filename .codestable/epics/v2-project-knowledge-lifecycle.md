---
status: accepted
created: 2026-08-01
updated: 2026-08-01
---

# v2 项目知识与 Epic 生命周期

## 起点与目标

CodeStable v2 已把普通任务压缩为 thin harness 和最小项目记忆，但 legacy 历史目录的实际检索
覆盖不完整，Epic 的唯一 work 文档又会在完成后删除。本 Epic 要建立可执行的 legacy 只读迁移
契约，并把持久目标、恢复游标、人工门槛和终态验收收回 `cs-epic`，不恢复 `cs-goal` runtime。

## 范围与非目标

- 让 task skills 可靠检索 v1
  `roadmap/features/issues/refactors/goals/compound/audits/brainstorms/feedback`，并禁止写回。
- 仅允许 `.codestable/attention.md` 明确登记为 canonical owner 的既有 requirements 继续维护。
- 建立永久 Epic 上下文与临时 work 游标的双层模型。
- 保留拆解确认、边界变化确认和最终 owner 验收，并补充独立整体验收。
- 同步 ADR、skills、AGENTS、WORKFLOW、README 中英文与契约测试。
- 不恢复 `cs-goal` 入口、goal package、YAML 状态机、逐轮报告或 legacy runtime gate。
- 不批量迁移、删除或改写仓库现有 v1 资产。

## 验收标准

- ADR 明确 legacy 只读政策、requirements 例外、Epic 双层模型和不恢复 `cs-goal` 的边界。
- `cs-feat`、`cs-issue`、`cs-refactor`、`cs-epic` 均按关键词覆盖 v1 的
  `roadmap/features/issues/refactors/goals/compound/audits/brainstorms/feedback`。
- `cs-keep` 命中旧 `compound` 时不再改写历史文件，新知识只进入 lessons。
- `cs-onboard` 仍只预建 attention、lessons 与 work；`.codestable/epics/` 由首次 Epic 按需创建。
- `cs-epic` 能从永久 Epic 文档和最小 work 游标恢复，持久记录目标契约与最终交付。
- Epic 在拆解、重大边界变化和终态保持 owner gate；终态按最新已批准验收标准先经独立整体验收。
- 完成后只删除 work 游标和所属子项 work，永久 Epic 文档继续保留。
- 中英文公开文档语义一致，契约测试能拦截目录读写与生命周期回退。
- 相关 pytest、全量 pytest、plugin package check 与 `git diff --check` 通过。

## 关键决策

- 项目已有明确 Epic/RFC 归宿时沿用，否则按需创建 `.codestable/epics/`。
- 永久文档拥有目标与结论；work 文档只拥有活动游标，不复制稳定上下文。
- 旧知识采用“原样保留、只读检索、按需毕业”，不做一次性迁移。

## 子项契约

- `PK-1`：ADR-005 与 ADR-004 的替代关系；无依赖；三轮 design review 的 blocking/important
  均已处理并留下证据。
- `PK-2`：shipped skills 的检索、写入和 Epic 生命周期契约；依赖 `PK-1`；契约测试可判定。
- `PK-3`：AGENTS、WORKFLOW、README 与 catalog 的中英文同步；依赖 `PK-2`；语义对称。
- `PK-4`：legacy 目录矩阵、Epic 双层生命周期和 `cs-goal` 不回归测试；依赖 `PK-2`、`PK-3`；
  相关/全量 pytest、package check 与 diff check 通过。

## 最终交付索引

- 决策基线：[ADR-005](../../docs/adr/005-project-knowledge-and-epic-lifecycle.md) 接替
  [ADR-004](../../docs/adr/004-project-knowledge-not-runtime-distribution.md)，定义 legacy 只读矩阵、
  requirements canonical 条件、Epic 双层 ownership 与不恢复 `cs-goal` runtime 的边界。
- 执行契约：`plugins/codestable/skills/` 下的 `cs-epic`、`cs-feat`、`cs-issue`、`cs-refactor`、
  `cs-keep`、`cs-onboard` 与 `cs` 已同步；`cs-review` 保持只读叶子，未引入递归委派。
- 公开上下文：`AGENTS.md`、`CLAUDE.md`、`WORKFLOW.md` / `WORKFLOW.en.md`、`README.md` /
  `README.en.md`、`SKILL_CATALOG.md` / `SKILL_CATALOG.en.md` 已对齐同一生命周期。
- 回归守卫：`tests/test_v2_architecture_contract.py`、`tests/test_skill_contracts.py` 与
  `tests/test_v2_documentation_contract.py` 锁定目录读写、双层 Epic、owner gate、双语文档和
  `cs-goal` 不回归；现有分发测试继续锁定 v2 skill 清单。

### 毕业清单

- 稳定架构决策进入 ADR-005；可执行约束进入 owning skills；用户入口说明进入中英文公开文档。
- 验收证据与交付关系保留在本永久 Epic；本轮没有需要新建 requirement 或 lesson 的独立结论。
- 临时执行进度已毕业到本节与整体验收，owner 接受后删除 work 游标，不保留重复状态。

## 整体验收

- 2026-08-01，fresh Paseo reviewer `6fd78969-26cd-438c-baa0-2673e88cf77e` 使用
  `claude-fable-5`、`plan/high` 对完整工作树 tree OID
  `ea90f86697ee01112566d8a20881d2d4fec22f1a` 完成 diff + acceptance review；审查前后目标一致，
  结论为“可合”，`0 blocking / 0 important / 2 nit`。
- reviewer 独立复现：定向契约 `23 passed`，全量 pytest `108 passed, 1 skipped`，分发清单
  `3 passed, 1 skipped`，plugin package check 与 `git diff --check` 通过。
- 永久 Epic 批准版本 SHA-256
  `84db471025723e5b3e5e92da1413f15cb3c40267deb5cefd36a3fb5ba1f92dfa` 在执行与审查期间保持一致。
- owner 已在终态报告后明确接受；全部验收标准满足，本 Epic 进入 `accepted`。

## 遗留风险

- legacy 只读依靠 skill 契约与回归测试约束，不增加 runtime hook；这是 thin harness 的有意取舍。
- active Epic 做契约变更时，永久文档更新到 owner 重确认之间会短暂与批准 hash 不一致；恢复流程
  必须先辨认在途重审并请求上下文，不能从聊天历史猜测或恢复执行。
- README 的负向旧措辞守卫较弱，但 WORKFLOW 正向契约和逐 skill 目录矩阵测试覆盖真实不变量；
  作为已接受 nit 保留，不影响当前正确性。
