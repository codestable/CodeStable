# author stage 协议（skill 编写契约）

工程化地写/改一个 cs skill。目标：可触发、可维护、**model/harness 无关**（Superpowers 教训：无关措辞才能到处稳定）。写完进 eval 用数据验证，别只靠直觉。

## frontmatter

```yaml
---
name: cs-xxx                 # 必须匹配目录名；小写字母/数字/连字符
description: 一句话「做什么 + 何时触发 + 触发词」；front-load 最常见场景（会被截断）
argument-hint: "[--stage ...] <arg>"   # 仅主入口
---
```

- `description` 是唯一决定「是否自动触发」的字段：写「用来做 X，触发词 A/B/C」，不要写「关于 X 的」。略偏推销：任务有 Y 特征就触发。
- 只有用户确实需要稳定参数契约时才加 `--stage/--mode`；不要为已退役入口创建兼容薄壳。

## 渐进披露（progressive disclosure）

三层：metadata（常驻）→ SKILL.md 正文（触发后加载）→ references/scripts（按需）。

- SKILL.md **≤300 行**（本仓硬约束）；厚规则拆到 `references/<stage>/protocol.md`，进该 stage 才加载。
- SKILL.md 写「贯穿任务的指引」，不是一次性步骤（触发后不重读）。

## 包结构（CS 合规）

```text
plugins/codestable/skills/cs-xxx/
├── SKILL.md
├── references/<stage>/protocol.md      # 复数 references/；一层；再嵌套用 support/
│   └── support/*.md
└── scripts/*.py                         # 自有工具；不 import 别的 skill 的 lib
```

- 用 `references/`（复数），嵌套用 `support/`，不得 `reference/` 单数或二层 `references/`。
- helper 放 owning skill 的 `scripts/`，不复制到项目；v2 不依赖 repo-local runtime。
- skill 间不耦合：A skill 不读 B skill 包内文件。项目事实走 `.codestable/attention.md`、
  `.codestable/lessons/`、`.codestable/work/` 或项目既有文档与 ADR。

## model/harness 无关（关键）

- 别写死某模型习惯（如「像 GPT 那样」）、别假设某 harness 专有工具名。
- 指令用能力描述（「用可用的搜索工具」）而非具体产品名，除非该 skill 就是绑定它。
- 判断准则型内容（当前步骤如何判断）留在 SKILL.md（对 LLM 决策准确率有实质贡献）；背景/历史移到 references。

## 两种性质

- 参考型（补背景知识）：像文档，`disable-model-invocation` 留默认，按需触发。
- 任务型（多步动作、有副作用）：像 playbook，常 `disable-model-invocation: true` 手动触发。

## 写完就验证

不要只靠审阅。为该 skill 建 `experiments/<skill>-NNN/`，写 planted-defect/golden fixtures，进 eval 量化；有改进假设就进 optimize。

## 退出条件

- [ ] frontmatter 合规，`description` 含明确触发词。
- [ ] SKILL.md ≤300 行，厚规则在 references。
- [ ] 包结构过 `tools/check-plugin-package.py`。
- [ ] 无 model/harness 专有假设（除非 skill 本身绑定）。
- [ ] 已建/更新对应 `experiments/` 以便 eval 验证。
