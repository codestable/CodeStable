---
doc_type: issue-report
issue: skills-update-removes-cs-skills
status: confirmed
severity: P1
summary: skills update 会删除已安装的 CodeStable cs 系列技能
tags: [installation, skills-cli, regression]
---

# Skills Update 删除 CodeStable Skills Issue Report

## 1. 问题现象

执行 `npx skills@latest update` 后，命令只报告更新少量其他 skills，但此前全局安装的全部 CodeStable `cs*` skills 从安装目录中消失；重新执行完整安装命令后才恢复。

## 2. 复现步骤

1. 通过 `skills` CLI 全局安装完整 CodeStable 多-skill package。
2. 在安装源有新提交后执行 `npx skills@latest update`。
3. 观察更新输出和全局 skill 安装目录。
4. 观察到：更新完成后 CodeStable `cs*` sibling skills 被删除。

复现频率：已在实际全局更新场景稳定观察到；隔离回归需覆盖 package discovery 与 reconciliation。

## 3. 期望 vs 实际

**期望行为**：更新 CodeStable package 时保留所有未删除或重命名的 sibling skills，并同步完整 package。

**实际行为**：更新少量 skills 的过程中，仍存在于上游 package 的 CodeStable `cs*` skills 被当作已删除并移除。

## 4. 环境信息

- 涉及模块 / 功能：`skills` CLI 全局安装与更新、CodeStable plugin package discovery。
- 相关文件 / 函数：`plugins/codestable/.codex-plugin/plugin.json`、`plugins/codestable/skills/`、README 升级指引；外部 `skills@1.5.17` update deletion detection。
- 运行环境：macOS，本机全局 skills 安装。
- 其他上下文：安装文档当前推荐裸 `npx skills@latest update`；关联 #28、#43。

## 5. 严重程度

**P1** — 正常升级会移除整套核心工作流 skills，虽可完整重装恢复，但会直接中断使用。

## 备注

GitHub Issue：#45。
