# CodeStable 共享口径

由 `cs-onboard` 复制到项目的 `.codestable/reference/shared-conventions.md`。所有 CodeStable 子技能用项目相对路径 `.codestable/reference/shared-conventions.md` 引用本文件——跨子技能共享但不适合堆在单个技能里的规范的唯一权威版本。

skill 本身不共享文件系统（每个 skill 是独立安装单元），共享口径不能放在某个 skill 内部被别的 skill 引用。放在"工作项目"里对所有 skill 都可达。

---

## 0. 目录结构与路径命名

onboard 完成后骨架（`cs-onboard` 负责搭建）：

```
.codestable/
├── .gitignore             忽略 CodeStable 运行期 Python 缓存等机器产物
├── attention.md           CodeStable 技能启动必读的项目注意事项
├── requirements/          能力愿景 + 领域模型 + 决策记录
│   ├── VISION.md           能力中心索引（cs-req 维护）
│   ├── {slug}.md           一个能力一份，扁平（cs-req 产出）
│   ├── CONTEXT.md          领域术语表（cs-domain lazy 创建；多 context 时被 CONTEXT-MAP.md 替代）
│   ├── CONTEXT-MAP.md      多 context 拓扑入口（cs-domain，仅多 context 时存在）
│   ├── adrs/               架构决策记录（cs-domain，lazy 创建）
│   │   └── NNN-{slug}.md   Nygard 四节 + 状态机 frontmatter
│   └── {ctx}/              子 context 子目录（仅多 context 时存在）
│       ├── CONTEXT.md      子 context 术语
│       ├── adrs/           子 context 特定 ADR
│       └── {capability}.md 归属本 context 的能力
├── roadmap/               规划层（"接下来怎么做这块大需求 + 模块怎么切 + 接口怎么定"）
│   └── {slug}/            一个大需求一个子目录（cs-epic 产出）
│       ├── {slug}-roadmap.md   主文档：背景 / 范围 / 模块拆分 / 接口契约 / 子 feature 清单 / 排期
│       ├── {slug}-items.yaml   机器可读子 feature 清单，acceptance 回写状态
│       ├── {slug}-roadmap-review.md 人工确认前的规划审查报告
│       └── drafts/             可选
├── goals/                 目标聚合根（起点报告 / 自主迭代 / 功能验收）
│   └── {slug}/           一个 bounded goal 一个子目录（cs-goal 产出）
│       ├── {slug}-start-report.md 起点报告
│       ├── {slug}-state.yaml     机器可读状态
│       ├── {slug}-iteration-*.md 迭代报告
│       └── {slug}-functional-acceptance.md Task agent 功能验收
├── features/              feature spec 聚合根
│   └── YYYY-MM-DD-{slug}/  每个 feature 一个目录
│       ├── {slug}-brainstorm.md  （可选，case 2 时产出）
│       ├── {slug}-design.md      （标准流程）
│       ├── {slug}-checklist.yaml （标准流程）
│       ├── {slug}-design-review.md（人审前方案审查）
│       ├── {slug}-review.md      （实现后代码审查）
│       ├── {slug}-qa.md          （代码审查后 QA gate）
│       ├── {slug}-acceptance.md  （标准流程）
│       └── {slug}-ff-note.md     （fastforward 通道唯一产物，与标准流程产物互斥）
├── issues/                issue spec 聚合根
│   └── YYYY-MM-DD-{slug}/
│       ├── {slug}-report.md
│       ├── {slug}-analysis.md   （根因不显然才有）
│       └── {slug}-fix-note.md
├── refactors/             refactor spec 聚合根
│   └── YYYY-MM-DD-{slug}/
│       ├── {slug}-scan.md
│       ├── {slug}-refactor-design.md
│       ├── {slug}-checklist.yaml
│       └── {slug}-apply-notes.md
├── feedback/              CodeStable skill 使用反馈和上报证据
│   └── YYYY-MM-DD-{slug}/
│       ├── {slug}-report.md
│       ├── evidence.json              local-private observations
│       ├── triage.json                local-private assessments + quality
│       ├── public-issue-context.json  allowlist preview，可选
│       ├── github-issue.md            用户确认后可上传，可选
│       └── regression-candidate.json  local-private eval 交接，可选
├── compound/              沉淀类文档统一目录（cs-keep 产出）
│   └── YYYY-MM-DD-{slug}.md
│                          纯 markdown，无 frontmatter，grep 检索
├── gates/                 workflow gate 配置（onboard 从技能包释放）
└── reference/             共享参考文档（onboard 从技能包释放）
```

