---
name: cs-keep
description: 沉淀可复用经验与项目记忆。触发：记录踩坑、教训、调研结论、纠偏，或用户说"记住这个"。
argument-hint: "[要沉淀的内容]"
contracts:
  - grep: "没有可追溯证据不写"
  - grep: "先合并"
---

# cs-keep

把这次学到的东西沉淀成下次能被检索到的项目记忆。落点由你判断，不追问用户分类。

## 落点判断

- 几乎每次会话都必须知道的一两行事实 → 追加到 `.codestable/attention.md`（全文保持 ≤25 条；存量分节结构保留，新条目放进合适分节或末尾。超限先合并旧条目再加）。
- 其余可复用经验——坑、技巧、调研结论、失败路径、对 CodeStable skill 本身的反馈 → 新建 `.codestable/lessons/YYYY-MM-DD-{slug}.md`。
- 难回退的结构性技术取舍 → 建议走项目的 ADR（项目惯例位置），不写进 lessons。
- 临时状态、本周计划、git 提交已表达的事实 → 不沉淀，向用户说明原因。

`.codestable/` 或 `lessons/` 不存在时直接创建，不要求先跑 cs-onboard。

## lesson 格式

一条一文件，slug 用小写连字符、≤30 字符：

```markdown
---
scope: 适用范围（模块 / 命令 / 场景关键词，供日后 grep）
date: YYYY-MM-DD
---
规则：一两句可执行的结论。
证据：来自本次对话、diff 或报错的可追溯事实。
来源：相关文件路径或对话要点。
```

## 写入纪律（硬门槛）

- 没有可追溯证据不写；不编造，不从模型记忆里泛化。
- 写前先 grep `.codestable/lessons/` 与 v1 存量 `.codestable/compound/` 查同域旧条目：能合并就更新旧文件，不新增重复；lessons 超过约 50 条时必须先合并再新增。
- 一次只写用户拍板过的内容，不顺手多写。

## 检索约定

日后找回：`grep -ri "关键词" .codestable/lessons/ .codestable/compound/`。命中引用时必须报告来源路径。

## 完成

报告写入或更新的文件路径与一句话摘要即可，不设写后确认。
