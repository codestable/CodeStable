---
doc_type: issue-analysis
issue: skills-update-removes-cs-skills
status: confirmed
root_cause_type: logic
related: [skills-update-removes-cs-skills-report.md]
tags: [installation, skills-cli, package-discovery]
---

# Skills Update 删除 CodeStable Skills 根因分析

## 1. 问题定位

| 关键位置 | 说明 |
|---|---|
| `skills@1.5.17 src/update.ts:334-366` | 全局更新用 `findSkillMdPaths(tree)` 判断同一 source 中哪些 lock 路径已被删除。 |
| `skills@1.5.17 src/blob.ts:250-366` | 通用扫描会累积所有 priority prefix 的匹配；一旦结果非空就不做深层 fallback，也不读取 plugin manifest。 |
| `.claude/skills/eval-cs-skill/SKILL.md` | 仓库中的维护者 skill 会产生 priority 结果，使通用扫描不再 fallback 到 plugin 深层路径。 |
| `plugins/codestable/.codex-plugin/plugin.json` | 正常安装会按 manifest 发现 `./skills/`，但 update 删除检测没有复用这条发现语义。 |
| `README.md:80` | 当前升级指引直接运行裸 `npx skills@latest update`，暴露了错误删除确认。 |

## 2. 失败路径还原

**正常路径**：完整安装读取 CodeStable plugin manifest → 发现 `plugins/codestable/skills/` 下全部 `cs*` skills → 为每个 skill 写入 lock 路径并安装。

**失败路径**：裸 update 按 source 读取 GitHub tree → 通用扫描在 `.claude/skills/*` 得到非空 priority 结果 → 跳过深层 fallback，且结果不包含 plugin manifest 声明的路径 → 32 个 CodeStable lock 路径被标为上游已删除 → 用户确认清理后 sibling skills 被移除。

**分叉点**：`skills@1.5.17 src/update.ts:346` — 删除检测使用的 discovery 与安装时的 plugin discovery 不同源。

## 3. 根因

**根因类型**：逻辑错误。

**根因描述**：外部 `skills` CLI 在安装与更新删除检测中采用两套不一致的 package discovery。CodeStable 是 manifest 声明的多-skill plugin，同时仓库还包含优先目录下的维护者 skills；该组合使更新器错误地认为 plugin skills 已从上游删除。

上游跟踪：`vercel-labs/skills#1298` 记录了同类 plugin-path 丢失问题；package-root `add` 是仓库侧安全升级入口，不代表裸 `update` 已在上游修复。

**是否有多个根因**：是。主因是外部更新器忽略 plugin manifest；次因是仓库文档把裸 update 当作可靠的完整 plugin 升级入口，且缺少真实 package reconciliation 回归。

## 4. 影响面

- **影响范围**：所有通过 `skills` CLI 安装、lock 指向 manifest 内深层路径且交互确认删除的 CodeStable 用户。
- **潜在受害模块**：全部 `cs` / `cs-*` skills；依赖 `cs-onboard` 工具的 runtime refresh 也会失去入口。
- **数据完整性风险**：全局安装状态与 lock 会被删除；项目源码不受影响，可通过完整重装恢复。
- **严重程度复核**：维持 P1，正常升级会中断整套工作流，但有明确恢复路径。

## 5. 修复方案

### 方案 A：仓库侧安全完整重装入口

- **做什么**：把 `skills` 升级指引改为针对 `codestable/CodeStable/plugins/codestable` package root 的完整 `add`；增加隔离 install/update reconciliation 测试，验证 canonical skill 集合与 sibling 保留。
- **优点**：不依赖错误的跨 manifest 删除检测；只安装 CodeStable plugin 的 32 个 skills，不混入维护者 skills；仓库可立即交付。
- **缺点 / 风险**：属于安全重装而非修复外部 CLI 的裸 update；上游修复后仍可保留该确定性入口。
- **影响面**：README 中英文、package checker、安装回归测试。

### 方案 B：复制或移动 skills 以适配外部通用扫描

- **做什么**：把全部 `cs*` skills 复制到外部 CLI 的优先目录，或迁走 `.claude/skills` 让扫描回退。
- **优点**：裸 update 的当前扫描能看到 CodeStable 路径。
- **缺点 / 风险**：制造 32 份重复源码，或破坏维护者 skill 自动发现；路径仍与现有 lock 不一致，风险高。
- **影响面**：skill package、维护工具、测试和发布布局大范围变化。

### 推荐方案

**推荐方案 A**。它在仓库可控边界内消除破坏性升级入口，并通过 package-root 限定保证完整集合；方案 B 为适配外部 bug 破坏了单一源码和现有工程边界。