`.codestable/.gitignore` 由 onboard 安装，至少忽略 `**/__pycache__/` 与 `**/*.pyc`；这些是 gate / validator 运行期缓存，不属于 CodeStable 证据产物。

### 命名规则

- 需求文档：`requirements/{slug}.md`（能力愿景，不带日期前缀，扁平不分组）；中心索引 `requirements/VISION.md`
- roadmap：`roadmap/{slug}/`（不带日期前缀，平铺不嵌套）
- feature / issue / refactor 目录：带日期前缀 `YYYY-MM-DD-{slug}`
- feedback 目录：带日期前缀 `YYYY-MM-DD-{slug}`，保存 report、local-private evidence/triage/candidate 与用户确认的 public preview
- 沉淀类：`compound/YYYY-MM-DD-{slug}.md`，日期用**归档当天**，纯 markdown 无 frontmatter（cs-keep 产出）
- 领域术语：`requirements/CONTEXT.md`（单 context）或 `requirements/{ctx}/CONTEXT.md`（多 context）；cs-domain lazy 创建
- 架构决策：`requirements/adrs/NNN-{slug}.md`（系统级）或 `requirements/{ctx}/adrs/NNN-{slug}.md`（子 context）；3 位编号，cs-domain 产出
- 项目注意事项入口固定为 `.codestable/attention.md`，所有 CodeStable 子技能启动前必须读取；不要用 `AGENTS.md` / `CLAUDE.md` 等外部入口代替它

### 单 context ↔ 多 context 拓扑

- `requirements/CONTEXT-MAP.md` 存在 → 多 context 模式：术语和 ADR 按子 context 分目录
- 只有 `requirements/CONTEXT.md` → 单 context：术语和 ADR 平铺在 `requirements/` 下
- 升级路径见 `cs-domain` 的"单 → 多 context 升级"节

### 改目录结构

改 `plugins/codestable/skills/cs-onboard/references/shared-conventions.md` 模板，新项目 onboard 时带上新版本；已有项目手动同步 `.codestable/reference/shared-conventions.md`。

---

## 1. 共享元数据口径

**feature spec**：brainstorm / design / design-review / review / QA / acceptance 共用 `doc_type` / `feature` / `status` / `summary` / `tags`。`cs-feat` 的各阶段只补特有字段。`status`：brainstorm = `confirmed`（落盘即确认无 draft）；design = `draft` / `approved`；design-review / review / QA / acceptance 见对应阶段协议。

新增 feature gate 的 `doc_type`：`feature-design-review`（status: `passed` / `changes-requested` / `blocked`）、`feature-review`（status: `passed` / `changes-requested` / `blocked`）、`feature-qa`（status: `passed` / `failed` / `blocked`）、`feature-acceptance`（status: `passed` / `blocked`）。review / QA 报告是后续 gate 的输入，不替用户批准 design，也不替 acceptance 做最终验收。

**issue spec**：report / analysis / fix-note 共用 `doc_type` / `issue` / `status` / `tags`。`severity` / `root_cause_type` / `path` 由对应阶段按需补。

**归档类（compound）**：由 `cs-keep` 统一产出，写到 `.codestable/compound/YYYY-MM-DD-{slug}.md`。纯 markdown，**无 frontmatter**。三段足够：背景 / 结论 / 证据。检索靠 grep。

