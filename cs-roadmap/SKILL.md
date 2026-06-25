---
name: cs-roadmap
description: 把"大到塞不进单个 feature"的需求做成完整事前规划：概设 + 接口契约 + 子 feature 拆解清单，放在 `.codestable/roadmap/{slug}/`。两种模式 new / update。触发：用户说"我想要一个 X 系统"、"帮我把这块需求拆一下"、"开一份 roadmap"，或 feature-design 阶段发现需求太大。
---

# cs-roadmap

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

`.codestable/roadmap/` 是项目的"规划层"——每个子目录承载一块大需求，主文档由三块构成：

1. **概设**：这块大需求要怎么搭、拆成哪几个模块 / 组件、各自职责
2. **架构层详设**：模块之间的接口契约、共享数据结构、跨 feature 的协议
3. **子 feature 拆解**：把方案分解成一串带依赖关系的子 feature 种子，feature 流程一次消费一条

三块**一起**作为这块大需求所有子 feature 的共同约束——每条子 feature 进 `cs-feat-design` 时，roadmap 第 2 块的接口契约就是它的**硬约束输入**（不能违反，要改先回 roadmap update）。

**为什么 roadmap 不直接写 ADR**：ADR（`requirements/adrs/`）记的是"已经拍板的稳定结构性决策"，roadmap 记的是"还没落地、可能还会变"的前瞻性接口契约。等子 feature 真正落地、对应接口稳定后，由 `cs-feat-accept` 盘点出来的领域影响触发 `cs-domain` 写 ADR——roadmap 完成过渡使命后归档。

**为什么单独一层**：requirements 记"要什么 + 怎么定义术语 + 拍板了哪些决策"（愿景 + 领域），roadmap 记"怎么分步实现"（执行）。把执行规划塞进 requirements 会把"要什么"和"打算怎么实现"混起来。

**为什么文件夹不是单文件**：拆解过程会产生草稿 / 调研 / 方案对比 / 白板转述，塞一份 md 会乱又舍不得删。每个 roadmap 一个子目录，主文档对外口径，旁边 `drafts/` 随便堆。

**规划原则**：roadmap 不是"任务列表"，而是一次可执行路线设计。动笔前要先把目标、约束、风险、依赖、可验证完成信号想清楚；拆出来的每条子 feature 都要能独立验证；整份 roadmap 交给用户前必须先做一次自我批判，修掉含糊验收、错误依赖和被打包过大的条目。

