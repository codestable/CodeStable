---
name: cs-onboard
description: CodeStable 接入。触发：初始化/迁移/搭骨架，自动判断空仓库或已有文档。
argument-hint: "[--mode refresh-runtime]"
---

# cs-onboard

把仓库**接入 CodeStable 工作流体系**——白纸或已有零散文档的都行。本技能做三件事：**搭骨架**、**归旧档**、**刷新 runtime 资产**。骨架搭好后子工作流（feature / issue / compound 等）即可直接运行。

---

## 入口意图

本次调用参数：$ARGUMENTS

参数为空或未被替换（仍是字面 `$ARGUMENTS`）时，自动扫描仓库并选择空仓库 / 迁移路径。`--mode refresh-runtime` 表示已接入项目只刷新技能包维护的 runtime 资产。

无参数默认行为：`.codestable/` 不存在走空仓库路径；存在则走迁移路径补齐骨架并刷新 runtime 资产。只想刷新 runtime、不审计或迁移文档时，显式传 `--mode refresh-runtime`。

---

## 三条路径

| 路径 | 适用 | 产出 |
|---|---|---|
| **空仓库** | 仓库内无 spec 类文档，也没有 `.codestable/` | 完整骨架 + 必要骨架文件 |
| **迁移** | 仓库内有零散文档 / `docs/` / 部分 `.codestable/` 结构 | 审计报告 + 迁移映射方案（用户逐条确认）+ 落盘 |
| **runtime refresh** | 已接入，只缺或需要升级 runtime 资产 | 同步 runtime 资产并写 `.codestable/runtime-manifest.json` |

启动后**先扫一次自动判断**，不要让用户选——TA 大概率不知道项目里现有哪些文档。扫描结果模糊（如只有 README）就明说判断依据并问用户。

---

## 标准骨架（目标状态）

> 共享路径与命名约定的权威版本是项目里的 `.codestable/reference/shared-conventions.md`——本技能从技能包内 `references/` 复制过去。下面只列 onboard 创建 / 检查的骨架文件。

```
.codestable/
├── .gitignore                  忽略 CodeStable 运行期 Python 缓存等机器产物
├── attention.md                CodeStable 技能启动必读的项目注意事项
├── requirements/               需求聚合根（空目录 .gitkeep）
│                               （CONTEXT.md / adrs/ 由 cs-domain 按需 lazy 创建）
├── roadmap/                    规划层聚合根
├── goals/                      目标聚合根（bounded goal 自主迭代 + 功能验收）
├── features/                   feature 聚合根
├── issues/                     issue 聚合根
├── refactors/                  重构聚合根（beta）
├── audits/                     审计聚合根
├── feedback/                   CodeStable skill 使用反馈和上报证据
├── brainstorms/                脑暴 / interview 持久记录聚合根
├── compound/                   沉淀类统一目录（cs-keep 写自由 markdown，grep 检索）
├── gates/                      workflow gate 配置（onboard 释放）
│   └── roadmap-goal-gates.yaml roadmap goal 阶段 gate policy
├── tools/                      跨工作流共享脚本（onboard 整目录释放）
│   ├── search-yaml.py / validate-yaml.py
│   ├── codestable-worktree-gate.py / codestable-ai-branch-guard.py / codestable-main-publish.py
│   └── codestable-doctor.py / codestable-spec-governance.py / codestable-dod-runner.py …
├── hooks/                      agent hook 配置（onboard 释放）
│   └── hooks.codex.json        PreToolUse branch-guard，拦截 main/master 上的实现
└── reference/                  跨子技能共享参考（onboard 整目录释放）
    ├── shared-conventions.md / tools.md / maintainer-notes.md
    ├── approval-conventions.md / goal-conventions.md / execution-conventions.md
    └── spec-governance-tools.md / branch-guard-hooks.md / tools-context.md
```

> `gates/`、`tools/` 与 `reference/` 由 onboard 整目录复制，自动带上 workflow gate 配置、gate 工具与共享口径。`hooks/` 是可选的分支保护层，详见下文「分支保护 hook」。

---

## 启动检查

**先检查一次现状**：

1. **检查 `.codestable/`**：不存在 → 空仓库候选；存在 → 迁移（部分补齐并刷新 runtime 资产）；用户显式传 `--mode refresh-runtime` → 只刷新 runtime
2. **旧 CodeStable兼容** CodeStable 经过多次改名，从 easysdd 到 codestable 再到 .codestable，如果遇到旧版的codestable目录，提示用户：

   > 检测到旧版codestable。建议直接 `git mv easysdd .codestable`，结构 / frontmatter 完全兼容，rename 后即用。要我执行吗？

   同意 → `git mv easysdd .codestable`，按迁移路径走（这时只需补齐可能缺失的 `attention.md`、`gates/`、`tools/` 和 `reference/`）。想保留旧目录 → 告诉他子技能只读 `.codestable/`，旧目录不会被读；按空仓库路径走新骨架

