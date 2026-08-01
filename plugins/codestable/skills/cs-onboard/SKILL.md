---
name: cs-onboard
description: 仓库接入 CodeStable：创建最小骨架，或为 v1 存量项目做无损升级说明。
---

# cs-onboard

给仓库一个最小的 CodeStable 骨架。规则和纪律都在 skill 包里，项目目录只放项目自己的知识。

## 骨架（目标状态）

```text
.codestable/
├── attention.md    # 每次会话必读的项目事实，≤25 条，从空开始
├── lessons/        # 沉淀的经验，一条一文件（cs-keep 写入）
└── work/           # 活动中的跨会话任务文档，完成即清
```

创建后确认 `.codestable/` 未被 .gitignore 忽略（它必须入库共享）；发现被忽略时停下报告，由用户决定怎么改，不擅自修改 .gitignore。attention.md 初始只写一行标题和一句用途说明，不预置分节模板。`.codestable/epics/` 不属于基础骨架：首次 Epic 优先沿用项目已有 Epic / RFC / initiative 归宿，没有时才由 `cs-epic` 按需创建。

## 硬门槛

- **存量文件一律不动**：v1 知识目录 `.codestable/roadmap/`、`.codestable/features/`、`.codestable/issues/`、`.codestable/refactors/`、`.codestable/goals/`、`.codestable/compound/`、`.codestable/audits/`、`.codestable/brainstorms/`、`.codestable/feedback/`，既有 `.codestable/requirements/`，以及 legacy runtime 资产 `.codestable/reference/`、`.codestable/tools/`、`.codestable/gates/`、`.codestable/hooks/`、`.codestable/runtime-manifest.json` 全部原样保留，不删除、不覆盖、不迁移格式。
- 上述 9 个 v1 知识目录及其他未被 v2 明确拥有的既有 `.codestable/` 目录默认只读：不得继续生成、原地改写或批量迁移；新结论进入 v2 Epic、项目文档、ADR 或 lesson。owning task skills 只按当前任务关键词检索存在的历史目录，命中时报告来源路径。
- 既有 `.codestable/requirements/` 仅在 `.codestable/attention.md` 明确记录其为 canonical requirement 位置时可继续维护；owner 首次指定时先记录 attention，否则按只读历史处理。目录不存在时不默认创建。
- **不复制**任何 skill 包内文件到项目（v1 的 reference/gates/tools 分发机制已废止）。
- 已有 `.codestable/` 的仓库只补缺失的 `attention.md`、`lessons/` 与 `work/`，其余不碰。

## v1 项目升级说明

对存量 v1 项目，创建缺失目录后向用户说明三点即可：

1. 旧产物与旧沉淀全部保留；owning task skills 按任务关键词只读检索存在的历史目录并报告命中路径；
2. 新工作不再生成 v1 形态产物（阶段文档、checklist、goal 包），普通任务零产物，跨会话任务一个 work 文档；
3. gate 与 runtime 工具不再由 skill 调用；项目侧 `.codestable/tools/` 若被用户自己的 hook 引用则继续自行维护。

## 收尾

报告创建了哪些文件、保留了哪些存量、`.codestable/` 的 git 状态。不写入任何业务判断。
