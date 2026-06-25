---
name: cs-onboard
description: 把新仓库或有零散文档的仓库接入 CodeStable 体系，两条路径自动判断：空仓库从零搭骨架，已有文档走审计 + 迁移映射。触发：用户说"在这个项目里用 CodeStable"、"搭 CodeStable 结构"、"初始化 CodeStable"、"迁移到 CodeStable"。
---

# cs-onboard

把仓库**接入 CodeStable 工作流体系**——白纸或已有零散文档的都行。本技能只做两件事：**搭骨架**、**归旧档**。骨架搭好后子工作流（feature / issue / compound 等）即可直接运行。

---

## 两条路径

| 路径 | 适用 | 产出 |
|---|---|---|
| **空仓库** | 仓库内无 spec 类文档，也没有 `.codestable/` | 完整骨架 + 必要骨架文件 |
| **迁移** | 仓库内有零散文档 / `docs/` / 部分 `.codestable/` 结构 | 审计报告 + 迁移映射方案（用户逐条确认）+ 落盘 |

启动后**先扫一次自动判断**，不要让用户选——TA 大概率不知道项目里现有哪些文档。扫描结果模糊（如只有 README）就明说判断依据并问用户。

---

## 标准骨架（目标状态）

> 共享路径与命名约定的权威版本是项目里的 `.codestable/reference/shared-conventions.md`——本技能从技能包复制过去。下面只列 onboard 创建 / 检查的骨架文件。

```
.codestable/
├── attention.md                CodeStable 技能启动必读的项目注意事项
├── requirements/               需求聚合根（空目录 .gitkeep）
│                               （CONTEXT.md / adrs/ 由 cs-domain 按需 lazy 创建）
├── roadmap/                    规划层聚合根
├── goals/                      目标聚合根（bounded goal 自主迭代 + 功能验收）
├── features/                   feature 聚合根
├── issues/                     issue 聚合根
├── refactors/                  重构聚合根（beta）
├── audits/                     审计聚合根
├── brainstorms/                脑暴 / interview 持久记录聚合根
├── brainstorm/                 脑暴 spike 实验代码区（验完结论回写 brainstorms note）
├── compound/                   沉淀类统一目录（cs-keep 写自由 markdown，grep 检索）
├── tools/                      跨工作流共享脚本（onboard 整目录释放）
│   ├── search-yaml.py / validate-yaml.py
│   ├── codestable-worktree-gate.py / codestable-ai-branch-guard.py / codestable-main-publish.py
│   └── codestable-doctor.py / codestable-spec-governance.py / build-review-packet.py …
├── hooks/                      agent hook 配置（onboard 释放）
│   └── hooks.codex.json        PreToolUse branch-guard，拦截 main/master 上的实现
└── reference/                  跨子技能共享参考（onboard 整目录释放）
    ├── shared-conventions.md / tools.md / maintainer-notes.md
    ├── approval-conventions.md / goal-conventions.md / execution-conventions.md
    └── spec-governance-tools.md / branch-guard-hooks.md / tools-context.md
```

> `tools/` 与 `reference/` 由 onboard 整目录复制，自动带上全部 gate 工具与共享口径，无需逐个列举维护。`hooks/` 是可选的分支保护层，详见下文「分支保护 hook」。

---

## 启动检查

**先检查一次现状**：

1. **检查 `.codestable/`**：不存在 → 空仓库候选；存在但不完整 → 迁移（部分补齐）
2. **旧 CodeStable兼容** CodeStable 经过多次改名，从 easysdd 到 codestable 再到 .codestable，如果遇到旧版的codestable目录，提示用户：

   > 检测到旧版codestable。建议直接 `git mv easysdd .codestable`，结构 / frontmatter 完全兼容，rename 后即用。要我执行吗？

   同意 → `git mv easysdd .codestable`，按迁移路径走（这时只需补齐可能缺失的 `attention.md`、`tools/` 和 `reference/`）。想保留旧目录 → 告诉他子技能只读 `.codestable/`，旧目录不会被读；按空仓库路径走新骨架

