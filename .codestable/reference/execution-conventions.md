# 执行约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/execution-conventions.md`。它只承载
所有 CodeStable skill 启动前必须共用的 preflight、runtime 恢复和按需规则索引。

## CodeStable Preflight

任何 CodeStable skill 在判断或动作前先执行 preflight。

**上下文幂等（首次做、已做复用）**：同一会话首次 preflight 成功后，attention 内容与 onboard / runtime 结论已在上下文内；后续 skill 直接复用，不重读 `.codestable/attention.md`、不重复 onboard / runtime 检查——除非上一轮 preflight 报告过缺失 / 不一致，或期间改动了 attention / runtime 资产。首次 preflight（或需重新确认时）执行：

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

## CodeStable 自身反馈

遇到 CodeStable 规则不清、阶段跑偏或工具失败时，可以提示用户显式调用 `cs-feedback`。
提示本身不得读取历史、后台采集、自动上传、自动修改目标 skill，也不得替用户确认 public preview。

## Skill 间同轮转交

公开 skill 选择另一个主入口后，按已安装 skill 名称加载目标协议，并在当前 run 继续。skill 是独立安装单元；不得靠读取 sibling skill 文件模拟转交。

- **已确认出口**：用户已经选中对象、确认方案或明确表达 ready，当前 skill 直接加载目标协议。比如 audit 选中 finding、brainstorm case 3 已 ready 拆解。
- **待确认出口**：下一阶段仍需 owner 点头时只停一个 checkpoint；用户确认后在当前 run 加载目标协议，不要求重新调用命令。brainstorm case 1 / case 2 / case 4 属于此类。
- 原始诉求、用户已选对象、相关产物路径和本会话已确认的 preflight 结论一并传递；目标 skill 仍按自身协议恢复业务事实。
- 一个请求同一时刻只加载一个主入口；`cs-onboard` 可作为串行前置 gate，完成后再继续原目标。
- 转交本身不授权写入、外部通信或跳过 checkpoint；这些权限与副作用继续由目标 skill 的协议决定。
- 目标 skill 不可加载时停下报告，不在当前 skill 内复制或猜测目标流程。

## Runtime 资产恢复

`.codestable/gates/`、`.codestable/reference/`、`.codestable/.gitignore` 和
`.codestable/runtime-manifest.json` 是 `cs-onboard` 释放的 package-owned repo-local runtime
资产。Python 工具脚本从当前 `cs-onboard` skill 包的 `tools/` 目录运行；旧项目已有
`.codestable/tools/` 只作兼容副本，不删除、不覆盖。已接入项目可以重复运行 runtime sync
刷新 repo-local 资产并写 `.codestable/runtime-manifest.json`；该模式不重新迁移文档、不移动
用户文件、不改 `attention.md` 的实质内容。

preflight 自动同步或调用工具时，先定位当前插件包的 `cs-onboard` skill 目录：优先用当前已加载
CodeStable skill 的 sibling `../cs-onboard`，找不到再加载 `codestable:cs-onboard`。不要用项目
`.codestable/tools/` 里的旧副本做版本判定或新版工具入口。运行：

```bash
python3 <cs-onboard skill 目录>/tools/codestable-runtime-sync.py --root . --source-skill-dir <cs-onboard skill 目录> --check --json
```

状态为 `ok` 继续；`runtime-incomplete` / `version-mismatch` / 缺 manifest 时，用当前插件包里的
`cs-onboard/tools/codestable-runtime-sync.py` 自动同步，运行同一命令去掉 `--check`。
`managed-paths-dirty`、`not-onboarded` 或 `onboard-incomplete` 停用户；managed paths 有未提交
改动时不自动覆盖。

常用 runtime capability：`base`、`workflow-next`、`goal-gates`。可用
`python3 <cs-onboard skill 目录>/tools/codestable-doctor.py --root . --json` 查看
`tooling.runtime.capabilities`；`repo_paths` 是项目资产，`skill_tool_paths` 是全局工具资产。

## 按需规则索引

- 目录、frontmatter、checklist、roadmap ↔ feature：`.codestable/reference/shared-conventions.md`
- context packet、commit planning 和 backlog 工具：`.codestable/reference/tools-context.md`
- Task agent 选择、Task agent 生命周期、Goal driver 派发：
  `.codestable/reference/agent-conventions.md`
- owner approval 报告：`.codestable/reference/approval-conventions.md`
- goal 包装器通用口径：`.codestable/reference/goal-conventions.md`
- 工具命令详情：`.codestable/reference/tools.md`、`.codestable/reference/tools-context.md`
