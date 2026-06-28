# CodeStable 共识与约定

所有 cs-* 技能共享的口径。由 `cs-onboard` 分发到项目 `.codestable/convention.md`，各技能开头一行「遵循 `.codestable/convention.md`」即可，不再各自重复样板。

源真相在技能包 `cs-onboard/reference/convention.md`，维护入口是 `cs-convention`。改了它，已 onboard 的项目重跑 `cs-onboard` 同步。

## 两轴模型

CodeStable 把开发活动建模成两根正交的轴：

- **变更轴**——要做、做完会关闭的事（issue / epic）。是增量。
- **现状轴**——现在是什么、为什么这样（context：词汇表 + 取舍说明）。是这些增量积分出的当前真相。

变更轴关闭时，把毕业的取舍回写现状轴。两轴谁都不讲对方的事：**context 不记历史叙事，issue 不长期描述现状。**

人在环：AI 是高效执行体，程序员对整体把控负责。

## 启动必读

任何 cs-* 技能动手前先读 `.codestable/attention.md`（项目硬约束 + 启动注意 + **变更轴载体**字段）。缺失视为骨架不完整，提示先补齐或跑 `cs-onboard`，不要回退到外部 AI 入口文件。

## 变更轴载体

`attention.md` 顶部记录本项目的变更轴落在哪：

- `载体: github` —— issue / epic 是 GitHub 原生实体，用 `gh` 操作
- `载体: local` —— issue / epic 是 `.codestable/{issues,epics}/` 下的 md spec（frontmatter 带 status）

cs-issue / cs-epic / cs-audit 启动读它决定产出形态。

## 路径与命名

- 所有本地产物在 `.codestable/` 下。
- slug：与当前对话语言一致，一眼看出是什么。英文用小写连字符 kebab-case；中文等直接用词，避免空格和 `/ \ : * ? " < > |`。例外：对外发布的 `docs/` 默认英文（URL / 跨语言协作友好），项目可覆盖。
- 日期：取事情发生 / 提报当天，定了不动。
- 会产生草稿的工作给子目录：主文档对外口径，旁边 `drafts/` 随便堆。

## 单目标规则

每次只动一份文档 / 一件事。一次吐多份用户 review 不过来，最后要么粗糙合入要么放着不看。一次扔多个目标 → 选一个，其余下次。

## 不发散 / 顺手发现

只动该动的。范围外发现值得改的别顺手做，记一条：

> 顺手发现：{位置} {问题简述}。不在本次范围，留后续。

混进来的顺手改让 review 和 git blame 分不清这次到底改了什么。

## 人在环 checkpoint

多阶段流程每阶段末留 checkpoint 让用户把关；拍板（选方案 / 定优先级 / 填没说清的角落）归用户，AI 不自己挑一个掩盖分歧。

## 收尾提交（scoped-commit）

一件事走完把产物提交为一个 commit：范围 = 本次代码 + 相关 spec + 本次实际改过的 context。无关的顺手改不进。提交前用户没明确同意不要 `git commit`。message 一句话说清做了什么。

## 退出条件通用骨架

每个技能退出条件都含（各技能再加自己独有的）：

- [ ] 锁定单一目标
- [ ] 用户 review 通过
- [ ] 没顺手改代码 / 其他 spec / 范围外文档
