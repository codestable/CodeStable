# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

## 报告语言

CodeStable 所有落盘产出的正文用**中文**：plan / design、plan review / design-review、code review、QA、验收、issue（report / analysis / fix-note）、refactor、roadmap、goal、沉淀（compound）等所有人读报告都用中文表达。机器状态（YAML / JSON / `state.yaml` / frontmatter 字段）保持机读格式不翻译。如需改默认语言，改这一节。

## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

### 运行与本地起服务

### 测试

- 默认 v2 产品与发布回归：`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests -rs`。该命令不运行
  repo-local maintainer eval。
- 修改 `.claude/skills/eval-cs-skill/` 的 scripts、harness 或 experiment 时，显式运行
  `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --strict-markers -q .claude/skills/eval-cs-skill/tests -rs`。
- eval suite 中的 `real_cli` 用例默认 skip；只有明确需要真实 CLI 验证时才传 `--run-real-cli`。

### 命令与脚本陷阱

### 路径与目录约定

### 环境变量与凭证

### 其他

- 调用 `cs-review`（含本仓库所有 CodeStable design review、code review 和修复后复审）时，发起者优先通过 Paseo 创建 fresh reviewer subagent，并与当前主 agent 异构：主 agent 为 Codex 时，首选 `provider=claude`、`model=claude-fable-5`、`thinkingOptionId=high`；没有可用 Fable 账户时，先回退 `provider=claude`、`model=claude-opus-5`，Opus 5 也不可用时才回退同构最强 reviewer。主 agent 为 Claude 时，使用 `provider=codex`、`model=gpt-5.6-sol`；该异构路径不可用时才回退同构最强 reviewer。记录最终 agent/model 与回退原因，不依赖默认模型
