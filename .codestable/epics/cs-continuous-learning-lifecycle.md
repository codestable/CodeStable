---
status: active
created: 2026-08-01
work: ../work/epic-cs-continuous-learning-lifecycle.md
---

# CodeStable 持续学习生命周期

## 起点与目标

四个 task skill 已会检索项目 lesson，`cs-keep` 也有证据、查重与合并门槛，但闭环停在“读过”和
“写下”：任务中不会稳定识别真正的晶化时刻，lesson 再次命中后不验证真伪，也没有项目内迁移
效果的因果证据。现有 eval 每个 cell 只有一次 agent invocation，不能证明任务 A 的经验改善了
fresh 任务 B。

本 Epic 先落地项目内三步闭环：

```text
任务内静默观察 -> 强信号候选 -> 显式授权后写 observed lesson
-> fresh 任务 read-repair -> validated / retired
-> 测试、checker、项目文档、ADR 等 canonical owner
```

最终用 paired cross-session 实验证明：A 形成的 lesson 在不传递聊天上下文、不向 B 泄题时，能
提高 fresh agent 完成 B 的正确率。跨项目、团队级与 CodeStable 全局方法论只预留边界。

## 范围与非目标

范围：

- `cs-feat`、`cs-issue`、`cs-refactor`、`cs-epic` 的静默信号识别、read-repair 与收尾 UX。
- `cs-keep` 的 lesson 创建、验证、反证、晋升、退役与清理。
- 项目内 session candidate -> lesson -> canonical owner 的迁移。
- 维护者侧 paired/sequential eval runner 与 `cs-learning-transfer-001`。
- ADR、双语公开文档、契约/eval 测试与 package 回归验证。

非目标：

- 不新增第九个 skill，不扩大 `cs` 最小决策核，不让 task skill 读取 sibling skill 文件。
- 不恢复 `cs-feedback`、production feedback importer、transcript 扫描、状态机或自动上传。
- 不创建 `.codestable/learning/`、全局 lessons、常驻索引、后台 telemetry 或集中 runtime。
- 不持久化未收敛讨论、原始问答、完整思考过程或候选分支。
- 不自动跨项目共享；脱敏反馈包、团队知识库与 shipped skill 上游更新留给后续 Epic。
- 不用更醒目的文字代替能落成测试、lint、checker、类型或 deterministic helper 的约束。

## 核心模型

| 对象 | 生命周期与 owner |
|---|---|
| Learning signal | 当前任务内的可核实事件；未过门槛即丢弃 |
| Crystallization candidate | 会话内有界候选；不是项目事实，不自动获得写入授权 |
| Lesson | 项目级 staging，一条一文件；只保留尚未被更强 owner 完整承接的经验 |
| Canonical guard | 测试、checker、lint、类型或 helper，机械阻止同类错误 |
| Canonical knowledge | 项目既有文档、glossary、ADR 或 `attention.md` 中的唯一事实 owner |
| Transfer evidence | fresh B 在有/无 lesson 的同源仓库上产生的 paired 结果 |

检索次数、模型自评置信度和“本次讨论过”不算学习证据。lesson 是可删、可纠偏的 staging，
canonical guard/knowledge 才是稳定归宿。

## 行为契约

### 开工：有效命中必须说明影响

只有 scope 符合、未退役、经当前代码/测试/canonical 文档核实，并真实改变计划或验证的条目才算
有效命中。四个 task skill 必须报告：`经验命中：{path}（{status}）；核验：{fact}；影响：
{plan_or_check}`。纯关键词碰撞不报告为有效命中，也不能把“读过”冒充“采用”。

应用前 read-repair：`retired` 不应用；`observed` / `validated` 先核实再用；只是相关但没有改变
行为时不制造复用证据；当前事实明确反证时立即停止应用并走窄退役，证据不足时不猜。

### 任务中：静默识别晶化时刻

任务内只在内存保留最多 3 条候选，按新证据替换低价值项，不暂停或询问。已有普通 work 时可
复用证据节；不得为候选新建 work、transcript 或状态文件。

强信号限于：owner 纠正实际改变方案/代码/术语/验证；可复现证据推翻根因；同一路径失败两次后
更换假设；blocking/important finding 暴露未编码不变量；新 red -> green 捕获可复发失败；lesson
真实改变本次行为或被反证；重复 workaround；方法显著降低重试、成本或风险。

候选还必须同时有可追溯证据、能写成未来动作、适用于本次精确 diff 之外、且没有现成 canonical
owner。网络波动、拼写、泛化口号、活动记录和已被机械 owner 完整覆盖的事实直接丢弃。选择时先看
失败后果，再看证据与复发可能，最后优先低成本机械化，不生成伪精确分数。

### 收尾：低打扰与机械化优先

- 普通任务只在强信号成立时展示最高价值一条，首行固定 `晶化候选：{rule}`，并给证据、范围与
  建议归宿；无强信号完全不显示模板。没有记忆写入授权时不落盘，候选随会话结束消失。
