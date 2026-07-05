---
name: cs-req
description: 能力愿景维护。触发：起草/回填/更新 requirements，或 design/acceptance 需要 req delta。
---

# cs-req

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`.codestable/requirements/` 是项目的"能力清单"——每份描述**一个能力因什么问题而产生、怎么解决、边界在哪**，写成人话非技术读者也能看懂。架构文档讲"怎么搭"，需求文档讲"为什么要有"。

**req 是系统的能力愿景层**——描述"用户需要什么、系统提供什么能力来满足"。三层时间深度用一个 `status` 字段区分：

- `draft`：用户有这个需要，系统还没实现（未来愿景）
- `current`：系统正在满足（现在的能力）
- `outdated`：曾经满足过，现已移除或不再维护（过去的痕迹）

**draft req 可以独立于实现存在**——用户说"我想要 X 能力"但还没想好什么时候做，可以先落一份 `status: draft` 的 req 把愿景定下来，后续 roadmap 排期、design 对齐时都有稳定参考。**不做 roadmap 规划不等于不该有愿景文档**。

**draft → current 的主路径是 feature-acceptance**：能力实现完成、验收通过后，acceptance 触发 cs-req update 把 `status` 从 `draft` 改为 `current`，同时按实际实现刷新用户故事 / 边界（保留原始愿景不被覆盖，只在文末加变更日志）。

**backfill 路径保留**：已经在跑但从没写过 req 的能力，走 backfill 直接落 `status: current`。

**不记"怎么分步实现"**——那是 `cs-epic` planning 阶段的事（内部仍落 roadmap 文档）。req 只回答"要什么、为什么"，不回答"第几个 sprint 做、拆成几个子 feature"。

需求文档价值在**扫一眼就抓到重点**——用户故事在最前、痛点和解法各一段短的、边界用列表。AI 容易破坏这个特性的几种问题：

