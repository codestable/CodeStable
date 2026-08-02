# CodeStable Roadmap

[English](./ROADMAP.en.md) · **中文**

CodeStable 的路线不是持续增加流程，而是随着模型和宿主能力提高，删掉已经不再产生可靠性收益的约束。

版本已经交付的事实以 [CHANGELOG.md](./CHANGELOG.md) 为准；这里记录仍在推进的方向，不代替 release notes。

## 已完成

- [x] 将 v1 的 32 个入口收敛为 8 个独立 thin-harness skill。
- [x] 建立 Codex、Claude 与 `skills` CLI 共用同一 canonical skill 源的插件分发。
- [x] 用 `attention.md`、`lessons/` 与 `work/` 取代分发式项目 runtime，新项目只创建最小记忆骨架。
- [x] 让 `cs` 支持明确行动同轮直转、当前会话讨论与收敛后 handoff。
- [x] 建立永久 Epic 文档与临时执行游标的双层模型，并保留三道 owner gate。
- [x] 通过路由 fixtures 和真实 Agent 对照实验验证基础行为与过程契约。

## 近期方向

- [ ] 扩大效果评测：覆盖多子项 Epic、长期恢复与跨模型一致性。
- [ ] 强化 `cs-refactor`：提高行为等价证据和性能重构场景的可操作性。
- [ ] 提升安装、升级和发布回归的真实环境覆盖。
- [ ] 持续用真实项目反馈删减重复确认、无价值产物和过期约束。

## 长期判断

以下信号会触发流程删减，而不是新增包装：

- 模型已经能在某类任务中稳定建立并解释证据；
- 宿主已经可靠提供同等的隔离、审查或恢复能力；
- 一条规则只增加文字和等待，没有改变失败概率；
- 项目已有 canonical 机制能够更好地承载同一事实。

欢迎在 Issue 区提交真实开发困境、失败案例和可复现证据。它们比抽象功能愿望更能决定 Roadmap。

返回 [README](./README.md)。
