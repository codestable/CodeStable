# cs-roadmap 参考模板

SKILL.md 只保留流程骨架，具体格式在这里。

---

## 1. 主文档 `{slug}-roadmap.md`

### 1.1 frontmatter

```yaml
---
doc_type: roadmap
slug: permission-system
status: draft           # draft | active | paused | completed
created: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
tags: [permission, auth]
related_requirements: []    # 相关 req slug 列表，可空
related_architecture: []    # 相关 architecture doc slug，可空
---
```

- `status`：`draft` 待独立 review 和用户确认 / `active` 进行中 / `paused` 暂停 / `completed` 所有条目 done 或 dropped
- `related_requirements`：本大需求涉及的 req slug，帮助跳转到"为什么要有这个能力"
- `related_architecture`：会被改到的 architecture doc slug，帮助理解"改了会触碰哪些现状"

### 1.2 正文节

```markdown
# {大需求标题——直接说是什么不玩比喻}

## 1. 背景

一两段讲是什么、为什么要做。对象是"新加入想知道接下来几个月在忙什么"的人。

## 2. 范围与明确不做

### 本 roadmap 覆盖
- 能力 A
- 能力 B

### 明确不做
- 能力 X（理由）
- 能力 Y（指向另一份 roadmap / req）

## 3. 模块拆分（概设）

拆成哪几个模块 / 组件、各自做什么。文字版结构树或 ASCII 框图都行 + 每个模块一段说明：

```
{大需求名}
├── 模块 A：{一句话职责}
├── 模块 B：{一句话职责}
└── 模块 C：{一句话职责}
```

### 模块 A · {名称}
- **职责**：{一两句讲清做什么、不做什么}
- **承载的子 feature**：{slug-1, slug-2}
- **触碰的现有代码 / 模块**：{已有的 X 模块 / 全新 / 重写某模块}

### 模块 B / C · ...

> 不需要模块拆分（纯改一个已有模块的内部行为）→ 明确写"本大需求在已有模块 {X} 内完成，不引入新模块也不调整模块边界"，跳过第 4 节直接到第 5 节。

## 4. 模块间接口契约 / 共享协议（架构层详设）

定义模块之间怎么交互——这一节是 feature-design 的硬约束输入。**写到函数签名 / 数据结构 / 协议字段 / 错误码这一级**，不允许"两边商量" / "待定"。

### 4.1 {接口 / 协议名 1}

**方向**：模块 A → 模块 B
**形式**：HTTP API / 函数调用 / 消息事件 / 共享数据库表 / 文件协议 / ...

**契约**：

```
# HTTP API 例：
POST /api/v1/permission/check
Request:  { user_id: str, resource: str, action: str }
Response: { allowed: bool, reason: str | null }
错误：    400 invalid_input, 404 user_not_found, 500 internal

# 函数签名例：
def check_permission(user_id: str, resource: str, action: str) -> PermissionResult
class PermissionResult: allowed: bool; reason: Optional[str]

# 事件例：
event_type: permission.changed
payload: { user_id: str, role: str, changed_at: ISO8601 }
```

**约束**：
- 调用方必须先确保 user_id 已认证
- response 的 reason 在 allowed=true 时必须为 null
- 事件必须幂等消费

### 4.2 ...

### 4.x 共享数据结构 / 状态

几个模块共享同一份数据结构 / 持久化 / 全局状态时在这里定义一次：

```
{表结构 / 类型定义 / 配置 schema}
```

> 没有跨模块接口（纯前端样式调整）→ 明确写"本 roadmap 无跨模块接口"。不允许空着或"暂无"。

## 5. 子 feature 清单

按依赖和推进顺序排列。每条对应 items.yaml 一个条目，两份保持同步。

1. **{slug}** — {一句话描述}
   - 所属模块：{模块 A / B / 跨模块——指明涉及哪些}
   - 依赖：{前置 slug 列表 / 无}
   - 状态：{planned | in-progress | done | dropped}
   - 对应 feature：{YYYY-MM-DD-{slug} / 未启动}
   - 备注：{可选}

**最小闭环**：第 {N} 条 `{slug}` 做完后 {描述能端到端跑通的最窄路径}。

## 6. 排期思路

一段短的：为什么这样拆（按模块 / 用户价值 / 风险 / 依赖）；第一条为什么选它作最小闭环；中间有没有卡点（前置架构改动 / 外部依赖 / 设计决策）。

## 7. 观察项

起草 / 刷新过程中发现、本 roadmap 不处理的事情交给用户决定：

- `requirements/adrs/NNN.md` 中的 Y 决策已过时，建议另起一条 ADR superseded
- requirement-Z 的边界和本 roadmap 第 5 条冲突，建议先对齐 req

## 8. 变更日志（update 模式）

- YYYY-MM-DD：{描述本次改动；改了第 4 节接口契约要单列"接口契约变化"和"受影响的已启动 feature 列表"}
```

