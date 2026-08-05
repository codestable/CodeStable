<div align="center">

# CodeStable

[English](./README.en.md) · **中文**

**让 AI 编码在长期项目中保持边界、证据和记忆。**

<p><img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/> <img src="https://img.shields.io/badge/cs--skills-8-6366F1?style=flat-square" alt="CodeStable Skills"/> <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/></p>
</div>

CodeStable 是一组面向严肃软件开发的轻量 skill 契约：不编排 Agent 团队，也不为项目建立第二套文档系统。模型在明确边界内行动，用证据证明结果，并把知识放回项目已有归宿。

## 30 秒运行模型

```text
用户诉求
   ↓
cs：直接执行 / 当前会话讨论 / 给出建议
   ↓
feat · issue · refactor · epic
   ↓
相称的验证 + 必要的 review / owner gate
   ↓ 代码结果 + 项目已有的 canonical knowledge
```

团队使用时，可以按职责组合：

- **稳定编码**：使用 CodeStable 明确任务边界、保障、证据和项目记忆；
- **团队上下文共享**：推荐使用 [Threadshare](https://github.com/team-harness/threadshare)，把 Codex、Claude Code
  等 Agent 会话转换成只读链接，供团队成员和后续 Agent 阅读、交接；
- **多 Agent 编码协同**：推荐使用 [cs-agent](https://github.com/codestable/cs-agent-mcp)，在编码过程中统一创建、
  调用和管理 Codex、Claude 等子 Agent，也可承担异构独立 review。

三者互补：CodeStable 不负责发布会话或编排 Agent，Threadshare 和 cs-agent 也不替代 CodeStable 的工程契约。

你只需要告诉 `cs` 想完成什么：

- **需求清楚时**：它直接开始，并用足够的验证交付结果；
- **遇到具体风险时**：它只增加与风险对应的确认、测试或 review，不自动启用整套流程；
- **你想先讨论时**：它先和你对齐目标、术语和边界；未经明确授权，不会修改代码；
- **名词可能影响理解时**：它先对齐含义，形成当前任务的共享语言；没有歧义时，直接沿用项目已有说法。

纯讨论、咨询和体系导览默认不写项目文件。还没讨论清楚的内容，CodeStable 不会专门保存，也不保证下次会话自动恢复。

## 5 分钟开始

### 安装

Codex plugin marketplace：

```bash
codex plugin marketplace add codestable/CodeStable
codex plugin add codestable@codestable
```

Claude plugin marketplace：

```text
/plugin marketplace add codestable/CodeStable
/plugin install codestable@codestable
```

`skills` CLI（v1 用户须先按[升级指南](./UPGRADE.md#从-v104-升级到-v2)精确删除 24 个退役入口，再安装 v2）：

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable
```

如果 marketplace catalog 没有发现插件实体，可改用 `npx skills@latest add codestable/CodeStable/plugins/codestable --full-depth` 深度扫描。

### 接入项目

在仓库根目录运行 `/cs-onboard`。它只创建最小项目记忆骨架，不接管项目文档结构、worktree 或 branch 策略。

### 开始工作

不知道该用哪个入口时调用 `/cs`；也可以直接调用 owning skill。v2 交付 8 个 skill：

| Skill | 用途 |
|---|---|
| `cs` | 路由明确行动、会话内讨论、咨询与体系导览 |
| `cs-onboard` | 为仓库创建最小项目记忆骨架 |
| `cs-feat` | 实现新功能或改变既有行为 |
| `cs-issue` | 诊断问题；获授权后用红到绿证据修复 |
| `cs-refactor` | 在行为等价证据下调整结构或性能 |
| `cs-epic` | 拆解并按已确认策略推进多个可交付子项 |
| `cs-review` | 只读叶子执行器；单轮审查，不创建子 agent |
| `cs-keep` | 管理有证据的项目事实、lesson 生命周期与 canonical 归宿 |

`cs-code-review` 是 `cs-review` 的兼容别名，只转发，不包含独立规则。

## 三个核心原则

### 1. thin harness, thick context

CodeStable 给强模型写责任，不写逐步脚本。skill 只约束目标、硬边界和完成证据；模型结合仓库事实选择路径，工程参考按需加载。

薄不等于没有门槛，而是不使用常驻状态机和阶段产物微操模型。

### 2. 证据先于结论

功能实现需要与风险相称的设计和验证；bug 修复先红后绿；重构先建立行为等价证据。独立审查由外层流程创建只读 reviewer。

人在产品契约变化、重大风险或整体接受时进入，不在每个机械步骤上重复确认。

### 3. 一个事实，一个 canonical owner

项目文档、ADR、代码和既有领域文档继续拥有原有事实。CodeStable 不复制平行档案，只补充少量会话事实、经验和活动游标。

稳定结论由 owning skill 放回唯一归宿；没有归宿时先请 owner 选择。

## 项目记忆

`/cs-onboard` 创建：

```text
.codestable/
├── attention.md
├── lessons/
└── work/
```

- `attention.md` 保存每次会话都需要的少量项目事实，最多 25 条。
- `lessons/` 一条经验一个文件，按 observed / validated / retired 演化，并在写入前查重合并。
- `work/` 只服务活动中的跨会话任务、多人交接或明确要求的持久记录。

CodeStable 边做边识别晶化时刻：任务中静默观察，普通收尾最多给一条有证据的候选。

能机械化的错误优先进入测试或 checker。新 lesson 仍需明确授权，后续会话核实后再验证或退役。

普通任务不生成 CodeStable 阶段文档。diff、测试输出和交付说明就是证据。会话内讨论不进入 `work/`；只有稳定、值得复用的结论才由 owning skill 毕业到 canonical 归宿。

### Epic 的双层模型

大型需求把长期契约和临时执行状态分开。永久 Epic 文档保存目标、范围、验收、已批准子项、关键决策与最终交付。

当路线尚不清晰时，永久 Epic 文档本身就是路线地图，决策依赖派生 frontier。

agent 解决事实，真正的产品判断与取舍进入 HITL。路线清晰、可审查、可执行后，才进入既有 design review、owner 确认与执行。

临时 work 游标只保存永久文档指针、批准 revision、执行进度、策略与证据。

Epic 优先沿用项目已有的 Epic、RFC 或 initiative 归宿；没有时才按需创建 `.codestable/epics/`。执行结束后删除临时游标，永久文档保留。

完整 owner gate、恢复与终态规则见 [WORKFLOW.md](./WORKFLOW.md)。

## 适用边界

CodeStable 更适合：

- 会持续迭代数月或数年的软件项目；
- 需要让不同会话、模型或开发者准确召回历史约束；
- 希望 AI 高效执行，同时由人掌握产品边界和最终接受；
- 重视可验证结果、独立审查和知识复用的团队。

它不是：

- 多 Agent 团队编排器或自动接力平台；
- 强制所有任务经过同一流水线的流程引擎；
- 替代项目现有文档、ADR、issue 或 PR 的第二套系统；
- 面向一次性原型、且完全不关心长期维护的必要依赖。

CodeStable 可以与 Agent 编排工具共存。它负责软件任务的边界、证据和记忆，不接管宿主如何组织 Agent。

需要多 Agent 协作，或需要在 CodeStable 流程中由异构 Agent 承担独立 review 时，推荐配合
[cs-agent](https://github.com/codestable/cs-agent-mcp) 使用。

## 深入文档

- [完整工作流与项目结构](./WORKFLOW.md)
- [8 个 skill 的职责与旧入口映射](./SKILL_CATALOG.md)
- [安装升级与 v1 项目边界](./UPGRADE.md)
- [为什么设计 CodeStable](./docs/why-codestable.md)
- [路线图](./ROADMAP.md)
- [版本变化](./CHANGELOG.md)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdong)、[@dafang](https://github.com/dafang)、Codex、Claude

</div>
