---
name: cs-feat-ff
description: feature 流程的超轻量通道——不写 design / checklist 直接动手，但先指引 AI 查 CodeStable 知识库再开工。触发：用户说"快速模式"、"fastforward"、"别那么多步骤"、"直接开干"，且需求小到不值得走 design 流程。
---

# cs-feat-ff

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

用户让你做小功能时本来 AI 就会直接动手——这个技能**不改变这件事**。它只做一件事：动手前把项目里已沉淀的 CodeStable 知识指给你，按需搜一下，写出来的代码就比裸写多一层保护；动手后回写一份**最简的 `{slug}-ff-note.md`** 让这次工作可追溯、可被 cs-req / cs-domain backfill 看到、能纳入 scoped-commit 提交。

很轻：没有 design doc / checklist / 验收清单 / 动手前的用户确认。看完指引，该读代码读、该写代码写、写完回写一段话。

---

## 动手前先扫一眼 .codestable/

Glob `.codestable/` 发现可用目录和文档，按需取用：

- **`requirements/CONTEXT.md`** — 领域术语；用项目术语命名，不自己造名
- **`requirements/adrs/`** — 已拍板的架构决策；改跨模块的东西前 grep 相关 adr 避免违反
- **`compound/`** — 沉淀的坑点 / 技巧 / 调研：
  ```bash
  grep -r "关键词" .codestable/compound/
  ```
- **`requirements/{slug}.md`** — 有相关 req 时读边界
- **`features/`** — 有同类 feature 时参考其 design
- **`reference/`** — shared-conventions.md / tools.md

---

## 怎么用

动手前问 2 个问题：

1. **这块代码以前有人栽过跟头吗？** → `grep -r "关键词" .codestable/compound/`
2. **这块代码有没有已经拍板的写法约束？** → 看 `requirements/adrs/` 相关 ADR + grep `compound/` 找写法沉淀

命中就把结论融进实现（**按约束来写**，不是抄）。没命中按自己判断写很正常。搜不到换几个关键词再试。

---

## 写代码时守住这几条

design / implement 的硬约束在 fastforward 的精简版。没 design doc 不代表可以不讲——这些是让你"直接动手"时不偏向 AI 默认会踩的坑。

### 先想"放在哪儿"再写

30 秒回答：**这次要加的东西在项目结构里属于哪儿？**

- 现有模块本该承担？→ 在那扩展，别另起
- 横跨多个模块？→ 抽公共层 / 让某一方主导
- 已有模块叫法不同？→ grep 同义词
- 跟现有都不像？→ 多半该切回完整 design 流程

默认坑：**不思考就往眼前最顺手的文件里加**——加完就成"什么都装的筐"。

### 扫一眼要改的文件现在什么状况

开写前看一眼：文件多长？承担几件事？类有多少方法？新加的是自然扩展还是把它推向"什么都能干"？

健康就直接加；要先收拾（拆长文件 / 抽重函数）就**先收拾再加**，范围锁死为"只搬不改行为"；结构性问题（职责重划 / 模块拆合）→ 停下来回 design 流程。

### 默认写最少的代码

只写用户明确要的。不顺手加：

- "以后可能要"的配置项 / 参数开关 / 抽象层 / 接口 / 工厂
- 没人要的防御性兜底 / try-catch
- 用户没提的边界处理

判据：写完觉得"是不是还得加点 X"——X 是不是用户能感知到的？不是就别加。多出来的代码不是中性的，是后人维护的负担。

### 只动该动的

只改要改的函数。同文件里别的函数丑 / 命名怪——**除非和这次冲突，否则别碰**。新代码风格匹配当前文件已有写法。看到值得改的别处 → "顺手发现：{文件:行号} {问题}，不在本次范围"让用户决定。

### 新逻辑默认放新文件

会被其他地方引用 → 新文件；只一处用的小工具函数 → 就近放。

### 不打补丁分支

冒出 `if (特殊情况) { 特殊处理 }` → **停**。这种分支基本只因为思路没覆盖到这种情况，硬写下去得到的是"为让代码能跑而加的特殊逻辑"。要么改数据结构让它不需要特殊处理，要么明确承认是边界情况并注释说明为什么特殊。

### 反射信号触发就停

- 往 > 300 行文件追加 / 往 > 10 个方法的类加方法
- 函数做的事越来越多超过一屏
- 写第二段"跟上面那段基本一样改了两个变量"的代码
- 函数参数加到第 4 个
- 往 `utils.ts` / `helpers.ts` 万能 util 堆东西
- 新起概念名时先 grep 同名 / 近义命名

