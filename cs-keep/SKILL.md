---
name: cs-keep
description: 把刚发现的坑、技巧、决策、调研沉淀到 .codestable/compound/，纯 markdown 文件，靠全文检索找回。触发：用户说"记下来"、"沉淀一下"、"留个 note"，或 cs-issue / cs-epic / cs-audit 收尾时推送。
---

# cs-keep

遵循 `.codestable/convention.md`。

把这次值得记的事写到 `.codestable/compound/YYYY-MM-DD-{slug}.md`：

- `{slug}` 30 字内，能让自己半年后看一眼标题就想起来是啥（命名规则见 convention）
- 纯 markdown，没有 frontmatter
- 三段足够：**背景**（这事是什么场景下冒出来的）/ **结论**（实际记的那一条）/ **证据**（能让别人复核结论的支撑）

## 自包含

keep 下来的是积分出来的真相，得耐放。证据靠内嵌、不靠指向：代码片段、命令和它的输出、原文摘录，统统抄进文档。会变的东西——路径、行号、链接、commit——只留作出处线索，不作复核的唯一依赖。

验收一句话：半年后代码挪了、链接挂了，这篇仍要能独立读懂。

## 检索

产物是纯 markdown、无索引、无 frontmatter，未来要找回来对 `.codestable/compound/` 做全文检索关键词即可——grep、ripgrep、框架自带搜索，任何全文搜索工具都能命中。