- 写成 PRD 格式（字段堆）——读者要一格一格读才能拼出全貌
- 语气过于 explain——像在上课不是介绍
- 起花哨标题或用比喻——读者要读半段才知道这能力是什么
- 把实现细节塞进来——"通过 XXX 服务调用 YYY 接口"

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md`。一份样例看 `.codestable/reference/requirement-example.md`——起草前读一遍对齐语气。

---

## 适用场景

- brainstorm 阶段触发：磋商后愿景清晰 → `draft` 起草愿景落 `status: draft`，后续 design 和 roadmap 都有稳定对齐基准
- feature-design 阶段触发：新能力首次被设计方案化 → `draft` 起草愿景（用户故事 / 痛点 / 解法 / 边界），落 `status: draft`
- feature-acceptance 第 6 节触发：draft req 对应的能力实现完成 → `update` 升级为 `current`（保留愿景，追加变更日志）；从未写过 req 的已存在能力 → `backfill` 直接落 `current`；已有 current req 的能力改了边界 / 用户故事 / pitch → `update` 刷新
- 用户主动盘点：已经在跑的能力从没写过 req（`backfill`）
- 用户主动修订：能力演进了要刷新（`update`）
- 用户主动起草愿景：还没排期的未来需求先落一份 `draft` req 把定位定下来

不适用：拍板架构决策 / 加术语 → `cs-domain`；写单次 feature 方案 → `cs-feat` design 阶段；操作性沉淀 → `cs-keep`；写外部"怎么用" → `cs-docs` tutorial mode；大需求拆几轮做 → `cs-epic`。

---

## 单目标规则

每次只动一份文档：

- **draft**：给还没实现的新能力起草愿景（用户故事 / 痛点 / 解法 / 边界），`status: draft`
- **backfill**：给已存在但从没写档的能力补一份，`status: current`
- **update**：按新素材 / 实现变化刷新一份

为什么不允许多份？req 价值在**每份都被读过**——一次吐多份用户没精力逐份 review，最后要么粗糙合入要么放着不看。

### 允许"没有 requirement 的 feature"

纯内部重构 / 技术债清理 / 工具链改造**不新增用户可感能力**的 feature 不强制要 req。feature-design 标"本次不新增能力"即可，不要为凑一份硬写。

---

## 工作流

### Phase 1：锁定目标

模式 + 目标文档 + 范围。

**draft 模式**：能力还没实现，凭用户素材（口述 / 产品想法 / 用户反馈）起草愿景。用户故事和痛点要真切，边界要写清楚"不管什么"——愿景的价值正在于把"要做什么"和"不做什么"的线画清楚。

一份 req 描述**一个能力**。用户说"把这模块的需求全写了"先问清：模块对外提供几个独立能力？每个独立能力一份不要塞一起。

### Phase 2：读取材料

**共同必读**：`VISION.md`（需求中心索引）+ `requirements/` 下其他 req（判断要不要互引、有没有重复）+ 用户素材（口述 / 产品想法 / 用户反馈 / 已有 feature 散落需求描述）。

**按情况读**：可能承载这能力的 architecture doc（用于 `implemented_by`）；相关已有 feature 方案；compound 沉淀（`python .codestable/tools/search-yaml.py --dir .codestable/compound --query "{能力关键词}"`）。

**draft 额外**：和 roadmap 对一眼——如果已经有 roadmap 提到了这个能力，读一下了解预期的拆解方向，但 req 本身不绑定 roadmap 条目。
**update 额外**：当前文档全文 + `last_reviewed` 之后相关实现的变化（`git log` 粗扫 `implemented_by` 对应的代码模块）。

### Phase 3：一次性起草

按下文"文档结构"写**完整初稿**不分批。用户故事 / 痛点 / 解法 / 边界四块经常有跨块矛盾（用户故事描述的场景和解法描述的路径对不上），只有放在一起才看得出来。

### Phase 4：自查清单

review 前自跑一遍。每条针对一种 AI 默认会犯的错：

1. **语气是人话吗**——挑一段读出来像在跟朋友介绍吗？还是像在上课 / 写 PRD？后者就重写
2. **标题平铺吗**——直接说能力是什么，不要比喻 / 花哨。"修 bug 时先探索和分析" > "让 AI 当你的第一个读者"
3. **用户故事够具体吗**——每条要能想象出具体场景。"作为用户希望系统好用"是废话
4. **有没有把实现细节塞进来**——不该出现"通过 X 接口"、"用 Z 算法"。有就移到 architecture
5. **边界写了没**——没写边界的需求会被误用
6. **pitch 能当宣传词吗**——去技术化、一句话、读者不用上下文也能看懂
7. **update 专项**：本次新加 / 改的段落都有素材或实现依据？凭空加听起来更完整的描述是漂移开端
8. **draft 专项**：愿景写清楚了吗——一个不了解项目的人读完"为什么需要"能复述这能力要解决什么痛点？

自查结果简短汇报——发现问题就说怎么处理（删 / 改 / 补），不走过场。

### Phase 5：用户 review

完整初稿贴给用户。改到用户明确"可以了"。

### Phase 6：落盘 + 索引更新

- draft：写入 `requirements/{slug}.md`，`status: draft`、`last_reviewed` 当天
- backfill：写入 `requirements/{slug}.md`，`status: current`、`last_reviewed` 当天
- update：覆盖已有，`last_reviewed` 当天；结构性改动大则文末 `变更日志` 加一条；draft → current 的状态升级是结构性改动，**必须**加变更日志
- **索引更新**：更新 `requirements/VISION.md`——按 status 分组列出所有 req，每条带 pitch 一句话和 status 标记

---

## 文档结构

### frontmatter

```yaml
---
doc_type: requirement
slug: {英文连字符；和文件名一致}
pitch: {一句话去技术化说清楚这能力，可直接当宣传素材}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
implemented_by: []   # 承载的 architecture doc slug 列表，可空
tags: []
---
```

### 正文节

```markdown
# {标题 — 直接平铺说这能力是什么，不玩比喻}

## 用户故事

- 作为 {具体角色 / 处境}，我希望 {能做什么}，而不是 {现在怎么难受}
- ...（2-4 条，每条一行）

## 为什么需要

