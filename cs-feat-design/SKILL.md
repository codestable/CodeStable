---
name: cs-feat-design
description: feature 流程阶段 1——为新功能起草 {slug}-design.md 作为后续实现、代码审查和验收的唯一输入，拍板后抽出 checklist。触发：用户说"开始设计方案"、"写 design doc"、"准备实现 XX"，前提是已知道做什么、为谁、怎么算成功。
---

# cs-feat-design

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

这一阶段的产出是一份方案文件 `{slug}-design.md`，加上从中抽出的行动清单 `{slug}-checklist.yaml`。这两份东西后面会被三个阶段消费——implement 照着推进、review 照着审查、acceptance 照着核对，所以这里写错或写漏，下游就跟着错。

> 共享路径和命名约定看 `.codestable/reference/shared-conventions.md`。本阶段一般 feature 目录已经由 brainstorm 创建好了；没有的话在这一步建。

本阶段有三个入口：

- **正式起草**：用户已经能讲清楚需求（或已经填好 `{slug}-intent.md`），直接进"流程"一节走完整起草。
- **初始化模式**：用户说"开一个新需求 / 起个草稿 / 新建一个 feature"，但想自己先写半成品方案而不是口述。走下一节"初始化模式"，建好目录和空 `{slug}-intent.md` 就结束本轮，等用户填完再回来。
- **从 roadmap 条目起头**：用户说"开始做 roadmap 里的 {子 feature slug}"或"推进 {roadmap} 的下一条"。slug 从 roadmap items.yaml 取，不另起；动笔前要读 roadmap 主文档和 items.yaml 了解上下文和依赖状态；落盘时 frontmatter 要带 `roadmap` / `roadmap_item` 两个字段，同时回写 items.yaml 把对应条目 `status` 改为 `in-progress`、`feature` 填为 feature 目录名。详见下文"从 roadmap 条目起头"。

**设计原则**：design 不是实现前的散文说明，而是后续实现和验收的可执行契约。它必须把"做好"翻译成可观察证据，把 steps 切成独立可验证单元，把风险和依赖前置暴露，并在交给用户前做一次自我批判，修掉含糊标准、混合步骤和薄弱依赖。

**推进原则**：design 要把后续执行需要的"操作手册"写到位：当前基线怎么确认、每步完成后看什么证据、哪些命令必须重跑、哪些交付物要真实落盘、失败时回到哪个契约修。否则 implement 只能临场判断，review 没有稳定契约可审，acceptance 也只能相信实现汇报。

---

## 初始化模式：帮用户建目录和 intent 草稿

触发：用户想自己写一份半成品方案（`{slug}-intent.md`）作为后续 design 的输入，但不想手动建目录。

动作：

1. **和用户快速对齐两件事**——一句话需求概要 + 敲定 slug（小写字母、数字、连字符；`user-auth`、`export-csv` 这种）。日期取当天（frontmatter 用 `currentDate` 即可）。feature 目录命名是 `YYYY-MM-DD-{slug}`。
2. **创建 `.codestable/features/{YYYY-MM-DD}-{slug}/` 目录**。
3. **写一份空的 `{slug}-intent.md`** 作为草稿骨架，内容就是下面这段：

   ```markdown
   ---
   doc_type: feature-intent
   feature: {YYYY-MM-DD}-{slug}
   status: draft
   summary: {一句话需求，AI 按和用户对齐的结果填}
   ---

   # {slug} intent

   ## 背景 / 为什么做

   （一句话就够）

   ## 大致怎么做

   （100 字左右描述想法，含关键步骤 / 数据流）

   ## 相关数据结构 / 类型

   （贴相关 types、接口签名、或指向代码位置）

   ## 已知不做 / 待定

   （可选：明确的边界或自己也没想清楚的地方）
   ```

4. **告知用户"骨架已建好，填完后再来找我，我基于 intent 写正式 design"**，然后**本轮结束，不继续推进 design 流程**。

为什么在这里停？intent 的价值就是让用户离线思考、把脑子里的东西落到纸面。AI 继续问会把 intent 模式退化成 brainstorm，失去意义。

---

## 从 roadmap 条目起头

触发：用户说"开始做 roadmap 里的 {子 feature}"或指向 items.yaml 里某条 `planned` 条目。

1. **读 roadmap 上下文**——打开 `{roadmap-slug}-roadmap.md` 和 `{roadmap-slug}-items.yaml`：
   - 目标条目必须 `status: planned` + `depends_on` 前置全 `done`，否则停下来报告
   - **必读主文档第 3 节"模块拆分"和第 4 节"接口契约 / 共享协议"**——这是本 feature 的硬约束输入。契约不合理 / 漏了 → 停下来建议回 `cs-roadmap update` 改，**不要在 design 里偷偷绕开**