---

## 2. items.yaml 格式

```yaml
roadmap: permission-system
created: YYYY-MM-DD

items:
  - slug: permission-rbac-core
    description: 基础 RBAC 模型和数据表，提供角色/权限两张表和最小查询 API
    depends_on: []
    status: planned             # planned | in-progress | done | dropped
    feature: null               # 启动 feature 后填 YYYY-MM-DD-{slug}，未启动写 null
    minimal_loop: true          # 只有一条标 true
    notes: null                 # 可选：备注 / 特殊约束 / drop 理由

  - slug: permission-admin-ui
    description: 管理员配置角色和权限的页面
    depends_on: [permission-rbac-core]
    status: planned
    feature: null
    minimal_loop: false
    notes: null
```

### 字段规则

- `slug`：子 feature 的 slug，小写字母 / 数字 / 连字符；将来 feature 目录 `YYYY-MM-DD-{slug}`
- `description`：一句话能独立讲清楚做什么
- `depends_on`：前置 slug 列表，空数组表示无依赖；必须指向同 roadmap 里的其他条目
- `status`：四态机
- `feature`：启动后填目录名，用于 acceptance 反查
- `minimal_loop`：全表只有一条为 `true`
- `notes`：drop 的条目必须写理由

### 状态机

```
planned  → in-progress  （feature-design 启动时由 design 改）
in-progress → done      （feature-acceptance 完成时由 acceptance 改）
planned  → dropped      （用户决定不做，roadmap update 改）
done / dropped 终态
```

**不合法跃迁**：`done` 回 `in-progress`（要改需求回退走新 feature）；`dropped` 回 `planned`（恢复要新加一条 slug 略改）。

### 校验

```bash
python .codestable/tools/validate-yaml.py --file .codestable/roadmap/{slug}/{slug}-items.yaml --yaml-only
```

---

## 3. 拆解 checklist（起草时自问）

### 架构方案层（先问这几条）

- [ ] 模块拆分讲清了？每个模块职责一句话？边界讲得清（哪些事这模块做、哪些不做）？
- [ ] 接口契约写到函数签名 / 数据结构 / 协议字段 / 错误码这一级了？feature-design 看完不需要回来问就能直接照着实现？
- [ ] 共享数据结构 / 持久化 / 全局状态列齐了？
- [ ] 没有跨模块接口的话第 4 节明确写"无跨模块接口"了？而不是空着 / "待定"？

### 子 feature 拆解层

- [ ] 能独立走完一次 feature 流程？走不通就继续拆或合并
- [ ] 做完后能单独验证？能写出"完成后 {具体可观测现象}"
- [ ] slug 和 `features/` 下已有目录冲突？grep 过了？
- [ ] 标了"所属模块"？该模块在第 3 节存在？
- [ ] 依赖关系讲得清具体理由？"B 需要 A 提供的 {具体产物}"
- [ ] 最小闭环真是"最窄的端到端路径"？还是只是"最容易的一条"？
- [ ] 有条目其实应该是 requirement 变化而不是 feature？（"把 XX 能力的边界改一下"）那种转 `cs-req`

---

## 4. review 提示

> roadmap 已起草完成请整体 review。**先看架构方案再看 feature 拆解**——架构方案改了下游全要重排：
>
> **架构方案层**
> 1. 模块拆分对吗？边界划得合理？有该合并 / 该拆开的？
> 2. 接口契约定得够具体吗？feature-design 拿着能直接照做？还是有"两边商量"的含糊地带？
> 3. 共享数据结构 / 协议字段 / 错误码有遗漏？
>
> **feature 拆解层**
> 4. 拆解粒度合适？每条都能独立做成 feature？
> 5. 每条落在哪个模块标对了？
> 6. 依赖关系对吗？有漏的前置或多余依赖？
> 7. 最小闭环选得对？第一条做完真能端到端演示点什么？
> 8. "明确不做"有遗漏？
> 9. 排期顺序符合你的产品优先级？
>
> 有修改意见直接说，确认后把 roadmap 从 `draft` 标为 `active`。

> 人工 review 前必须先有 `{slug}-roadmap-review.md` 且 `status: passed`。用户修改 roadmap/items 后，实质变化要重跑 `cs-roadmap-review`。
