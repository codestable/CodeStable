---
doc_type: issue-review
issue: standalone-runtime-version-unknown
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-14
round: 2
---

# Standalone Runtime 版本 Unknown 代码审查报告

## 1. Scope And Inputs

- Report / analysis / fix-note：同目录三份 issue 产物。
- Implementation evidence：standalone `VERSION`、runtime sync/health、release bump、package checker、相关测试与隔离安装 smoke。
- Diff basis：当前 `fix/issues-45-47-install-runtime` 工作区完整 diff。
- Baseline dirty files：none；当前改动均归属于 #45/#47 goal。

### Independent Review

- Detection：Paseo Task agent 与 OCR CLI 均可用。
- 环节 A：Paseo agent `30472bea-886f-4914-848b-35ebc27e6962` 完成 Round 1 审查与 Round 2 focused closure。
- 环节 B：OCR 完成 10 个本轮代码文件扫描，0 comments。
- Merge policy：外部 findings 均由主 agent 用代码、测试和临时目录反例核验后合并。
- Gate effect：none。

## 2. Diff Summary

- 新增：`plugins/codestable/skills/cs-onboard/VERSION`。
- 修改：runtime health/sync、release bump、package checker、runtime 人读说明与测试。
- 删除：none。
- 风险热点：版本发现失败语义、manifest 写入前置条件、dirty/incomplete 状态优先级。

## 3. Adversarial Pass

- 假设的生产 bug：`force=True` 绕过缺版本保护，或错误优先级覆盖 dirty/incomplete 诊断。
- 主动攻击：缺 VERSION、`force=True`、dirty managed paths、runtime incomplete、standalone CLI 安装后从已安装目录同步。
- 结果：缺版本始终结构化返回 `version-unavailable` 且不写 manifest；既有优先级保持；真实安装写入 `1.0.3`。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-047-N1 fix-note 的 ruff 结论仅覆盖本次改动文件，不代表全仓既有 lint 债清零。

### suggestion

- 后续 release 阶段按仓库惯例 bump 版本；本 bugfix PR 不单独执行 release。

### learning

- runtime 版本不可发现必须在任何复制和 manifest 写入之前 fail-closed，`force` 也不能绕过元数据完整性。

### praise

- standalone、release bump、checker 与 runtime sync 形成了单一版本一致性闭环。

## 5. Test And QA Focus

- 必测：真实 skills CLI standalone 安装后，从已安装 `cs-onboard` 目录运行 runtime sync。
- 已执行：manifest 的 `plugin_version` / `runtime_version` 均为 `1.0.3`；相关、全量、checker 与 runtime 门禁通过。
- 不能完全确认：远端 blob CDN 分发是否携带非 Markdown 的 `VERSION`；local `--copy` 路径已验证。

## 6. Residual Risk

- 若 standalone `VERSION` 被异常删除，祖先目录中的无关 `VERSION` 仍可能被既有向上搜索逻辑拾取；checker 与正常安装包降低了触发面。
- blob CDN 分发路径未在本轮直接验证，功能验收继续关注安装产物中 `VERSION` 是否存在。

## 7. Verdict

- Status: passed
- Next: 进入 goal 功能验收与提交收尾。
