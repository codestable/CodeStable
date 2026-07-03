# Feature Acceptance Protocol

代码已经写完，但流程没结束。本阶段做四件事，缺一不可：

1. **核对实现有没有偏离方案**——逐层对照 `{slug}-design.md`，发现偏差当场修，**不是在报告里"记一下"**就过去
2. **盘点领域影响**——识别本次是否引入新术语 / 结构性决策，提示用户走 `cs-domain` 写 CONTEXT.md / ADR（不在 accept 里代写）
3. **能力落档到 requirement**——draft req 对应的能力实现完成后升级为 current（保留愿景，追加变更日志）；从未写过 req 的能力 backfill
4. **完成状态回写到 roadmap**——方案 frontmatter 有 `roadmap` / `roadmap_item` 字段时**必须**改 items.yaml 对应条目为 `done` 并同步主文档

漏掉任何一件的代价：CONTEXT.md / adrs/ 没跟上下个 feature 读到错术语；req 和实际能力脱节；roadmap 规划层和实际进度脱节，下次推进会重复跑流程。

**验收原则**：acceptance 是最终审计，不是实现汇报的整理。要重新读取原始 design 和 checklist，以最终工作区为准逐项复验；实现阶段说通过只能当线索，不能当结论。发现缺口要先修代码 / 方案 / 文档并重验，再写通过。

**推进原则**：验收阶段要用仓库事实关闭任务，而不是用对话自述关闭任务。最终结论必须回答四个问题：原始契约是否满足、验证证据是否足够且在最终状态仍成立、承诺交付物是否真实落盘、这次学到的可复用知识是否进入 CodeStable 的沉淀出口。

**独立审计边界**：可按 `.codestable/reference/execution-conventions.md` 的 Task agent 选择规则启动只读 acceptance auditor，复核 design/checklist/review/QA/final diff 和状态回写候选；但 auditor 只能返回 findings，不得写 `{slug}-acceptance.md`、checklist、roadmap、requirement 或状态文件。auditor 输出被消费后按 Task agent 生命周期关闭；容量失败只在失败后清理最老已完成 agent 并重试一次。acceptance 是流程关闭动作，最终 verdict、状态推进和文件写入必须由当前主流程 owner 完成。

**没产出报告 = 工作流未完成**。后人查"上次这个功能验收时确认了哪些行为"，没报告就只能翻 git diff 重新推断。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。
>
> 本阶段默认 **L3**，遵守 Global Route Governance：不在 accept 阶段自由重写长期 requirement，capability-boundary 变化必须先有 owner-approved req delta，缺 delta 就停下写 `approval-report.md`。详见同目录 `reference.md`。

---

## 跟 design 的章节强依赖

本阶段整套对照表按 design 当前章节编号硬编码。**design 升级章节名 / 编号时本协议必须同步**，否则下面所有"第 X 节"指针都指错地方。

**标准 design 章节快照**：

- 第 0 节：术语约定
- 第 1 节：决策与约束（需求摘要 / 复杂度档位 / 关键决策 / 前置依赖）
- 第 2 节：名词与编排（2.1 名词层 / 2.2 编排层 / 2.3 挂载点 / 2.4 推进策略）
- 第 3 节：验收契约（关键场景清单 + 反向核对项）
- 第 4 节：领域影响（新术语 / 结构性决策 / 流程级约束）

**Fastforward design**：第 0 需求摘要 / 第 1 设计方案 / 第 2 验收标准 / 第 3 推进步骤

---

## 启动检查

