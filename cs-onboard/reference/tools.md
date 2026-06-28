# CodeStable 工具用法参考

本文件由 `cs-onboard` 复制到项目的 `.codestable/reference/tools.md`，所有 CodeStable 子技能用项目相对路径 `.codestable/reference/tools.md` 引用。

`.codestable/tools/` 下共享脚本的完整用法参考。子技能里只写本技能特有的 1-2 行典型查询；完整语法和示例看这里。

---

## 1. search-yaml.py

通用 YAML frontmatter 搜索工具。从项目根目录运行，无需安装额外依赖（PyYAML 可选，有则用，无则内建 fallback parser）。

### 基本语法

```bash
python .codestable/tools/search-yaml.py --dir {目录} [--filter key=value]... [--query "全文关键词"] [--sort-by FIELD [--order asc|desc]] [--full] [--json]
```

### filter 语法

- `key=value`：字段精确匹配（大小写不敏感）
- `key~=value`：字符串字段子串匹配；列表字段元素包含匹配
- `key=a|b|c` / `key~=a|b|c`：同一字段多个候选值，候选之间是 OR；在 PowerShell / Bash 中请给整个 filter 加引号，例如 `--filter "status=approved|draft"`

### 排序语法

- `--sort-by FIELD`：按 frontmatter 字段排序（典型字段：`last_reviewed`、`date`、`updated_at`）
- `--order desc|asc`：`desc` 默认，新的在前；`asc` 老的在前（查"谁最久没更新"用这个）
- 字段缺失 / 值为空的文档一律排到最后，不干扰前排结论

### 常用命令

`search-yaml.py` 用于扫**带 frontmatter 的产物**——feature spec / issue spec / requirements / adrs / guides / library-docs。

`.codestable/compound/` 由 `cs-keep` 写纯 markdown（无 frontmatter），**不用 search-yaml**，用全文检索即可——grep / ripgrep / 框架自带搜索都行，下例以 grep 示意：

```bash
grep -r "关键词" .codestable/compound/
grep -rl "prisma" .codestable/compound/   # 只列文件名
ls -lt .codestable/compound/ | head        # 看最近沉淀
```

带 frontmatter 的目录用 search-yaml：

```bash
# 搜索 feature 方案 doc
python .codestable/tools/search-yaml.py --dir .codestable/features --filter doc_type=feature-design --filter status=approved

# 按时间排序
python .codestable/tools/search-yaml.py --dir .codestable/library-docs --sort-by last_reviewed --order asc         # 最久没 review 的在前（找陈旧文档）
python .codestable/tools/search-yaml.py --dir .codestable/guides --filter status=current --sort-by last_reviewed --order asc

# 输出控制
python .codestable/tools/search-yaml.py --dir .codestable/features --filter status=approved --full
python .codestable/tools/search-yaml.py --dir .codestable/features --filter tags~=llm --json
```

### 典型使用场景

| 场景 | 命令建议 |
|---|---|
| feature-design 开始前查 compound 已有沉淀 | `grep -r "{关键词}" .codestable/compound/` |
| issue-analyze 根因分析前查历史 | `grep -rl "{关键词}" .codestable/compound/` 再人工挑相关的看 |
| cs-keep 落盘前查重叠 | `grep -rl "{关键词}" .codestable/compound/`，命中就先看那条决定更新还是新写 |
| 找最久没 review 的库文档 / 指南 | `--dir {目录} --filter status=current --sort-by last_reviewed --order asc` |

---

## 2. validate-yaml.py

YAML 语法校验工具。用于验证 frontmatter 语法和必填字段。

```bash
# 校验单个文件的 YAML 语法
python .codestable/tools/validate-yaml.py --file {文件路径} --yaml-only

# 校验必填字段
python .codestable/tools/validate-yaml.py --file {文件路径} --require doc_type --require status

# 批量校验目录下所有文件
python .codestable/tools/validate-yaml.py --dir {目录} --require doc_type --require status
```
