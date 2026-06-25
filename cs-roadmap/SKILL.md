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

**update 额外**：当前主文档全文 + items.yaml 当前状态 + 已启动 / 完成的子 feature 的 design / acceptance。

### Phase 3：拆解与起草

按 `reference.md` "主文档结构"和"items.yaml 格式"写**完整初稿**不分批。

**拆解纪律**：

0. **先做架构方案再拆 feature**——顺序：先想模块拆分（概设第 3 节）→ 模块间接口 / 数据结构 / 协议（详设第 4 节）→ 才把方案分解成子 feature（第 5 节）。**架构方案不清楚就硬拆 feature，结果是每个 feature 各自重新发明轮子、接口对不齐**
1. **接口契约要写到 feature 可拿来当硬约束的程度**——函数签名 / 数据结构 / 协议字段 / 错误码这一级。讲不到这级回去想。无跨模块接口（如纯前端样式调整）就明确写"无跨模块接口"
2. **每条子 feature 能当独立 feature 流程跑完**——能单独写 design / 实现 / 验收。跑不下来颗粒度不对
3. **依赖图必须是 DAG**——A 依赖 B 写清楚，别循环
4. **依赖关系要有具体理由**——"B 依赖 A，因为 A 提供 XX 表结构"而不是"A 先做"
5. **先列一条最小闭环**——做完后能端到端跑通最窄路径的标第一条
6. **明确不做的边界**——用户脑子里的"权限系统"可能包括审计日志 / 数据脱敏，不打算覆盖就写进"明确不做"
7. **不替用户决定优先级**——技术依赖之外的排序让用户拍板

### Phase 4：自查清单

review 前自跑一遍汇报处理：

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

### Phase 5：用户 review

主文档 + items.yaml 完整贴给用户。改到用户明确"可以了"。

### Phase 6：落盘

**new**：建 `.codestable/roadmap/{slug}/`；写主文档（`status: active` / `created` / `last_reviewed` 当天）；写 items.yaml（每条 `status: planned`、`feature: null`）；`validate-yaml.py` 校验。

**update**：改主文档（`last_reviewed` 当天，结构性改动文末加变更日志）；改 items.yaml 对应条目（drop 不删，`status: dropped` 留存理由）；重新校验 yaml。

**不改 requirements / architecture**——roadmap 是规划层，那两层只描述现状。拆解过程发现 req / 架构过时，在主文档"观察项"记一句给用户，不顺手改。

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
- [ ] items.yaml 通过 `validate-yaml.py` 校验
- [ ] Phase 4 自查清单逐条跑过并汇报
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
