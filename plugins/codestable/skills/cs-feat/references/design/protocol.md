# Feature Design Protocol

这一阶段的产出是一份方案文件 `{slug}-design.md`，加上从中抽出的行动清单 `{slug}-checklist.yaml`，以及人审前的 `{slug}-design-review.md`。这些东西后面会被 implement / code review / QA / acceptance 消费，所以这里写错或写漏，下游就跟着错。

> 共享路径和命名约定看 `.codestable/reference/shared-conventions.md`。本阶段一般 feature 目录已经由 brainstorm 创建好了；没有的话在这一步建。
> 报告语言：design / plan 正文必须按 `.codestable/attention.md` 用**中文**；若草稿用了英文，落盘前先改写为中文。frontmatter / yaml 字段不翻译。

本阶段有三个入口：

- **正式起草**：用户已经能讲清楚需求（或已经填好 `{slug}-intent.md`），直接进"流程"一节走完整起草。
- **初始化模式**：用户说"开一个新需求 / 起个草稿 / 新建一个 feature"，但想自己先写半成品方案而不是口述。走下一节"初始化模式"，建好目录和空 `{slug}-intent.md` 就结束本轮，等用户填完再回来。
- **从 roadmap 条目起头**：用户说"开始做 roadmap 里的 {子 feature slug}"或"推进 {roadmap} 的下一条"。规则见下文"从 roadmap 条目起头"一节。

当 `cs-epic` 批量推进子 feature design 时，会带内部上下文 `epic_child_batch: true`。
该上下文下，本阶段只负责产出 draft design、checklist、design-review 和 items.yaml 回写；
不执行单 feature 用户整体 review，不把 design 改成 `approved`。所有子 feature 由
`cs-epic` 统一交给用户确认。

**设计原则**：design 不是实现前的散文说明，而是后续实现和验收的可执行契约。它必须把"做好"翻译成可观察证据，把 steps 切成独立可验证单元，把风险和依赖前置暴露，并在交给用户前做一次自我批判，修掉含糊标准、混合步骤和薄弱依赖。

**推进原则**：design 要把后续执行需要的"操作手册"写到位：当前基线怎么确认、每步完成后看什么证据、哪些命令必须重跑、哪些交付物要真实落盘、失败时回到哪个契约修。否则 implement 只能临场判断，review 没有稳定契约可审，QA 不知道该跑什么证据，acceptance 也只能相信实现汇报。

---

## 初始化模式：帮用户建目录和 intent 草稿

适用：用户想自己写一份半成品方案（`{slug}-intent.md`）作为后续 design 的输入，但不想手动建目录。

动作：

1. **和用户快速对齐两件事**——一句话需求概要 + 敲定 slug（小写字母、数字、连字符；`user-auth`、`export-csv` 这种）。日期取当天（frontmatter 用 `currentDate` 即可）。feature 目录命名是 `YYYY-MM-DD-{slug}`。
2. **创建 `.codestable/features/{YYYY-MM-DD}-{slug}/` 目录**。
3. **写一份空的 `{slug}-intent.md`** 作为草稿骨架，模板见 `support/intent-template.md`
   的“feature intent 草稿模板”。

4. **告知用户"骨架已建好，填完后再来找我，我基于 intent 写正式 design"**，然后**本轮结束，不继续推进 design 流程**。

为什么在这里停？intent 的价值就是让用户离线思考、把脑子里的东西落到纸面。AI 继续问会把 intent 模式退化成 brainstorm，失去意义。

---

## 从 roadmap 条目起头

适用：用户说"开始做 roadmap 里的 {子 feature}"或指向 items.yaml 里某条 `planned` 条目。

