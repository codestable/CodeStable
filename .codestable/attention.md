# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

## 报告语言

CodeStable 所有落盘产出的正文用**中文**：plan / design、plan review / design-review、code review、QA、验收、issue（report / analysis / fix-note）、refactor、roadmap、goal、沉淀（compound）等所有人读报告都用中文表达。机器状态（YAML / JSON / `state.yaml` / frontmatter 字段）保持机读格式不翻译。如需改默认语言，改这一节。

## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

### 运行与本地起服务

### 测试

### 命令与脚本陷阱

### 路径与目录约定

### 环境变量与凭证

### 其他

- 调用 `cs-review`（含本仓库所有 CodeStable design review、code review 和修复后复审）时，发起者优先通过 Paseo 创建 fresh reviewer subagent，并与当前主 agent 异构：主 agent 为 Codex 时，首选 `provider=claude`、`model=claude-fable-5`、`thinkingOptionId=high`，不可用则回退 `provider=claude`、`model=claude-opus-5`；主 agent 为 Claude 时，使用 `provider=codex`、`model=gpt-5.6-sol`。指定路径均不可用时停下报告，不静默改用其他 reviewer
