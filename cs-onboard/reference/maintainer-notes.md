# CodeStable 维护者说明

由 `cs-onboard` 复制到项目 `.codestable/reference/`。维护技能家族时反复查阅、不适合放各子技能正文的说明。

## 1. 断点恢复

AI 对话随时可能中断（token 超限、网络断开、换设备）。各技能发现不是从零开始时，先检查已有产物完成度，从上次停下处续：

- **context**：某篇取舍说明 / 词汇表已有部分 → 逐节补缺，不重写已完成节
- **issue / epic**：载体上已有记录（GitHub issue 正文 / 本地 md）→ 读完从未完成步骤续；代码已改但收尾记录没写 → 直接补验证 + 记录
- **clarify**：已有 `clarify.md` → 读完问"接着聊还是推翻"

恢复时先简短汇报："检测到上次到 X 阶段，我从 Y 继续"。

## 2. 扩展点

- **新增子技能**：定型后在 `system-overview.md` 的两轴 / 横切清单 + `cs` 路由表加索引，登记目录位置
- **跨技能新约束**：适用所有技能的规则 → 走 `cs-convention` 写进 `convention.md`，不只改一个技能
- **共享术语**：体系自己形成的稳定术语 → 沉淀进 `convention.md`，别散落重复定义

## 3. 维护规则

- 改体系共享口径走 `cs-convention` 改 `convention.md`，已 onboard 项目重跑 `cs-onboard` 同步副本
- 每次扩展同步更新 `system-overview.md` 索引 + `cs` 路由表 + 相关子技能表述（CLAUDE.md 要求）
- 共享说明优先进 `convention` / `reference`，不散落各子技能
- 每个 `SKILL.md` < 100 行；超了把模板 / 详表拆到同目录 `reference.md`