1. **代码确实实现到位**——git status / 最近提交看到本功能改动，否则退回 implement
2. **方案 doc 完整**——frontmatter `doc_type=feature-design` / `feature` 一致 / `status=approved` / `summary` 非空 / `tags` ≥ 2；标准 design 第 0/1/2/3 节 + 第 4 节已填写
3. **`{slug}-checklist.yaml`**——存在且 `feature` 一致；`steps` 全 `done`（有 `pending` 退回 implement）；`checks` 非空全 `pending`
4. **`{slug}-review.md`**——存在且 frontmatter `doc_type=feature-review`、`status=passed`；没有 unresolved `blocking` findings。缺失 → 先跑 `cs-code-review`；有 blocking → 退回 `cs-feat` implementation 阶段 review-fix；status 不是 passed → 不进入验收
5. **Gate / DoD evidence**——goal / gate 模式下读取 `{slug}-evidence-pack.md`、`{slug}-gate-results.json`、`{slug}-dod-results.json`；缺失或 blocking DoD 无 pass evidence 时退回 implementation gate。
6. **验证证据来源**——独立 `cs-feat` QA 阶段 不是 standalone accept 的硬前置；但验收必须有同等强度的验证证据：
   - 已有 `{slug}-qa.md`：读取并复核。frontmatter 必须 `doc_type=feature-qa`、`status=passed`；failed / blocked → 退回 `cs-feat` implementation 阶段 qa-fix；status 不是 passed → 不进入验收。
   - 没有 `{slug}-qa.md`：不要强制切去跑 `cs-feat` QA 阶段。在本次 accept 里建立 `Inline Verification Matrix`，对照 design 第 3 节、checklist checks、review Test And QA Focus / residual risk 和项目测试入口，现场运行验证，并把证据写入 acceptance 第 3 节和第 10 节最终审计。这个模式等价于“accept-inline QA”，但不额外生成 QA 报告。
   - Goal 模式例外：`cs-feat` / `cs-epic` 的 goal 协议都明确要求生成 QA 报告；goal 模式缺 `{slug}-qa.md` 时按 goal protocol 停止，不走 accept-inline。
7. **核心证据复核**——不管证据来自 QA 报告还是 accept-inline，都按同一标准复核：
   - 功能性或 mixed feature：design 第 3 节、checklist checks、review QA focus 中的核心功能路径必须有运行证据。若核心路径未运行、真实用户/API/运行时路径未验证、必跑命令未执行，acceptance 必须写 `status=blocked`。下一步按原因选择：代码/测试缺口 → `cs-feat` implementation 阶段 qa-fix 后重跑 review 和 accept-inline；环境缺口 → 先补环境；用户希望独立 QA 报告 → 跑 `cs-feat` QA 阶段。
   - 非功能性 feature：不要求 e2e / browser / API，但必须写明为什么不需要端到端运行，并提供静态检查、diff 复核、文档一致性、schema/快照/类型/构建/目标测试等替代证据。缺说明或证据不足时继续补证据，不直接通过。
8. **上下文读全**——方案 doc 全文（重点：第 1 节明确不做、2.1 接口示例、2.2 流程级约束、2.3 挂载点、第 3 节场景）+ checklist + review 报告（findings / residual risk / Test And QA Focus）+ QA 报告（如有：Feature type / Core evidence gate / Verification Matrix / Command Results / Scenario Results / residual-risk）+ evidence pack / DoD results / Gate results + accept-inline 验证矩阵（如无 QA 报告）+ implement 完成汇报里的基线预检 / step 证据 / 实际交付物索引 / 知识回写候选 + 第 4 节提到的领域影响候选 + `requirements/CONTEXT.md` + 相关 ADR + 本次代码改动（git log / diff）
9. **断点恢复**——`{slug}-acceptance.md` 已存在且部分填好 → 从下一个未完成节继续，跳过 checks 中已 `passed` 的项；汇报"上次做到第 X 节，从第 Y 节继续"

**Fastforward design 验收报告映射表**：

| 验收报告节 | 标准 design 对照 | Fastforward design 对照 |
|---|---|---|
| 1 接口契约核对 | 第 2.1 接口示例 | 第 1 节改动点 |
| 2 行为与决策核对（含挂载点） | 第 1 节 + 第 2.2 + 第 2.3 | 第 0 节；挂载点现场盘点 |
| 3 验收场景核对 | 第 3 节场景清单 + 反向核对 | 第 2 节验收标准 |
| 4 术语一致性 | 第 0 节 + 第 2.1 命名 | 检查代码命名一致性 |
| 5 领域影响盘点 | 第 4 节 | 通常无；写"无领域维度变更" |

---

## 验收报告模板

逐节填写**别跳节**。报告路径在 feature 目录下（位置看 `shared-conventions.md` 第 0 节）。

