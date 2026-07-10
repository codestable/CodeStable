---
doc_type: feature-review
feature: 2026-07-10-cs-router-direct-dispatch
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-10
round: 2
---

# cs-router-direct-dispatch 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-design.md`
- Checklist: `.codestable/features/2026-07-10-cs-router-direct-dispatch/cs-router-direct-dispatch-checklist.yaml`
- Evidence pack / gate / DoD results: none；本 feature 使用 checklist、实现记录和命令输出取证
- Implementation evidence: `cs-router-direct-dispatch-implementation.md`
- Diff basis: 当前 unstaged diff + 全部 untracked feature/experiment 文件；初始工作区干净，无范围外 baseline dirty 文件

### Independent Review

- Detection: Paseo Claude Fable Task agent 与 open-code-review（OCR）CLI 均可用
- 环节 A: Paseo subagent `21907498-948d-4917-9a47-569086996065`，`claude/claude-fable-5`，plan mode，round 1/2 均 completed
- 环节 B: OCR CLI v1.7.5 completed；Medium 映射为 nit/suggestion，结果经本地核验
- Merge policy: 两路结果均逐条对照 design、skill、tests、fixtures 与 scorer 事实；round 1 小修后由同一 Fable agent 复审
- Gate effect: none；所有 started lanes 已完成，无 unresolved blocking / important

## 2. Diff Summary

- 新增：feature design/checklist/design-review/implementation/review 产物；`experiments/cs-routing-001/` config 与 16 个 fixtures
- 修改：根 `cs`、brainstorm、audit、execution/system overview 模板与 runtime copy；README/WORKFLOW/catalog 中英文镜像；3 个 pytest 文件
- 删除：测试内硬编码 `route_request()` 模拟和 root 旧 route-level 表；未删除兼容 skill
- 风险热点：入口模式语义判定、onboard 串行恢复、二级出口 checkpoint、routing scorer 测量精度

## 3. Adversarial Pass

- 假设的生产问题：行动请求仍在 route brief 后终止，或咨询请求误触发写入型 workflow
- 主动攻击：四模式边界、feature-vs-goal、audit-vs-refactor、domain-vs-keep、onboard 前置/恢复、双诉求、目标不可加载、brainstorm/audit 二级出口、模板/copy 漂移、deprecated target 与组合 target 假阳性
- 结果：runtime 契约与静态护栏通过；共享 scorer 的包含匹配是假阳性风险，已登记为测量局限和后续 issue，不影响本轮 runtime 行为

## 4. Findings

### blocking

none

### important

none。round 1 的 scorer 测量局限已按约定在实现记录登记人工复核动作与后续 issue，round 2 确认关闭。

### nit

- [ ] REV-N01 `plugins/codestable/skills/cs/SKILL.md` 跨轮恢复句没有独立 pytest literal 锚点；rt-c11 间接覆盖。
- [ ] REV-N02 `plugins/codestable/skills/cs-brainstorm/SKILL.md` case 4 已有产物不新建 case 3 产物的澄清句没有独立锚点。

### suggestion

- 后续收紧 `routing_decision.py` target 匹配，并补组合 target / deprecated stage 两个 scorer 回归用例。

### learning

- 双向包含匹配与 allowed-candidate 豁免组合会削弱 `must_not_target`；禁止分支需要精确 target 语义或人工核对 observed target。

### praise

- contracts、静态 pytest、routing fixtures 三层互补；移除测试自写路由模拟后，退化检测更贴近真实 prompt 契约。

## 5. Test And QA Focus

- 复核 Execute route brief 后是否在当前 run 真正加载目标，而不是输出即止。
- 复核无参数 / 字面 `$ARGUMENTS` 进入 Explain；Advise 在未 onboard 仓库不写骨架。
- 复核 onboard checkpoint 后原始诉求/原目标恢复，以及 brainstorm case 2、audit selected finding 的上下文传递。
- 人工检查 16 个 fixtures 的完整 expected/observed target；不能只依赖 scorer 总分。
- 本轮未运行付费多模型 routing eval，真实模型的 IntakeMode 准确率留给后续量化实验。

## 6. Residual Risk

- Execute / Advise 是语义判定，fixtures 只能抽样，目标 skill checkpoint 继续兜底。
- onboard 跨轮恢复依赖会话上下文；文本已定义缺失时询问，但无真实多轮自动化证据。
- `README.en.md` 363 行为 pre-existing 超限，本 diff 未增行，留待独立 docs refactor。
- routing scorer 可能接受组合/deprecated target；QA/acceptance 必须人工核对 target 全串。

## 7. Verdict

- Status: passed
- Next: 进入 `cs-feat` QA 阶段