**推进原则**：一个长期软件任务能不能稳步推进，取决于有没有把"当前状态 → 下一步 → 验证 → 修复 → 记录"闭环设计清楚。roadmap 阶段要提前识别基线是否可能已坏、哪些条目承担 safety net / polish / harden、哪些产物必须落盘、哪些经验要回写到 CodeStable 知识层。没有这些，后续 feature 只是顺序执行，不是可恢复、可审计的推进。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md`。主文档和 items 完整模板看同目录 `reference.md`。

---

## 适用场景

- 用户描述"一眼看出做不完"的大需求（"加权限系统"、"做通知中心"、"接 SSO"）
- `cs-brainstorm` 判为 case 3 移交过来（brainstorm 只做分诊，不做拆解）
- 已有 roadmap 加新子 feature / 改依赖 / 调顺序 / 标废弃
- feature-design 发现要做的事实际是多个 feature 集合，先退回拆

不适用：单 feature 能装下 → `cs-feat`；描述能力"是什么、边界" → `cs-req`；拍板长期规约 / 架构选型 / 加术语 → `cs-domain`；操作性沉淀 → `cs-keep`。

---

## 模式分流

| 用户说什么 | 模式 |
|---|---|
| "拆一下 X 需求"、"开一份 X 的 roadmap"、"我想要一个 X 系统" | `new` |
| "往 {已有 roadmap} 加子 feature"、"重排顺序"、"标 drop" | `update` |

判断不出问用户。

---

## 单目标规则

每次只动一份 roadmap。一次扔出"我想要 X 和 Y"先选一个，另一个下次。理由同 req / arch——一次吐多份用户 review 不过来。

---

## 目录结构

```
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md       主文档：背景 / 范围 / 模块拆分（概设）/ 接口契约（架构层详设）/ 子 feature 清单 / 排期
├── {slug}-items.yaml       机器可读清单（feature-design 读、feature-acceptance 回写）
├── {slug}-roadmap-review.md 独立规划审查报告（人审前 gate）
└── drafts/                 可选，调研 / 讨论 / 草稿
```

`{slug}` 小写字母 / 数字 / 连字符，和大需求一致（`permission-system`、`notification-center`）。平铺不嵌套 epic / sub-epic。`drafts/` 按需建，AI 不强制归档。

---

## 工作流

### Phase 1：锁定目标

模式 + 目标 + 范围。new 模式先敲定一个英文 slug（参考现有 req / arch slug 习惯）。

### Phase 2：读取材料

**共同必读**：`.codestable/attention.md` + 用户素材 + `roadmap/` 其他 roadmap（防重复）+ `requirements/` 相关 req + `requirements/CONTEXT.md` + `requirements/adrs/` 相关 ADR。

**按情况读**：
- 相关 compound 沉淀：`grep -r "{大需求关键词}" .codestable/compound/`
- 已有相关 feature 方案
- 项目可用验证命令 / 已知基线：从 `.codestable/attention.md`、架构 doc、历史 acceptance、README / package scripts / CI 配置里找 build / typecheck / lint / test / e2e / 浏览器验证入口。roadmap 不直接跑完整命令，但要知道后续每条 feature 靠什么验证

**update 额外**：当前主文档全文 + items.yaml 当前状态 + 已启动 / 完成的子 feature 的 design / acceptance。

### Phase 3：拆解与起草

按 `reference.md` "主文档结构"和"items.yaml 格式"写**完整初稿**不分批。

**先写深度规划底稿**（可写进主文档第 6 / 7 节，不必单独成文件）：

- **目标完成信号**：这块大需求做到什么可观察状态才算完成，不写"能力完善"这种感受词
- **Top 3 风险与缓解**：最可能翻车 / 最难回滚 / 最容易漏到上线后才发现的三件事，各自写清本 roadmap 怎么降低风险
- **非显然依赖**：外部系统、数据迁移、现有模块约束、用户拍板项，哪些会卡住后续 feature
- **关键假设**：不是用户原话、但本次规划依赖它成立的判断；review 时让用户能精确反驳
- **基线与验证入口**：后续 feature 应优先使用哪些命令 / 手工验证入口；如果当前仓库很可能缺测试或基线不稳，要在拆解里安排 safety net / characterization 条目
- **交付物落点**：每条子 feature 完成后应该真实落在哪些代码 / 配置 / 文档 / roadmap 状态里，避免只在汇报里说完成
- **知识回写点**：哪些约定、环境坑、跨 feature 规则如果被验证成立，应在 acceptance 收尾时沉淀到 attention / learning / decide / guide

**拆解纪律**：

0. **先做架构方案再拆 feature**——顺序：先想模块拆分（概设第 3 节）→ 模块间接口 / 数据结构 / 协议（详设第 4 节）→ 才把方案分解成子 feature（第 5 节）。**架构方案不清楚就硬拆 feature，结果是每个 feature 各自重新发明轮子、接口对不齐**
1. **接口契约要写到 feature 可拿来当硬约束的程度**——函数签名 / 数据结构 / 协议字段 / 错误码这一级。讲不到这级回去想。无跨模块接口（如纯前端样式调整）就明确写"无跨模块接口"
2. **每条子 feature 能当独立 feature 流程跑完并独立验证**——能单独写 design / 实现 / 验收，完成后能拿出明确证据（命令、测试、截图、接口响应、文档归并）。跑不下来颗粒度不对
3. **依赖图必须是 DAG**——A 依赖 B 写清楚，别循环
4. **依赖关系要有具体理由**——"B 依赖 A，因为 A 提供 XX 表结构"而不是"A 先做"
5. **先列一条最小闭环**——做完后能端到端跑通最窄路径的标第一条
6. **明确不做的边界**——用户脑子里的"权限系统"可能包括审计日志 / 数据脱敏，不打算覆盖就写进"明确不做"
7. **不替用户决定优先级**——技术依赖之外的排序让用户拍板
8. **最后要有收口 / 硬化意识**——UI、全栈、权限、安全、迁移类大需求，如果前面条目只覆盖功能上线，要补一条收口型子 feature 或在最后一条里明确覆盖：错误态、空态、边界输入、安全、性能、回归扫尾、文档归并
9. **条目数量由任务形态决定**——不要为了凑固定数量合并 / 拆散。能独立验证、交付一件 coherent thing 就是一条；名字里需要写"和 / 以及"通常说明塞了两条
10. **验收词要可证伪**——每条子 feature 的描述和 notes 里不写"完善 / 优化 / 打通"这类空词，改成"输入 A 时得到 B"、"页面 X 展示 Y"、"命令 Z 通过"
11. **需要安全网时先建安全网**——brownfield 重构、迁移、核心路径改动、历史测试薄弱时，第一条或前几条应先补 characterization / baseline tests / 观测手段，再改行为
12. **每条都要能断点续跑**——items.yaml 的 `status` / `feature` 是恢复锚点。条目 notes 里写清阻塞项、跳过原因、外部依赖，不靠对话记忆

### Phase 4：自查清单

独立 review 前自跑一遍汇报处理：

1. 模块拆分讲清了吗？每个模块职责一句话能说出来？
2. 接口契约写到可执行程度了吗？feature-design 看完不需要回来问就能直接照着实现？
3. 每条子 feature 的 slug 规范？（grep `.codestable/features/` 确认不冲突）
4. 每条描述一句话讲清楚？讲不清就拆得不够或 scope 太模糊
5. 依赖关系是 DAG？有没有自指 / A→B→A 回环
6. 最小闭环真的最小？第一条做完能独立给用户演示点什么？
7. "明确不做"有没有写？没写就说"没有明确不做"
8. 和已有 req / arch 有没有矛盾？有就写"和 req-X 冲突待用户决定"，不偷偷选边
9. **update 专项**：本次新加 / 改条目都有素材依据？凭空"加一条让看起来更完整"是漂移
10. **update 专项**：改了接口契约的话，已 in-progress / done 的子 feature 受影响吗？影响到的列"观察项"提示用户
11. **可证伪性自查**：每条完成信号是不是 yes/no？有没有"体验更好 / 更稳定 / 支持完善"这类无法核对的词？
12. **条目原子性自查**：有没有一条实际包含两个可独立验收的交付？名字或描述里出现"和 / 以及 / 同时"时重点复查
13. **最弱依赖自查**：哪条失败会拖垮最多后续条目？它的前置验证和风险缓解是否足够早？
14. **收口覆盖自查**：是否覆盖 polish / harden / regression sweep？如果没有，写清为什么本 roadmap 不需要
15. **基线自查**：是否知道后续 feature 的验证入口？当前基线不稳 / 测试薄弱时是否安排了 safety net？
16. **交付物自查**：每条做完后是否能从仓库事实看到产物，而不是只从汇报看到？
17. **知识回写自查**：哪些规则或坑会影响后续 feature？是否放进观察项，等 acceptance 验证后触发对应沉淀流程？

### Phase 5：候选落盘 + 独立 review gate

先把候选稿写到标准 roadmap 目录，给 `cs-roadmap-review` 稳定输入：

- **new**：建 `.codestable/roadmap/{slug}/`；写主文档 `status: draft`；写 items.yaml（每条 `status: planned`、`feature: null`）；`validate-yaml.py` 校验。
- **update**：直接更新主文档 / items.yaml 的候选内容，结构性改动文末加变更日志；重新校验 yaml。

然后运行 `cs-roadmap-review`：

- `passed`：才能把 roadmap 交给用户 review。
- `changes-requested`：按 finding 修 roadmap/items，重新校验并重跑 `cs-roadmap-review`。
- `blocked`：补齐输入、等待 independent reviewer，或让用户明确降级 local-only 后重跑。

### Phase 6：用户 review

主文档 + items.yaml + `{slug}-roadmap-review.md` 完整贴给用户，并附上 Phase 4 自查结论、Top 3 风险与缓解、关键假设、review findings / residual risk。改到用户明确"可以了"。如果用户修改导致 roadmap/items 发生实质变化，回到 Phase 5 重跑 review gate。

### Phase 7：确认落盘

用户确认后，new 模式把主文档 `status` 改为 `active`、`last_reviewed` 改为当天；update 模式更新 `last_reviewed` 当天。重新校验 yaml。

**不改 requirements / architecture**——roadmap 是规划层，那两层只描述现状。拆解过程发现 req / 架构过时，在主文档"观察项"记一句给用户，不顺手改。

如果用户想把整份 roadmap 自动推进到底，确认落盘后提示下一步可以走 `cs-roadmap-impl-goal`：它会先完成所有子 feature design + design review，再让用户二次确认，最后输出可直接运行的 goal 指令。

确认落盘后再提示一句："这份 roadmap 已经改变了后续工作入口和文档索引，要不要做一轮文档与记忆整理？（`cs-docs-neat`）" 用户说不用就跳过；这是收尾引导，不是 roadmap 通过条件。

---

## 和 feature 流程的衔接

### feature 从 roadmap 起头

用户说"开始做 roadmap 里的 {子 feature}"时：

1. `cs-feat-design`（或 ff / brainstorm）起 feature 目录
2. design frontmatter 带 `roadmap: {slug}` + `roadmap_item: {子 slug}`
3. items.yaml 对应条目 `status: in-progress`、`feature: YYYY-MM-DD-{slug}`

职责在 `cs-feat-design` 不在本技能。

### feature-design 必须把 roadmap 接口契约当硬约束

**roadmap 主文档第 4 节"接口契约"是 feature 的硬约束输入**——不是参考，是不能违反、要改先回 roadmap update。这就是为什么 roadmap 要在拆 feature 前先把架构方案定下来：让多条 feature 并行 / 串行实现时对外接口对齐。

feature-design 发现接口契约不合理 / 漏了 / 描述不准 → **回 `cs-roadmap update` 改了再继续**，不要在 feature 里偷偷绕开（绕开会让下一条同模块 feature 接到老契约导致二次冲突）。

### acceptance 自动回写

`cs-feat-accept` 收尾时如果 design frontmatter 有 `roadmap` 字段就改对应 `roadmap_item` 的 `status: done`，同时同步主文档子 feature 清单勾选状态。职责在 `cs-feat-accept` 不在本技能。

### roadmap 自身生命周期

- 所有 items `done` / `dropped` 后主文档 `status: completed`，目录留作历史档案
- 长期无进展：`status: paused`，主文档加理由

---

## 硬性边界

1. **不写单 feature 内部实现细节**——roadmap 写到"模块边界 / 接口契约 / 共享协议"为止，单模块内部怎么实现归 feature-design。判据：**会被多个 feature 共同遵守**归 roadmap，**只在某个 feature 内部用**归 feature-design
2. **不改愿景和结构档案**——不顺手改 requirements / architecture / 代码 / 已有 feature。问题记"观察项"
3. **不替用户拍产品优先级**——技术依赖外的排序让用户决定
4. **单目标**——一次只动一份
5. **不发散**——用户范围外问题记观察项不扩大
6. **接口契约要么可执行级要么明确"无跨模块接口"**——不允许"待定 / 后面再说"。含糊掉的接口在 feature-design 各条会各自补出来必然不一致

---

## 退出条件

- [ ] 已锁定单一模式 + 单一目标
- [ ] 主文档 frontmatter 完整（`doc_type: roadmap` / `slug` / `status` / `created` / `last_reviewed` / `tags`）
- [ ] 主文档含：背景 / 范围与明确不做 / **模块拆分** / **接口契约** / 子 feature 清单 / 排期 / 观察项
- [ ] 模块拆分节每个模块职责一句话讲清
- [ ] 接口契约节写到 feature-design 可拿来当硬约束的级别（函数签名 / 数据结构 / 协议字段 / 错误码）或明确"无跨模块接口"
- [ ] items.yaml 每条有 `slug` / `description` / `depends_on` / `status` / `feature`
- [ ] 依赖图是 DAG 无循环
- [ ] 最小闭环条目已标
- [ ] Top 3 风险、非显然依赖、关键假设已写入主文档或 review 摘要
- [ ] 每条子 feature 都有可独立验证的完成信号 / 证据类型
- [ ] 已做可证伪性 / 条目原子性 / 最弱依赖 / 收口覆盖自查并汇报
- [ ] 已识别验证入口 / 基线风险；必要时拆出 safety net 条目
- [ ] 每条子 feature 的交付物能被后续 acceptance 从仓库事实核验
- [ ] 需要后续沉淀的 convention / learning / guide / attention 候选已写入观察项
- [ ] items.yaml 通过 `validate-yaml.py` 校验
- [ ] Phase 4 自查清单逐条跑过并汇报
- [ ] `{slug}-roadmap-review.md` 已通过 `cs-roadmap-review`，没有 unresolved blocking finding
- [ ] 用户 review 通过
- [ ] 没有顺手改 req / arch / 代码 / 已有 feature

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-req` 配合 | req 记"为什么有这个能力"、roadmap 记"打算怎么分步做出来"。大需求下可能多份 req；缺 req 提示用户先 `cs-req` |
| `cs-domain` 配合 | adrs/ 记已拍板决策、roadmap 记前瞻接口契约。读 ADR 理解现状但不改它 |
| `cs-feat` 下游 | 每条子 feature 是未来一次 feature 流程的种子；起头时 design frontmatter 带 `roadmap` / `roadmap_item` |
| `cs-feat-accept` 回写方 | acceptance 自动改 items.yaml 为 `done`，本技能只定义格式不负责回写 |
| `cs-roadmap-impl-goal` 下游 | 用户确认 roadmap 后，可把所有子 feature design 和后续 impl / review / QA / accept 编排成可恢复的 goal |
| `cs-onboard` 创建者 | 建 `roadmap/` 空目录 |
| `cs-brainstorm` 上游 | case 3 移交本技能，带"真问题 / 大致范围 / 可能子模块"一句话汇总。本技能不重复分诊直接拆 |

---

## 常见错误

- **跳过架构方案直接拆任务**——上来就列子 feature，模块边界 / 接口没想，feature-design 各自发明轮子
- **接口契约写得含糊**——"两边商量"、"待定"、"用一个统一的事件总线"——讲不到字段 / 签名 / 协议级。feature-design 接到这种没法当硬约束
- 把单 feature 内部细节写进 roadmap（某模块内部怎么分文件 / 用哪个库）——归 feature-design
- 颗粒度失衡——一条装得下三个独立功能、另一条只改个配置
- 依赖关系靠脑补——讲不清为什么依赖
- 替用户排优先级
- 和已有 req / arch 冲突不停下——自己选一边掩盖真实分歧
- 一次做多份 roadmap
- 顺手改 req / arch
- drop 条目直接删——历史丢失
- roadmap 跑偏成给单条子 feature 写详细方案
- update 改接口契约不评估存量影响——已 in-progress / done 的 feature 没人看到契约变了
- 跳过 `cs-roadmap-review` 直接让用户拍板——用户只能看到规划表面，看不到接口、依赖、验收策略的独立审查结论