```markdown
---
doc_type: feature-acceptance
feature: YYYY-MM-DD-slug
status: passed|blocked
accepted: YYYY-MM-DD
round: 1
---

# {功能名称} 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：YYYY-MM-DD
> 关联方案 doc：{方案 doc 路径}

## 1. 接口契约核对

对照方案第 2.1 节名词层逐一核查：

**接口示例逐项核对**：
- [ ] 示例 A（{文件路径 + 函数名}）：示例输入→输出 → 代码实际行为：{一致 / 偏差说明}

**名词层"现状 → 变化"逐项核对**：
- [ ] 名词 X：声称的变化 → 代码改动：{一致 / 偏差}

**流程图核对**（第 2.2 节开头 mermaid 图）：
- [ ] 图中节点 / 调用关系在代码均有实际落点（grep 确认）

发现偏差**先修代码或回填方案 doc**。报告里写"已知偏差暂不处理"是反模式——下次按方案找代码会被绊倒。

## 2. 行为与决策核对

对照方案第 1 节 + 第 2.2 节：

**需求摘要逐项验证**：
- [ ] 行为 A：{描述 + 实测结果}

**明确不做逐项核对**（用第 3 节"反向核对项"）：
- [ ] 范围外事项 X **确实没做**（grep / review 确认）

**关键决策落地**：
- [ ] 决策 D1：{决策内容} → 代码体现：{描述}

**编排层"现状 → 变化"逐项核对**：
- [ ] 变化 V1：{在哪一步插入 / 哪条分支变更} → 代码实际落点

**流程级约束核对**（错误语义 / 幂等 / 并发 / 扩展点 / 可观测点）：
- [ ] 纪律 R1：{描述} → 代码遵守方式

**挂载点反向核对（可卸载性）**——对照第 2.3 节，必做两件事：
- [ ] 挂载点 M1：清单条目 → 代码实际落点：{一致 / 偏差}
- [ ] **反向核查**（grep）：本 feature 在代码里的所有引用是否都落在清单内？清单外的引用 → 漏记，补进第 2.3 节
- [ ] **拔除沙盘推演**：按清单逆向操作后是否还有残留？残留 → 写进"遗留"或补挂载点

Fastforward 方案没有挂载点清单 → 现场 grep 盘点本次改动命中的挂入位置作为卸载依据。

## 3. 验收场景核对

对照方案第 3 节关键场景清单，逐条可观察证据验证：

- [ ] **S1**：{场景"输入 / 触发 → 期望可观察结果"}
  - 证据来源：{类型系统 / 单测 / 集成 / 手工 / 肉眼}
  - 结果：{通过 / 未通过 + 原因 + 补救}

**功能性前端改动必须浏览器肉眼验证**（typecheck 通过不代表用户用起来对；非功能性前端改动用替代证据复核）：
- [ ] UI 区域 X：浏览器验证 OK / 截图链接

**review 报告重点复核**：
- [ ] `{slug}-review.md` 第 4 节 Test And QA Focus 已逐条覆盖
- [ ] `{slug}-review.md` 第 5 节 residual risk 已逐条处理 / 明确留作用户确认遗留

**QA 报告重点复核**：
- [ ] 验证证据来源：`{slug}-qa.md` / accept-inline verification
- [ ] QA 报告或 Inline Verification Matrix 已覆盖 design 关键场景和 review QA focus
- [ ] QA 报告或 Inline Verification Matrix 中的 feature 性质与核心证据说明合理：功能性核心路径有运行证据；非功能性 feature 有替代证据理由
- [ ] failed / blocked 项为 none
- [ ] residual-risk 已逐条处理 / 明确留作用户确认遗留，且没有承载核心验收缺口
- [ ] Evidence pack、DoD Results、Gate Results 已复核；blocking DoD 均有 pass evidence

## 4. 术语一致性

对照方案第 0 节 + 第 2.1 节命名 grep 代码：

- 术语 X：代码命中 N 处全部一致 ✓
- 防冲突：禁用词 grep 无命中 ✓

发现不一致 → 改代码，别在报告里写"已知差异"。

## 5. 领域影响盘点（提示而非代写）

**目标**：识别本次 feature 是否引入了应进 CONTEXT.md / adrs/ 的内容，**提示用户走 cs-domain**——不在 accept 里替它写。

对照方案第 4 节 + 实际实现，三类信号逐项盘点：

- **新名词** → `requirements/CONTEXT.md` 候选：新增 / 改名的实体、类型、对外契约；grep CONTEXT.md 看是否已有定义，没有就提示"走 cs-domain 加术语？"
- **结构性选择**（满足 ADR 3 判据：难回退 + 不显然 + 真权衡）→ `requirements/adrs/` 候选：新增模块 / 跨模块接口模式 / 新依赖选型 / 拒绝的备选
- **流程级约束** → `requirements/adrs/` 候选：稳定的错误语义 / 幂等约束 / 扩展点规约

逐项核对：
- [ ] 候选 X（{术语 / 结构选择 / 流程约束}）：建议 {cs-domain 写 CONTEXT / 写 ADR} → 已建议用户 ✓ / 不需要（理由：{具体}）

**不在 accept 里直接改 CONTEXT.md 或写 ADR**——这是 cs-domain 的事。accept 只盘点 + 建议。本节是登记表，不是动作。

## 6. requirement delta / clarification 回写

req 是能力愿景层，但 **accept 阶段不自由重写长期 requirement**（Global Route Governance，本阶段 L3）。对照方案 frontmatter 的 `requirement`、第 1 节需求摘要、feature 目录下已有 `*-req-delta.md` 与 clarifications：

- 纯重构 / 无 requirement 影响 → 写"无 requirement 影响"，跳过。
- 新增了用户可感能力，或改了边界 / 用户故事 / pitch：**必须有 owner-approved req delta** 才机械应用（`draft`→`current` 或刷新 current，保留原始愿景 + 变更日志）；**没有 approved delta 就停下**写 `approval-report.md`，回 clarification / `cs-req` delta 流程，不在 accept 里直接落 current。
- `requirement` 指向 current 但本次未改用户视角 → 写"req-{slug} 未变"。

完整 7 分支判据与 Global Route Governance 全文见同目录 `reference.md`。这是受 delta 约束的实际写文件动作，不是把 accept 当成自由重写 requirements 的机会。

## 7. roadmap 回写

对照方案 frontmatter 的 `roadmap` / `roadmap_item`：

- [ ] 两字段都空（feature 未从 roadmap 起头）→ 跳过，写"非 roadmap 起头"
- [ ] 两字段都有值：
  - 打开 `.codestable/roadmap/{roadmap}/{roadmap}-items.yaml`
  - 找到 `slug: {roadmap_item}`，核对当前 `status: in-progress` + `feature: {目录名}`——不对停下来找原因
  - 改 `status: done`，用 `validate-yaml.py` 校验
  - 同步 `{roadmap}-roadmap.md` 主文档第 3 节子 feature 清单的对应条目状态
- [ ] 两字段不一致（只填了一个）→ 停下来补齐或澄清

衔接协议看 `shared-conventions.md` 第 2.5 节。和 req 同规则：实际写文件的动作。

## 8. attention.md 候选盘点

回看本次实现，结合 implement 完成汇报里的"知识回写候选"，盘点"每个 feature 都会撞一次"的环境 / 工具 / 工作流类信息。典型候选：编译命令、代理配置、本地起服务步骤、反复踩的环境坑、仓库内非显然的工作流约定。

**判据**：下一个 feature 的 AI 还会再踩一次的事才记。一次性踩坑、和具体业务耦合的细节归 learning / decide。

- [ ] 无候选：写"本 feature 未暴露需要补入 attention.md 的内容"
- [ ] 有候选：列出来，**不擅自写入**——本节只登记，落不落由用户在"退出后"环节定
  - 候选 1：{描述 + 建议放 attention.md}

同时分流其他知识出口：

- 稳定技术约束 / 目录归属 / 命名规约 / 可复用坑点 / 库 API 经验 / 调试路径 → 第 9 节遗留或退出后提示 `cs-keep`
- 用户操作指南或开发者指南变化 → 退出后提示 `cs-docs` tutorial 模式
- 公开 API / 组件 / 命令表面变化 → 退出后提示 `cs-docs` api 模式

## 9. 遗留

- 后续优化点（已开 issue 或加入 issue 列表）：{列表}
- 已知限制：{列表}
- 实现阶段"顺手发现"列表：{列表}
```

