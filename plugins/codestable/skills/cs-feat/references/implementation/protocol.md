# Feature Implementation Protocol

到这一步用户已经在方案上签过字了，你的活是把方案变成代码。容易出问题的不是写代码本身，而是**实现路上发现方案没覆盖到的情况时怎么办**——硬冲下去就把方案当摆设了。下面整套规则就是为了让"停下来"成为默认动作。

**执行原则**：实现不是"一口气改完再说"，而是按已批准 checklist 做可验证增量。每一步要先明确退出信号，做完立刻拿证据验证；失败先诊断和重试，仍失败再写窄范围修复说明；连续失败才交还用户。不要让未验证的中间状态滚进下一步。

**推进原则**：实现阶段要让任务随时可恢复、可归因、可审计。开始前先确认基线；每步完成就更新 checklist 和证据；失败只修当前失败标准；每步都检查清洁度；遇到用户中断就在 step 边界停；学到会影响后续 feature 的知识先记录为候选，交给 acceptance 收尾沉淀。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。

---

## 执行 gate（worktree + commit）

进入实现前运行 start gate，路径用项目运行时 `.codestable/tools/...`：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-{slug}
```

gate 不通过就不要开始改代码；用户批准 override 时先在 unit 目录写 `worktree-override.md`（reason / scope / approval）。

dogfood / 临时隔离仓库例外：只有当用户任务明确要求在一次性隔离 repo 里真实执行 workflow，且该 repo 不是交付目标主仓库时，允许不创建 linked worktree；仍必须在 unit 目录写 `worktree-override.md`，记录 `reason=dogfood-ephemeral-repo`、用户授权原文、影响范围和后续清理策略。不能把这个例外用于普通 feature 实现。

实现完成、输出汇报前运行 commit gate：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-{slug}
```

gate 不通过就先处理 findings，不把"测试已过"当成完成。gate 工具的安装与 branch-guard hook 说明见 `.codestable/reference/branch-guard-hooks.md`。

---

## 写代码时的三条姿态

先做 `.codestable/reference/shared-conventions.md` 第 7 节的**第一性原则 pre-pass**：明确外部行为、不可破约束、最小充分改动和必须不写的东西。具体规则是这三条姿态的落点，理解姿态比记规则重要。

### 1. 默认写最少的代码

只写当前步骤明确要的东西。不顺手加"以后可能要"的可配置项、抽象层、参数开关、防御性兜底。判据：写完一段觉得"是不是还得加点 X"，先问 X 是不是当前用户能感知到的——不是就别加。整体写完一看 200 行其实 50 行能讲清楚 → 重写。多出来的代码不是中性的，是后人维护的负担。

### 2. 只动该动的，不顺手"改善"邻居

改某个函数时只改那个函数。同文件里别的函数风格丑、命名怪——除非和本次改动直接冲突，否则别碰。新代码风格匹配当前文件已有写法。混进的"顺手改"会把功能 PR 稀释成"一坨综合改动"，review 成本翻几倍。值得改的按下文"顺手发现"格式记成后续 issue。

孤儿处理：你这次改动让某个 import / 函数变成死代码 → 删掉。**不是**你改动造成的死代码 → 留着记成顺手发现。

### 3. design 没说的事别自己拍板

写到一半发现 design 没覆盖的角落（边界条件、错误路径、方案外文件）——默认停下来回 design 谈。下面"补丁分支"和"术语守护"是这条姿态的两个典型落点；**任何"design 没明说我替它选了一个"的瞬间都触发**。

---

## 启动检查

### 1. 方案文件够不够撑实现

frontmatter：`doc_type=feature-design` / `feature` 一致 / `status=approved` / `summary` 非空 / `tags` ≥ 2。

**标准 design**（节 0/1/2/3/4）：
- 第 0 节有内容；第 1 节含"明确不做"和复杂度档位
- 第 2.1 名词层用"现状 → 变化"两段式，每个新增/变更接口至少一个示例 + 来源位置
- 第 2.2 编排层开头有主流程图，"现状 → 变化"齐全，流程级约束已记
- 第 2.3 挂载点按"删了它 feature 是否消失"判据，没把内部代码改动误列进来
- 第 3 节有关键场景清单 + 反向核对项（不含测试代码 / framework 选型）

