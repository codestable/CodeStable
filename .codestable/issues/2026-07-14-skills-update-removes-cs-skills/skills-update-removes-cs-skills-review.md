---
doc_type: issue-review
issue: skills-update-removes-cs-skills
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-14
round: 2
---

# Skills Update 删除 CodeStable Skills 代码审查报告

## 1. Scope And Inputs

- Report / analysis / fix-note：同目录三份 issue 产物。
- Implementation evidence：当前 `fix/issues-45-47-install-runtime` 工作区完整 diff、固定 `skills@1.5.17` 源码和隔离 E2E。
- Diff basis：README 双语升级命令、package checker、distribution 测试、legacy inventory，以及与 #47 共享的版本/runtime 改动。
- Baseline dirty files：none；当前改动均归属于 #45/#47 goal。

### Independent Review

- Detection：Paseo Task agent 与 OCR CLI 均可用。
- 环节 A：Paseo agent `30472bea-886f-4914-848b-35ebc27e6962` 完成 Round 1 审查与 Round 2 focused closure。
- 环节 B：OCR 完成 10 个本轮代码文件扫描，0 comments。
- Merge policy：两路结果均由主 agent 结合仓库事实核验；Round 1 两条 important 修复后由同一 reviewer 独立复核。
- Gate effect：none。

## 2. Diff Summary

- 新增：`tests/test_skills_cli_distribution.py`、legacy inventory fixture。
- 修改：README 双语升级指引、package checker 与相关测试。
- 删除：none。
- 风险热点：外部 CLI discovery 与 lock 删除判定、可选真实 CLI E2E。

## 3. Adversarial Pass

- 假设的生产 bug：测试用集合并集自证 sibling 保留，实际删除行为仍可回归。
- 主动攻击：把 package skill 移除、移除维护者 priority skills、预装第三方 probe 后重复完整安装。
- 结果：原恒真测试被真实 deletion-diff oracle 替换；两个变异都会翻转断言；真实 E2E 保留 32 个 `cs*` 与第三方 probe。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-045-N1 `tests/test_skills_cli_distribution.py` 未复刻上游三层容器分支的 `SKIP_DIRS`；当前 tracked tree 无该形态，不影响本轮 oracle。
- [ ] REV-045-N2 fix-note 的 ruff 结论仅覆盖本次改动文件，不代表全仓既有 lint 债清零。

### suggestion

none

### learning

- 外部 CLI 行为测试必须证明断言能杀死与根因同形的变异，不能用构造出来的并集证明保留。

### praise

- 离线 oracle 固定上游版本并逐语义复刻 discovery/deletion；真实 E2E 又覆盖了第三方 skill 保留。

## 5. Test And QA Focus

- 必测：固定 `skills@1.5.17` 的第三方 probe + 两次完整 CodeStable package 安装。
- 已执行：相关 `45 passed, 1 skipped`、全量 `443 passed, 1 skipped`、显式 E2E `1 passed`。
- 不能完全确认：上游 `vercel-labs/skills#1298` 尚未修复，裸 `update` 仍不安全。

## 6. Residual Risk

- 仓库侧提供安全完整重装入口，无法修复外部 CLI 的裸 `update`；README 与 checker 已阻止继续推荐该命令。
- 仓库无 CI，显式网络/CLI E2E 依赖提交前门禁执行；本次已独立执行并通过。

## 7. Verdict

- Status: passed
- Next: 进入 goal 功能验收与提交收尾。
