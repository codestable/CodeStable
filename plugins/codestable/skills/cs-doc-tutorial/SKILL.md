---
name: cs-doc-tutorial
description: Deprecated 兼容入口：旧 cs-doc-tutorial 调用用；转交 cs-docs --mode tutorial。新请求不要主动选择。
---

# cs-doc-tutorial

本技能是 `cs-docs` 的长期兼容入口，不维护独立流程规则。

入口意图：`requested_mode: tutorial`

## 执行规则

1. 按已安装 skill 名称加载 `cs-docs` 作为权威主协议，不把兄弟目录相对路径当作主路径。
2. 在当前 run 按 `cs-docs` 主协议继续执行，并带上入口意图 `requested_mode: tutorial`。
3. 不要要求用户重新调用 `cs-docs`。
4. 如果当前运行时无法加载主入口协议，停止并报告兼容入口不可继续。

## 维护规则

- 不在本文件复制阶段流程、模板或 gate 规则。
- 规则变更只更新 `cs-docs` 及其 `references/`。
- 本入口只用于保持旧调用、旧提示词和历史习惯可用。
