---
name: cs-note
description: attention 短规则追加。触发：记一笔/加到 attention/以后每次都得知道 X。
---

# cs-note

## 启动必读

开始任何判断或动作前，先检查 `.codestable/attention.md`：存在就读取；缺 `.codestable/` 就提示先运行 `cs-onboard`；只有 attention.md 缺失时，本技能可以先创建固定分节骨架再写入。不要用 `AGENTS.md` / `CLAUDE.md` 等外部入口代替它。

`cs-keep` 产出独立 markdown 文件到 `.codestable/compound/`，**通过 grep 检索**被读到；`.codestable/attention.md` 是 CodeStable 技能启动时的**强制必读**上下文。这两类信息归宿不同——本技能专管后者：把"短、稳、每次都要知道"的碎片追加到 attention 文件里。

不替代 cs-keep，是另一个入口。

---

## 什么进 cs-note，什么不进

**判据：长度 + 频次 + 稳定度**——三条都过才走 cs-note。

| 项 | 进 cs-note | 走别处 |
|---|---|---|
| 长度 | 一两行能讲清 | 超过半屏 / 需要展开背景 → cs-keep |
| 频次 | 几乎每次会话都用得上 | 只在某类具体任务相关 → cs-keep |
| 稳定度 | 项目长期生效的硬约束 | 临时绕过 / 短期 workaround → 写到 issue spec 或 feature spec |
| 拍板状态 | 已既成事实（不需要决策记录） | 需要记选型理由 / 拒方案 → cs-keep |

✅ **典型该进**：

- "编译要先 `pnpm run gen` 生成 schema"
- "本地起服务前必须 `docker compose up redis`"
- "项目用 yarn berry，**别**用 `npm install`"
- "测试命令是 `bun test`，不是 `npm test`"
- "src/legacy/ 是历史代码，改之前先问"
- "`OPENAI_KEY` 走 1Password，别从 .env.example 复制"

❌ **典型不该进**（会让 attention.md 膨胀）：

- 某个 bug 的修法（→ cs-keep）
- 某个库怎么用（→ cs-keep）
- 一段架构说明（→ cs-domain 起一条 ADR）
- "本周在做 X"这种短期状态（→ 别记，会过期）
- 需要 3 行以上才讲清的（→ cs-keep）

**判不准就反问用户一句**："这条以后是不是每次会话都要让 AI 知道？"答"不一定" → 不是 cs-note。

---

## 目标文件

目标文件固定为 `.codestable/attention.md`。`AGENTS.md` / `CLAUDE.md` / `.cursorrules` 等外部 AI 工具入口不是 CodeStable attention 的替代源。

- `.codestable/` 不存在 → 本仓库还没接入 CodeStable，先提示用户运行 `cs-onboard`
- `.codestable/attention.md` 不存在 → 视为骨架缺失，先创建最小骨架再写入
- `AGENTS.md` / `CLAUDE.md` 即使存在也不作为目标文件；需要同步外部入口时走 `cs-docs-neat`

attention.md 是 CodeStable 自己的启动注意事项入口，价值来自所有 CodeStable 技能都明确要求读取它，而不是依赖外部工具的自动注入。

---

## 固定分节结构

为了防止文件膨胀成另一个胖文件，分节**写死**一组（不在列表里的不开新节）：

```markdown
## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

### 运行与本地起服务

### 测试

### 命令与脚本陷阱

### 路径与目录约定

### 环境变量与凭证

### 其他
```

**规则**：

- 新条目去对应分节末尾追加，每条一行（最多两行）
- 没有合适的分节 → 进"其他"。"其他"超过 5 条就停下来和用户讨论是否新增固定分节（不要默默加节）
- 分节为空时整段保留，不删（让 AI 看到这一节是有意义的）
- 注释行 `<!-- cs-note managed -->` 是本技能的识别锚——找不到就在文件末尾插入整块结构
- **整段长度软上限 ~150 行**——超过提示用户："碎片知识太多了，挑几条沉到 cs-keep 里？"

---

## 流程

### 1. 判定该不该进

按上面"判据"表对一遍。任一项不过 → 引导到对应别的技能，本轮结束。

### 2. 确认 attention 文件

检查 `.codestable/attention.md`。缺 `.codestable/` 就停止并提示先 `cs-onboard`；只缺 `attention.md` 就创建本技能的固定分节骨架。

### 3. 找位置：分节归类 + 查重

- 读 `.codestable/attention.md`，找 `<!-- cs-note managed -->` 锚定位
- 找不到锚 → 在文件末尾追加整块"项目碎片知识"骨架
- 在"项目碎片知识"段内 grep 关键词查重——已有相似条目时**不另起一条**，问用户"是更新已有那条还是确实是另一条"
- 选好分节，没有合适分节进"其他"

### 4. 写一条进去

每条格式：

```
- {一句话事实 + 必要时一句话原因}
```

例：

```
- 编译前要先 `pnpm run gen`，否则 schema 类型对不上
- 别用 `npm install`，项目锁文件是 yarn berry 的
- src/legacy/ 是 2023 前的老代码，改之前先和 @ldz 确认
```

写完用户 review 一句确认就退出。**不主动连写多条**——一次一条，避免顺手把没拍板的也塞进去。

### 5. 触发软上限检查

写完看一眼"项目碎片知识"段总行数：

- ≥150 行 → 提示用户挑几条沉到 cs-keep
- "其他"分节 ≥5 条 → 提示用户讨论是否新增固定分节

只是**提示**，不替用户决定。

---

## 主动推荐时机

不要每次都问。只在两个明确信号触发时推一句：

1. **用户在对话中说出明显属于碎片知识的事实**——"哦对这个项目要先 X 才能 Y"、"我们这个用 Z 不用 W"——推："这条要不要 `cs-note` 一下？以后 AI 每次都能看到。"
2. **AI 自己刚踩了一个一句话能讲清的项目特殊设置**（编译失败 / 命令不对 / 路径找错）——修复后推："这个坑是项目通用的吗？是的话 `cs-note` 记一笔，下次会话直接知道。"

用户说"不用了"立刻跳过，不重复推。

---

## 容易踩的坑

- 把详细背景 / 多步骤指南塞进 attention.md——超过两行就该走 cs-keep
- 写到 `AGENTS.md` / `CLAUDE.md`——它们不是 CodeStable attention 的替代源；外部入口同步走 `cs-docs-neat`
- 默默新增分节——分节是写死的，新增要先和用户讨论
- 看到一条就连带把其他几条也写进去——一次一条
- 写"短期状态"（本周在做 X / 这个 sprint 的目标）——会过期但没人删，慢慢变误导
- 不查重就追加——同一条事实被记 3 次后 AI 反而搞不清哪条是准的
