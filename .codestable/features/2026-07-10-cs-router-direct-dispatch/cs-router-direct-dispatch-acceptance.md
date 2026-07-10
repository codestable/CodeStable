---
doc_type: feature-acceptance
feature: 2026-07-10-cs-router-direct-dispatch
status: passed
accepted: 2026-07-10
round: 1
---

# cs-router-direct-dispatch 验收报告

> 阶段：阶段 3（验收闭环）
> 关联方案：`cs-router-direct-dispatch-design.md`
> owner 指定终审：Claude Fable Task agent round 2 `approve`

## 1. 接口契约核对

- [x] `IntakeMode` 四值与结果词汇：Execute→RoutedTo、Advise/Explain→Completed、Ambiguous→HumanCheckpoint，和 routing harness 既有枚举一致。
- [x] route brief 固定 `Route/Reason/Dispatch`，且只用于 Execute/Advise；正文无旧 route level。
- [x] Execute 输出 brief 后加载一个 canonical 主 skill，原始诉求原样传递并在当前 run 继续。
- [x] Explain/Ambiguous 不伪造 route brief；target unavailable 返回 NeedsHuman，不在 root 模拟下游。
- [x] 流程图各节点均落在 root Spec/模式表/转交协议与 fixtures 中。

## 2. 行为与决策核对

- [x] 入口模式先于目标；明确诉求不全局扫描，续作才扫 8 个活动根。
- [x] 专用 workflow 优先于 goal；已知优化/主动发现、domain/keep 相邻边界均落地。
- [x] 一个请求同一时刻只转交一个主入口；双诉求先确认顺序。
- [x] onboard 是串行前置 gate，checkpoint 不被绕过；完成后恢复原目标，跨轮缺上下文时询问。
- [x] 转交不扩大写入/外部通信授权，目标 skill 自己恢复事实并执行 gate。
- [x] 已确认/待确认出口进入共享 execution conventions；brainstorm/audit 使用同一权威口径。
- [x] 明确不做：未新增路由引擎/公开 skill，未删除 15 个兼容入口，未修改发布元数据或 scorer。
- [x] 挂载点反查：root、两份共享 reference 模板/copy、brainstorm/audit、6 份双语 docs、3 个测试文件、routing experiment 均在 design §2.3/§2.4 范围内。
- [x] 拔除推演：逆向移除上述 skill/docs/tests/experiment 与 feature 产物后，运行时代码和兼容入口无残留依赖；本 feature 不引入 adapter/schema migration。

## 3. 验收场景核对

- [x] S1-S4 四模式：Opus QA C01-C04 全部符合；C01 continuing-current-run，C02 recommendation-only，C03 Overview，C04 ClarifyRoute。
- [x] S5-S7 冲突路线：C05-C09 分别命中 feat/audit/refactor/domain/keep，无 forbidden target。
- [x] S8 onboard：C10 前置 `cs-onboard`，C11 gate 完成后恢复 `cs-issue`；C16 咨询不自动 onboard。
- [x] S9 续作：C12 唯一 refactor 直转，C13 多候选 ClarifyRoute。
- [x] S10-S11：C14 unavailable→NeedsHuman；C15 双诉求→ClarifyRoute。
- [x] S12 二级出口：static tests + Fable review 确认 brainstorm case 1/2/4 待确认、case 3 已确认、audit selected finding 已确认。
- [x] review Test And QA Focus：16 条 observed target 已人工全串复核，deprecated=0、combined=0、Execute brief 后停止=0。
- [x] QA 来源：`cs-router-direct-dispatch-qa.md`，`status=passed`，failed/blocked 均 none；mixed feature 的核心 prompt 行为有独立 LLM runner 证据。
- [x] Evidence pack / DoD / gate：非 goal/gate feature，无对应文件；CMD-001/002/004/005 通过，CMD-003 只有登记基线。

## 4. 术语一致性

- `入口模式` / `IntakeMode`、`路由目标` / canonical main skill、`同轮转交` / current-run dispatch、`route brief` 四组术语与 design 一致。
- `RoutedTo/HumanCheckpoint/Completed/NeedsHuman` 复用 harness 既有词汇；无自造 result type。
- `L0-L4` 仅存在于 frontmatter `not-grep` 声明，不在 skill body；旧死端文案仅在“常见错误”反例中合法出现。

## 5. 领域影响盘点

- [x] 新领域名词：none；上述术语是 CodeStable 编排协议，不进入业务 CONTEXT.md。
- [x] 结构性 ADR：none；复用已安装 skill 加载 seam，不新增依赖、模块或难回退架构选择。
- [x] 稳定流程约束：已进入 `execution-conventions.md` 权威模板与 runtime copy，无需另写 ADR。

## 6. requirement delta / clarification 回写

- `requirement` 为空。本 feature 收敛既有 root-router 的交互和转交语义，没有新增 capability boundary、用户故事或产品 pitch；记录为无 requirement 影响，不 backfill / 改写长期 requirement。

## 7. roadmap 回写

- design 无 `roadmap` / `roadmap_item` 字段；非 roadmap 起头，无 items.yaml 或主文档状态需要回写。

## 8. attention.md 候选盘点

- 本 feature 未暴露每个后续 feature 都会重复踩的环境/命令规则，无 attention.md 候选。
- routing scorer 的包含匹配局限属于 eval 基建经验，已登记后续 issue / `cs-keep` 候选，不写入启动必读。

## 9. 遗留

- 后续 issue：收紧 routing scorer target 精确匹配，补组合 target 与 deprecated stage 回归测试。
- 已知限制：未运行付费多模型 routing eval；动态加载 seam 未在全部 provider 宿主逐一验证。
- 既有债：`README.en.md` 363 行超项目建议值；本 diff 未增行，留待 docs refactor。
- 量化前人工规则：运行 `cs-routing-001` 时检查 observed target 全串，不能只看 scorer 总分。

## 10. 最终审计

- 验证证据来源：`cs-router-direct-dispatch-qa.md`
- Evidence sources：approved design/checklist、goal package、round 2 `subagent+ocr` review、实现记录；无 evidence-pack/dod/gate 文件
- 聚合命令：targeted `92 passed`；full `215 passed`；runtime `status=ok`；`git diff --check` 通过；package 只有两条既有发布基线
- 场景复核：re-verified 12 / trust-prior-verify 0；16 个 QA 输入覆盖全部 12 个 design 场景
- 交付物复核：skill/shared refs/docs/tests/fixtures/goal package/feature reports 均存在；requirement/roadmap/architecture 无需回写
- 完整工作区复核：tracked diff 与两个 untracked 交付目录均纳入；无范围外 dirty 文件
- diff 清洁度：debug/TODO/FIXME/注释旧代码/方案外文件检查通过
- 知识沉淀出口：scorer 局限→后续 issue/keep；README.en 行数→docs refactor；attention/ADR/req/roadmap 无候选
- 结论：通过；owner 指定的 Claude Fable 终审已 approve，无 unresolved blocking / important
