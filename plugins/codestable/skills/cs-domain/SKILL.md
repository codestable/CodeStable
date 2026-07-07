---
name: cs-domain
description: "领域模型维护。触发：记决策、加术语、拆 context、维护 CONTEXT/ADR。不要用于功能实现(cs-feat)、对外文档(cs-docs)、大需求拆解(cs-epic)、需求澄清与能力 doc(cs-req)。"
contracts:
  - grep: "CONTEXT.md"
  - grep: "CONTEXT-MAP.md"
  - grep: "守门 3 判据"
  - grep: "Nygard 四节"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-domain

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

cs-domain 管三件事：**术语**（CONTEXT.md）、**决策**（ADR）、**拓扑**（单 context ↔ 多 context）。所有产物在 `.codestable/requirements/` 下。

`cs-domain` 是领域模型维护 operator（单一职责，非 stage 编排型 workflow）；下方 `## Spec` 是前门契约，正文「拓扑判断」「CONTEXT.md 写作规范」「ADR 写作」「单 → 多 context 升级」是方法论主体。

## Spec

```haskell
csDomain :: DomainRequest -> DomainOutcome

data DomainRequest = DomainRequest
  { intent    : Maybe DomainIntent    -- 术语 / ADR / 拓扑升级；缺则读用户话术
  , repoFacts : RepoFacts             -- .codestable/requirements/ 下现有产物，优先于聊天历史
  , attention : Maybe Attention       -- .codestable/attention.md；缺则 route to cs-onboard
  }

data DomainIntent = AddTerm | WriteADR | UpgradeTopology

data Topology = None | Single | Multi -- 由 CONTEXT.md / CONTEXT-MAP.md 是否存在判定

data DomainState = DomainState        -- 从 .codestable/requirements/ 恢复
  { topology     : Topology
  , hasContext   : Bool               -- CONTEXT.md 是否存在
  , hasContextMap: Bool               -- CONTEXT-MAP.md 是否存在
  , maxAdrNum    : Int                -- 对应 adrs/ 目录最大编号，新 ADR = +1
  }

data DomainOutcome
  = TermWritten Path                  -- CONTEXT.md 落对拓扑位置，同义词入 _Avoid_
  | AdrWritten Path                   -- 通过守门 3 判据；frontmatter 全 + Nygard 四节齐
  | TopologyUpgraded                  -- CONTEXT-MAP.md + 子目录 + 术语拆分 + ADR 分级
  | NeedsHuman Reason
```

`selectDomainAction` 从仓库事实定位拓扑并选产物动作（决策细则见「拓扑判断」「ADR 写作」「单 → 多 context 升级」；此处只固定分支形态）：

```haskell
selectDomainAction :: DomainState -> DomainIntent -> DomainOutcome
selectDomainAction(s, intent)
  | attentionMissing                                   -> NeedsHuman "route to cs-onboard"
  | intent == WriteADR && not (passesGate3 intent)     -> NeedsHuman "ADR 未过守门 3 判据"
  | intent == WriteADR                                 -> AdrWritten (adrPath s)
  | intent == AddTerm                                  -> TermWritten (contextPath s)
  | intent == UpgradeTopology && not explicitTrigger   -> NeedsHuman "升级需用户显式触发"
  | intent == UpgradeTopology                          -> TopologyUpgraded
```

## 拓扑判断

每次启动先扫一眼，确定项目当前处于哪种拓扑：

- `.codestable/requirements/CONTEXT-MAP.md` 存在 → **多 context** 模式
- 只有 `.codestable/requirements/CONTEXT.md` → **单 context**
- 都没有 → 项目还没起 domain 文档，按需 lazy 创建

## 单 context 路径

```
.codestable/requirements/
├── CONTEXT.md              # 术语表
├── adrs/                   # 顺序编号 ADR
│   ├── 001-xxx.md
│   └── 002-xxx.md
└── {capability}.md         # 能力 doc（cs-req 产出，不归本技能管）
```

## 多 context 路径

```
.codestable/requirements/
├── CONTEXT-MAP.md          # 子 context 列表 + 关系
├── adrs/                   # 系统级 ADR（跨 context）
├── ordering/
│   ├── CONTEXT.md          # 子 context 术语
│   └── adrs/               # 子 context 特定 ADR
└── billing/
    ├── CONTEXT.md
    └── adrs/
```

## CONTEXT.md 写作规范