3. **Glob 全仓库 `.md`**（排除 `node_modules/` `.git/`）：根目录 `DESIGN.md` / `ARCHITECTURE.md` / `SPEC.md` / `README.md`；`docs/` `doc/` `design/` `spec/` `wiki/`；现有 `.codestable/` 下文件
4. **检查 `.codestable/attention.md`**：缺失则列为骨架待补齐项
5. **汇报扫描结论**：找到的相关文档（列路径）+ 走哪条路径 + 判断依据 + 不确定项

---

## 空仓库路径

**步骤 1：和用户确认范围**

- 项目名 / 简介（汇报时引用）
- attention.md 只建最小骨架；用户已经给出的项目硬约束才写入，不凭空代填

**步骤 2：创建目录骨架**

按下面顺序执行，**不等用户逐步确认**——骨架是整体一次性的：

- `.codestable/{requirements,roadmap,goals,features,issues,refactors,audits,brainstorms,brainstorm,compound}/.gitkeep`
- `.codestable/attention.md`（最小骨架模板见同目录 `reference.md`）
- `.codestable/tools/`（用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录拷贝技能包 `cs-onboard/tools/`，**不要 Read 再 Write**）
- `.codestable/reference/`（同上）
- `.codestable/hooks/`（同上；可选的分支保护层，见下文「分支保护 hook」）

`requirements/CONTEXT.md` 和 `requirements/adrs/` 不在骨架里——交给 `cs-domain` 在用户第一次需要术语 / ADR 时 lazy 创建。

> **落盘用 shell 整目录覆盖**，不要 Read 再 Write——这两个目录是机器共享资产，Read+Write 会截断大文件、改缩进、吃空行，还慢费 token。具体命令见迁移路径步骤 4。

**步骤 3：attention.md 提醒**

attention.md 已创建但默认只有空骨架。汇报时提醒用户：有编译前置、测试命令、目录禁区、凭证规则、报告语言偏好这类"每次 CodeStable 技能启动都必须知道"的信息，后续用 `cs-note` 一条条追加。

**步骤 4：验收汇报**

列建了哪些文件：

> CodeStable 骨架已就绪。现在可以：开始新功能 `cs-feat` / 报告问题 `cs-issue` / 沉淀知识 `cs-keep`

---

## 迁移路径

**步骤 1：生成审计报告**

| 现有文件 | 推测内容类型 | 建议归入 CodeStable | 置信度 |
|---|---|---|---|
| `docs/glossary.md` | 领域术语 | `.codestable/requirements/CONTEXT.md`（cs-domain 写） | 高 |
| `docs/adr-*.md` | 架构决策 | `.codestable/requirements/adrs/NNN-{slug}.md` | 高 |
| `docs/feature-auth.md` | 功能设计稿 | `.codestable/features/YYYY-MM-DD-auth/auth-design.md` | 中 |
| `SPEC.md` | 功能需求？ | 需用户确认 | 低 |

**置信度**：高 = 语义明确匹配；中 = 可推断有歧义；低 = 不明确或映射多个位置都合理。

**步骤 2：逐条对齐**

中 / 低置信度的用 `AskUserQuestion` 问：

- 中：给推断理由，问"按这个方式归位？"
- 低：描述文件内容，给 2-3 个候选位置 + "跳过"

高置信度不逐条问但要在汇报里列，给用户复审机会——逐条问会让节奏失控。

