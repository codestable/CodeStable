# CodeStable 体系总览

本文档介绍 CodeStable 工作流家族整体——有哪些子技能、各管什么场景、产物怎么组织。无论是 AI 在运行时读到这个文件，还是人打开来看，都能对整个体系有个完整印象。

AI 辅助开发里，有几类场景会反复出现——加新功能、修 bug、遇到值得沉淀的经验、做技术选型、摸新模块的代码、接入新仓库。每种场景如果每次从零处理，都会出各自的典型问题：AI 给功能起的术语跟老代码冲突、bug 改完没人记得当时怎么诊断的、上周刚踩过的坑下周又踩一遍。

CodeStable 把这几类场景各配一套子技能，产物放进统一的目录结构、带统一的 YAML frontmatter,互相之间可以检索引用。


## 技能分成四部分

**根入口**——开放式诉求 / 不知道走哪个时的统一入口:

- `cs` — 介绍体系全貌 + 把诉求路由到正确的 cs-* 子技能。本技能不做事,只做分诊和提示

**做事**——从一段模糊想法走到上线的功能、或者从一份错误报告走到修好的 bug:

- `cs-feat` — 新功能,design → implement → acceptance（想法还模糊时先走讨论层 `cs-brainstorm` 做分诊，不属于 feature 流程内部）
- `cs-issue` — 修 bug,report → analyze → fix
- `cs-refactor` — 代码优化(行为不变、结构/性能/可读性变),scan → design → apply

两类都不直接让 AI 写代码,而是先产出 spec(功能方案 / 问题分析),用户 review 后再动手,代码和 doc 一起交付。针对的是术语冲突、范围失控、改完不留存档这三种 AI 默认会出的问题。

**沉淀**——把做事过程产生的知识存下来,下次遇到同类问题直接复用:

- `cs-keep` — 把坑点 / 技巧 / 决策 / 调研沉淀到 `.codestable/compound/`，纯 markdown，grep 检索
- `cs-note` — 把一两行启动必读的项目注意事项追加到 `.codestable/attention.md`

**讨论层**——想法还模糊时的统一入口,不直接产出设计或代码:

- `cs-brainstorm` — 和用户对话做分诊:case 1(已经够清楚,直接 feature-design)、case 2(小需求,在 feature 里继续讨论并落 `{slug}-brainstorm.md`)、case 3(大需求,移交给 roadmap)

**辅助**——围着前几类转的周边工具:

- `cs-onboard` — 把新仓库接入 CodeStable 目录结构
- `cs-req` — 起草或刷新 `.codestable/requirements/` 下的需求文档——系统的能力愿景层，覆盖过去/现在/未来
- `cs-domain` — 领域模型一站式：CONTEXT.md 术语维护 + ADR 决策记录（守门 3 判据 + Nygard 四节）+ 单/多 context 拓扑管理
- `cs-roadmap` — 把一块装不进单个 feature 的大需求拆成带依赖和状态的子 feature 清单,作为后续多次 feature 流程的种子和排期依据;独立于需求 / 架构档案
- `cs-doc-tutorial` — 写给外部读者的开发者指南 / 用户指南（任务导向）
- `cs-doc-api` — 为公开 API 逐条目生成参考文档（从源码反推）


## 场景路由

仓库里还没有 `.codestable/` 目录,先用 `cs-onboard` 搭骨架。

| 场景 | 子技能 |
|---|---|
| 想法还模糊 / "有个想法没想清楚" / "先聊聊" | `cs-brainstorm`(分诊后路由到 design / feature-brainstorm 落盘 / roadmap) |
| 新功能 / 新能力 | `cs-feat` |
| BUG / 异常 / 文档错误 | `cs-issue` |
| 代码优化 / 重构 / 重写(行为不变) | `cs-refactor` |
| 摸代码、提问调研 / 踩坑回顾 / 技术选型沉淀 / 可复用模式 | `cs-keep` |
| 补 / 更新需求文档 | `cs-req` |
| 拍板技术决策 / 加术语 / 项目要分子系统 | `cs-domain` |
| 大需求拆解 / 排期规划 | `cs-roadmap` |
| 开发者指南 / 用户指南 | `cs-doc-tutorial` |
| 库 API 参考 | `cs-doc-api` |

完整的操作手册、退出条件、和其他工作流的关系,各子技能里讲。


## 愿景档案 vs 结构档案 vs 规划档案 vs 单次动作

四类文档各管一段时间尺度,不要混:

- **愿景档案**(requirements)——描述"用户需要什么、系统提供什么能力来满足"。`status` 区分三个时间深度：`draft`（未来愿景）、`current`（现在的能力）、`outdated`（过去的痕迹）。draft req 可独立于实现存在——先把愿景定下来，后续 roadmap 排期和 design 实现才有稳定对齐基准
- **领域档案**(CONTEXT.md / adrs/)——描述"项目用什么术语、为什么做出这些结构性决策"。术语跟着 capability 引入；ADR 严格 3 判据，不每个决定都记。cs-domain 维护
- **规划档案**(roadmap)——描述"接下来打算怎么分步实现"。独立于愿景和领域档案,改动不牵连 requirements。所有条目 done / dropped 后 roadmap 进入 `completed` 状态,作为历史档案留存
- **单次动作**(feature / issue / refactor)——本次要做的一件具体事情的 spec。动作走完后,相关沉淀提炼进愿景档案、结构档案和 compound

用户说"我想要一个 X 系统"这种大需求,先走 roadmap 拆成若干子 feature,再一条一条走 feature 流程。直接起 feature 会变成巨型 design 塞不下、拆了又没有追踪抓手。


## feature 和 issue 的阶段不可跳

feature 走 brainstorm(可选) → design → implement → acceptance,issue 走 report → analyze → fix。每个阶段有退出条件,上一个没满足,下一个不开始。

AI 最常见的问题是一口气铺几百行代码才让人看——等发现问题已经很难中止。阶段间的人工 checkpoint 就是为了早一步中止。每个 checkpoint 具体检查什么,对应子技能里讲。

例外两种:issue 根因一眼确定时走快速通道,跳过 analyze 直接 fix;feature 范围小时走 `cs-feat-ff`,写完 spec 直接进实现。


## 进一步参考

- `.codestable/reference/shared-conventions.md` — 目录结构、YAML frontmatter 口径、`{slug}-checklist.yaml` 生命周期、收尾 commit 约定、cs-keep 守护规则
- `.codestable/reference/tools.md` — `search-yaml.py` / `validate-yaml.py` 用法（compound 不用这俩，直接 grep）
- `.codestable/reference/maintainer-notes.md` — 断点恢复、新增子工作流的登记

目录结构(requirements/、roadmap/、features/、issues/、compound/、tools/、reference/)的权威定义在 `shared-conventions.md`。要改目录先改那里——方法是改 `cs-onboard/reference/shared-conventions.md` 这个模板,新项目 onboard 时会带上新版本。


## 相关

- `.codestable/attention.md` — CodeStable 技能启动必读的项目注意事项
- `.codestable/requirements/CONTEXT.md` — 项目领域术语表（cs-domain，lazy 创建）
