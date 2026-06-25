---
name: cs-audit
description: 系统审计——从代码中主动发现 bug 隐患、安全漏洞、性能问题、可维护性债务和架构偏离，产出批量发现清单。触发：用户说"审查系统"、"审计代码"、"扫描问题"、"找找 bug"、"有什么可以优化的"。
---

# cs-audit

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

`cs-issue` 等你报 bug，`cs-refactor` 等你指优化点，`cs-keep` 等你说"这事记一下"——但"我也不知道哪有问题，你先扫一遍看看"这个诉求没人接。`cs-audit` 补上这块：**在用户限定的范围内主动扫描，产出一份按严重度 × 性质交叉分类的发现清单**。

本技能只发现、不定修。修是 `cs-issue` / `cs-refactor` 的事。

---

## 文件放哪儿

```
.codestable/audits/{YYYY-MM-DD}-{slug}/
├── index.md           # 速览：范围、总评、发现清单交叉矩阵
├── finding-01.md
├── finding-02.md
└── ...
```

日期取审计当天。slug 短到一眼看出审计目标（`auth-module`、`order-flow`、`payment-security`）。

所有 audit 文档带 YAML frontmatter（`doc_type` 分别为 `audit-index` 和 `audit-finding`）便于 `search-yaml.py` 检索。

---

## 维度矩阵（交叉分类）

每个发现打两个标签：

**性质**：`bug` | `security` | `performance` | `maintainability` | `arch-drift`

**严重度**：`P0`（必须修）| `P1`（应该修）| `P2`（可以修）

交叉示例：
- `security` × `P0`：SQL 注入、明文存密码
- `bug` × `P1`：特定边界条件下空指针，实际触发概率低
- `performance` × `P2`：循环内多余的对象分配，热点路径才需要改

另外每个发现带 **置信度**（`high` / `medium` / `low`）和**建议动作**（`cs-issue` / `cs-refactor`）。

完整模板见 `reference.md`。

---

## 工作流

### Phase 1：范围收敛

审计不能全仓库盲扫——成本高、噪音大。先帮用户把范围收窄到可执行。

问用户三样（有一样就能起步）：

1. **关键词**："跟 auth / payment / upload 相关的"
2. **模块 / 目录**："`src/services/` 下面"
3. **一段话描述**："最近用户反馈订单页慢，帮我扫一下订单相关代码"

用户描述已清楚直接进 Phase 2。用户说"整个项目都扫" → 推回去——建议先扫最常改的模块或最近出过问题的区域。

收敛后给用户确认：**"扫 `src/services/order/` 和 `src/api/order.ts`，约 12 个文件，看安全 / 性能 / bug 隐患三个维度。范围 OK 吗？"**

### Phase 2：扫描

按用户圈定的维度逐维扫描（用户没指定就全扫 5 维）：

- **bug 隐患**：空值路径、边界条件缺失、竞态条件、错误处理吞异常、类型断言无保护
- **安全**：注入风险、敏感数据暴露、权限校验缺失、不安全依赖
- **性能**：N+1 查询、重复计算、无缓存热点路径、内存泄漏、无分页全量加载
- **可维护性**：超长函数（> 80 行）、圈复杂度 > 15、重复逻辑块、神秘常量、循环依赖
- **架构偏离**：代码违反 `.codestable/requirements/adrs/` 已拍板决策、分层泄漏、跨模块隐式耦合

扫描时用 Glob / Grep / Read 真实读代码。每条发现必须记录 `文件:行号` + 具体代码片段。

**上限**：每种维度最多报 5 条。不是凑数——够了就停，不够也不硬凑。

**置信度口径**：
- `high`：代码路径可确认触发，影响明确
- `medium`：静态分析能定位问题，但触发条件不确定
- `low`：线索可疑，需要进一步确认但值得标记

### Phase 3：定级 + 产出

1. 每个发现打性质 + 严重度 + 置信度 + 建议动作
2. 写 `index.md`：范围、总评、发现清单表格（交叉分类）
3. 逐条写 `finding-NN.md`

**先写 index 再写 finding**——这个顺序让 AI 先做整体判断再展开细节，避免陷入单条发现迷失全局。

### Phase 4：建议下一步

index.md 末尾给优先级建议：

- "P0 的 3 条建议立刻开 issue 修"
- "P1 的 5 条可以排下个迭代"
- "P2 的 4 条有空再看"

用户选哪条 → 路由到 `cs-issue` 或 `cs-refactor`。`cs-audit` 自己不修。

---

## 与相邻技能的边界

| 技能 | 触发 | cs-audit 怎么对待 |
|---|---|---|
| `cs-issue` | 用户报已知 bug | audit 发现 bug 后建议开 `cs-issue` |
| `cs-refactor` | 用户指已知优化点 | audit 发现可优化点后建议开 `cs-refactor` |
| `cs-keep` | 沉淀单点经验 / 决策 | audit 是批量扫多维度发现新问题，cs-keep 是把已知的事写下来 |
| `cs-domain` | 维护 ADR / CONTEXT.md | cs-domain 写决策，cs-audit 检查代码是否偏离已拍板的 ADR |
| `cs-security-review` | 安全审查 | audit 的安全维度是轻量扫描，深度安全审查走专项 |

---

## 守护规则

- **不盲扫全仓库**——Phase 1 必须收敛范围，没范围不动手
- **每条发现必有证据**——file:line + 代码片段 + 为什么构成问题。不准出现"感觉不好"、"可能有问题"类无证据发现
- **置信度必标**——不准所有发现都标 `high`
- **每种维度上限 5 条**——逼 AI 挑最值得报的，不是 dump 所有发现
- **只发现不定修**——cs-audit 不出代码改动。出现"顺便修了"就算越界
- **架构偏离引用 ADR**——不准凭记忆判断架构应该长什么样，必须读 `.codestable/requirements/adrs/` 对照
- **旧审计标注过期**——同名模块新审计覆盖旧审计时，旧 index 标 `status: superseded` + `superseded-by: {新目录}`

---

## 退出条件

- [ ] 审计范围已和用户确认
- [ ] 各维度扫描完成，至少有一个发现（若零发现：告知用户此范围内未发现明显问题）
- [ ] index.md 含完整交叉分类表
- [ ] 每条发现 file:line + evidence + confidence
- [ ] 每种维度 ≤ 5 条
- [ ] 给用户按优先级排列的下一步建议

---

## 相关文档

- `reference.md` — index.md / finding-NN.md 模板
- `.codestable/reference/shared-conventions.md` — 跨工作流共享口径
- `.codestable/requirements/adrs/` — 架构偏离类发现对照源