**反馈类（feedback）**：由 `cs-feedback` 显式调用后产出，写到 `.codestable/feedback/YYYY-MM-DD-{slug}/`。`evidence.json` 保存脱敏 observation/incident，`triage.json` 保存 assessment 与 readiness，二者及 candidate 均为 local-private；`github-issue.md` 只能从 public allowlist 渲染并在上传前让用户确认。

**外部读者文档**（`cs-docs` tutorial / api mode）：frontmatter 由对应模式定义。无特殊说明：`draft` = 待 review，`current` = 当前有效，`outdated` = 代码已变更待同步。

**写作约束**：子技能提字段时优先写"额外字段"或"阶段状态变化"，不重复展开整套通用字段。

---

## 2. {slug}-checklist.yaml 生命周期

- 是 feature 工作流的唯一执行清单
- 由 `cs-feat` design 阶段在 draft design 成型后先生成 `steps` + `checks`，供 design-review 阶段和用户 review；用户确认后随 design 一起进入实现
- `cs-feat` fastforward mode **不生成** checklist（也不写 design / acceptance），是跳过 spec 流程直接写代码的超轻量通道；唯一留下的痕迹是动手后回写的 `{slug}-ff-note.md`（轻量回顾，参与 scoped-commit、可被 cs-req / cs-domain backfill 检索到）

`steps` 的粒度是 **编排-计算分离维度的切片策略**——按"先编排骨架、后计算节点、最后持久化与测试"写（最简 Workflow 先行 → 逐个节点填充），**不下沉到 file:line / 函数级**。具体改哪个文件由 implement 阶段决定。

**design 的职责**：

- 提取 `steps`（4-8 步，每步独立可验证退出信号）：后端节奏 = 编排骨架 → 计算节点逐个填 → 接通持久化 → 测试覆盖；前端 = 静态结构 → 交互逻辑 → 状态接入 → 联调收尾
- 提取 `checks`：第 1 节"明确不做"→ 范围守护；第 2.1 接口 → 名词契约；第 2.2 主流程 + 流程级约束 → 编排骨架；第 2.3 挂载点 → 挂载点；第 3 节场景清单 → 验收场景

**implement 的职责**：

- 按 `steps` 顺序执行，每步完成把 status `pending` → `done`
- 实现到具体文件级时需要拆分某步、或发现微重构是其前置（参考第 7 节反射检查）→ 跟用户对齐后追加 / 拆分 steps，**不偷偷做**
- 不改写 `checks`

**acceptance 的职责**：只更新 `checks[].status`（`pending` → `passed` / `failed`），不重写 `steps`。

**写作约束**：子技能描述 checklist 时只补本阶段读 / 写哪一部分，不重新定义生命周期。

---

## 2.5 roadmap ↔ feature 衔接协议

`.codestable/roadmap/{slug}/{slug}-items.yaml` 是规划层和 feature 执行层的唯一接口。三个技能共同读写它——是 skill 都读写项目共享产物，不算耦合。

**items.yaml 状态机**：

```
planned  → in-progress  （cs-feat design 阶段启动 feature 时改）
in-progress → done      （cs-feat acceptance 阶段验收完成时改）
planned  → dropped      （cs-epic planning update 模式，用户决定不做时改）
```

`done` / `dropped` 是终态。需要回退重做的新加一条 slug 略改的条目，不改终态。

**cs-epic planning 阶段的职责**：生成和维护 roadmap 主文档 + items.yaml；把 `planned` 改 `dropped`（用户放弃时）；不改 `in-progress` / `done`（feature 流程负责）。第一版内部仍使用 `.codestable/roadmap/`。

**cs-epic review 阶段的职责**：在人审前只读审查 roadmap 主文档 + items.yaml + 相关事实，写 `{slug}-roadmap-review.md`；不修改 roadmap，不替用户批准。

**cs-feat design 阶段的职责**（从 roadmap 起头时）：

1. design.md frontmatter 加 `roadmap: {roadmap-slug}` + `roadmap_item: {子 feature slug}`
2. items.yaml 对应条目 `status: in-progress` + `feature: YYYY-MM-DD-{slug}`
3. 校验 yaml