CONTEXT.md 是**术语表，不是 spec**。只写"X 是什么"，不写"X 怎么实现"。

格式：

```md
# {Context 名}

{一两句描述这个 context 是什么、为什么存在。}

## Language

**Order**:
{一两句话定义。}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request
```

规则：

- **下定义，不描述行为**——写 "X 是什么"，不写 "X 做什么"
- **同义词列在 `_Avoid_`**——多个词指同一概念时挑最好的，其他列为禁用
- **只收项目特有术语**——通用编程概念（timeout、error type）不进
- **聚类用子标题**——同领域术语自然分组就给小节

## ADR 写作

### 何时该写（守门 3 判据，必须同时满足）

1. **难以回退**——以后改主意成本明显
2. **不带上下文就难理解**——读者会问"为什么这么做"
3. **真实权衡的结果**——有备选方案，因为具体原因挑了一个

三条少一条就**不写**。轻易能回退的决定不写、不奇怪的决定不写、没真备选的决定不写。

### 路径与编号

- 单 context：`.codestable/requirements/adrs/NNN-{slug}.md`
- 多 context 子系统 ADR：`.codestable/requirements/{ctx}/adrs/NNN-{slug}.md`
- 多 context 系统级 ADR（跨 context）：`.codestable/requirements/adrs/NNN-{slug}.md`
- 编号 3 位（001、002...）；扫对应 adrs/ 目录最大编号 + 1
- `{slug}` kebab-case，能让人一眼想起决策内容

### Frontmatter

```yaml
---
id: 001
title: 选择 X 而不是 Y
status: proposed | accepted | superseded | deprecated | partially-superseded
date: YYYY-MM-DD
supersedes: [003]                          # 可选
superseded_by: [015, 017]                  # 可选
relates_to: [requirements/{slug}, 002]     # 可选
---
```

### 正文（Nygard 四节）

```md
# {Title}

## Context
{决策面对的问题、约束、当时的状况。}

## Decision
{我们决定做什么。}

## Consequences
{这个决定带来的正负影响、新出现的约束。}

## Alternatives Considered
{讨论过的备选方案 + 为什么没选。}
```

写 ADR 时用 CONTEXT.md 里已定义的术语；用到新术语就顺手 `_Avoid_` 别名补到 CONTEXT.md。

## 单 → 多 context 升级

**显式触发**——用户必须明确说"这项目要分子系统了"才升级。不要因为 CONTEXT.md 长就自动建议。

升级流程：

1. 跟用户对齐子 context 列表（典型 2-4 个，超过 5 个先质疑是不是切得太细）
2. 创建 `CONTEXT-MAP.md`：列子 context + 它们之间的关系（事件流、共享类型、调用方向）
3. 为每个子 context 建子目录 + `CONTEXT.md` + `adrs/`
4. 把原 `CONTEXT.md` 的术语按归属拆到各子 context；跨多个 context 的术语留在 `CONTEXT-MAP.md` 顶层 Language 节
5. 把原 `adrs/` 下的 ADR 按影响范围分：跨 context 的留原位（系统级），单 context 内部的 mv 到对应 `{ctx}/adrs/`
6. 不动 `{capability}.md`——能力 doc 归 cs-req 管，升级时 cs-req 跟进归类（cs-domain 不替它做）

## Failure Behavior

返回 `NeedsHuman` 当：`.codestable/attention.md` 缺失（→ `cs-onboard`）；候选决策过不了守门 3 判据（易回退 / 不奇怪 / 无真备选，就不写 ADR）；用户没有显式说"这项目要分子系统了"却要升级拓扑；子 context 该切几个、术语/ADR 归哪个 context 存在重大歧义；需求本质是能力实现或需求澄清（→ `cs-feat` / `cs-req`）而非领域模型维护。

报告：当前拓扑（单/多 context）、目标产物路径、阻塞原因、下一步用户动作、已写文件、是否可安全重试。不要为过不了守门 3 判据的决定硬写 ADR，也不要因 CONTEXT.md 变长就自动建议升级拓扑。

## 退出条件

- 写 ADR：文件落盘 + 编号正确 + frontmatter 完整 + Nygard 四节齐
- 写 CONTEXT：术语进对位置（单/多 context 拓扑判断正确）+ 同义词列到 `_Avoid_`
- 升级拓扑：CONTEXT-MAP.md + 子目录创建完 + 术语拆分完 + ADR 分级完
