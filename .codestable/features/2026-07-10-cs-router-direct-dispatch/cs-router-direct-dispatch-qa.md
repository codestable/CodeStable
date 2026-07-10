---
doc_type: feature-qa
feature: 2026-07-10-cs-router-direct-dispatch
status: passed
tested: 2026-07-10
round: 1
---

# cs-router-direct-dispatch QA 报告

## 1. Scope And Inputs

- Design / checklist / review: 同 feature 目录下 approved design、全 done checklist、round 2 passed review
- Evidence pack / gate / DoD results: none；使用实现记录、命令输出与独立 QA runner 取证
- Diff basis: 当前 unstaged diff + 全部 untracked feature/experiment 文件；无范围外 baseline dirty 文件
- Feature type: mixed；实现载体是 skill 文案/fixtures，但根路由语义是用户可见行为
- Core evidence gate: `claude/opus` plan-mode runner 对不含 expect 的 16 个输入做实际 LLM 判定；静态 contracts/tests、fixture schema 与完整回归补充证明
- QA runner: Paseo Task agent `f4d4305a-c932-43cb-b6df-4bb114c9d1a7`

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据 | 结果 |
|---|---|---|---|---|---|
| QA-001 | design 1-4 | core-functional | Execute / Advise / Explain / Ambiguous | Opus C01-C04 + static contracts | pass |
| QA-002 | design 5-7 | core-functional | feat-vs-goal、audit-vs-refactor、domain-vs-keep | Opus C05-C09 | pass |
| QA-003 | design 8 | core-functional | onboard 前置 gate 与原目标恢复 | Opus C10-C11 + rt-c10/c11 | pass |
| QA-004 | design 9 | core-functional | 唯一 / 多候选续作 | Opus C12-C13 | pass |
| QA-005 | design 10-11 | core-functional | target unavailable、双诉求顺序 | Opus C14-C15 | pass |
| QA-006 | design 2/8 | core-functional | 未 onboard 的纯咨询不写骨架 | Opus C16 | pass |
| QA-007 | design 12 | supporting | brainstorm/audit 已确认与待确认出口 | targeted pytest + Fable review | pass |
| QA-008 | docs/copies | non-functional | 双语投影、模板/runtime copy、旧死端清零 | pytest + cmp + reverse search | pass |
| QA-009 | review focus | supporting | scorer 组合/deprecated target 假阳性 | 人工检查 16 条 Opus observed target | pass |
| QA-010 | DoD | supporting | 全量回归、runtime、格式、package 基线 | CMD-001..005 | pass |

## 3. Command Results

- CMD-001 targeted pytest → exit 0：`92 passed`
- CMD-002 `pytest -q tests` → exit 0：`215 passed`
- CMD-003 package check → exit 1：仅已登记的 `CHANGELOG 1.0.2` 与 marketplace/VERSION 两条既有 finding
- CMD-004 runtime sync check → exit 0：`status=ok`，plugin/runtime `1.0.2`，capabilities 无 missing
- CMD-005 `git diff --check` → exit 0
- eval runner mock dry-run → exit 0：3 models × 16 fixtures × k=1，共 48 cells；未发起付费调用
- fixture `jq` schema lint、两对 `cmp`、旧死端反向搜索、cleanliness 检查、feature YAML/frontmatter validation → 全部 exit 0

## 4. Scenario Results

- [x] QA-001 四模式：C01 `RoutedTo cs-issue/continuing-current-run`；C02 Recommendation；C03 Overview；C04 ClarifyRoute。
- [x] QA-002 路线优先级：C05-C09 分别为 `cs-feat/cs-audit/cs-refactor/cs-domain/cs-keep`，无误选目标。
- [x] QA-003 onboard：C10 只转 `cs-onboard`，C11 完成 gate 后恢复 `cs-issue`。
- [x] QA-004 续作：C12 唯一 refactor 直转；C13 多候选停 ClarifyRoute。
- [x] QA-005 失败/顺序：C14 `NeedsHuman cs-issue`；C15 两诉求停 ClarifyRoute。
- [x] QA-006 未接入咨询：C16 `Completed cs-issue/recommendation-only`，不自动 onboard。
- [x] QA-009 observed target：16 条中 deprecated target=0、combined target=0、Execute brief 后停止=0。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- QA runner 证明了当前 prompt 的实际 LLM 路由判定，但没有在全部 provider 宿主中执行“按名加载已安装 skill”的动态机制；该机制是本 feature 复用的既有宿主 seam，未改运行时代码。
- C05-C09/C11-C12 输入未声明 installed skills；runner 正确选择目标，但无法证明目标在任意真实安装中可用。C14 已单独验证 unavailable 分支。
- 未运行付费多模型 `cs-routing-001`；真实 IntakeMode 准确率仍需后续量化实验。当前 observed target 已人工全串复核，不依赖 scorer 总分。
- onboard 跨会话压缩仍可能丢原始诉求；文本规定缺失时询问，未假装自动持久化。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass；两条发布元数据 finding 与 README.en 行数为已登记既有债

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段