**Fastforward design**（节 0/1/2/3）：
- 第 0 含"明确不做"；第 1 有改动点（文件 + 函数/类型名）
- 第 2 验收标准每条可验证；第 3 推进步骤有退出信号

任一项不达标 → 退回 `cs-feat` design 阶段 补齐。原因：方案漏的项实现时一定要现场补，等于绕过 checkpoint。

**注意**：标准 design 第 3 节"验收契约"只说"做完后什么应该成立"，不说"具体怎么做"。改动文件清单 / 函数级落点 / 测试代码归 implement 自决，不要因为 design 里没写就退回去要求补。

### 2. {slug}-checklist.yaml 在不在

- 文件存在，`feature` 字段一致
- `steps` 非空（design 已产出，paradigm 维度切片，4-8 步）；`checks` 非空
- 不存在 → 退回 `cs-feat` design 阶段 生成

### 3. 把上下文读全

- 方案 doc 全文（标准 design 重点：第 1 节、2.1/2.2/2.3/2.4、3）
- `{slug}-checklist.yaml`、需求来源（用户描述 + brainstorm note）、`.codestable/attention.md`
- 第 2.1 节接口示例的来源位置 / fastforward 第 1 节改动点提到的代码文件——读相关函数即可
- 如果是 review-fix：读取 `{slug}-review.md`，只把 unresolved `blocking` findings 作为本轮目标
- 如果是 qa-fix：读取 `{slug}-qa.md`，只把 failed / blocked QA items 作为本轮目标

### 4. 跟用户确认从哪一步开始

通常第 1 步；接续上次中断从已 `done` 的下一步继续。

design 给的 `steps` 是 paradigm 维度切片（编排骨架 → 计算节点 → 持久化 → 测试），**具体每步改哪个文件由你执行时决定**。如果某一步实际是 3 个独立子动作、或发现微重构是它的前置（参考反射检查），跟用户对齐后追加 / 拆分 steps，**不偷偷做**。

### 5. 基线预检

动第一行代码前，读取 design 里的"必跑验证命令 / 基线风险"。对本 feature 最相关、成本可接受的命令先跑一遍（至少 typecheck / targeted tests；前端可先确认 dev server / 页面入口可打开）。

- 全绿：在工作记录里记"基线预检通过：{命令列表}"
- 有红灯：先判断是既有问题还是本 feature 必须先修的前置
  - 既有红灯且不影响当前 feature：记录为基线风险，后续验证只要求"不新增失败 / targeted checks 通过"，最终汇报必须写清
  - 既有红灯但会影响当前 feature：停下来和用户确认，是先补 safety net / 修基线，还是调整 design
  - 无法归因：不要继续大改，先缩小命令或读错误定位

这一步的目的不是把全仓库修绿，而是避免把"启动前已经坏"误判为本 step 失败，也避免在坏基线上继续堆代码。

**design 第 2.5 节微重构的衔接**：

- 如果 2.5 结论是"做微重构（拆文件）"或"做微重构（重组目录）"，checklist 第 1 步就是它——**独立跑完**，按 2.5 节"行为不变怎么验证"那条核对：
  - 拆文件：编译绿灯 + 现有测试通过 + 对外接口签名零 diff
  - 重组目录：编译绿灯 + 现有测试通过 + diff 仅限文件移动 + import 路径更新（**没有任何函数体改动**）

  **不要合并到下一步**——一旦混在一起，行为变更和结构变更就分不开，出问题回滚不到干净中间态
- 如果 2.5 结论是"不做"但写到中途反射检查触发了拆分信号 → 走下面"反射检查"那条路径（停下来 → 和用户对齐 → 能 provable 解决就追加独立 step），**不要绕过用户确认偷偷追加**
- 如果 2.5 末尾有"建议沉淀的 convention"段：implement 阶段**不主动归档**——只在重组目录跑通且行为零改动确认后，在汇报里带一句"design 2.5 建议沉淀的 convention 已就绪，等 acceptance 阶段确认是否走 cs-keep"，把决定权交给 acceptance / 用户