3. **Glob 全仓库 `.md`**（排除 `node_modules/` `.git/`）：根目录 `DESIGN.md` / `ARCHITECTURE.md` / `SPEC.md` / `README.md`；`docs/` `doc/` `design/` `spec/` `wiki/`；现有 `.codestable/` 下文件
4. **检查 `.codestable/attention.md`**：缺失则列为骨架待补齐项
5. **汇报扫描结论**：找到的相关文档（列路径）+ 走哪条路径 + 判断依据 + 不确定项

---

## Runtime refresh 路径

`cs-onboard --mode refresh-runtime` 可重复执行，用来把已接入项目升级到当前技能包的 runtime。它只覆盖技能包维护的资产：`.codestable/gates/`、`.codestable/tools/`、`.codestable/reference/`、`.codestable/hooks/`、`.codestable/.gitignore` 和 `.codestable/runtime-manifest.json`；不重新审计 / 迁移文档，不移动用户文件，不改 `attention.md` 的实质内容。

运行 `python3 <cs-onboard skill 目录>/tools/codestable-runtime-sync.py --root . --source-skill-dir <cs-onboard skill 目录>`。若报告 managed paths dirty，先让用户提交 / stash / 明确允许覆盖；不要静默覆盖本地改动。

---

## 空仓库路径

**步骤 1：和用户确认范围**

- 项目名 / 简介（汇报时引用）
- attention.md 只建最小骨架；用户已经给出的项目硬约束才写入，不凭空代填

**步骤 2：创建目录骨架**

按下面顺序执行，**不等用户逐步确认**——骨架是整体一次性的：

- `.codestable/{requirements,roadmap,goals,features,issues,refactors,audits,feedback,brainstorms,compound}/.gitkeep`
- `.codestable/.gitignore`（从当前 `cs-onboard` skill 目录的 `codestable.gitignore` 复制，忽略运行期缓存）
- `.codestable/attention.md`（最小骨架模板见同目录 `reference.md`）
- `.codestable/gates/`（用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录拷贝当前 `cs-onboard` skill 目录的 `gates/`）
- `.codestable/tools/`（用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录拷贝当前 `cs-onboard` skill 目录的 `tools/`，**不要 Read 再 Write**）
- `.codestable/reference/`（从当前 `cs-onboard` skill 目录的 `references/` 整目录复制）
- `.codestable/hooks/`（同上；可选的分支保护层，见下文「分支保护 hook」），再运行 `codestable-runtime-sync.py --force` 写 `.codestable/runtime-manifest.json`

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

**`.codestable/gates/`、`.codestable/tools/` 和 `.codestable/reference/` 一律用技能包新版本覆盖**——这些目录是技能包维护的共享资产，权威源在当前 `cs-onboard` skill 目录的 `gates/`、`tools/` 和 `references/`；项目里的只是落盘副本，且运行时目录名固定为 `.codestable/reference/`。技能包升级后再跑 onboard 的目的之一就是刷新副本，留旧版本会让子技能按过时口径工作。

覆盖前在汇报列出被覆盖文件让用户知道；用户明确说"我改过 tools/xxx.py 请保留"才例外保留并标红。这是迁移路径**唯一强制覆盖**的动作，其他已有文件遵守"不经确认不动"。

**落盘命令**：

```bash
# macOS / Linux
cp -rf <cs-onboard skill 目录>/gates/.      .codestable/gates/
cp -rf <cs-onboard skill 目录>/tools/.      .codestable/tools/
cp -rf <cs-onboard skill 目录>/references/.  .codestable/reference/
cp -rf <cs-onboard skill 目录>/hooks/.      .codestable/hooks/
cp -f  <cs-onboard skill 目录>/codestable.gitignore .codestable/.gitignore
find .codestable/tools -type d -name __pycache__ -prune -exec rm -rf {} +
find .codestable/tools -type f -name '*.pyc' -delete
python3 <cs-onboard skill 目录>/tools/codestable-runtime-sync.py --root . --source-skill-dir <cs-onboard skill 目录> --force

# Windows PowerShell
Copy-Item -Recurse -Force <cs-onboard skill 目录>\gates\*      .codestable\gates\
Copy-Item -Recurse -Force <cs-onboard skill 目录>\tools\*      .codestable\tools\
Copy-Item -Recurse -Force <cs-onboard skill 目录>\references\*  .codestable\reference\
Copy-Item -Recurse -Force <cs-onboard skill 目录>\hooks\*      .codestable\hooks\
Copy-Item -Force <cs-onboard skill 目录>\codestable.gitignore .codestable\.gitignore
Remove-Item -Recurse -Force .codestable\tools\__pycache__ -ErrorAction SilentlyContinue
Get-ChildItem .codestable\tools -Recurse -Filter *.pyc | Remove-Item -Force
python <cs-onboard skill 目录>\tools\codestable-runtime-sync.py --root . --source-skill-dir <cs-onboard skill 目录> --force
```

