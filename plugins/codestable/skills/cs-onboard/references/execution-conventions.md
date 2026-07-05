# 执行约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/execution-conventions.md`。它只承载
所有 CodeStable skill 启动前必须共用的 preflight、runtime 恢复和按需规则索引。

## CodeStable Preflight

任何 CodeStable skill 在判断或动作前先执行 preflight：

1. 读 `.codestable/attention.md`。
2. 缺 `.codestable/attention.md` 时视为骨架不完整，提示补齐或运行 `cs-onboard`。
3. 不用 `AGENTS.md` / `CLAUDE.md` / `.cursorrules` 等外部 AI 入口代替
   `.codestable/attention.md`；需要同步外部入口时走 `cs-docs-neat`。
4. 检查 `.codestable/runtime-manifest.json`；缺失、版本不匹配或 runtime capability 缺失时，
   按下方「Runtime 资产恢复」同步。
5. 正文报告语言按 `.codestable/attention.md` 的报告语言策略执行；默认中文。frontmatter /
   yaml 字段不翻译。

`cs-note` 是唯一例外：`.codestable/` 存在但 `attention.md` 缺失时，它可以创建最小分节骨架
后写入。

## Runtime 资产恢复

`.codestable/tools/`、`.codestable/gates/`、`.codestable/reference/`、
`.codestable/hooks/` 和 `.codestable/.gitignore` 是 `cs-onboard` 释放的 package-owned
runtime 资产。已接入项目可以重复运行 runtime sync 刷新这些资产并写
`.codestable/runtime-manifest.json`；该模式不重新迁移文档、不移动用户文件、不改
`attention.md` 的实质内容。

preflight 自动同步时，先定位当前插件包的 `cs-onboard` skill 目录：优先用当前已加载
CodeStable skill 的 sibling `../cs-onboard`，找不到再加载 `codestable:cs-onboard`。不要用
项目 `.codestable/tools/` 里的旧副本做版本判定。运行：

```bash
python3 <cs-onboard skill 目录>/tools/codestable-runtime-sync.py --root . --source-skill-dir <cs-onboard skill 目录> --check --json
```

状态为 `ok` 继续；`runtime-incomplete` / `version-mismatch` / 缺 manifest 时，用当前插件包里的
`cs-onboard/tools/codestable-runtime-sync.py` 自动同步，运行同一命令去掉 `--check`。
`managed-paths-dirty`、`not-onboarded` 或 `onboard-incomplete` 停用户；managed paths 有未提交
改动时不自动覆盖。

常用 runtime capability：`base`、`workflow-next`、`worktree-gate`、`goal-gates`。可用
`python3 .codestable/tools/codestable-doctor.py --root . --json` 查看项目副本的
`tooling.runtime.capabilities`；`workflow-next` 对应 `codestable-workflow-next.py`。

## 按需规则索引

- 目录、frontmatter、checklist、roadmap ↔ feature：`.codestable/reference/shared-conventions.md`
- 代码编辑、执行 worktree、commit、finish、context packet：
  `.codestable/reference/worktree-conventions.md`
- Task agent 选择、Task agent 生命周期、Goal driver 派发：
  `.codestable/reference/agent-conventions.md`
- owner approval 报告：`.codestable/reference/approval-conventions.md`
- goal 包装器通用口径：`.codestable/reference/goal-conventions.md`
- 工具命令详情：`.codestable/reference/tools.md`、`.codestable/reference/tools-context.md`