1. **读 roadmap 上下文**——打开 `{roadmap-slug}-roadmap.md` 和 `{roadmap-slug}-items.yaml`：
   - 目标条目必须 `status: planned` + `depends_on` 前置全 `done`，否则停下来报告
   - **必读主文档第 3 节"模块拆分"和第 4 节"接口契约 / 共享协议"**——这是本 feature 的硬约束输入。契约不合理 / 漏了 → 停下来建议回 `cs-epic` planning/update 改，**不要在 design 里偷偷绕开**
2. **slug 从 roadmap 取**，feature 目录 `YYYY-MM-DD-{roadmap 条目 slug}`，不另起
3. **走"流程"一节**，frontmatter 加 `roadmap` / `roadmap_item` 两字段
4. **候选落盘时回写 items.yaml**：对应条目 `status: in-progress` + `feature: YYYY-MM-DD-{slug}`，用 `validate-yaml.py` 校验；design 先保持 `status: draft`，普通单 feature 通过 `cs-feat` design-review 阶段且用户确认后才改 `approved`；`epic_child_batch: true` 时交回 `cs-epic` 批量确认

完整衔接协议看 `.codestable/reference/shared-conventions.md` 第 2.5 节。

---

## design 写什么、不写什么

design 只管"编排-计算分离"里的编排那一侧：**这次 feature 在名词层和编排层的现状与变化**。计算层细节（具体怎么写、改哪些函数、测试怎么搭）归 implement。

写三类东西，名词层和编排层都用"**现状 → 变化**"两段式：

1. **名词层**——值对象 / 实体 / 数据结构 / 对外契约 / 类型定义
2. **编排层**——主流程 / workflow / 关键编排函数 / 控制流拓扑（线性 / 分支 / 并行 DAG / 状态机）。开头一张主流程图建 mental model
3. **流程级约束**——错误语义、幂等性、并发 / 顺序、扩展点位置、可观测点。挂载点清单也归这类

当本 feature 引入或改变 module interface、seam、adapter、跨依赖测试策略时，按 `support/codebase-design.md` 做内嵌 deep-module 检查；这不是切换到独立 `codebase-design` skill。

外加一个**固定结构健康度环节**（第 2.5 节）：评估即将被改动的文件是否偏胖 / 职责混杂、以及新文件要落进的目录是否摊平，决定是否在实现前先做"只搬不改行为"的微重构（拆文件 / 重组目录）。即使结论是"不做"也要在 design 里显式写出来——否则 AI 默认会持续往胖文件里塞代码、往拥挤目录里加文件。这一节随整稿一起进整体 review，不单独走确认。

**判据**：换一种写法名词层或编排层会变得不同 → design 的事；换一种写法只是"代码不那么好看 / 函数拆法不同 / 测试用了别的 framework" → implement 的事。

不写改动文件清单、函数级落点、测试代码、库选型细节——design 阶段还没读完相关代码，预测多半会回头改。implement 拿到 design 后才扫现状决定。

---

## 方案文件是给人概览的，不是给人仔细阅读的

读者打开 `{slug}-design.md` 是想 5 分钟内抓到要点，不是逐字精读。具体做法：

1. **每节超过 1 屏就砍或拆**——一屏装不下读者会失去定位
2. **术语先锁死**——动笔前 grep 代码 / 架构 / 历史 feature 防冲突，事后理顺成本远高于预防
3. **示例优先于定义**——接口行为先给"输入→输出"示例，复杂时再补正式类型
4. **同一条信息只在最自然的位置出现一次**——重复表述比缺一条还烦
5. **新逻辑默认放新文件**（写在改动计划里）——文件越大越难分清职责

---

## 起草时的三条纪律

### 1. 别替用户做决定

碰到"用户没说清的角落"默认停下来问，不自己挑一个填上去。具体：

- **声明假设**：非用户原话的判断写成"假设：……"，让用户能精确反驳
- **给选项不自选**：2-3 种合理做法都摆出来再讲倾向
- **看不懂就停**：硬猜着写下去到了 acceptance 阶段对不上验收点

### 2. 目标和约束都写成可验证的

