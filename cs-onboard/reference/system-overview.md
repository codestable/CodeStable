# CodeStable 体系总览

CodeStable 是面向严肃工程的 AI 编码工作流。它编排的是**软件本身的生命周期**——不是编排 Agent。人在环：程序员对整体把控负责，AI 是高效执行体。

## 两根正交的轴

开发活动归到两根轴，产物聚在 `.codestable/`：

### 变更轴——要做、做完会关闭的事

增量。落在 GitHub 或本地（onboard 时选，见 `attention.md` 的 `载体` 字段）。

- `cs-issue` — 一件可关闭的变更：bug / 重构 / 小功能 / 杂务，tag 分类型。闭环：记清楚 → 定位 → 改 + 验证 → 关闭回写
- `cs-epic` — 大到塞不进单条 issue 的变更：先定架构（模块拆分 + 接口契约），再拆成带依赖 DAG 的子 issue
- `cs-audit` — 主动扫描发现器 + 对账 context，产出 triage 清单，选中的升级成 issue

### 现状轴——现在是什么、为什么这样

变更积分出的当前真相，落在 `context/`。

- `cs-context` — 领域词汇表 + 取舍说明（happy path / 边界 / 为什么需要灵活性）。只承载代码读不出来的东西，不引用代码位置，不记历史叙事

**两轴的接口**：变更轴关闭时，把毕业的取舍回写现状轴。context 不记历史（那在关闭的 issue 里），issue 不长期描述现状。

## 横切与周边

- `cs-code` — 写代码的纪律（只写当前要的、漂移那刻停）。正交于两轴，任何动手写代码都用
- `cs-keep` — 坑点 / 技巧 / 选型 / 调研沉淀到 `compound/`，纯 markdown，全文检索
- `cs-note` — 一两行启动必读追加到 `attention.md`
- `cs-clarify` — 想法还模糊时的讨论 + 分诊入口，聊清楚后路由到直接写或 `cs-epic`
- `cs-convention` — 维护体系共享口径（分发成 `.codestable/convention.md`）
- `cs-onboard` — 把仓库接入体系
- `cs-doc-tutorial` / `cs-doc-api` — 写给外部读者的指南 / API 参考

## 路由

没有 `.codestable/` → 先 `cs-onboard`。其余诉求由 `cs` 根入口按两轴分诊，详见各子技能。

## 进一步参考

- `.codestable/convention.md` — 体系共识与约定（两轴 / 启动必读 / 载体 / 命名 / 单目标 / scoped-commit / 退出骨架）
- `.codestable/reference/tools.md` — `search-yaml.py` / `validate-yaml.py` 用法（本地载体的 yaml frontmatter；compound 走全文检索）
- `.codestable/reference/maintainer-notes.md` — 断点恢复、新增子工作流登记
- `.codestable/attention.md` — 启动必读项目注意 + 变更轴载体
