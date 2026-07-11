---
doc_type: feature-review
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: passed
reviewer: subagent
reviewed: 2026-07-11
round: 17
---

# cs-feedback-evidence-pipeline 代码审查报告

## 1. Scope And Inputs

- Design/checklist：approved；6 implementation steps done，21 checks 等 acceptance。
- Gate evidence：171 targeted、341 full、65 eval；scope/evidence/runtime/diff passed；package 仅既有
  `cs-onboard/` baseline。
- Diff：baseline `30fecaae5e747dbad1f0e599d592d7c04cc7f0c4` 加完整工作区；无越界文件。
- Implementation：主报告、review-fixes continuation、当前代码与测试。

### Independent Review

- 环节 A：Paseo agent `2187c439-2b3a-4a32-bac9-c4fd0bf43d74`，Claude Fable 5 / high /
  plan，completed；独立复跑 targeted 171 passed。
- 环节 B：OCR `skipped-by-user-constraint`。
- Merge：REV-16-01 类级闭合成立；新增反例、旧实现中性化探针和隐私对照均已核验。
- Gate effect：无 blocking/important，允许进入 QA。

## 2. Diff Summary

- 新增：反馈 normalization/incident/triage/privacy/repo-context 模块、promotion 工具、测试与 fixture。
- 修改：collector/converter/reporter、skill/runtime/reference、ADR 与公开文档。
- 风险热点：公开路径脱敏的隐私/保真张力，以及 candidate/promotion 的 fail-closed 边界。

## 3. Adversarial Pass

- 假设：中文无空格粘连仍可被 continuation 吞掉，或新谓词使真实路径泄漏。
- 反例：在原三例之外攻击不同词位、单跳/多跳、纯 CJK/ASCII、`Program Files`、Unicode
  文件名，并复核 trigger cutoff、配对、triage、原子写、promotion 与 reporter 门禁。
- 结果：可判定的粘连类已闭合；只剩与真实终端文件名机械同形的不可判定保真 residual。

## 4. Findings

### blocking

none。

### important

none。

### nit

- [ ] **REV-17-01** `[paseo-fable]` CJK 直接粘 `.`+合法扩展名且位于句末时，与
  `合同.docx` 机械同形，当前落向隐私侧并可能吞掉正文；方向为过脱敏、无泄漏。
- [ ] **REV-17-02** `[paseo-fable]` 粘连谓词只覆盖 CJK 统一表意文字，假名/谚文粘连仍可能
  被 continuation 吞掉；本中文项目频率低。
- [ ] **carry** Windows 伪盘符、CJK 相对目录内部斜杠重启、transcript 死条件、未闭合引号
  远吞、converter 非原子单文件写等既有 nits 保持记录。

### suggestion

- 若后续继续优化保真，可独立评估中文虚词/动词停用表；不应在本 feature 继续扩张扫描规则。

### learning

- 隐私形状与正文形状机械同形时，应落向隐私侧并显式记录不可判定边界，而不是继续堆启发式。

### praise

- 单一共享谓词同时约束 continuation 与终端文件名，双向矩阵锁定泄漏和过吞；public eligibility、
  reporter 单源、原子写、triage 状态机与 promotion fail-closed 均无回归。

## 5. Test And QA Focus

- 用真实中文反馈语料评估句末 `没写.gitignore` 与换行折叠形状的过吞频率。
- 中文 correction → public incident → confirmed issue 的真实 provider 全链路。
- 真实 Codex/Claude 大历史 current 定位、stale mtime、多候选交互。
- Windows 伪盘符、未闭合引号与 CJK 相对路径重启的实际出现率。

## 6. Residual Risk

- CJK 粘 `.`+扩展名的句末/换行终端形状落向隐私侧，可能损失正文，但不会公开私有路径。
- 已接受的无扩展名不可判界尾部目录与混合脚本真实路径组件继续依赖人工 preview。
- ENV_NAME 过脱敏、candidate 语义真实性、CMD-004/TODO baseline 保持记录。

## 7. Verdict

- Spec 合规：`passed`；design 16 个场景与关键兼容/隐私/fail-closed 契约均有证据。
- 代码质量：`passed`；无 unresolved blocking/important。
- Next：进入 `cs-feat` QA，重点执行本报告第 5 节和 design 场景矩阵。