一段短的，讲这能力不存在时的痛点。非技术读者也能读懂。直接当宣传素材——痛点描述得越真切，对外讲这系统解决什么问题时就越有抓手。

## 怎么解决

一段短的，讲这能力大概怎么工作。**不写实现细节**——不提模块名 / 接口 / 算法。讲"用户体验上发生了什么"就够。

## 边界

- 它不管什么（哪些事情看起来相关但它不负责）
- 什么情况下别用它
- 用的前提（用户需要先做什么）
```

### 变更日志（update 模式才有）

```markdown
## 变更日志

- YYYY-MM-DD：{一句话描述}
```

---

## 硬性边界

1. **语气是人话不是 PRD**——字段堆 / 上课腔 / 花哨标题都不行
2. **不写实现细节**——只讲"是什么 / 为什么 / 解决什么"，涉及实现的一律移到 architecture
3. **不替用户编用户故事**——必须来自用户素材或可追溯场景（已有 feature / 用户反馈 / explore），不允许凭空造"听起来合理"的使用场景
4. **单目标**——一次一份
5. **不改代码、不改 architecture doc**——只写 req。发现 arch 有问题记"观察项"
6. **不发散**——范围外问题记观察项

---

## 退出条件

- [ ] 已锁定单一模式 + 单一目标
- [ ] Phase 4 自查清单逐条跑过并汇报
- [ ] frontmatter 完整（`doc_type: requirement` / `pitch` / `status` / `last_reviewed`）
- [ ] 正文四节齐全（用户故事 / 为什么需要 / 怎么解决 / 边界）
- [ ] 用户故事每条能想象具体场景，无"希望系统好用"废话
- [ ] 没有实现细节塞进来
- [ ] `pitch` 读起来能直接当宣传词，draft 也能直接当宣传词（愿景也需要卖得出去）
- [ ] draft：status 为 draft，未编造实现细节，边界画清楚了
- [ ] update：结构性改动有 `变更日志`（含 draft → current 状态升级）
- [ ] 用户 review 通过
- [ ] 没有顺手改代码 / architecture / 其他 spec
- [ ] 没有范围外文档改动

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-domain` 配合 | req 写"为什么要有"、cs-domain 管 CONTEXT 术语 / 拍板 ADR；ADR frontmatter 可用 `relates_to: [requirements/{req-slug}]` 反向链 |
| `cs-brainstorm` 可触发 | 磋商后愿景清晰时可触发 `draft` 模式起草愿景 req |
| `cs-feat` design 阶段可写 | design 读已有 req 对齐用户故事和边界；新能力首次设计方案化时触发 `draft` 模式起草愿景 req |
| `cs-feat` acceptance 阶段主路径 | 验收统一处理 req 落档：draft req 对应的能力实现完成触发 `update`（draft → current，保留愿景追加变更日志）；从未写过 req 的能力触发 `backfill`（直接落 current）；已有 current req 的能力改变触发 `update` 刷新 |
| `cs-epic` 配合 | req 记"要什么、为什么"、roadmap 记"怎么分步实现"。roadmap 条目可关联 req slug，但 req 不绑定具体 roadmap。draft req 不给 roadmap 压力——愿景可以先于排期存在 |
| `cs-onboard` 创建者 | onboard 建 `requirements/` 空目录 + `VISION.md` 空骨架 |

---

## 常见错误

- 把 draft req 当 backfill 写——能力还没实现但写了 `status: current`，或编造了解法细节假装已存在
- backfill 时没确认能力是否真的在代码里跑——凭用户一句话写了一份"听起来合理"的 req
- draft req 里塞实现细节——还没做就先定了怎么实现，应该在 design 阶段定
- draft req 边界写太宽——愿景的价值在画线，什么都想要等于什么都没说
- 写成 PRD 字段堆 / 语气像在上课 / 标题用比喻 / 用户故事太抽象 / 把实现细节塞进来 / 没写边界
- `pitch` 塞了技术黑话——宣传时抽不出来用
- 一次起草多份——用户 review 不深
- 范围太大塞了多个独立能力——拆
- update 凭空加段——内容会越写越飘离实际
