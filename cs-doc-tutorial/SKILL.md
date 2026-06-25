---
name: cs-doc-tutorial
description: 写或更新对外指南文档——开发者指南（dev-guide）和用户指南（user-guide），产物在项目 docs/ 目录。任务导向（怎么用 X 做 Y），与 doc-api 的零件参考不同。触发：用户说"写文档"、"开发者指南"、"用户指南"，或 feature-acceptance 收尾时推送。
---

# cs-doc-tutorial

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

代码解决问题，文档让别人能用它解决问题。spec 记录"做了什么、为什么这么做"，但下游开发者和终端用户不需要、也不应该读 spec——他们需要面向自己角色的、可发布的指南。doc-tutorial 就是从 spec 和代码出发写成读者真正能用的指南。

---

## 两条轨道

| 轨道 | 目标读者 | 典型内容 | 输出路径 |
|---|---|---|---|
| `dev-guide` | 贡献者、集成方、下游开发者 | 本地 setup、架构解说、API 说明、扩展方式 | `docs/dev/{slug}.md` |
| `user-guide` | 终端用户 | 功能概述、操作步骤、概念解释、常见问题 | `docs/user/{slug}.md` |

**轨道选择从"谁读"出发**——同一个 feature 经常需要两份：API 变化进 dev-guide，对应的用户操作进 user-guide。

> 路径 `docs/dev/` 和 `docs/user/` 是默认约定，项目已有自己的 docs 结构就以项目为准——开始前先确认。

---

## 触发时机

| 情境 | 说明 |
|---|---|
| feature-acceptance 结束 | 主动推：方案第 2 节（接口契约）有变更问"需要更新 dev-guide 吗？"；第 1 节（用户可见行为）有变更问"需要更新 user-guide 吗？" |
| 用户主动触发 | "写文档"、"doc-tutorial"、"补一份开发者指南" |
| onboard 完成后 | 新仓库可触发补全基础文档骨架 |

主动推送一句话即可，用户说"不用"就别再提——多次推会让用户觉得 AI 在加戏。

---

## 涉及路径

doc-tutorial 产物**不在 `.codestable/` 下**——指南是面向外部读者的可发布产物，和 spec 工件分开。

- dev-guide → `docs/dev/{slug}.md`
- user-guide → `docs/user/{slug}.md`

文件命名 `{slug}.md`（英文小写连字符，**无日期前缀**）——指南持续更新按主题管理。

检索：

```
python .codestable/tools/search-yaml.py --dir docs/dev --filter doc_type=dev-guide --filter status=current
python .codestable/tools/search-yaml.py --dir docs/user --filter doc_type=user-guide --filter component={feature-slug}
```

---

## YAML frontmatter

```yaml
---
doc_type: dev-guide | user-guide
slug: {英文连字符}
component: {关联模块名或 feature slug}
status: draft | current | outdated
summary: {一句话描述涵盖什么}
tags: []
last_reviewed: YYYY-MM-DD
---
```

`status` 三态：`draft` 待 review；`current` 当前有效；`outdated` 对应代码已变文档没跟上（保留原文，标记后推送更新）。

---

## 文档格式

### dev-guide 正文结构

```markdown
## 概述
一段话描述功能定位和适用场景。

## 前置依赖
集成此模块所需的环境、依赖或配置（如有）。

## 快速上手
最小可运行示例。代码优先文字辅助。

## 核心概念
（可选）理解接口 / API / 模块行为所需的关键术语和设计决定。

## 接口参考
主要 API / 配置选项 / 事件 / 钩子。表格或逐项列举。

## 常见场景
2-4 个实际使用场景代码示例，覆盖 happy path 和常见边界。

## 已知限制与注意事项
（可选）边界、性能考虑、已知 bug 绕过方式。

## 相关文档
关联的 user-guide、方案 doc、相关 ADR 或外部参考。
```

### user-guide 正文结构

```markdown
## 功能简介
一段话描述功能是什么、解决什么问题。

## 前置条件
（可选）使用前的前提（账号权限、需先完成的操作）。

## 如何使用
步骤化操作。每步一行，关键操作配截图占位（`![描述](./assets/xxx.png)` 或注明"此处需截图"）。

## 常见问题
Q: ...
A: ...

## 相关功能
（可选）关联功能跳转链接或说明。
```

---

## 工作流步骤

1. **明确任务范围**——轨道（dev / user / 都要）+ 覆盖范围（新写还是更新）+ 信息来源（方案 doc 已有吗？同 component 已有 guide？需要读哪些代码？）
2. **收集输入**——读方案 doc（重点第 0 节术语、第 2 节接口契约、第 1 节用户可见行为）+ `search-yaml.py` 搜 docs/ 确认有无已有 guide。发现已有 guide 标 `outdated` → 任务定性为**更新**
3. **起草**——按对应轨道结构起草，frontmatter `status: draft`。约束：只写面向目标读者的内容——**不要把方案 doc 里"实现提示"或内部设计搬过来**；术语与方案 doc 第 0 节一致；代码示例必须来自实际代码不虚构接口
4. **用户 review**——展示草稿，逐节确认覆盖范围 / 描述准确性 / 是否有读者看不懂的地方
5. **落盘**——用户放行后：写入路径；`status: current` + `last_reviewed` 当天；更新已有文档时小修直接改，大改（结构重组 / 读者定位调整）先把旧文档 `status: outdated` 留作参考再新写一份

---

## 与其他工作流的关系

| 来源 | 关系 |
|---|---|
| `cs-feat-accept` | 验收后主动推：接口变更推 dev-guide，用户可见变更推 user-guide |
| `cs-feat-design` | 方案第 2 节是 dev-guide 主要信息源；第 1 节是 user-guide 主要信息源 |
| `cs-onboard` | 新仓库接入后可补全基础文档骨架 |
| `cs-keep` | dev-guide 引用的技术选型 / 用法示例若 compound 里已有沉淀，交叉引用而不重复写 |
| `cs-doc-api` | guide 引用 doc-api 条目做详细参考；doc-api 是零件参考，doc-tutorial 是任务教程 |

---

## 容易踩的坑

- 把方案 doc 里"实现提示"原文搬进 dev-guide——那是内部 spec
- 没检查已有 guide 就新建——可能两份冲突
- 写完 `status` 还是 `draft`——落盘必须改 `current`
- 代码已更新相关 guide 还是 `current`——应标 `outdated` 并推送更新
- dev-guide 和 user-guide 内容高度重叠——其中一份定位有误
- 用 guide 存放 spec 信息（不变量 / 测试约束 / 根因分析）——这类内容属于 `.codestable/`