**步骤 3：处理已部分存在的 .codestable/**

- 命名不符规范（`YYYY-MM-DD-{slug}` 格式）但有内容 → 提示用户问是否重命名
- 空占位（`.gitkeep` / 空 `.md`）→ 直接补齐不问

**步骤 4：补齐缺失骨架**

对照标准骨架补齐**用户确认后仍缺失**的目录 / 文件。已有内容不覆盖。

**`.codestable/tools/` 和 `.codestable/reference/` 一律用技能包新版本覆盖**——这两个目录是技能包维护的共享资产，权威源在 `cs-onboard/tools/` 和 `cs-onboard/reference/`，项目里的只是落盘副本。技能包升级后再跑 onboard 的目的之一就是刷新副本，留旧版本会让子技能按过时口径工作。

覆盖前在汇报列出被覆盖文件让用户知道；用户明确说"我改过 tools/xxx.py 请保留"才例外保留并标红。这是迁移路径**唯一强制覆盖**的动作，其他已有文件遵守"不经确认不动"。

**落盘命令**：

```bash
# macOS / Linux
cp -rf <技能包路径>/cs-onboard/tools/.      .codestable/tools/
cp -rf <技能包路径>/cs-onboard/reference/.  .codestable/reference/
cp -rf <技能包路径>/cs-onboard/hooks/.      .codestable/hooks/

# Windows PowerShell
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\tools\*      .codestable\tools\
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\reference\*  .codestable\reference\
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\hooks\*      .codestable\hooks\
```

不要：Read+Write 手工搬（截断 / 改缩进）、一个个 cp（多步骤多出错）、先比 diff（规则就是无条件覆盖）。

技能包路径一般是 skill 安装目录（`~/.claude/skills/cs-onboard/` 或插件目录）。不确定先 `ls` 定位。拷完 `ls .codestable/tools/ .codestable/reference/` 验证。

**步骤 5：处理不迁移的文件**

用户选"跳过"的文件：**不移动 / 不删除 / 不重命名**，汇报标"保留原位（未纳入 CodeStable）"。**绝不允许未经确认就动**——onboard 只允许 AI 整理不允许替用户做删除决定。

**步骤 6：attention.md 提醒**（同空仓库路径步骤 3）

**步骤 7：验收汇报**

列：迁移文件清单（from → to）、新建骨架、未迁移文件（保留原位）、下一步建议。

---

## 骨架文件模板

`attention.md` 最小模板见同目录 `reference.md`。

---

## 分支保护 hook（可选）

`.codestable/hooks/hooks.codex.json` 注册一个 `PreToolUse` 钩子，调用 `.codestable/tools/codestable-ai-branch-guard.py`，在 AI 试图于 `main`/`master` 等受保护分支上 Edit/Write/Bash 改代码时拦截，强制改动落到 linked worktree 的类型分支（`feat/` / `fix/` / `refactor/`）。详细规则见 `.codestable/reference/branch-guard-hooks.md`。

- **接入**：把 `hooks.codex.json` 的内容合并进 agent 的 hook 配置（Claude Code `.claude/settings.json` 或 Codex 等价位置）。onboard 只释放文件，**不自动改 agent 全局配置**——是否启用由 owner 决定。
- **侵入性**：启用后日常在 main 上的直接编辑会被挡下，需走 worktree 流程。不想要这套强约束就不接入，留着 `tools/` 里的 gate 脚本手动调用即可。
- **关闭**：从 agent hook 配置移除该条即可，工具脚本仍可被各实现技能显式调用。

---

## 退出条件

- [ ] `.codestable/` 各聚合根目录（requirements/roadmap/goals/features/issues/refactors/audits/brainstorms/compound）都存在
- [ ] `.codestable/attention.md` 已建
- [ ] `.codestable/tools/`、`.codestable/reference/`、`.codestable/hooks/` 已从技能包复制
- [ ] 已告知 owner 分支保护 hook 是可选项及如何接入 / 关闭
- [ ] 迁移路径：每条映射都有明确处理结果（迁移 / 保留原位）
- [ ] 迁移路径：没有未经确认就移动的文件
- [ ] 验收汇报已给出

---

## 容易踩的坑

- **未经确认就移动 / 删除已有文件**——迁移核心原则是用户拍板
- **替用户填 attention.md 实质内容**——必须项目 owner 来定，AI 只提供模板
- **重新引入 `AGENTS.md` / `CLAUDE.md` 兼容路径**——CodeStable 的启动注意事项入口固定为 `.codestable/attention.md`
- **建完骨架立刻开始 feature/issue**——onboard 是"搭环境"不是"开始干活"
- **低置信度直接执行**——低 = 必须问
- **`.codestable/tools/` 和 `.codestable/reference/` 走"不覆盖"保守策略**——这两个**必须**用技能包新版本覆盖，否则升级后用户停留在过时口径
- **用 Read + Write 手工搬**——必须 `cp -rf` / `Copy-Item -Recurse -Force` 整目录覆盖
- **Glob 时忘记排除 `node_modules/` `.git/`**——会让扫描结果充斥噪声

---

## 相关文档

- `.codestable/reference/system-overview.md` — CodeStable 体系总览
- `.codestable/reference/shared-conventions.md` — 目录结构和共享口径的权威版本
- `.codestable/attention.md` — CodeStable 技能启动必读的项目注意事项