---

## 核对节奏

逐节做。每节完成后**逐条更新 `{slug}-checklist.yaml` 的 `checks`**：通过 → `passed`，失败 → `failed`（先修代码 / 方案再改回 `passed`）。所有 checks 全 `passed` 后报告才算完成。

第 1/2 节最容易暴露偏离，先做。第 2 节挂载点反向核对**必须实际 grep + 沙盘推演**，不能凭印象勾选。第 5/6/7 节是写文件的动作，不是自评。

## 最终审计节奏

9 节报告填完、checks 全部 `passed` 之后**还不能直接宣布完成**，再跑一轮 final audit 用最终工作区反查原始设计：重读原始契约、聚合命令复验、场景抽样复核、交付物 / 完整工作区 / diff 清洁度 / 知识沉淀复核、覆盖率诚实标记（写 `re-verified` / `trust-prior-verify` 数）。发现缺口先把对应 check 改回 `failed`、只修失败项、重跑对应节与 final audit；同一缺口三轮仍失败则停下交还用户，不写"通过"。

**完整 8 步、缺口处理与「## 10. 最终审计」报告模板见同目录 `reference.md`**。验收报告在第 9 节后追加第 10 节最终审计。

---

## 退出条件

- [ ] 验收报告 9 节都填完
- [ ] review 报告存在且 `status=passed`，无 unresolved blocking findings
- [ ] 验证证据来源已明确：QA 报告 passed，或 acceptance 第 3 / 10 节已有 accept-inline verification matrix
- [ ] 验证证据中没有 unresolved failed / blocked items
- [ ] 没有把功能性核心路径未验证、真实用户/API/运行时路径未运行、必跑命令未执行写成 residual-risk 后放行；非功能性 feature 的替代证据理由已复核
- [ ] 第 1/2 节核对全部勾选，无未处理偏差（含挂载点 grep + 拔除沙盘推演）
- [ ] 第 3 节场景核对全部勾选；功能性前端已浏览器验证，非功能性前端已有替代证据
- [ ] 第 4 节术语一致性无遗漏
- [ ] 第 5 节领域影响盘点：每条候选有明确结论（已建议 cs-domain / 不需要）
- [ ] 第 6 节 req 回写有结论：跳过 / 未变 / 已 backfill / draft→current / 已 update
- [ ] 第 7 节 roadmap 回写有结论：跳过（非 roadmap 起头）/ 已更新（items.yaml + 主文档同步，yaml 通过校验）
- [ ] checklist 所有 checks 都 `passed`
- [ ] 最终审计已完成：聚合命令重跑、完整工作区复核、交付物落盘复核、diff 清洁度复核、知识沉淀出口分流、re-verified / trust-prior-verify 已记录；无未处理缺口
- [ ] 用户终审确认

