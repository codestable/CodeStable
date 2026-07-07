# Results — routing 三方 eval（六 skill 汇总）

主实验文档；cs-feat/cs-epic/cs-docs/cs-refactor/cs-docs-neat 的 routing-001 实验共享本 verdict。
评分：routing_ok [measured]（机械比对），oracle 经两轮校准（见 hypotheses.md 校准记录），全段离线统一重打分。
n=每变体 72~90（fixtures × 3 模型 × k3）。

## Verdict

| skill | original（重构前） | hardened（表格+Spec 并列） | baseline（Spec 唯一真相） | Δ(base−orig) |
|---|---|---|---|---|
| cs-issue | 0.989 | 1.000 | 0.989 | ±0.000 |
| cs-feat | 0.861 | — | 0.958 | +0.097 |
| cs-epic | 0.867 | **0.833** | **1.000** | +0.133 |
| cs-docs | 0.528 | 0.944 | **0.958** | **+0.430** |
| cs-refactor | 0.750 | — | **0.972** | +0.222 |
| cs-docs-neat | 0.889 | —（直接替代式，无中间态） | **1.000** | +0.111 |
| cs-goal | 0.765 | — | **0.951** | +0.186 |
| **均值** | **0.807** | — | **0.975** | **+0.168** |

cs-goal 补注（2026-07-07，两轮）：第一轮加「迭代内 review 经附近**可见 Task agent** 独立执行、不在 goal driver 主线程自审」（rt-g04 判别"由谁执行"：baseline 0.89 vs original 0.33）+ `AcceptanceAgentUnavailable` 枚举 + CheckpointReason「grill 前不适用」限定，0.765→0.877。第二轮（结构性，owner 授权）按 build-cs-skill full-protocol 清单复审发现 **Spec 生命周期不完整**：`selectNextAttempt` 缺 grill 入口分支与重建条件对偶分支、含不可达死分支——补全后 0.877→**0.951**（sonnet/gpt 满分）。**关键数据点**：rt-g02 在两轮措辞限定下 0.33→0.33 纹丝不动，补 grill guard 后一轮 0.33→0.89——措辞优化无效时该查结构缺失（已回写 Measured Rules 6）。剩余：rt-g03 baseline 0.67（haiku 对"有证据仍可重建"保守答 NeedsHuman，接受为模型行为差异）。

## 结论（对预注册 H1/H2 的裁决）

1. **H2a 部分成立，H1 部分成立——按 skill 复杂度分层**：
   - 规则简单清晰的 skill（cs-issue）：三方无差（H1），表达形式不影响路由。
   - 其余 4 个 skill：`baseline`（Spec 唯一真相）一致最优（0.958~0.989），增益与 original 规则含混度成正比（docs +0.43 > refactor +0.22 > epic +0.12 > feat +0.10）。
2. **并列冗余接近装饰、甚至有害**：cs-epic 上 `hardened`(0.833) **低于 original**(0.867)——表格与 Spec 两份"真相"并列会干扰路由。用户对加固式（并列形态）"感觉是装饰"的直觉被数据证实；但"替代"形态有真实行为增益。
3. **增益集中在非顶级模型与复杂分支**：gpt-5.5 在 feat/issue 上两版全对；差距主要来自 haiku/sonnet 在嵌套分支（epic 批量、ff 资格、docs 状态恢复）上的表现。
4. **优化闭环两例**（eval→定位→改 live→复评）：
   - cs-feat rt-f04（ff 优先级歧义）：0.67 → **1.00 跨三模型**（两轮措辞，详见 hypotheses.md）。
   - cs-docs Spec 内部矛盾（AmbiguousReader 在 CheckpointReason 但 guard 走 NeedsHuman）：rt-d02 暴露，已修。

## 方法学记录（认知诚实）

- oracle 两轮校准：初跑后按预注册 caveat 2 修 10 个 fixture 的宽匹配（original 无 Spec 类型名词汇、语义正确措辞不同），修复对 original **有利**（0.222→0.528 in docs），差距是挤掉 oracle 偏差后的净值。
- rt-r02 fixture 设计缺陷（utterance 无目标触发歧义分支）：修 state 后真重跑替换，旧数据作废。
- rt-f04 已进优化循环、非 held-out；verdict 表用优化前原段口径（0.67），优化后复评 1.00 单独标注。
- rt-p09 复核：baseline 唯一 miss 是 haiku 答 `GoalHandoff/execute-goal`（reason 正确、target 措辞不在词表）——oracle 去掉多余 target 约束（GoalHandoff 类型已完全表达决策，同 rt-p05 判例）后 cs-epic baseline = 1.000 三模型满分。**cs-epic live 无任何路由瑕疵，未改 SKILL.md**。
- 剩余 baseline 小尾巴（0.67~0.89）：rt-d03、rt-i01、rt-r01（含 JSON 输出纪律 PARSE-ERR）——单点非系统性，未追加优化（两轮为限防过拟合）。
- evidence_pointer：`artifacts/runs/rt-*.json`（各实验目录）+ 重打分脚本逻辑见 hypotheses.md。
