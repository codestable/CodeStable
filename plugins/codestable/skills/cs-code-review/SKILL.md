---
name: cs-code-review
description: cs-review 的兼容别名（v1 沿用名）。触发后按 cs-review 的纪律执行，不维护独立规则。
argument-hint: "[--range <git-range>] [scope 或 audit 目标]"
---

# cs-code-review → cs-review

本入口是 `cs-review` 的兼容别名，为 v1 用户的既有习惯保留。收到调用时直接按 `cs-review` 的 SKILL.md 执行，参数原样传递；本文件不含任何独立规则，不得在此基础上演进行为。
