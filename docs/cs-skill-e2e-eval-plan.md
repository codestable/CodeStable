# cs skills 端到端效果评测方案（e2e outcome eval）

状态：方案（未实施）。作者：eval-cs-skill 闭环 campaign（2026-07-07）收口时整理。
前置阅读：`experiments/cs-issue-routing-001/results.md`（routing 层 verdict 与方法学）、
`.claude/skills/build-cs-skill/references/cs-skill-quality-gates.md`（Measured Rules）。

## 动机

已完成的 routing eval 证明的是**代理指标**：模型能读懂 skill 文档、在给定仓库状态下走对下一步
（七 skill 均值 original 0.807 → 重构后 0.965，[measured]）。它**不能证明**"最终干出来的活更好"。
软件研发 skill（cs-issue / cs-feat / cs-epic）有个天然优势：产出可以用测试机械判定——
这是把评测升级到 outcome 层的抓手（对标 SWE-bench 思路）。

## 总体设计

```text
场景包 = 种子仓库（真实小项目：有代码、有测试、有提交历史、已 onboard .codestable/）
       + 一个任务（bug 报告 / feature 需求 / 大需求，用户口吻）
       + 隐藏验收测试（hidden tests：模型不可见，跑完后取出判分）
```

### 种子仓库：自建，不 fork 开源项目（已决策，2026-07-07）

- **数据污染**是 outcome eval 的头号效度杀手：知名 repo 在模型训练语料里，测出来的是记忆
  不是能力（SWE-bench 的已知问题）。自建新代码零污染。
- cs skills 的设计环境是 onboarded `.codestable/` 仓库——自建才能原生满足（效度教训：
  bare-input 0.31 vs 带环境 0.92）。
- 成本可控：seed 须千行级、测试秒级、零第三方依赖；真实项目的体量/依赖树在沙箱里失控。
- 自建的两个风险及化解：①太干净不像真的 → **演进式构建 + 刻意做旧**（多阶段提交历史、
  风格漂移、TODO/废弃模块、测试覆盖不均）；②作者偏差（建 repo/种 bug/出题同一人）→
  bug 取自真实模式库 + hidden test 先写后种 + **L2 对照对两组同等作用，相对差仍有效**。
- 入库形态：**构建脚本 + 阶段快照**（`experiments/seeds/<name>/build-seed.py` 逐 commit
  构建到 tmp，固定日期确定性输出）——避免嵌套 git repo，可 diff review。
- 种 bug 铁律：**注入点必须落在 seed 自带测试的暗角**（注入后自带回归仍绿）——否则
  agent 一跑测试就看到失败点，难度骤降且不真实；做旧的"覆盖不均"正是为此准备。
- fork 的唯一合理变体：用 owner 自己的**私有**真实项目快照（模型没见过、可真 onboard），
  作为后期补充轨道。

执行：真 agent harness（`claude-headless` / `codex-cli`，eval-cs-skill 已有适配器）在沙箱
worktree 里按 skill 完整跑流程——不是单次问答。

打分（全机械 [measured]）：

| 指标 | 判法 |
|---|---|
| 活干成没有（主指标） | 隐藏验收测试 红→绿 通过率 |
| 有没有干坏别的 | 种子仓库既有测试套件仍全绿（回归） |
| 过程守没守规矩 | 产物契约（fix-note / design / checklist 存在且合规，复用 dod_gate scorer）；该停的 checkpoint 停了没（从产物状态判） |
| 成本 | tokens / turns / wall time（metrics.py 现成） |

## 三个 skill 的场景设计

### cs-issue（P0，最先做）