- 不写"让它能跑"、"用户体验顺畅"这种弱标准——改写成"输入 A 时返回 B"
- "明确不做"具体到能被 grep 或测试反向核对，不写"不过度设计"这种空话

### 3. 每个 feature 都要能被卸载

回答："如果想把它拔掉，要拔哪些地方？" 答不出说明边界没想清楚，feature 一上线就变成拆不动的既成事实。

落到挂载点清单（第 2.3 节）。**判据**：删掉这一项，feature 在用户/系统视角是不是就消失了？是→列，否→不列。详细 ✅/❌ 例子和写法看 reference.md。这清单顺带帮你发现自己有没有不小心往太多地方插桩——真挂入点越多代表耦合越散，是个信号。

---

## 流程：什么时候做什么

### 1. 启动检查

**前置 gate**：需求输入至少含 用户目标 / 核心行为 / 成功标准 / 明确不做 四项（来源 intent / brainstorm / 对话）。缺了补；用户自己说不清就回退到 brainstorm。

**必做 4 条**：

1. **续作检查**——Glob `{slug}-design.md` / `{slug}-intent.md` / `{slug}-brainstorm.md`：
   - intent / brainstorm：当作输入读入，不重复问已讲清的部分
   - design `status=draft` 各节基本完整 → 若 checklist 存在则跳到本流程"5. 独立 design review gate"，否则先生成 checklist
   - design 部分节缺失 → 补缺失节，汇报"上次写到 X，补齐统一给你 review"
   - design `status=approved` → 别默认覆盖，问用户接着改还是另起 slug
2. **扫 .codestable/ 全局输入**——Glob `.codestable/` 发现可用目录和文档类型，按类取用：
   - `requirements/CONTEXT.md` → 读领域术语表，用项目术语命名，不自己造名
   - `requirements/adrs/` → 跨模块或流程级约束相关的 ADR 必读；命中和方案冲突的 ADR **必须**正面回应"为什么仍然这么做"或调整方案
   - `requirements/{slug}.md` → 有对应 req：frontmatter `requirement` 填 slug，读"用户故事 / 边界"两节；新能力首次出现 → 触发 `cs-req draft` 起草愿景 req，frontmatter `requirement` 填新 slug；纯重构 / 技术债留空
   - `compound/` → `grep -r "关键词" .codestable/compound/` 搜历史沉淀；命中相关坑点 / 写法约束就融进方案
   - `features/` → 搜历史 design 有无同类 feature 可参考
   - 其余目录按内容类型自行判断
3. **读需求相关的现有代码**——读哪些文件由需求线索决定
4. **识别验证基线**——从 attention / README / package scripts / CI / 历史 acceptance 里找本 feature 应用的 build / typecheck / lint / test / e2e / 浏览器验证入口；如果命令当前可能已红，写入第 1 节"基线风险"，implement 开始前要先做轻量预检，避免把既有红灯误算成本 feature 失败

**按信号触发 3 条**（没信号跳过）：

- **术语 grep 防冲突**——新概念名没在代码 / 架构 / 历史 feature 里见过时，grep 一遍；冲突就换名或在第 0 节明确区分
- **复杂度档位对齐**——需求里出现"对外 SDK / 高并发 / 一次性工具"等偏离信号时，打开 `.codestable/reference/code-dimensions.md` 列偏离点；无信号写"走默认档位"
- **grep 找"叫法不同的类似模块"**——直觉"可能已有人做过但命名不同"时，grep 同义词

详细规则看 `.codestable/reference/shared-conventions.md` 第 5 节。

### 2. 想清楚这功能该放在哪儿

动笔写名词层 / 编排层前，先回答：**这次要加的东西在项目整体结构里属于哪儿？**

- 现有模块本该承担？→ 在那个模块里扩展，别另起
- 横跨多个模块？→ 抽公共层 vs 让某一方主导、其他方依赖
- 跟现有任何模块都不像？→ 新建独立模块/子系统，对外暴露什么、跟别人怎么交互提前想清楚
- 可能已有模块在做类似的事但叫法不同？→ grep 几个同义词

