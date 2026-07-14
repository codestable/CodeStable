---
doc_type: goal-functional-acceptance
goal: fix-skills-update-and-standalone-version
status: passed
reviewed: 2026-07-14
---

# #45/#47 独立功能验收报告

## Reviewer

- Role：独立功能验收 Task agent，只读黑盒验收。
- Paseo agent：`9329c609-7264-47d1-af0d-7e1021101984`。
- Provider：`claude-fable-5`，`thinking=high`，`mode=plan`。
- Lifecycle：验收结果已消费，agent 已成功归档。
- Final iteration：`iterations/002.md`。

## Acceptance Checks

### 1. 多 Skill 安装与安全升级

Status: pass

- 固定本机缓存的 `skills@1.5.17`，在隔离 HOME/XDG 中先安装 `third-party-probe`，再两次完整安装 `plugins/codestable` package。
- 最终安装目录恰有 32 个 `cs` / `cs-*` skills 与 probe，共 33 个；probe 保留，CodeStable 集合与 package 目录一致。
- 离线 oracle 复刻 priority discovery 与删除差集：repo root 会把 32 个 lock 路径判为删除，package subpath 删除差集为空。
- README 双语均改为 package-root 完整重装，并明确裸 `update` 的误删风险；package checker 禁止重新写回裸命令。

### 2. Standalone Runtime 版本

Status: pass

- 在第二个隔离 HOME/XDG 中 standalone 安装 `cs-onboard`，安装产物包含 `VERSION: 1.0.3`。
- 从安装后的 skill 目录运行 runtime sync 到临时已接入仓库，返回 `status: ok`。
- 实际 manifest 的 `plugin_version` 与 `runtime_version` 均为 `1.0.3`，没有 `unknown`，capability missing 为空。

### 3. 版本一致性与 Fail-Closed

Status: pass

- root VERSION、standalone VERSION、两个 plugin manifest 与两个 marketplace manifest 均为 `1.0.3`。
- release bump targets 与 package checker 覆盖全部六处版本载体。
- 删除临时 standalone VERSION 后，`force=False` 与 `force=True` 均返回 `version-unavailable`；既有 manifest 字节不变，新仓库也不创建 manifest。

### 4. 自动化门禁

Status: pass

- 相关四文件：`45 passed, 1 skipped`。
- 全量：`443 passed, 1 skipped`。
- 显式真实 CLI E2E：`1 passed`。
- package checker：`ok: true`，findings 为空。
- runtime sync check：`status: ok`，expected/installed 均为 `1.0.3`，missing 为空。
- 本次改动 Python 文件 ruff、`git diff --check`、Markdown ≤300 行均通过。

### 5. Review 与交付准备

Status: pass

- 两份 issue review 均为 `status: passed`、`reviewer: subagent+ocr`、`round: 2`。
- 独立 code review 最终 verdict 为 blocking 0 / important 0。
- 当前分支与 dirty scope 均只归属于 #45/#47；PR 创建属于本报告后的 goal 收尾动作。

## Functional Evidence

- E2E #1：隔离安装 probe、完整 package、修改源副本 `cs/SKILL.md` 后二次安装；终态 33 个 skills 且无删除记录。
- E2E #2：standalone 安装 `cs-onboard`，从安装目录同步 runtime，再删除版本元数据验证 force 两态。
- 临时目录均已清理；验收前后仓库状态一致，Task agent 未修改仓库文件。

## Verdict

pass。Owner 的五条 acceptance criteria 均有直接、可执行证据，本次阻塞项为 0。

## Residual Risks

- 上游 `vercel-labs/skills#1298` 未修复，裸 `update` 仍不安全；本仓库只能用安全重装入口和 checker 拦截。
- 远端 blob CDN 是否携带非 Markdown 的 `VERSION` 未直接验证；本轮真实 local `--copy` 安装已验证。
- 向上版本搜索仍可能在 standalone VERSION 异常缺失时拾取祖先目录的无关版本文件；正常包与 checker 已显著收窄触发面。
- 仓库无 CI，显式 CLI E2E 依赖发布/提交前门禁；本次已独立执行通过。

## Follow-Up

- 创建关联 #45/#47 的 PR 后，在 `iterations/002.md` 记录最终 commit、PR URL 与 completion audit。