- 种真 bug 三档：单行逻辑错（易）/ 跨函数状态错（中）/ 需读多文件推理根因（难）。
- 验收：hidden test 红→绿 + 回归绿 + `fix-note.md` 根因正确（关键词/judge 双轨）。
- **陷阱场景**：bug 报告实为新需求 → 正确动作是转 `cs-feat` 而非硬修（防"无脑往前冲"）。
- **未来 diagnosis-only 场景（未实施）**：用户只授权排查真实 bug，不授权修复。机械判分“零产品
  写入”（不修改产品代码、测试或配置，不创建 commit）、结论证据等级，以及临时 harness / 埋点清理；
  该场景仍是待实现的评测设计，不代表已完成效果评测。

### cs-feat（P1）

- 需求含显式验收标准 + **隐含边界**（如"导出 CSV"隐含空数据/逗号转义）；hidden tests
  覆盖隐含项——design 阶段认真挖需求才会过。
- 测 checkpoint 遵守：design-review passed 后是否停等确认（headless 下判产物状态：
  design 保持 draft + 输出含等待确认，而非自批准进实现）。

### cs-epic（P2/P3）

- P2 便宜版：只评**拆解质量**——items.yaml 与专家拆解对比（覆盖度/依赖顺序）+
  各 child design 验收标准质量。
- P3 全程版：3-4 child 小 epic 跑到底，集成测试判定 + 过程合规（批量 design、
  统一确认、不逐个停）。做前单独确认预算。

## 对照组（决定"证明了什么"）

| 对照 | 回答的问题 |
|---|---|
| L1：重构前 vs 重构后 skill 文档 | 本轮 prompt-as-code 重构在 outcome 层是否仍有增益 |
| **L2：有 skill vs 裸 agent 同任务** | **skill 本身值不值得存在**（最有说服力，此前从未测过） |
| L3：便宜模型+skill vs 贵模型裸奔 | 性价比：skill 能否让便宜模型达到贵模型水平 |

## 效度铁律（承接 routing campaign 的教训）

1. **hidden tests 模型不可见**——可见即应试。
2. **种子仓库要像真的**：提交历史 + 既有测试 + `.codestable/`。已验证教训：把 skill
   拉出设计环境测，测出的全是假象（bare-input 0.31 vs 补上下文 0.92）。
3. **出题先自证可解**：每个场景先用参考实现跑通 hidden tests（oracle 校准的事前版）。
4. **必须含"该停/该拒绝"场景**：全是"往前冲得分"的题会把 skill 优化成莽夫。
5. **分诊纪律**：分数异常先看 transcript / 产物，分类 oracle 问题 vs fixture 缺陷 vs
   skill 真缺陷 vs 模型行为差异；live 优化两轮为限；受影响变体重跑统一口径。
6. **feature 场景：显式/隐含要用不同的出题与自证标准**（2026-07-08 两次实证后修订）：
   - **explicit hidden**：接口细节（子命令/参数形式/输出格式/列名）必须以用法示例写进
     需求文本（否则合理实现被误判：sonnet `--output` vs hidden 锁位置参数 → exit 2）；
     自证 = 第三方视角只读需求文本实现，explicit 应全绿。
   - **implicit hidden**：隐含边界**绝不写进需求文本**——写进去它就不再隐含（第一版修复
     把 f02/f03 的隐含全集显式化，直接摧毁了"design 挖隐含需求"的测量对象 H3）。
     其自证标准不是"只读需求满分"（逻辑上不可能），而是"**资深工程师标准**的参考实现
     应全绿"——断言只许覆盖专业共识边界（合理工程师即使需求没写也会处理的），且
     implicit 断言不得依赖任何接口自由度（只测行为语义，经由 explicit 已锁定的接口触达）。
   - 两条自证矛盾的仲裁：某断言既过不了"资深标准自证"又不能写进需求 → 删掉该断言。
   - **观测通道规则**（第三轮实证后补）：隐含行为必须经某个通道观测，通道无契约 = 接口
     锁定换形态回归（f03 断言 `untagged` 字面桶名 → 四变体全挂 0/24）。implicit 断言只测
     **状态/数据行为**（查库、或解析 explicit 已锁定接口输出中的数据，数值比较不比字符串）；
     呈现细节（桶名/报错文案/exit code）要么补进接口契约、要么宽容匹配。判别力校验：
     f01 的 RFC4180 断言四格全过 = `csv.writer` 免费获得，判别力≈0——低判别断言留作下界
     锚点可以，但不能是 implicit 组的主体。