代价：放错了模块就变"什么都装的筐"；新建平行实现就有几个版本同存。

结论写进第 1 节"决策与约束"。涉及新建模块或跨模块接口时，提示用户走 `cs-domain` 起一条 ADR 记下这个结构性决策。

AI 默认翻车的姿势是**不思考就往眼前最顺手的文件里加**。

### 3. 写"现状 → 变化"两段式的名词层和编排层

按 reference.md 模板写第 2 节四个子节（2.1 名词层 / 2.2 编排层 / 2.3 挂载点 / 2.4 推进策略）。重点提示：

- "现状"必须指向代码位置，不能想当然——读者要靠它判断"变化"是否合理
- 触碰 module interface / seam / adapter 时，补 `support/codebase-design.md` 里的 Interface 设计检查
- 编排层开头一张 mermaid 图建 mental model
- 挂载点按"删了它 feature 是否消失"判据，3-5 条为正常区间
- 推进策略按 paradigm 维度切片（编排骨架 → 计算节点 → 持久化 → 测试），不下沉到 file:line
- **第 2.5 节"结构健康度与微重构"是固定步骤**——评估两类对象：要改的文件（文件级）+ 新文件要落进的目录（目录级）；评估前先查 compound 已有 convention，命中直接照办。结论三选一（不做 / 微重构拆文件 / 微重构重组目录）且必须显式写出；选微重构时给"搬什么 → 搬到哪 → 怎么验证行为不变"，落进 checklist 作为**第 1 步且独立验证退出**，再开始 feature 主体
- **只做"只搬不改行为"的微重构**（编译器全程绿灯）——涉及改函数签名 / 返回值结构 / 调用关系语义 / 模块拆合就超出 design 范围：写进"超出范围的观察"提示后续走 `cs-refactor`，不阻塞本 feature。重组目录若属稳定模式（未来其他 feature 也该遵守），在 2.5 末尾加"建议沉淀的 convention"段；design 阶段不直接归档，钩子留给 implement 跑通后。评估维度、结论模板和判据细则看 reference.md §2.5
- **第 2.5 节随整稿一起 review，不单独确认**——和功能方案打包给用户一次过

### 4. 补齐剩下各节，生成 review candidate

按 reference.md 模板补齐剩余节（第 0 / 3 / 4 节）。初稿 frontmatter `status: draft`。

整稿成型后先确认正文语言符合 `.codestable/attention.md`（默认中文；英文草稿先改写），再落盘 draft design，并从 `{slug}-design.md` 抽出 candidate `{slug}-checklist.yaml`。checklist 的 steps/checks 初始都保持 `pending`，用 `validate-yaml.py` 校验。不要等用户确认后才生成 checklist，因为人审前的 `cs-feat` design-review 阶段 需要同时审 design 和 checklist 是否对齐。

第 3 节"验收契约"提示：每条写成"输入 / 触发 → 期望可观察结果"，覆盖正常 + 边界 + 错误，并补 `Acceptance Coverage Matrix` 和 `DoD Contract`；完整模板看 reference.md。

**补一段执行风险与证据计划**（写进第 1 节或第 2.4 节，按文档自然位置放）：

- **Top 3 风险**：最可能实现偏、最难回滚、最容易验收遗漏的三点；每点写对应缓解（某个 step、某条验收场景、某个先验命令）
- **非显然依赖**：外部服务、数据迁移、现有模块顺序、用户拍板项；说明阻塞哪个 step
- **证据类型**：每个验收场景最终靠什么证明（类型 / 单测 / 集成 / 手工 / 浏览器截图 / API 响应 / diff review）
- **关键假设**：不是用户原话但方案依赖它成立的判断，review 时让用户能改
- **必跑验证命令**：本 feature 完成前必须运行哪些命令；命令可能基线已红时写清"预检先跑，红灯要分清既有问题 / 本次引入"
- **交付物清单**：最终应该新增 / 修改 / 删除的用户可见或系统可见产物类别（代码入口、配置 key、schema、路由、文档归并、roadmap 状态），acceptance 要按仓库事实反查
- **清洁度规则**：本 feature 不允许新增的调试输出、临时 TODO/FIXME、注释掉代码、无用 import；如某类 debug 输出是功能本身，必须在 design 里显式说明例外和范围