---

## 退出后

告诉用户："验收报告已就绪，领域影响候选已盘点，cs-feat 工作流走完。后续 BUG 走 issue 流程。"

按 `shared-conventions.md` 第 3 节收尾推荐顺序逐项一句话提示（用户说"不用"立刻跳过）：

1. 复用价值的坑点 / 经验 / 长期约束 / 技术选型 → "沉淀到 compound？（`cs-keep`）"
   - **特检**：design 第 2.5 节是否有"建议沉淀的 convention"段。有就把那条规则原文念给用户："design 2.5 建议沉淀这条 convention：『{规则一句话}』，跑通了，要不要现在 `cs-keep` 归档？"——这种是 design 阶段就识别出的稳定模式，比一般"问问看"更应该主动提
2. 接口变更 / 用户可见行为变更 → "需要更新指南吗？（`cs-docs` tutorial 模式）"
3. 库公开接口（组件 / 函数 / 命令）变了 → "需要更新 API 参考吗？（`cs-docs` api 模式）"
4. 第 8 节有 attention.md 候选 → 逐条问"候选 X 加到 attention.md 吗？" 用户明确同意 → 触发 `cs-note` 走分节归类 / 查重 / 软上限检查（不在 accept 里手写，避免和 cs-note 各搞一套口径）；**一次一条**
5. 阶段 / 里程碑收尾、准备交接，或本次改动影响 README/docs、`CLAUDE.md` / `AGENTS.md`、agent 记忆 → "要做一轮文档与记忆整理吗？（`cs-docs-neat`）"
6. 最后问是否代为 scoped-commit

收尾提交规则看 `shared-conventions.md` 第 4 节。提交范围：功能代码 + 方案 doc + 验收报告 + 本次实际更新的 req doc / CONTEXT.md / ADR / roadmap items.yaml + 主文档。

---

## 容易踩的坑

常见坑（测试/QA passed ≠ 验收场景满足、挂载点要 grep 不能只看清单、领域盘点是当下动作不是建议、accept 不直接改 CONTEXT.md 或写 ADR——那是 cs-domain 的事，accept 只盘点 + 建议、final audit 缺口要先修不能写"遗留"、accept 不自由重写 requirement 必须走 delta、未经用户终审 / 同意不宣告完成或 commit 等）见同目录 `reference.md`。
