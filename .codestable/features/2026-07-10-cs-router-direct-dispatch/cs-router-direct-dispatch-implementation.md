---
doc_type: feature-implementation
feature: 2026-07-10-cs-router-direct-dispatch
status: complete
updated: 2026-07-10
---

# cs-router-direct-dispatch 实现记录

## 基线

- `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_skill_entry_simplification.py tests/test_skill_workflow_scenarios.py tests/test_skill_contracts.py`：改动前 `83 passed`。
- runtime sync `--check --json`：`status=ok`，plugin/runtime 版本均为 `1.0.2`，capabilities 无缺失。
- dirty scope：仅本 feature 新建的 design、checklist、design-review；无用户侧既有改动。

## Step 1：契约骨架

- 退出信号：四种入口模式映射到 RoutedTo / Completed / HumanCheckpoint，根 skill 明确当前 run 继续。
- RED：新增 4 个 root prompt 契约测试并把 `cs` 加入 core contracts；5 个测试真实失败，原因均为旧 `cs/SKILL.md` 缺少新模式、直转和 contracts 文案。
- GREEN：重写 `cs/SKILL.md`，删除测试内硬编码 `route_request()` 模拟；首轮 GREEN 暴露 body/frontmatter 断言边界及两条既有锚点，窄修复后通过。
- VERIFY：三份定向测试 `87 passed in 1.33s`。
- REFACTOR：删除重复 route level 表，未拆文件或新增运行时代码。
- 影响面：根路由 frontmatter/Spec/优先级/续作扫描/转交协议，静态 workflow 与 contracts 测试。
- 清洁度：无调试输出、临时 TODO/FIXME、注释旧代码或方案外文件。
- 需求迭代：无。

## Step 2：共享出口

- 退出信号：两对模板/runtime copy 逐字一致；brainstorm 待确认与已确认出口、audit 已确认 finding 均可机械验证。
- RED：新增共享转交、brainstorm、audit 三个契约测试；3 个测试因旧文案缺失真实失败，copy 基线测试保持绿色。
- GREEN：execution conventions 新增同轮转交权威口径并同步 runtime copy；brainstorm case 1/2/4 保留一次确认，case 3 直接同轮进入 epic；audit 选中 finding 后同轮进入 issue/refactor。
- VERIFY：新增 4 项测试全绿；三份定向测试 `90 passed in 1.37s`；execution/system overview 两对 copy 的 `cmp` 均通过。
- REFACTOR：无，仅替换出口语义；`cs-brainstorm/SKILL.md` 为 260 行，仍低于 300 行上限。
- 影响面：共享 execution conventions、brainstorm 四 case、audit Phase 4、runtime copy 一致性测试。
- 清洁度：无调试输出、临时 TODO/FIXME、注释旧规则或方案外文件。
- 需求迭代：无。

## Step 3：文档投影

- 退出信号：中英文公开文档都表达行动直转、咨询只建议，且仍只推荐主入口。
- RED：新增双语 docs 投影测试，因中文 README 仍使用旧“告诉你走哪个 skill”口径而真实失败。
- GREEN：原位更新 README、WORKFLOW、SKILL_CATALOG 中英文镜像，以及 system overview 模板/runtime copy。
- VERIFY：docs 投影与 copy 两项测试通过；三份定向测试 `91 passed in 2.57s`；旧死端文案定向搜索无命中。
- REFACTOR：无；不改文档结构或兼容入口清单。
- 影响面：7 份公开/共享说明与 1 份 runtime copy。
- 清洁度：无临时文案、方案外入口或模板/copy 漂移。
- 需求迭代：无。

> 顺手发现：`README.en.md` 改动前已有 363 行，超过项目 300 行建议值。本 step 未增加行数；拆分英文 README 会扩大 approved design 范围，留待独立 docs refactor。

## Step 4：验证闭环

- fixtures：新增 `cs-routing-001` baseline config 与 16 个 routing fixtures；runner mock dry-run 成功解析 48 个 cell，未发起付费模型调用。
- 核心验证：CMD-001 `92 passed`；CMD-002 `215 passed`；CMD-004 runtime `status=ok`；CMD-005 无 whitespace error。
- package 基线：CMD-003 仍只有 `CHANGELOG.md` 缺 1.0.2、marketplace version 与 `VERSION` 不一致两条既有 finding，本 feature 未改发布元数据。
- 独立 review round 1：Claude Fable Task agent `21907498-948d-4917-9a47-569086996065` verdict `approve`，无 blocking；open-code-review（OCR）CLI 完成行级扫描，给出 1 条字段一致性建议。Fable 另报 1 条共享 scorer 测量局限、5 nit、3 suggestion 和 2 项主要 residual risk。
- review 后小修：补 root preflight/跨轮恢复说明、audit Spec 的 selected finding 路由、cs-req 测试锚点、brainstorm/WORKFLOW 文案一致性，并统一/扩展 fixtures；复跑核心命令结果不变，等待同一 Fable agent 复审。
- 独立 review round 2：同一 Fable agent 复核小修与登记动作，verdict `approve`，无 unresolved blocking / important；Step 4 退出信号满足。

### 测量局限与后续项

- `routing_decision.py` 的 target 双向包含匹配与 allowed-candidate 豁免会让组合 target 或 deprecated stage target 出现假阳性；这是 pre-existing 共享 eval 基建，approved design 明确不在本 feature 修改。
- 本 feature 的关闭动作：QA/acceptance 人工核对 fixtures 的完整 observed target，不能只看 scorer 分数。
- 后续 issue 候选：收紧 routing scorer 为主入口精确匹配，并补组合 target / deprecated stage 两个回归用例。