**steps 写法原则**：

- 步数由工作自然切片决定，不为了凑 4-8 合并不相干内容；如果确实超过 8，先检查是不是应该退回 roadmap 拆子 feature
- 每步交付一件 coherent thing，能独立验证；名字里出现"和 / 以及 / 同时"时复查是否该拆
- 每步 `exit_signal` 必须是 yes/no，可由命令、测试、截图、接口响应、页面观察、类型检查或 diff review 证明
- 每步要标出建议验证动作（命令 / 手工 / 浏览器 / diff review）和主要交付物类型，方便 implement 做 step 证据块
- UI feature 最后必须覆盖可见状态与 polish：空态、加载、错误、禁用 / 未授权、长文本 / 小屏、focus / keyboard / contrast；如果不适用写明原因
- 涉及安全 / 权限 / 输入处理 / 数据迁移时，最后一个功能 step 或单独 step 必须覆盖 harden：校验、越权、回滚、兼容、回归面

**交给用户前做一次自我批判**，并先在文档里修掉问题：

1. **可证伪性**：第 3 节和 checklist 的每条是不是 yes/no？有没有"正常 / 完善 / 友好 / 稳定"这种无法核对的词？
2. **步骤原子性**：有没有一个 step 塞了两件可以独立验收的事？有没有 step 只有下一步完成后才有意义？
3. **最弱依赖**：哪个 step 出错会污染后续最多内容？是否需要提前验证、拆成独立 step、或补验收场景？
4. **证据完整性**：每条关键场景是否都有证据类型？前端是否需要浏览器截图 / 肉眼验证？
5. **基线可执行性**：必跑命令是否明确？如果命令当前可能已红，是否有预检和归因说明？
6. **交付物可核验性**：acceptance 是否能从 git diff / 文件系统 / 配置 / 文档状态看到每个承诺产物？
7. **清洁度覆盖**：是否明确禁止临时调试输出、TODO、死 import、注释掉代码，并说明必要例外？
8. **接口深度**：新增 / 改动的 interface 是否给 caller 足够 leverage？seam 和 adapter 是否真实需要？

### 5. 独立 design review gate

运行 `cs-feat` design-review 阶段：

- `passed`：普通单 feature 才能把 design + checklist + design-review 报告交给用户整体 review；`epic_child_batch: true` 时不要停用户，返回 `cs-epic` 继续下一个子 feature。
- `changes-requested`：按 finding 修 design/checklist，重新校验 yaml 并重跑 `cs-feat` design-review 阶段。
- `blocked`：补齐输入、等待独立 Task agent reviewer，或让用户明确降级 local-only 后重跑。

### 6. 用户整体 review

发一次整体 review 提示（提示词在 reference.md 第 5 节），同时附上 Top 3 风险、关键假设、自我批判结论和 `{slug}-design-review.md` 摘要。用户提意见就改；如果修改影响名词层、编排层、验收契约、steps/checks、roadmap 契约或风险策略，必须同步更新 checklist 并回到 Phase 5 重跑 design review。用户明确放行后，把 `status` 从 `draft` 改 `approved`。

`epic_child_batch: true` 时跳过本节；保持 `status: draft`，由 `cs-epic` 在所有子 feature design-review passed 后统一执行用户确认和 `approved` 标记。

### 7. 确认 checklist