- 用户已明确说“记住 / 更新 / 退役”时同轮按 `cs-keep` 处理，不重复确认。
- Epic 子项不展示、不询问；每个子项至多把一条去重候选写入既有游标证据区，最终毕业清单一次
  处理并复用最终 owner gate。
- 当前任务范围内能直接落成 red -> green 测试/checker 的约束优先机械化，不另写重复 lesson；
  会扩大范围时只给候选，不借学习名义扩权。

## Lesson 生命周期与授权

新 lesson 最小格式：

```markdown
---
status: observed
scope: 模块 / 命令 / 场景关键词
date: YYYY-MM-DD
---
规则：未来可执行的结论。
适用 / 不适用：边界与停止应用信号。
证据：最多三个代表性路径、测试、diff 或任务指针。
候选归宿：test | checker | attention | project-doc | adr | codestable-eval
```

| status | 判据 |
|---|---|
| `observed` | 单次任务有证据，尚未在独立后续任务验证 |
| `validated` | 非创建该 lesson 的任务和 agent invocation 中有效命中，真实改善行为并验证成功 |
| `retired` | 被事实反证、范围完全失效或已被更强 owner 替代；不得应用且不再复活原结论 |

旧 lesson 缺 `status` 按 `observed` 读取，不批量迁移；只有真实状态变化或 `cs-keep` 本来就要更新
时才补字段。不得保存原始对话、逐次命中日志或无限 evidence history。

创建、改写规则/scope、晋升、删除与跨项目反馈仍须用户显式 `cs-keep` 诉求、接受普通候选，或
Epic 最终毕业 gate。为实现不中断的 read-repair，仅对已有且有效命中的 lesson 开放两种窄维护：

- `observed -> validated`：独立后续任务确实采用并验证成功，只补一次代表性证据；
- `observed|validated -> retired`：当前仓库事实直接反证，只写原因与替代/反证指针。

窄维护不新建事实、不改规则、不扩 scope、不新增 gate，随当次代码、证据和游标进入同一语义原子
milestone，最终报告文件变化；稳定 validated 命中不写文件。需要改写结论或证据不足时只给候选。
任务内发现已有 canonical owner 时先 retire，删除留给 `cs-keep`；`cs-keep` 显式晋升则先验证新 owner，
再在同一更新中直接删除重复 lesson。新结论不得通过复活 retired 条目获得 validated 身份。

`cs-keep` 继续负责查重、合并与约 50 条预算，并按以下顺序路由：机械 guard 优先；高频必读事实进
`attention.md`（≤25 条）；同时满足难回退、缺少上下文会令人意外、源于真实取舍的结构性决定进
ADR；其他方法进项目既有文档。目标不存在时请 owner 选择，不发明目录。`codestable-eval` 只标记
未来上游候选，本轮不导出、不上传、不改 skill。

## 项目内跨会话迁移实验

现有 runner 每 cell 只调用一次 agent。新场景增加 `answerType/task.kind: learning-transfer`，由独立
sequence 模块承载；fixture 明确 A/B owning skill，每次 invocation 只注入该 skill 的冻结快照。

每个 paired cell：

1. 从 seed repo 运行 A，机械验证结果并捕获最多一条候选：普通任务读最终输出的 `晶化候选`，
   Epic 子项读既有游标证据区；A 失败计入失败，不得丢弃。
2. 复制完全相同的 post-A repo 为 treatment/control。
3. 先验证候选确属 lesson 类；若应进 attention/ADR，则标 fixture invalid，不算 skill failure。
4. 仅 treatment 用 fresh `cs-keep` invocation 接收候选、证据和显式“记录”授权；除 lesson 外的
   mutation 视为失败。
5. 可选 `between_tasks` hook 必须同样作用于两份 repo；stale guard 用它制造真实版本反证。
6. treatment/control 各启动 fresh B；skill snapshot、任务文本和 prompt hash 相同，不点名 lesson，
   不继承 A、curation 或彼此上下文，唯一处理变量是 lesson。
7. 临时目录销毁前跑 hidden/deterministic checks；B diff 白名单为任务改动、必要 work 证据，以及
   matched lesson 的窄状态/证据迁移，禁止改规则/scope 或破坏 schema。checkpoint key 含 phase，
   半 pair 不算完成，treatment/control 顺序按 k 交替；只存结构化指标、必要 diff 与哈希。

Epic 正向 fixture 不豁免 owner gate：seed 提供 `active` 永久 Epic、有效批准 hash、完整执行策略和至少
两个已批准子项，A/B 只执行边界内子项。这样测试恢复与学习，不伪造 owner/reviewer 授权。

`cs-learning-transfer-001` 至少含四个正向场景（feat/issue/refactor/epic）和无关、stale 两个 guard。
正向 fixture 的 golden 必须全绿，naive 只在目标不变量上红；真实运行前冻结 fixture、hypothesis、
primary metric、预算与失败判据，禁止看到结果后删案例。