**cs-feat design-review 阶段的职责**：在人审前只读审查 design + checklist + 相关事实，写 `{slug}-design-review.md`；不修改 design/checklist，不替用户批准。

直接起 feature（非 roadmap 来）两字段留空，不触发 roadmap 写。

**cs-feat acceptance 阶段的职责**：

1. 读 design frontmatter `roadmap` / `roadmap_item`
2. 空 → 跳过
3. 有值 → items.yaml 对应条目 `status: done`；同步主文档子 feature 清单显示状态；校验 yaml

回写是**实际写文件的动作**，验收报告要明确记录回写结果。

**最小闭环标记**：items.yaml 每份只有一条 `minimal_loop: true`，标记"做完后系统能端到端跑通最窄路径"。design 启动 `minimal_loop` 条目时优先级最高。

---

## 3. 阶段收尾推荐

**feature-acceptance** 收尾按顺序判断：

1. `cs-keep`：沉淀坑点 / 技巧 / 长期约束 / 选型
2. `cs-docs` tutorial mode：开发者 / 用户指南
3. `cs-docs` api mode：公开 API 参考
4. `cs-docs-neat`：阶段 / 里程碑收尾时同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆
5. `scoped-commit`

**issue-fix** 收尾按顺序判断：

1. `cs-keep`：沉淀坑点或暴露的长期约束
2. `cs-docs-neat`：修复暴露了文档、agent 入口或记忆不一致时做全局整理
3. `scoped-commit`

**feature-ff** 收尾按顺序判断（比标准 acceptance 短，没有 req 回写动作）：

1. `cs-keep`：动手过程暴露的坑或拍板的长期约束
2. `cs-docs-neat`：快速改动影响 README/docs 或 agent 入口时同步
3. `scoped-commit`

**epic / roadmap** 收尾按顺序判断：

1. `cs-docs-neat`：roadmap 确认落盘或整个 roadmap goal 完成后，同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆
2. 后续若要自动推进整份 roadmap，再走 `cs-epic` goal-package 阶段

**统一规则**：一律一句话提示；用户说"不用"立即跳过；不强制；上游主动提示，下游承接执行。

---

## 4. 收尾提交（scoped-commit）

acceptance / issue-fix 走完后把本次产物提交为一个 commit：

- **范围**：本次工作改到的代码 + 相关 spec 文档 + 本次实际更新过的 CONTEXT.md / ADR / req doc + 本次实际更新过的 roadmap items.yaml / 主文档
- **不该进**：和本次工作无关的顺手修改；属于"下次另起 feature / issue"的扩大范围
- **提交前确认**：用户没明确同意不要 `git commit`
- **commit message**：一句话说清"做了什么"，不贴 spec 目录路径

子技能只描述本阶段特有提交范围，通用规则看这里。

---

## 5. 归档检索规则

feature-design / issue-analyze / issue-fix 动手前到 `.codestable/compound/` 搜已有沉淀，遵守上下文幂等（首次读、已载复用）：

- **首次进入该工作项**时搜 `requirements/CONTEXT.md`、`requirements/adrs/`、`compound/`（防术语冲突、防违反已拍板决策）；若本会话/本阶段已加载过这些全局输入，则复用已读摘要，不重复 Glob+Read。`epic_child_batch: true` 时这些全局输入已由 `cs-epic` 在批量开始时统一加载，子 feature 直接复用、不重扫
- `compound/` 直接 `grep -r "关键词" .codestable/compound/`（纯 markdown，无 schema）
- 搜到的结果只作参考输入，不盲目套用——可能已过时或不适合当前上下文
- 搜到和当前方向冲突的决策类沉淀 → **必须**正面回应"为什么仍然这么做"或调整方向

---

## 6. cs-keep 守护规则

`cs-keep` 写 compound 时遵守：