确认 `{slug}-checklist.yaml` 已与最终 approved design 同步。完整格式、提取规则、典型节奏看 reference.md 第 3 节。

落盘后 `python .codestable/tools/validate-yaml.py --file {path} --yaml-only` 校验。

### 8. 退出

按下文退出条件核对，引导用户进入阶段 2。

---

## 退出条件

普通单 feature：用户整体 review 通过，并且：

`epic_child_batch: true`：design-review 已 passed、design 仍为 draft、items.yaml 已回写，返回 `cs-epic` 继续批量流程；不要单独停等用户。

- [ ] frontmatter 完整（`doc_type` / `feature` / `summary` / `tags`），requirement 字段已对齐；普通单 feature 为 `status=approved`，`epic_child_batch: true` 为 `status=draft`
- [ ] design 正文已按 `.codestable/attention.md` 的报告语言落盘（默认中文；frontmatter / yaml 字段保持机读格式）
- [ ] 第 1 节含"不做什么"和复杂度档位偏离（或明确走默认）
- [ ] 第 2.1 / 2.2 用"现状 → 变化"两段式；接口有示例 + 来源位置；编排层开头有主流程图
- [ ] 触碰 module interface / seam / adapter 时，已记录 depth / locality / seam / dependency strategy 检查结论
- [ ] 第 2.3 挂载点按"删了它 feature 是否消失"判据收紧（一般 3-5 条）
- [ ] 第 2.4 推进策略按 paradigm 维度切片，每步有退出信号
- [ ] 第 2.5 结构健康度评估覆盖文件级 + 目录级；评估前已查 compound convention；结论显式写出（不做 / 拆文件 / 重组目录）；选"微重构"时 checklist 第 1 步是它且有独立退出信号；选"重组目录"且属稳定模式时含"建议沉淀的 convention"段；超出"只搬不改行为"的结构性问题列在"超出范围的观察"，仅提示不阻塞
- [ ] 第 3 节关键场景覆盖正常 + 边界 + 错误；含"明确不做"反向核对项；每条都有证据类型、Acceptance Coverage Matrix 和 DoD Contract
- [ ] Top 3 风险 / 非显然依赖 / 关键假设已写入 design 或 review 摘要
- [ ] checklist steps 每步都能独立验证，exit_signal 是 yes/no；UI / 安全 / 迁移类 feature 已覆盖 polish / harden 或写明不适用
- [ ] 已做可证伪性 / 步骤原子性 / 最弱依赖 / 证据完整性自我批判并修正问题
- [ ] 必跑验证命令 / 基线风险 / 预检要求已写清
- [ ] 交付物清单可被 acceptance 从仓库事实核验
- [ ] 清洁度规则已写清：调试输出、临时 TODO/FIXME、注释掉代码、无用 import 的处理口径明确
- [ ] `{slug}-design-review.md` 已通过 `cs-feat` design-review 阶段，没有 unresolved blocking finding
- [ ] `{slug}-checklist.yaml` 已落盘并通过 `validate-yaml.py` 校验
- [ ] roadmap 起头时 items.yaml 已回写（`status: in-progress` + `feature` 填上）

---

## 容易踩的坑

- 没读相关架构 / 术语没 grep 就动笔——方案跟现有代码对不上、术语冲突后 git blame 找十倍时间
- 接口只写签名不写 invariant / ordering / error mode / seam rationale——implement 和测试会各自补语义
- 强行画图——模块 ≤ 2 个、调用线性时画图反而模糊重点
- 只给半份文档先 review——用户看不出全局一致性
- 在需求摘要里偷偷扩范围——验收时对不上
- 跳过 `cs-feat` design-review 阶段 直接让用户拍板——用户看不到 checklist、契约、验收策略的独立审查结论
- 其余红线是退出条件的反面：现状缺失、接口无示例、挂载点混入内部改动、design 写实现细节、"体验良好"式弱验收词、step 不可独立验证——交稿前逐条对照退出条件自查