7. **skill 的环境依赖要么提供要么豁免**（同日实证）：cs-feat 的实现阶段设计为经可见
   Task agent goal driver 派发——headless 无 driver 时 agent 守规矩 handoff 退出（design
   完打印 /goal），实现零落地。inject_context 豁免块须显式覆盖"driver 不可用：本会话
   内直接完成"，否则测出的是环境缺失不是 skill 能力。
8. **生成型/拆解型 eval 必须校验 output 未撞 `max_tokens` 上限**（2026-07-08 cs-epic 实证）：
   36/36 撞 2048 时覆盖率测成"上限内塞得下多少文本"，冗长格式（roadmap 含阶段/依赖/验收）
   被砍更狠，差点误导出 H4 NULL。修 `adapter_api.py`（默认 8192 + `CS_EVAL_MAX_TOKENS` 覆盖）
   后 edge 优势才现。**撞上限的批次数据作废，须重跑**。
9. **拆解/生成型覆盖度只能用语义 judge，token recall 不可作 measured 下界**（同日）：
   planted_defect（token）对自然语言拆解系统性低估 32pp（0.49 vs opus judge 0.81）；决定性
   案例同一 roadmap planted=0.43（漏 4 项含 obvious）vs judge=1.0（7 项全覆盖）。措辞自由度高
   token 匹配必漏。diff-based 缺陷召回仍可用 token（缺陷文本相对固定），自然语言拆解不行。
10. 认知诚实标注不变：[measured]/[soft]/[underpowered]；hypotheses 先于运行注册。

## 框架衔接（复用现有 eval-cs-skill）

- 已有可复用：harness 注册表（claude-headless/codex-cli/api）、dod_gate scorer、
  checkpoint/resume + 分段、per-cell 容错 + 重试、`--dry-run` 成本护栏、认知诚实 tag。
- 需新建：
  - `fixtures/e2e/`：每场景一个目录（seed-repo/ + hidden-tests/ + scenario.json）；
    新 answerType `e2e-outcome`。
  - runner 的 e2e 模式：workdir=解压 seed → agent harness 跑 skill → 执行 hidden tests
    与回归套件 → 收集产物/transcript。
  - `e2e_outcome` scorer：测试通过率 + 回归 + 产物契约合成。
- 沙箱隔离：每 cell 独立 tmp workdir（既有约定），不触宿主仓库。

## 成本与分期

| 期 | 内容 | 估算 | 前置 |
|---|---|---|---|
| P0 | cs-issue ×8 场景、单模型、k=3 | ~$10-20 | 无 |
| P1 | cs-feat ×6 + 裸 agent 对照（L2） | ~$30-50 | P0 管线 |
| P2 | cs-epic 拆解质量版 | ~$10 | P0 |
| P3 | cs-epic 全程版 | $50+ | 单独确认预算 |

单次 cs-feat 全流程 50-200k tokens，比 routing 选择题贵 50-100 倍——P0 先跑通管线，
后续只是换场景。统计功效：每 skill ≥6 场景 × k≥3；hidden tests 为二元判定，方差低于
LLM judge，所需样本量小于 soft 指标。

## 风险与开放项

- headless harness 的 checkpoint 交互：等确认类场景需注入"用户确认"脚本或以
  "停在正确状态"为判分点——实施时定。
- 种子仓库维护成本：每场景一个可跑项目，优先共享 1-2 个 seed（同仓库种不同 bug/需求）。
- cs-epic 全程版的长时执行受环境 kill 影响——依赖既有 resume 机制，必要时分 child 分段。