---

## 实现期间的几条核心约束

### 严格按 steps 顺序走

按 `steps` 列表顺序执行，不合并、不跳。每一步开始前先重读该 step 的 `action` / `exit_signal`，确认它是本轮唯一目标；每完成一步立即验证退出信号，并把 status `pending` → `done`。

最常见违规是"顺手把下一步也做了"——每步都对应独立可验证的退出信号，两步合做意味着出问题时不知道是哪一步引入的、回滚也回不到干净中间态。

每步完成后立刻把 `{slug}-checklist.yaml` 对应 step 状态落盘。不要等所有步骤完成再统一改；状态文件就是断点恢复锚点。中断恢复时先读它，而不是靠记忆。

### 每步都要有证据块

完成每个 step 后，在工作记录 / 汇报素材里留下最小证据：

- 退出信号：原文摘出
- 验证动作：跑了什么命令 / 看了什么页面 / 检查了什么 diff / 调了什么接口
- 结果：通过 / 未通过；失败写真实错误摘要
- 影响面：本步新增 / 修改的主要函数、类型、路由、配置或文档
- 清洁度：本步新增代码里是否有调试输出、临时 TODO/FIXME、注释掉代码、无用 import、方案外文件

证据不要求每步都发给用户，但最终完成汇报必须能按 step 追溯。UI step 的证据不能只写 typecheck，必须有浏览器 / 截图 / 肉眼验证；后端接口 step 优先用测试或真实请求证明；纯类型约束可以用 typecheck 证明。

### Step 清洁度检查

每步验证时额外看本步 diff：

- 新增调试输出：`console.log` / `console.error` / `print` / `fmt.Println` / 临时 logger
- 新增临时 TODO / FIXME / XXX
- 注释掉的旧代码或大段死代码
- 新增 import 但未使用
- 非本 step 需要的文件改动

命中就按失败处理：能当场删掉就删并重跑验证；确实是功能的一部分（例如新增日志能力）必须在 design / 汇报里说明原因和范围。清洁度不是审美问题，它是防止临时施工痕迹进入后续阶段。

### 不做方案外的改动

发现值得重构的点（参考 `.codestable/reference/shared-conventions.md` 第 7 节"写代码时的反射检查"），只要**不在本次功能影响面内**就记成后续 issue：

```markdown
> 顺手发现：{文件:行号} {问题简述}。不在本次范围，记录待后续 issue。
```

顺手改的代码不在方案里，验收对不上；后人 git blame 也分不清是为本次功能还是顺手。

### 术语守护

**标准 design**：新写的类型 / 函数 / 变量名都要去方案 doc 第 0 节对照，不允许出现 doc 里没有的新概念。要引入新概念 → 先停下来改第 0 节、grep 防冲突、用户确认。

**Fastforward design**：没有正式术语表，但要新起概念名时也要 grep 一下当前代码防冲突。

代价：术语冲突意味着同概念两个名字 / 同名字两个概念——后者会让搜索完全失效。

### 出现"补丁分支"的冲动时停下来

写代码时冒出 `if (特殊情况) { 特殊处理 }` 这种结构，**停**。这种分支基本只有一个原因：方案没覆盖到这种情况。继续写得到的是"为了让代码能跑而加的特殊逻辑"——下次别人改这块时不知道这个分支为什么存在。回方案谈：补进 design / 砍掉 / 明确为遗留问题。

### Step 失败恢复：诊断 → 窄修复 → 交还

某个 step 的退出信号或相关测试失败时，不直接推进下一步，也不把失败掩进最终汇报。按三段处理：

1. **第一次失败：失败诊断**
   写清失败项、实际错误、刚改过的范围、根因假设；只围绕当前 step 做一次重试。重试前不要扩大 scope。
