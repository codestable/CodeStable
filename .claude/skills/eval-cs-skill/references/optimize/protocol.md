# optimize stage 协议（autoresearch OCA 循环）

把「评测」升级成 `hypothesis → 变体 → 评测 → keep/kill → 收敛`。**分工**：变体的创意生成是你（agent）的活；`scripts/optimize.py` 是确定性的测量+记账+收敛引擎。**不要** Task-launch BAIME `iteration-executor`——它调不到本地 runner；OCA 由 optimize.py + 本协议驱动，方法论判据借自 BAIME（内联如下）。

## 前置：预注册并冻结

1. 写/更新 `experiments/{skill}-{NNN}/hypotheses.md`（`H-<id>: metric ≥ threshold`）。
2. **先 `git add` + `git commit` 再跑任何 LLM**——provenance 由
   `.claude/skills/eval-cs-skill/tests/test_cs_skill_convergence.py` 与 optimize 的
   `pre_registration` 分量机械校验。未提交=未冻结=不给分。

## 循环

每轮 n：

1. **Observe**：读 `iteration-{n-1}.md` 的 V 与「V_meta 分量 fail 项」，定位差距（instance 差距=召回/质量不够；meta 差距=功效/校准/混杂/预注册没达标）。
2. **Codify（提变体）**：把被测 skill 的 `SKILL.md` 拷一份改进版写到 `experiments/{skill}-{NNN}/variants/iter-{n}.md`。改进方向（按差距选）：
   - 召回差 → 在 skill 指令里强化 adversarial pass、显式列常见缺陷族、要求逐条 `[file:line]`。
   - 质量差 → 收敛输出契约、要求证据/影响/修复范围。
   - 稳健差（跨模型方差大）→ 去除依赖单一模型习惯的措辞，改 model/harness 无关表达。
   - 保持渐进披露与 ≤300 行；只改措辞与结构，不偷改评测口径。
3. **Automate（测量记账）**：
   ```bash
   python3 {skill_dir}/scripts/optimize.py --experiment experiments/{skill}-{NNN} --max-iterations {N}
   ```
   它评当前 `variants/iter-{n}.md`（缺则复用 baseline 并标注），算 V_instance/V_meta，判 keep/kill，写 `iteration-{n}.md`。
4. 读结果决定下一轮或停。

## 双层价值函数（借 BAIME）

- **V_instance**：任务质量，加权 measured 分数（默认 recall；可在 config `v_instance_weights` 配）。目标 ≥ 0.80。
- **V_meta_experiment**：方法质量，四机械分量各 0/1 → 分/4，全 [measured]：
  1. `pre_registration`：hypotheses.md 已提交且早于首个 run。
  2. `statistical_power`：k ≥ 5 且每类 n ≥ 8。
  3. `oracle_calibration`：`calibration.md` 存在。
  4. `confound_control`：用 judge 时 judge_model 非空且不在被测 model_list。

## 收敛判据（三模式，借 BAIME convergence-criteria）

- **standard**：V_instance ≥ 0.80 **且** V_meta ≥ 0.80 → 收敛。
- **meta-focused**（方法本身是目标，如自指优化 eval-cs-skill）：V_meta ≥ 0.80 且 V_instance ≥ 0.55。
- **practical**：预算耗尽或连续 2 轮无严格改进 → 停并如实记「未达标即停」，不得谎报收敛。

不要 force convergence；baseline V_meta 常在 0.15–0.30，正常。

## 认知诚实（硬约束）

- 一切数值带 `[measured]/[soft]/[underpowered]`；禁止裸 `V_instance = 0.XX`。
- k<5 或 n<8 → 结论标 `[underpowered]`，仅作方向性。
- 不得为凑收敛调 fixtures 或放宽 oracle；要改口径先改 hypotheses 并重新冻结。

## 退出条件

- [ ] hypotheses.md 已冻结并 git commit。
- [ ] 至少 iter-0 baseline 已评并写 `iteration-0.md`。
- [ ] 每轮 `iteration-{n}.md` 含 V_instance/V_meta（带 tag）、分量、keep/kill、收敛判定。
- [ ] 收敛或如实记录「practical 停止」；`results.md` 收敛模式已更新。
