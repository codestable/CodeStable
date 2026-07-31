---
name: cs-code-review
description: cs-review 的兼容别名（v1 沿用名）。触发后在当前 agent 中转到 cs-review，不维护独立规则或创建子 agent。
argument-hint: "[--range <git-range>] [scope 或 audit 目标]"
---

# cs-code-review → cs-review

本入口是 `cs-review` 的兼容别名，为 v1 用户的既有习惯保留。收到调用时在当前 agent 中调用
canonical entry `cs-review`，参数原样传递；不得读取 sibling skill 文件、创建子 agent 或在
本入口复制并演进审查规则。