完整清单看 `.codestable/reference/shared-conventions.md` 第 7 节。

---

## 写完回写 `{slug}-ff-note.md`

代码写完、验证完、用户确认效果 OK **之后**才动这一步——动手前先建空壳会破坏 ff 的轻体感。

### 自动生成 slug

不问用户。规则：

- 从用户最初的请求里抽 2-4 个英文 kebab-case 词概括动作 / 对象（如 "rename-cwd-helper"、"add-export-button"、"fix-toolbar-layout"）
- 不抽业务名词缩写、不音译中文、保持小写连字符
- 拿不准就保守一点："tweak-{对象}" / "small-{动作}" 也比强求精准好

最终路径：`.codestable/features/YYYY-MM-DD-{slug}/{slug}-ff-note.md`，日期用今天。

### 模板

```markdown
---
doc_type: feature-ff-note
feature: {slug}
date: YYYY-MM-DD
requirement: {req-slug 或留空}
tags: [...]
---

## 做了什么
{1-3 句：解决什么需求 / 加了什么能力，业务视角}

## 改了哪些
- {file:行号区间或函数名} — {一句话说改了什么}
- ...

## 怎么验证的
{1-2 句：跑了哪些验证 / 浏览器走通了哪条路径 / 跑了什么测试}

## 顺手发现（可选，不阻塞）
- {文件:行号} {问题简述} — 不在本次范围
```

**写得真的轻**：每节就那么几行，不要把它写成迷你 design / 迷你 acceptance。这份文档的目标是"半年后有人看 git log 能跳进来 30 秒搞清楚做了啥"，不是替代标准流程。

落盘后告诉用户："已写 `{slug}-ff-note.md`，本次 fastforward 闭环。"

---

## 不做什么

- **不写 design doc / checklist / acceptance**——这就是 fastforward 的意义。要写就去 `cs-feat-design`
- **不跟用户确认方案**——用户让你做小功能就是不想等你开会
- **不在 `.codestable/` 里留 `{slug}-ff-note.md` 之外的新文件**——除非发现值得沉淀的坑 / 技巧，另起对话用 `cs-keep` 写

---

## 什么时候跳出 fastforward

干到一半发现下面任一情况，**停下来告诉用户"这比想象的复杂，建议切回完整流程"**：

- 改动涉及 3 个以上子系统
- 需要引入新术语或和现有术语冲突
- 要打破 `.codestable/requirements/adrs/` 既定的模块边界 ADR
- 用户追加的要求让范围翻倍

切回方式：触发 `cs-feat-design`。已写的代码在 design 里标"已部分实现"即可。

---

## 退出条件

- [ ] 代码写完且用户确认效果 OK
- [ ] `{slug}-ff-note.md` 已落盘且四节填齐（顺手发现可省）
- [ ] 没有未对齐的"顺手发现"（都进 ff-note 末节，留给后续）

---

## 收尾提交

按 `.codestable/reference/shared-conventions.md` 第 4 节"scoped-commit"规则执行。本通道：

- **提交范围**：本次代码改动 + `{slug}-ff-note.md`
- ff-note 落盘后告诉用户"已就绪，是否代为 commit？"，用户明确同意才执行

按 `shared-conventions.md` 第 3 节"feature-ff"收尾推荐顺序逐项一句话提示（用户"不用"立即跳过）：

1. 暴露的坑或拍板的长期约束 → "沉淀到 compound？（`cs-keep`）"
2. 最后问是否代为 scoped-commit

---

## 容易踩的坑

- 完全跳过知识检索就写——这个技能的唯一理由就是让你搜一下再写
- 把搜到的 learning / decision 当"参考"而不是"约束"——decision 拍过板，违反要么重新 decision 要么别做
- 开始写 design doc——fastforward 就是不写 design
- 发现任务变复杂还硬在 fastforward 推——切回成本远低于带着错误方案改到底
- **动手前就建 ff-note 空壳**——破坏 fastforward 的轻体感，必须代码 + 验证完才回写
- **把 ff-note 写成迷你 design / 迷你 acceptance**——四节加一起十几行就够，多了说明这事不该走 fastforward
- **跳过 ff-note 直接 commit**——和 issue-ff 强制 fix-note 同样的理由：没记录后人追溯不了