2. **slug 从 roadmap 取**，feature 目录 `YYYY-MM-DD-{roadmap 条目 slug}`，不另起
3. **走"流程"一节**，frontmatter 加 `roadmap` / `roadmap_item` 两字段
4. **落盘 `status: approved` 同时回写 items.yaml**：对应条目 `status: in-progress` + `feature: YYYY-MM-DD-{slug}`，用 `validate-yaml.py` 校验

完整衔接协议看 `.codestable/reference/shared-conventions.md` 第 2.5 节。

---

## design 写什么、不写什么

design 只管"编排-计算分离"里的编排那一侧：**这次 feature 在名词层和编排层的现状与变化**。计算层细节（具体怎么写、改哪些函数、测试怎么搭）归 implement。

写三类东西，名词层和编排层都用"**现状 → 变化**"两段式：

1. **名词层**——值对象 / 实体 / 数据结构 / 对外契约 / 类型定义
2. **编排层**——主流程 / workflow / 关键编排函数 / 控制流拓扑（线性 / 分支 / 并行 DAG / 状态机）。开头一张主流程图建 mental model
3. **流程级约束**——错误语义、幂等性、并发 / 顺序、扩展点位置、可观测点。挂载点清单也归这类

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
   - design `status=draft` 各节基本完整 → 跳到本流程"5. 整体 review"
   - design 部分节缺失 → 补缺失节，汇报"上次写到 X，补齐统一给你 review"
   - design `status=approved` → 别默认覆盖，问用户接着改还是另起 slug
2. **扫 .codestable/ 全局输入**——Glob `.codestable/` 发现可用目录和文档类型，按类取用：
   - `architecture/` → 读 ARCHITECTURE.md + 索引 + 相关子系统 doc，关注名词复用和流程级约束
   - `requirements/` → 有对应 req：frontmatter `requirement` 填 slug，读"用户故事 / 边界"两节；新能力首次出现 → 触发 `cs-req draft` 起草愿景 req，frontmatter `requirement` 填新 slug；纯重构 / 技术债留空
   - `compound/` → 用 `search-yaml.py --dir .codestable/compound` 搜相关 decision / explore / trick / learning；命中冲突 decision 必须正面回应
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

结论写进第 1 节"决策与约束"。涉及新建模块或跨模块接口时同步写进第 4 节，提示在 `ARCHITECTURE.md` 加指向。

AI 默认翻车的姿势是**不思考就往眼前最顺手的文件里加**。

### 3. 写"现状 → 变化"两段式的名词层和编排层

按 reference.md 模板写第 2 节四个子节（2.1 名词层 / 2.2 编排层 / 2.3 挂载点 / 2.4 推进策略）。重点提示：

- "现状"必须指向代码位置，不能想当然——读者要靠它判断"变化"是否合理
- 编排层开头一张 mermaid 图建 mental model
- 挂载点按"删了它 feature 是否消失"判据，3-5 条为正常区间
- 推进策略按 paradigm 维度切片（编排骨架 → 计算节点 → 持久化 → 测试），不下沉到 file:line
- **第 2.5 节"结构健康度与微重构"是固定步骤**——按 reference.md 写作要求评估**两类对象**：要改的文件（文件级）+ 要落新文件的目标目录（目录级）。**评估前先查 compound 已有 convention**（关键词围绕"目录组织 / 文件归属 / 命名约定"），命中就直接照办。结论三选一：
  1. **不做**——文件健康 / 目录不挤 / 改动量小 / 微重构收益不抵风险，写"本次不做微重构，原因：……"
  2. **做微重构（拆文件）**——文件偏胖或职责混杂但能用 provable refactor（拆函数 / 拆文件 / 移动定义，编译器全程绿灯）解决
  3. **做微重构（重组目录）**——目标目录摊平且能通过纯文件移动 + import 路径更新解决（编译器全程绿灯）

  选择 2 / 3 时给出"搬什么 → 搬到哪 → 怎么验证行为不变"的具体方案，落进 checklist 作为**第 1 步且独立验证退出**，再开始 feature 主体
- **重组目录时多问一步：是稳定模式还是一次性整理**——稳定模式（如"自定义业务组件统一放 `components/custom/`"，未来其他 feature 也该遵守）就在 2.5 末尾加"建议沉淀的 convention"段，提示用户 implement 跑通后走 `cs-decide` 归档；一次性整理（只是这个目录碰巧挤了）就只搬不归档。**design 阶段不直接归档**——方案还没真跑过，留钩子给 implement 后再决定
- **design 只做安全的微重构，边界严格守住**："只搬不改行为"——文件级靠 IDE rename / move + 编译器校验，目录级靠纯文件移动 + import 路径更新 + 编译器校验。一旦涉及改函数签名 / 改返回值结构 / 改调用关系语义 / 模块拆合，就**超出 design 范围**：写进第 2.5 节末尾的"超出范围的观察"里提示用户"建议后续走 `cs-refactor` 处理"，**不阻塞本 feature、不作为前置依赖**。是否真去做、什么时候做由用户在 feature 之外决定
- **第 2.5 节随整稿一起 review，不单独确认**——和功能方案打包给用户一次过，避免拆成两轮把节奏拖长

