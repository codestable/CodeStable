---
name: cs-onboard
description: 把 CodeStable 接入一个项目，创建或补齐 `.cs/` 本地工作区和基础实体目录。触发：第一次使用 cs、项目还没有 `.cs/`、用户说接入 CodeStable/初始化 cs/搭好 cs 基础结构/重跑 onboard 同步缺失骨架。只做初始化和补齐，不迁移旧需求、不改业务代码、不覆盖已有内容。
---

# cs-onboard

`cs-onboard` 负责把 CodeStable 的本地工作区放进项目：创建 `.cs/`、基础实体目录和启动事实。

它只做初始化和补齐。已有内容默认保留，不迁移旧文档，不替用户整理需求，不创建 issue。

开始前先确认：如果当前对话/执行上下文已经读过 `cs` 技能，就复用；没读过就先读一次，理解 CodeStable 的实体和技能边界。

onboard 可以观察项目，但不能编项目。能从代码、README、配置、测试和 git 历史推断的，只能作为候选事实或下一步建议；业务目标、路线图、明确不做什么、用户故事和长期取舍，除非已有文档证据或用户确认，否则不要写进 `.cs/`。

## 使用脚本

优先运行：

```bash
python cs-onboard/scripts/init_codestable.py --project .
```

脚本会创建 `.cs/facts.md` 和这些目录：

- `.cs/talks/`
- `.cs/issues/`
- `.cs/epics/`
- `.cs/requirements/`
- `.cs/notes/`
- `.cs/tools/`

默认不覆盖已有文件。只有用户明确要求重置 `facts.md` 时，才使用 `--force`，并在执行前再次确认。

## 初始化后检查

确认：

- `.cs/facts.md` 存在。
- 如果项目已有旧文档，只指出下一步可以用 `cs-talk`、`cs-plan`、`cs-note`、`cs-maketools` 或 `cs-close` 逐步沉淀，不在 onboard 里强迁移。

## 结束输出

告诉用户：

- 创建或补齐了哪些目录和文件。
- 哪些文件已存在所以保留。
- 下一步该用哪个技能：想法模糊用 `cs-talk`，已有讨论用 `cs-plan`，要记知识用 `cs-note`，内部流程未知用 `cs-maketools`。
