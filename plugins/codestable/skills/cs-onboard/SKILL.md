---
name: cs-onboard
description: 仓库接入 CodeStable：创建最小骨架，或为 v1 存量项目做无损升级说明。
contracts:
  - grep: "存量文件一律不动"
  - grep: "不复制"
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

创建后确认 `.codestable/` 未被 .gitignore 忽略（它必须入库共享）；发现被忽略时停下报告，由用户决定怎么改，不擅自修改 .gitignore。attention.md 初始只写一行标题和一句用途说明，不预置分节模板。

## 硬门槛

- **存量文件一律不动**：v1 项目的 `reference/`、`tools/`、`gates/`、`hooks/`、`runtime-manifest.json`、`compound/`、`features/`、`issues/`、`roadmap/` 等全部原样保留，不删除、不覆盖、不迁移格式。旧沉淀继续被各 skill 的 grep 检索覆盖。
- **不复制**任何 skill 包内文件到项目（v1 的 reference/gates/tools 分发机制已废止）。
- 已有 `.codestable/` 的仓库只补缺失的 `lessons/` 与 `work/`，其余不碰。

## v1 项目升级说明

对存量 v1 项目，创建缺失目录后向用户说明三点即可：

1. 旧产物与旧沉淀全部保留且继续生效（grep 可检索）；
2. 新工作不再生成 v1 形态产物（阶段文档、checklist、goal 包），普通任务零产物，跨会话任务一个 work 文档；
3. gate 与 runtime 工具不再由 skill 调用；项目侧 `.codestable/tools/` 若被用户自己的 hook 引用则继续自行维护。

## 收尾

报告创建了哪些文件、保留了哪些存量、`.codestable/` 的 git 状态。不写入任何业务判断。