### 4. 补齐剩下各节，整稿一次性给 review

按 reference.md 模板补齐剩余节（第 0 / 3 / 4 节）。初稿 frontmatter `status: draft`。

整稿成型后才交给用户看，**不分批 review**——分批用户只看到局部，发现不了"第 1 节范围跟第 2 节变化对不上"这种跨节问题。

第 3 节"验收契约"提示：每条写成"输入 / 触发 → 期望可观察结果"，覆盖正常 + 边界 + 错误。不写测试代码 / framework / mock。

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

### 5. 整体 review

发一次整体 review 提示（提示词在 reference.md 第 5 节），同时附上 Top 3 风险、关键假设、以及自我批判结论（clean 或已改哪些点）。用户提意见就改，反复直到放行，把 `status` 从 `draft` 改 `approved`。

### 6. 生成 {slug}-checklist.yaml

方案确认后从 `{slug}-design.md` 抽出 `steps` + `checks` 落到 `{slug}-checklist.yaml`。完整格式、提取规则、典型节奏看 reference.md 第 3 节。

落盘后 `python .codestable/tools/validate-yaml.py --file {path} --yaml-only` 校验。

### 7. 退出

按下文退出条件核对，引导用户进入阶段 2。

---

## 退出条件

用户整体 review 通过，并且：

- [ ] frontmatter 完整（`doc_type` / `feature` / `status=approved` / `summary` / `tags`），requirement 字段已对齐
- [ ] 第 1 节含"不做什么"和复杂度档位偏离（或明确走默认）
- [ ] 第 2.1 / 2.2 用"现状 → 变化"两段式；接口有示例 + 来源位置；编排层开头有主流程图
- [ ] 第 2.3 挂载点按"删了它 feature 是否消失"判据收紧（一般 3-5 条）
- [ ] 第 2.4 推进策略按 paradigm 维度切片，每步有退出信号
- [ ] 第 2.5 结构健康度评估覆盖文件级 + 目录级；评估前已查 compound convention；结论显式写出（不做 / 拆文件 / 重组目录）；选"微重构"时 checklist 第 1 步是它且有独立退出信号；选"重组目录"且属稳定模式时含"建议沉淀的 convention"段；超出"只搬不改行为"的结构性问题列在"超出范围的观察"，仅提示不阻塞
- [ ] 第 3 节关键场景覆盖正常 + 边界 + 错误；含"明确不做"反向核对项；每条都有证据类型
- [ ] Top 3 风险 / 非显然依赖 / 关键假设已写入 design 或 review 摘要
- [ ] checklist steps 每步都能独立验证，exit_signal 是 yes/no；UI / 安全 / 迁移类 feature 已覆盖 polish / harden 或写明不适用
- [ ] 已做可证伪性 / 步骤原子性 / 最弱依赖 / 证据完整性自我批判并修正问题
- [ ] 必跑验证命令 / 基线风险 / 预检要求已写清
- [ ] 交付物清单可被 acceptance 从仓库事实核验
- [ ] 清洁度规则已写清：调试输出、临时 TODO/FIXME、注释掉代码、无用 import 的处理口径明确
- [ ] `{slug}-checklist.yaml` 已落盘并通过 `validate-yaml.py` 校验
- [ ] roadmap 起头时 items.yaml 已回写（`status: in-progress` + `feature` 填上）

---

## 容易踩的坑

- 没读相关架构 / 术语没 grep 就动笔——方案跟现有代码对不上、术语冲突后 git blame 找十倍时间
- 用散文描述接口行为，没给具体示例——读者建不起模型
- 名词层 / 编排层只写"变化"不写"现状"——读者无法判断变化是否合理
- 把挂载点清单写成改动文件清单——内部改动归 implement，挂载点只列"删了它 feature 就消失"的登记条目
- 在 design 写测试代码 / framework / mock / 函数级落点——这些归 implement 自决
- 强行画图——模块 ≤ 2 个、调用线性时画图反而模糊重点
- 只给半份文档先 review——用户看不出全局一致性
- 在需求摘要里偷偷扩范围——验收时对不上
- 验收场景写成"体验良好 / 状态完整 / 逻辑正确"——acceptance 无法判定，只能靠感觉
- checklist step 只有下一步完成后才能验证——说明切片不独立，执行中失败时无法定位
