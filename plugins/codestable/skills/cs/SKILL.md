---
name: cs
description: CodeStable 体系速读。触发：用户想了解 CodeStable、问该用哪个 cs skill，或不确定诉求归属。
argument-hint: "[问题]"
---

# cs

介绍 CodeStable 并帮用户选对入口。本 skill 只解释和推荐，不启动流程、不写文件。

## 体系速读

CodeStable 是一层薄的研发纪律加一个项目记忆闭环，7 个入口：

| 诉求 | 入口 |
|---|---|
| 新功能、功能改造 | `cs-feat` |
| bug、报错、行为异常 | `cs-issue` |
| 行为等价的重构、优化 | `cs-refactor` |
| 审查 diff 或按需审计代码 | `cs-code-review` |
| 大需求拆解与长程推进 | `cs-epic` |
| 沉淀经验、教训、"记住这个" | `cs-keep` |
| 仓库接入 / v1 升级 | `cs-onboard` |

项目记忆在 `.codestable/`：attention.md（每次必读）、lessons/（grep 检索的经验）、work/（活动中的跨会话任务）。普通任务零产物，证据是 diff 与测试。

v1 的旧入口（cs-feat-design、cs-issue-fix、cs-goal、cs-brainstorm、cs-docs、cs-domain、cs-req、cs-audit、cs-roadmap 等）已并入上表：设计与需求澄清是 cs-feat / cs-epic 的内置步骤，审计是 cs-code-review 的模式，ADR 与文档由对应工作顺带完成或直接对话处理。

## 回答方式

用户带着具体诉求来时，推荐一个入口并说明理由，让用户自己调用或同意后继续；诉求含糊时只问一个聚焦问题。
