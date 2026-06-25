# cs-audit 参考模板

## index.md 模板

```markdown
---
doc_type: audit-index
audit: {YYYY-MM-DD}-{slug}
scope: {审计范围一句话}
created: {YYYY-MM-DD}
status: active
total_findings: {N}
---

# {slug} 审计报告

## 范围

{扫描了哪些目录 / 文件，用户给的关键词或描述}

## 总评

{一段话总结：共发现几条、按维度分布、按严重度分布、最值得关注的是哪几条、整体代码质量印象}

## 发现清单

| # | 性质 | 严重度 | 置信度 | 标题 | 文件 |
|---|---|---|---|---|---|
| 1 | security | P0 | high | SQL 注入隐患 | [finding-01.md](finding-01.md) |
| 2 | performance | P1 | medium | 订单列表 N+1 查询 | [finding-02.md](finding-02.md) |
| ... | ... | ... | ... | ... | ... |

## 按维度分布

| 性质 | P0 | P1 | P2 | 合计 |
|---|---|---|---|---|
| bug | 0 | 2 | 1 | 3 |
| security | 1 | 0 | 0 | 1 |
| performance | 0 | 1 | 1 | 2 |
| maintainability | 0 | 0 | 3 | 3 |
| arch-drift | 0 | 1 | 0 | 1 |
| **合计** | **1** | **4** | **5** | **10** |

## 下一步建议

- **P0 立刻修**：{列表，建议开 cs-issue}
- **P1 本迭代修**：{列表}
- **P2 有空再看**：{列表}
```

---

## finding-NN.md 模板

```markdown
---
doc_type: audit-finding
audit: {YYYY-MM-DD}-{slug}
finding_id: "{nature}-{NN}"
nature: bug | security | performance | maintainability | arch-drift
severity: P0 | P1 | P2
confidence: high | medium | low
suggested_action: cs-issue | cs-refactor
status: open
---

# Finding {NN}：{一句话标题}

## 速答

{一句话描述——什么问题、在哪、什么影响}

## 关键证据

- `{file}:{line}` — {代码片段或描述} —— {为什么这构成问题}
- `{file}:{line}` — ...

## 影响

{影响范围 / 触发条件 / 影响用户数估计（如能判断）}

## 修复方向

{一句话建议修法，不展开——展开了就是抢 cs-issue / cs-refactor 的活}

## 建议动作

{`cs-issue` 或 `cs-refactor`}，因为 {一句话理由}
```

---

## 维度扫描检查项

扫描时逐项对照，不是每项都要有发现——没发现跳过。

### bug 隐患
- [ ] 空值路径：可选链缺失、null/undefined 未守卫
- [ ] 边界条件：空数组、空字符串、0、负数、极大值
- [ ] 竞态条件：异步操作顺序依赖、状态更新时序
- [ ] 错误处理：try-catch 为空、Promise rejection 未捕获、错误信息被吞
- [ ] 类型安全：类型断言无保护（`as` / `!`）、any 扩散

### 安全
- [ ] 注入：SQL/NoSQL 拼接、命令注入、XSS（innerHTML / dangerouslySetInnerHTML）
- [ ] 敏感数据：日志打印 token/密码、前端暴露密钥、响应体泄露字段
- [ ] 权限：缺少鉴权中间件、越权（资源归属未校验）
- [ ] 依赖：已知漏洞的第三方包、过期的安全敏感库

### 性能
- [ ] N+1 查询：循环内数据库调用 / API 请求
- [ ] 重复计算：未 memo 的昂贵运算、render 内创建对象/函数
- [ ] 无分页/虚拟化：全量加载大列表
- [ ] 内存泄漏：事件监听未清理、定时器未清除、闭包持有大对象
- [ ] 阻塞主线程：大文件同步读取、CPU 密集无 Web Worker

### 可维护性
- [ ] 超长函数（> 80 行）
- [ ] 高圈复杂度（> 15）
- [ ] 重复逻辑块（相同或高度相似代码出现 ≥ 3 次）
- [ ] 神秘常量（魔法数字无命名）
- [ ] 循环依赖（A → B → A）

### 架构偏离
- [ ] 分层泄漏：上层直接调下层实现细节、绕过中间层
- [ ] 模块隐式耦合：跨模块直接 import 内部文件（非公开 API）
- [ ] 与 `.codestable/requirements/adrs/` 已拍板决策不一致
- [ ] 约定违背：命名 / 目录结构 / 错误处理模式与项目约定不符