不要：Read+Write 手工搬（截断 / 改缩进）、一个个 cp（多步骤多出错）、先比 diff（规则就是无条件覆盖）。`codestable-runtime-sync.py` 会重做同步并写 `.codestable/runtime-manifest.json`。

`<cs-onboard skill 目录>` 是已加载 `SKILL.md` 所在目录。不确定先 `ls` 定位。拷完 `ls .codestable/gates/ .codestable/tools/ .codestable/reference/` 验证。

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

## 行级代码审查工具 open-code-review（可选）

`cs-code-review` 的审查分两环节：独立隔离 agent review（必需）+ OCR 行级扫描（增强）。OCR 用的是 [open-code-review](https://github.com/alibaba/open-code-review) 的 `ocr` CLI——装上后 `cs-code-review` 会自动检测并调用，没装则自然降级，不阻塞。

### 1. 安装：先检测，已装就别重装

```bash
which ocr   # 已经有路径 → 跳过安装，直接进第 2 步
```

只有 `which ocr` 找不到时，才**问 owner 是否安装**（默认建议装），同意后全局装：

```bash
npm install -g @alibaba-group/open-code-review
```

> 全局安装是 owner 环境改动（需联网），必须先确认再装，不自动执行。owner 拒绝 → 不装，`cs-code-review` 检测不到会记 `not-available` 并继续。

### 2. 配置 LLM：用 provider 体系，别用旧 `llm.*` 块

> ⚠️ **最容易踩的坑**：ocr v1.x 用的是 **`provider` / `providers` 体系**。网上 / 旧文档教的 `ocr config set llm.url ...`（`llm.*` 块）在新版**不生效**——配了也会被忽略，`ocr` 仍按默认 provider 连官方端点，表现为 `ocr llm test` 卡住超时（`context deadline exceeded`）。

`ocr` 是**独立 CLI 进程**，不复用 codex / claude agent 的模型——agent 只是替它执行 `ocr review` 命令，`ocr` 自己去连配置好的 LLM backend，必须单独配。

内置 provider 列表用 `ocr llm providers` 查。配置（以 anthropic 兼容网关为例）：

```bash
ocr config set provider anthropic
ocr config set providers.anthropic.url <网关 base-url>   # 不含 /v1/messages，ocr 按协议自动拼
ocr config set providers.anthropic.api_key <api-key>
ocr config set model <model>                             # 如 claude-opus-4-8
ocr llm test                                             # 必须看到 ✓ Connection test successful
```

- 字段名是 **`url`** 不是 `base_url`；anthropic 协议下 ocr 会自动拼 `/v1/messages`。
- OpenAI 兼容网关同理：`ocr config set provider <name>`（用 openai 协议的内置 provider 或自定义）+ `providers.<name>.url` + `.api_key`。
- 绝不替 owner 编造 / 硬编码 API key——只给命令模板，由 owner 自己填。

### 3. 收尾自检

跑 `python3 .codestable/tools/codestable-doctor.py --root .`，输出末尾 `OCR tool:` 行会报 `configured` / `unconfigured` / `misconfigured` / `not-installed`，并对错配（如残留旧 `llm.*` 块、provider 缺失）给出精确修复指引。doctor 只做静态体检、不发网络请求，连通性仍以 `ocr llm test` 为准。

---

## 退出条件

- [ ] `.codestable/` 各聚合根目录（requirements/roadmap/goals/features/issues/refactors/audits/brainstorms/compound）都存在
- [ ] `.codestable/.gitignore` 已安装
- [ ] `.codestable/attention.md` 已建
- [ ] `.codestable/gates/`、`.codestable/tools/`、`.codestable/reference/`、`.codestable/hooks/` 已从技能包复制
- [ ] `.codestable/runtime-manifest.json` 已写入当前技能包版本
- [ ] 已告知 owner 分支保护 hook 是可选项及如何接入 / 关闭
- [ ] 已 `which ocr` 检测：已装则跳过安装、确认配置为 provider 体系（非旧 `llm.*` 块）；未装则询问 owner 是否安装并记录结果
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
- **`.codestable/gates/`、`.codestable/tools/` 和 `.codestable/reference/` 走"不覆盖"保守策略**——这些目录**必须**用技能包新版本覆盖，否则升级后用户停留在过时口径
- **用 Read + Write 手工搬**——必须 `cp -rf` / `Copy-Item -Recurse -Force` 整目录覆盖
- **带入 `__pycache__` / `*.pyc` 或 Glob 忘排 `node_modules/` `.git/`**——清理缓存，避免噪声

---

## 相关文档

- `.codestable/reference/system-overview.md` — CodeStable 体系总览
- `.codestable/reference/shared-conventions.md` — 目录结构和共享口径的权威版本
- `.codestable/attention.md` — CodeStable 技能启动必读的项目注意事项
