---
doc_type: issue-analysis
issue: standalone-runtime-version-unknown
status: confirmed
root_cause_type: missing-guard
related: [standalone-runtime-version-unknown-report.md]
tags: [runtime, versioning, release]
---

# Standalone Runtime 版本 Unknown 根因分析

## 1. 问题定位

| 关键位置 | 说明 |
|---|---|
| `plugins/codestable/skills/cs-onboard/tools/codestable_runtime.py:62` | 只从 skill 目录及祖先查找 `VERSION` 或 plugin manifest。 |
| `plugins/codestable/skills/cs-onboard/tools/codestable_runtime.py:188` | 发现失败时用 `or "unknown"`，随后仍写 manifest 并可能返回健康。 |
| `.claude/skills/eval-cs-skill/scripts/bump_version.py:31` | release bump 未包含 standalone `cs-onboard` 版本文件。 |
| `tools/check-plugin-package.py:86` | checker 只比较插件/marketplace manifest，未校验 standalone 单元版本。 |

## 2. 失败路径还原

**正常路径**：完整 plugin 安装中的 `cs-onboard` 向祖先查到根 `VERSION` 或 plugin manifest → runtime sync 写入实际版本 → health 可比较 installed 与 expected。

**失败路径**：standalone 安装只复制 skill 目录 → 祖先没有版本文件或 manifest → discovery 返回 `None` → sync 回退 `unknown` 并写入两处版本 → health 比较同一个回退值后给出成功信号。

**分叉点**：`codestable_runtime.py:188` — 缺失版本被转换成可持久化的普通字符串，而不是结构化错误。

## 3. 根因

**根因类型**：缺少防御。

**根因描述**：standalone 安装单元没有自包含版本元数据，发布与 package checker 也未把该元数据纳入一致性契约；runtime sync 又把发现失败降级成 `unknown` 成功路径，掩盖了发布缺陷。

**是否有多个根因**：是。主因是 standalone 单元缺版本载体；次因是 runtime sync 未 fail-closed，release/checker 也没有防漂移。

## 4. 影响面

- **影响范围**：所有 standalone `cs-onboard` 安装和任何未来遗漏版本元数据的分发形式。
- **潜在受害模块**：runtime manifest、preflight version mismatch、doctor/runtime health、升级判断。
- **数据完整性风险**：会持久化无法验证的版本并给出成功状态；不会损坏业务数据。
- **严重程度复核**：维持 P1，错误成功信号会使 runtime 漂移长期不可见。

## 5. 修复方案

### 方案 A：自包含版本文件并 fail-closed

- **做什么**：在 `cs-onboard` 根加入 `VERSION`；release bump 与 checker 强制它等于仓库版本；发现失败时返回 `version-unavailable` 且不写 manifest。
- **优点**：复用现有 discovery；standalone 和完整 plugin 同一语义；遗漏会在发布、运行两层被阻断。
- **缺点 / 风险**：新增一个发布时必须同步的文件，但自动 bump 与 checker 已消除人工负担。
- **影响面**：runtime helper、release script、checker 和三组测试。

### 方案 B：把版本硬编码进 Python 或 SKILL frontmatter

- **做什么**：在可执行源码常量或 skill metadata 中写版本，runtime 直接读取。
- **优点**：无需额外普通文件。
- **缺点 / 风险**：引入另一种非既有 schema 或源码常量，release 漂移更隐蔽，职责混乱。
- **影响面**：runtime parser、skill schema、release 与 checker。

### 推荐方案

**推荐方案 A**。普通 `VERSION` 已被现有发现函数支持，真实 `skills` standalone 安装也会复制该文件；配合 fail-closed 能同时修复根因和错误成功信号。