主 oracle 均为 `[measured]`：A 结果、候选唯一性、lesson schema/mutation、B treatment/control hidden
pass、paired win/loss、stale retirement、prompt equality 和回归。语义质量只作 `[soft]`；统计不足时
整体 verdict 标 `[underpowered]`。dry-run 成本必须累加 A、curation、B×2 及场景 hook 的实际 invocation，
不得沿用 one-shot 估算。校准可用 `k=2`，但不能形成接受证据。

最终运行至少两个 model family、每 fixture `k >= 5`，使每个 family 在四个正向 fixture 上至少有
20 个完成 pair；任一 primary aggregate 仍标 `[underpowered]` 时扩大 fixture/repeat 后重跑，不能接受
Epic。只有 treatment 比 control 高至少 25pp、两个 family 都为正、losses 不多于 wins、两 guard
无回退、隔离检查 100% 通过，才能完成；失败保留负结果并继续修正。

## 子项契约

- `LEARN-1`（feat）：ADR-006、晶化算法、窄维护授权、四 task skills，以及 skill/architecture
  等集与负向契约测试；无依赖；测试先红，Epic 不新增暂停，lesson 状态变更进入当次 milestone。
- `LEARN-2`（feat）：`cs-keep` schema/lifecycle/晋升与清理；依赖 LEARN-1；同时拥有 WORKFLOW、
  README、SKILL_CATALOG、why-codestable 双语同步及 documentation tests；测试先红。
- `LEARN-3`（feat）：ADR-003 paired 增量、sequence runner/scorer、fixture 校验、成本模型、eval 单测与
  `cs-learning-transfer-001` 真实跨模型实验；依赖 LEARN-1/2；runner/fixture 测试先红。

## 影响面

必须修改：

- 五个 shipped skills：`cs-feat`、`cs-issue`、`cs-refactor`、`cs-epic`、`cs-keep`。
- `docs/adr/003-cs-skill-evaluation-loop.md`；新建 `docs/adr/006-project-learning-lifecycle.md`。
- `WORKFLOW*`、`README*`、`SKILL_CATALOG*`、`docs/why-codestable*` 中英文。
- `tests/test_skill_contracts.py`、`test_v2_architecture_contract.py`、`test_v2_documentation_contract.py`。
- `.claude/skills/eval-cs-skill/SKILL.md` 与 scripts 的 `runner.py`、`fixtures.py`、`buildprompt.py`、
  `_model.py`、`config.py`、`metrics.py`、scorer registry、新 sequence/scorer 模块。
- `tests/test_cs_skill_eval.py`；新建 `experiments/cs-learning-transfer-001/`。

需要验证：`cs`、`cs-onboard`、`cs-review`、alias、AGENTS/CLAUDE 与 build-cs-skill 不变；8 skills、
README 精简结构、全部 Markdown ≤300、plugin/package/distribution tests 继续成立。发布元数据只在 owner
决定发布时处理。

仍待调查：LEARN-3 dry-run 核实两个 model family 的 adapter 与预算；不可用时按 ADR-003 报告，
不得用单模型冒充跨模型结论。

## 验收标准

- 四 task skills 对有效命中报告路径、核验与具体影响；候选静默、普通最多一条、Epic 最终处理。
- 三态可解析且按需迁移；退役不再应用，validated 稳定命中无 churn，机械化与单一 owner 优先。
- 新 lesson 与跨项目分享保持显式授权；无 transcript、feedback runtime、global lessons 或新 skill。
- paired 单测证明四类 invocation 独立、B prompt 相同、只有 lesson 差异、半 pair 不完成、成本不低估。
- 冻结实验在两个 model family 上以非 `[underpowered]` 证据满足 verdict；否则本 Epic 保持未完成。
- 中英文契约对称；相关/全量 pytest、分发测试、plugin check 与 `git diff --check` 通过。
- 最终由 fresh reviewer 按最新批准版本做 acceptance review，再由 owner 整体验收。

## 关键决策

- 持续学习靠任务证据与按需 read-repair，不靠后台采集或每任务仪式。
- 已有 lesson 的两种窄状态维护可静默进行；新知识与跨项目分享仍须显式授权。
- 项目到全局的未来路径必须经过脱敏 packet、fixture、跨模型 eval 与 regression，本轮不实现。

## 最终交付索引

待执行后以 ADR、diff、测试与 `experiments/cs-learning-transfer-001/` 指针填写，不复制完整日志。

## 整体验收

待全部子项完成后填写。

## 遗留风险

- 模型可能漏掉信号；以低打扰换取较低召回，不用 transcript 扫描补偿。
- thin harness 无 runtime 强制；契约测试与 paired eval 是主要回退防线。
- 校准小样本可能只能给 `[underpowered]` 证据；必须扩大最终运行后才能接受，不得隐藏该标签。