2. **第二次失败：窄范围修复说明**
   如果重试仍失败，在 feature 目录写一份临时 `{slug}-step-N-fix.md`（或在完成汇报中等价记录）：
   - 失败的 exit_signal / checks
   - 根因判断
   - 只允许改哪些文件 / 行为
   - 修复后必须重跑哪些验证
   执行这份窄修复，成功后回到原 step 的验证，不直接标 done。
3. **第三次失败：交还用户**
   仍失败就停下来，报告三次尝试、证据、当前风险和建议下一步。不要为了"完成流程"继续改大范围代码。

这个机制只处理当前 step 的失败，不是绕过 design 的许可证。发现设计缺口仍然回 `cs-feat` design 阶段，不是用窄范围修复说明现场拍板。

### 用户中断与续跑

如果用户在实现中途发来新消息：

- 当前 step 未到安全点：先把正在做的最小变更验证 / 回滚到可解释状态，再回应
- 当前 step 已验证：更新 checklist 状态和证据后停在下一步开始前
- 用户要求改方向：不要继续执行旧 checklist；先判断是改 design、拆 step、还是取消当前 feature

恢复时固定顺序：读 design → 读 checklist 当前状态 → 读最近实现汇报 / 临时 step fix 文档 → 从第一条 `pending` step 继续。

### 代码质量反射检查

除上面流程约束外，还有一组针对代码质量的反射检查——看 `.codestable/reference/shared-conventions.md` 第 7 节。

核心：**不是"超过 N 行必须拆"，而是"遇到 X 情况就停下来问自己"**。每条对应 AI 默认会走进去的坑（往大文件继续追加、往大类加方法、补丁分支、复制粘贴、第 4+ 个参数、往万能 util 堆东西）。

反射检查结论是"要拆 / 新建文件 / 重命名 / 抽共用层"且超出现有 steps 范围 → 跟用户商量决定，不偷偷拆完继续写。判据按和 design 2.5 一致的边界分两路（避免 impl 自己造一套口径）：

- **能用"只搬不改行为"解决**（拆函数 / 拆文件 / 移动定义，编译器全程绿灯，对外签名零 diff）→ 和用户对齐后**追加为独立 step**插在当前 step 之前，跑完独立验证退出再继续
- **超出"只搬不改行为"边界**（要改函数签名 / 改返回值结构 / 改调用关系语义 / 模块拆合）→ **本 feature 不做**，记成"顺手发现"格式提示用户后续走 `cs-refactor`，当前 step 用最少的改动绕过去；不要因为"反正都看到了"就在 feature 里顺手做掉——这会把功能 PR 稀释成综合改动，也违反 design 2.5 早就划好的边界

### 最后一轮本地审计

所有 steps 标 `done` 后，完成汇报前做一轮小型 final audit：

1. 重读 `{slug}-design.md` 第 1 / 2 / 3 节和 `{slug}-checklist.yaml`
2. 逐条确认 steps 全 done、checks 还未验收但已有实现证据
3. 重新跑本 feature 所需的 build / typecheck / lint / test 或项目等价命令；有前端改动则跑浏览器验证
4. 过一遍 `git diff`，检查本次新增的 debug 输出、临时 TODO/FIXME、注释掉的代码、无用 import、方案外文件
5. 用第 3 节关键场景倒查：有没有某条没有证据；没有就补测或回实现
6. 列出实际交付物：新增 / 修改 / 删除的代码入口、配置、schema、路由、文档、roadmap 状态，为 acceptance 的交付物复核做索引
7. 列出知识候选：项目命令、环境坑、稳定 convention、库 API 坑、用户确认的偏好；不直接写入 knowledge，只交给 acceptance 第 8 节处理

audit 发现问题就回到对应 step 处理，不把问题留给 acceptance 首次发现。

### review-fix 模式

当 `cs-code-review` 产出 `status: changes-requested` 且有 unresolved `blocking` findings 时，进入 review-fix 模式：

