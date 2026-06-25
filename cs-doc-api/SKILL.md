---
name: cs-doc-api
description: 给库的公开表面（组件 / 函数 / 命令）逐条目生成参考文档，带清单追踪，支持单条目和批量。信息源是源码本身（与 doc-tutorial 任务导向不同）。触发：用户说"写 API 文档"、"组件文档"、"doc-api"，或 acceptance 后发现新增公开接口。
---

# cs-doc-api

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

doc-tutorial 教你"怎么用 X 做 Y"，doc-api 告诉你"X 的每个零件长什么样、怎么配"。

doc-tutorial 写错可能是表达不清，doc-api 写错就是错——信息源是源码本身，类型 / 默认值 / 签名都有唯一正确答案。**核心规则：不靠猜、不复制改名、每个条目独立读源码**。

---

## 和 doc-tutorial 的对比

| | doc-tutorial | doc-api |
|---|---|---|
| 性质 | 任务导向（Tutorial / How-to） | 参考导向（Reference） |
| 回答 | "如何用 X 实现某个目标" | "X 的每个零件长什么样、怎么配" |
| 粒度 | 一个 feature / 一个场景一篇 | 一个条目一篇 |
| 信息源 | 方案 doc + 用户知识 | **源码本身**（类型 / 注释 / 默认值） |
| 数量级 | 几篇到十几篇 | 几十到上百篇 |

互补：doc-tutorial 引用 doc-api 做详细参考（"完整 props 见 xxx"），doc-api 的"相关条目"链回 doc-tutorial。

## "条目（entry）"

| 项目类型 | 条目粒度 |
|---|---|
| UI 组件库 | 一个组件 = 一个条目 |
| 工具函数库 | 一个模块或函数族 = 一个条目 |
| API Client | 一个 endpoint 族 = 一个条目 |
| CLI 工具 | 一个子命令 = 一个条目 |

初始化阶段确认条目粒度后续保持一致——粒度变来变去清单和搜索都会乱。

---

## 涉及路径

doc-api 产物**不在 `.codestable/` 下**——API 参考是面向外部读者的可发布产物。

- 条目文档 → `docs/api/{slug}.md`
- 条目清单 → `docs/api/manifest.yaml`

`docs/api/` 是默认约定，项目已有其他约定（`reference/` / `components/`）就以项目为准——开始前先确认。

---

## manifest / 模板 / 源码提取

参考材料在同目录 `reference.md`：

- `manifest.yaml` 完整格式与 status 语义
- 条目文档 frontmatter 和正文模板
- 源码提取清单（接口签名、默认值、导出方式等）

本技能正文只保留流程约束：**doc-api 以源码为事实源，不靠猜，不复制上一个条目改名**。

---

## 工作流

### Phase 1：初始化——扫描与清单

1. **确认项目类型 + 条目粒度 + 输出路径**
2. **扫描源码目录**——读 `source_root` 下文件结构，识别公开导出按逻辑分组
3. **生成 `manifest.yaml`**——所有条目初始 `status: pending`；落盘后 `validate-yaml.py --file docs/api/manifest.yaml --yaml-only` 校验；展示给用户 review
4. **用户确认范围**——可标 `skipped`（内部实现）/ 调整分类 / 合并或拆分

### Phase 2：生成

#### 模式 A：单条目模式

适合 1-3 个条目或首次试跑确认质量。

选定条目 → 读 source_files → 按模板生成 → 用户 review → 落盘 → `validate-yaml.py --file {路径} --require doc_type --require entry --require status` → manifest 对应条目 `status: current`

#### 模式 B：批量模式

适合清单里大量 `pending`。

1. **先出样板**——从清单选 2-3 个有代表性的条目（不同 category）走"读源码 → 提取 → 按模板生成"并落盘，状态先 `draft`（不直接进 current——批量模式下样板是"风格参考样本"等整体 review 一起转 current）
2. **用户确认质量标准**——review 这 2-3 篇确认模板 / 详略 / 风格。**这步不能跳**——50 篇全白写就因为用户想要的风格不一样
3. **批量生成**——剩余 `pending` 逐条走"读源码 → 提取 → 生成"，可用 subagent 并行；每条 `status: draft`
4. **整体 review**——批量完成展示概况（条目数 / 跳过数 / 待确认数）；review 前先 `validate-yaml.py --dir docs/api --require doc_type --require entry --require status` 批量校验
5. **确认落定**——用户确认后把样板和批量产出一起改 `status: current`

**批量模式硬规则**：

- **每个条目独立读源码**——即使批量也不允许复制上一个改名。两个看起来很像的接口经常有微妙差异
- **样板确认不可跳**
- **源码结构特殊（动态导出 / 代码生成）暂标 `skipped` 加 note**——硬猜出来的文档比没文档更有害

### Phase 3：增量更新

代码变更后同步文档。三种入口任选：

- `search-yaml.py` 搜 `status=outdated`——架构 check 或上次更新已标记的
- 对比 `manifest.yaml` 里 `last_scanned` 之后变更的源码文件
- `search-yaml.py --sort-by last_reviewed --order asc` 按最久没复核的排在前主动复核

重新读源码 → 对比已有文档 → 增量更新变化部分 → `validate-yaml.py` 校验 → `status: current` + `last_reviewed` 当天。

---

## 与其他工作流的关系

| 来源 | 关系 |
|---|---|
| `cs-feat-accept` | 验收后新增/修改库公开接口 → 推送"需要更新 doc-api 吗？" |
| `cs-doc-tutorial` | doc-tutorial 引用 doc-api 做详细参考；doc-api "相关条目"链回 doc-tutorial |
| `cs-feat-design` | 方案第 2 节可作 doc-api 补充信息源（**但以源码为准**） |
| `cs-keep` | doc-api "注意事项"与 compound 沉淀重合时交叉引用而不重复写 |

---

## 退出条件

**Phase 1**：manifest.yaml 已落盘 + 用户已确认范围（含 skipped 理由）+ 粒度和输出路径已确认

**Phase 2 单条目**：条目按模板生成 + frontmatter 完整 + API 参考节信息来源于源码提取（非编造）+ 用户确认 + manifest 已更新

**Phase 2 批量**：样板（2-3 篇）已获用户确认 + 所有 pending 条目已生成或标 skipped + 用户做了整体 review + manifest 所有条目 status 已同步

**Phase 3**：outdated 条目已全部更新或确认不需更新 + manifest 无残留 outdated（除非用户明确暂缓）

---

## 容易踩的坑

- 没扫清单就写文档——可能遗漏或重复
- 没读源码就写 API 参考——doc-api 核心价值是准确反映源码
- 复制上一个条目改名——必然漏掉微妙差异
- 批量模式跳过样板确认——50 篇全白写
- 把 spec 信息（不变量 / 测试约束）写进 doc-api——属于 `.codestable/`
- doc-api 和 doc-tutorial 内容高度重叠——其中一份定位有误
- `manifest.yaml` 直接删行——改 `status: skipped` 并写 note
- 源码接口不存在却在文档写了——以源码为事实源不编造
