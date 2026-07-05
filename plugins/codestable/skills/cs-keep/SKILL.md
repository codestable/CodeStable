---
name: cs-keep
description: 项目知识沉淀。触发：用户说“记下来/沉淀/留个 note”，或流程收尾发现可复用坑、技巧、决策。
---

# cs-keep

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

把这次值得记的事写到 `.codestable/compound/YYYY-MM-DD-{slug}.md`：

- `{slug}` kebab-case，30 字内，能让自己半年后看一眼标题就想起来是啥
- 纯 markdown，没有 frontmatter
- 三段足够：**背景**（这事是什么场景下冒出来的）/ **结论**（实际记的那一条）/ **证据**（代码片段、路径、命令、链接，任何能让别人复核的）

写完报路径就完事。不要追问"还要不要分类"、"要不要写 tags"——没这些东西。

未来要找回来直接 `grep -r "关键词" .codestable/compound/`。