1. 只读取并修复 review 报告里的 blocking findings；不要借机实现新需求、重构邻居或处理非阻塞建议。
2. 每个 REV 编号都要留下修复证据：改动文件、验证命令、为什么阻塞已解除。
3. 如果修 blocking 需要改变 design 契约、扩大 feature 范围或触碰 roadmap item 边界，停下来回 `cs-feat` design 阶段 / 用户确认。
4. 修完后跑相关验证和清洁度检查，输出 review-fix 汇报。
5. 下一步必须重跑 `cs-code-review`；不能直接进入 `cs-feat` acceptance 阶段。

review-fix 不要求 checklist 新增普通 step，除非用户明确要求把修复动作纳入 checklist 追踪。默认把 REV 编号和证据写在汇报里，保留 review 报告作审查输入。

### qa-fix 模式

当 `cs-feat` QA 阶段 产出 `status: failed` 或 `status: blocked` 且失败项归因于本 feature 时，进入 qa-fix 模式：

1. 只读取并修复 QA 报告里的 failed / blocked items；不要借机处理新需求、非阻塞建议或 review 已接受的 residual risk。
2. 每个 QA 编号都要留下修复证据：改动文件、验证命令、为什么失败已解除。
3. 如果修 QA 失败项需要改变 design 契约、扩大 feature 范围或触碰 roadmap item 边界，停下来回 `cs-feat` design 阶段 / 用户确认。
4. 修完后跑相关验证和清洁度检查，输出 qa-fix 汇报。
5. qa-fix 改变了代码 diff，下一步必须重跑 `cs-code-review`；review passed 后再重跑 `cs-feat` QA 阶段。不能直接进入 `cs-feat` acceptance 阶段。

qa-fix 不要求 checklist 新增普通 step，除非用户明确要求把修复动作纳入 checklist 追踪。默认把 QA 编号和证据写在汇报里，保留 QA 报告作复测输入。

---

## 写完后输出统一汇报

所有步骤完成后，按 `support/reference.md` 的"实现完成汇报"模板输出并停等用户 review。模板必须列出真实 `git status`、按步骤归类的改动、方案外触碰、新概念、step 证据、清洁度、交付物、知识候选、最后一轮本地审计和验收场景自检。

Goal 模式例外（本轮按 feature / roadmap 目录下 `goal-protocol.md` 长程执行）：汇报照常落盘留档，但不停等用户 review，直接按 goal 协议进入 before_review gates 和 `cs-code-review`；只有命中 goal handoff 条件才停下交还用户。

---

## 测试用例怎么落

标准 design 第 3 节"关键场景清单"每条 = 一个可验证行为约束。把每条变成可观察证据：单测 / 集成 / 手工操作 / 类型编译期保证。coding step 适合自动化测试时，可在 step 内采用 TDD vertical slice；这是 `cs-feat` implementation 阶段的内嵌实现策略，不是切换到独立 `tdd` skill。具体测试策略看 `support/reference.md` 和 `support/tdd.md`。

---

## 退出条件

完整 checklist 见 `support/reference.md`。主文件保留硬门摘要：

- [ ] 所有 steps 的 status 都 `done`，且每步有退出信号证据。
- [ ] 完成汇报已输出，用户 review 通过（或 review-fix / qa-fix 汇报已输出，等待重跑对应 gate；goal 模式为汇报落盘留档后按 goal 协议继续）。
- [ ] 没有未处理的"需要叫停"信号、方案外改动或清洁度缺口。
- [ ] 开始前做过基线预检；完成前做过最后一轮本地审计。
- [ ] 第 3 节关键场景每条都有证据 / 测试覆盖（fastforward 对照第 2 节）。

---

## 退出后

告诉用户下一步：普通实现完成后触发 `cs-code-review`；review-fix 后重跑 `cs-code-review`；qa-fix 后重跑 `cs-code-review` 和 `cs-feat` QA 阶段。不要顺手进入验收报告；完整话术见 `support/reference.md`。

---

## 容易踩的坑

完整列表见 `support/reference.md`。最常见红线：半成品汇报、方案外顺手改、新概念不回填、补丁分支硬冲、跳过 review/QA gate、关键场景没有证据。
