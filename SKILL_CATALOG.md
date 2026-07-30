# CodeStable 技能目录

v2 共 8 个 skill：一层薄研发纪律 + 一个项目记忆闭环。普通任务零产物，证据是 diff 与测试；跨会话任务一个 work 文档。

| 技能 | 用途 |
|---|---|
| `cs` | 体系速读与入口推荐；只解释，不启动流程 |
| `cs-onboard` | 创建 `.codestable/` 最小骨架（attention / lessons / work）；v1 存量无损保留 |
| `cs-feat` | 新功能与功能改造；风险升级信号触发时先对齐设计 |
| `cs-issue` | bug 修复；没有能变红的验证不许猜根因 |
| `cs-refactor` | 行为等价重构；先有等价性验证再动代码 |
| `cs-code-review` | 独立代码审查；默认审 diff，可按需做 repo 审计 |
| `cs-epic` | 大需求拆解与长程推进；一个 epic 文档维护全景 |
| `cs-keep` | 沉淀经验到 attention / lessons；写入必须有可追溯证据 |

## v1 旧入口

v1 的阶段技能与长尾入口（`cs-feat-design`、`cs-issue-fix`、`cs-goal`、`cs-brainstorm`、`cs-docs`、`cs-domain`、`cs-req`、`cs-audit`、`cs-note`、`cs-feedback`、`cs-roadmap` 系等）已移除：设计与需求澄清是 `cs-feat` / `cs-epic` 的内置步骤，审计是 `cs-code-review` 的模式，沉淀统一走 `cs-keep`，文档与 ADR 由对应工作顺带完成。存量项目的 v1 产物与沉淀全部保留并可被 grep 检索。