1. **宁缺毋滥**——用户说不出理由的内容直接省略，不要 AI 编造
2. **不替用户写实质内容**——AI 负责起草结构和串联语言，实质结论必须来自用户或可追溯的代码证据
3. **attention.md 检查**——写完若沉淀暴露出"每次启动都该知道"的一两行硬约束，提示用户用 `cs-note` 追加到 `.codestable/attention.md`
4. **起草前先 grep 查重叠**——`grep -r "关键词" .codestable/compound/`。命中相近旧文档就问用户：更新已有 / 新写一份。默认优先更新已有，沿用原文件名，文末加"YYYY-MM-DD 更新"。
5. **识别用户意图是"改已有"还是"记新的"**——用户说"改 / 更新 / 补充 {某条}"或话题高度重合时默认走"更新已有"，不要闷头新建。分不清就问。

---

## 7. 写代码时的反射检查

`cs-feat` implementation / fastforward、`cs-issue` fix、`cs-refactor` apply / fastforward 共用。AI 默认会往"大函数 / 大文件 / god class / 处处特殊分支"漂，这一节把漂移截在发生那一刻。（这里截"往复杂漂"的结构膨胀；选型层"往省事漂"的实现降级——最小闭环 / fake / 正则凑——见 `.codestable/reference/solution-depth-conventions.md` 的方案深度 pre-pass。）

### 第一性原则 pre-pass

动手前先用一句话写清四件事：本次真正要改变的外部行为；不可破的设计 / 领域 / API 约束；最小充分改动；无法从前三项推出、必须不写的东西。后续每次想新增抽象、参数、兜底、特殊分支或顺手重构，都回到这四项核对：推不出来就删掉、记顺手发现，或回设计 / 用户重新对齐。

**不是阈值，是触发器**——硬数字会诱发为拆而拆把自然聚合的代码切碎。每条都是"遇到 X 情况就停下来问自己"。

| 触发场景 | 停下来问自己 |
|---|---|
| 要往一个已经很长的文件追加代码时 | 文件承担几件事？新加的是已有职责延伸还是第 N+1 件事？是第 N+1 就默认新建文件 |
| 要给已经很多方法的类加方法时 | 新方法是核心职责的自然扩展，还是把类推向"什么都能干"？ |
| 写的函数已超过一屏时 | 函数在做几件事？几件事就拆 |
| 要加 `if (特殊情况) { 特殊处理 }` 分支时 | 抽象维度选错了？正确做法可能是把特殊路径和通用路径分成不同函数 / 策略 / 类 |
| 要 copy-paste 一段代码时 | 能抽成共用还是只字面相似？能抽就抽 |
| 要给函数加第 4+ 个参数时 | 函数做的事是不是太多了？参数列表是 API 恶化的早期信号 |
| 要新写"万能工具类 / helper"时 | 真没归属还是只是想不起来放哪儿就先堆 util？ |

**停下来之后**：反射检查只把问题提出来，结论用户定。停下来想清楚的动作（拆 / 新建 / 重命名 / 抽共用）会让改动超出现有 steps 范围 → 跟用户对齐再决定（纳入当前推进 / 记顺手发现留后续）。

不许偷偷拆完继续写，也不许忽略信号硬冲。默认动作是停、问、再继续。

## 8. 报告语言策略

- CodeStable 所有落盘产出的正文**默认用中文**：plan / design、plan review / design-review、code review、QA、验收、issue、refactor、roadmap、goal、compound 等所有人读报告都用中文表达。
- 默认语言以 `.codestable/attention.md` 的「报告语言」节为准（onboard 模板默认中文）；只有 attention 显式改写默认语言时才以 attention 为准。
- 机器状态（YAML / JSON / `state.yaml` / frontmatter 字段）保持机读格式不翻译，不从不同语言的叙述反推状态。
- 默认只写 canonical 报告文件；只有 attention 明确要求多语言副本时，才额外写 `{name}.{lang}.md`。

## 9. 执行约定

preflight 和 runtime 恢复在 `.codestable/reference/execution-conventions.md`；Task agent 与 Goal driver 在 `agent-conventions.md`；approval 报告口径在 `approval-conventions.md`；context packet、commit planning 和 backlog 工具在 `tools-context.md`。
