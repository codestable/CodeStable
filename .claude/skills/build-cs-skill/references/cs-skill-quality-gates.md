# CodeStable Skill Quality Gates

Use this reference when reviewing whether a `cs-*` skill is maintainable and testable.

## Prompt-As-Code Rule

A skill is an executable protocol, not an explanatory article. Quality comes from:

- narrow trigger;
- explicit state model;
- process protocol appropriate to the skill kind;
- recoverable outputs;
- clear failure behavior;
- small active protocol;
- machine-checkable invariants;
- decision fixtures for risky branches.

Longer is not automatically better. Extra context can reduce reliability when it hides the rules the agent must follow.

## P0/P1/P2/P3 Sorting

Sort every paragraph by priority:

| Level | Meaning | Best location |
|---|---|---|
| P0 | Safety/security that must not rely on prompt obedience | hooks, scripts, sandbox, CI |
| P1 | Workflow contract the agent must follow | top-level `SKILL.md`, `## Spec`, contracts |
| P2 | Quality preference needing judgment | review checklist, QA protocol |
| P3 | Background, examples, rationale, templates | `references/` or docs |

Refactor when P3 appears before P1, or when the first 150 lines do not tell the agent how to act.

## Progressive Loading Gate

For skills with references, check:

- main `SKILL.md` names each reference;
- each reference has a clear load condition;
- startup does not read every reference;
- each stage loads one protocol first;
- support files are loaded only when the protocol asks for them.

Good wording:

```text
Load exactly one stage protocol before acting, plus only the support files that protocol requests.
```

## Contract Gate

Contracts protect the skeleton of the skill. They do not prove the agent will make the right decision.

Good contract targets:

- the routing function name (`restoreXStage` / `selectXAction`) when the Spec is the sole routing truth;
- behavioral invariant phrases (required artifacts, checkpoint sentences, forbidden-action rules);
- forbidden actions as `not-grep`;
- critical marker names.

Bad contract targets:

- bare Spec type names (`XState`, `XOutcome`, `HumanCheckpoint`, `CheckpointReason`) — they only prove the Spec block exists, not that any behavior is protected (measured: routing eval 2026-07 showed they add no behavioral value);
- generic words like `quality`, `review`, `check`, `best`;
- strings that appear in examples but not in the actual rule;
- brittle sentences likely to change during normal editing.

If frontmatter contracts are not supported in the local system, keep the invariant list in `## Machine Contracts` so it can be wired later.

## Behavior Gate

For each important branch, ask:

- What repository facts trigger it?
- What artifact proves it happened?
- What would be unsafe to skip?
- Can a fixture test the decision?

If a branch cannot be tested directly, at least document the expected input state and output outcome.

## Refactor Completeness Gate

Label the depth before judging quality:

- `minimal hardening patch`: only tightens trigger, adds a small Spec, adds contracts, or fixes one local rule.
- `full protocol refactor`: rewrites the active skill body into a complete recoverable protocol.

A full protocol refactor must include trigger contract, Spec, process protocol appropriate to the skill kind, state restoration or branch selection, decision rules when needed, progressive loading when references exist, human checkpoints when applicable, failure behavior, output contract, machine contracts, and fixture recommendations. A proposal that only adds three sections is useful hardening, but it is not a full refactor.

## Measured Rules（routing eval 2026-07，5 skill × 3 模型 × k3，[measured]）

以下规则有量化依据（evidence: `experiments/cs-issue-routing-001/results.md`）：

1. **Spec 必须是唯一路由真相，不与散文状态机表格并列**。并列冗余接近装饰甚至有害：cs-epic 上「表格+Spec 并列」(0.833) 低于重构前只有表格的原版 (0.867)；替代后 0.989。
2. **Spec 的行为增益与原规则含混度成正比**（cs-docs +0.43 > refactor +0.22 > epic +0.12 > feat +0.10 > issue ±0）。规则本就简单清晰的 skill 不必为形式重写。
3. **增益集中在非顶级模型与复杂/嵌套分支**（epic 批量上下文、fastforward 资格、多产物状态恢复）。顶级模型对表达形式不敏感。
4. **给中小模型的分支澄清要显式排除错误选项**（负向澄清），只加正向描述可能引入新歧义：cs-feat ff 分支加「并说明」后 haiku 从全对变全错（答成 NeedsHuman），改为「结果是 RoutedTo Design（不是 NeedsHuman、不是 checkpoint）」后三模型全对。
5. **decision fixture 的 oracle 必须宽容语义等价措辞**（`result_type_any`/`target_any`），且先抽查 observed 再下 verdict——未校准的严格 oracle 会对无 Spec 词汇的旧版本系统性不公平（cs-docs original 校准前 0.222 → 校准后 0.528）。
6. **措辞优化两轮无效 → 查结构缺失，别继续磨措辞**。模型在某分支上持续答错且答案集中在"最接近的枚举项"，通常是 Spec 生命周期有分支没形式化（模型无 guard 可走）：cs-goal rt-g02 两轮枚举限定 0.33→0.33，补上 grill 入口 guard 后一轮 0.33→0.89。routing 函数必须覆盖从触发到退出的**完整**生命周期（含入口/重建/降级分支），guard 顺序即优先级，不可达的尾分支是 bug。

## Anti-Patterns

Fix these before adding more prose:

- Spec branch function AND a prose state-machine table both present (duplicate routing truths — measured harmful, see Measured Rules 1);
- active skill has no `## Spec`;
- workflow skill has no concise `## Workflow`, `## Protocol`, or `## Lifecycle`;
- single-step operator has no `## Operation` or `## Algorithm`;
- stage routing relies on chat history;
- compatibility skill duplicates main rules;
- fastforward mode has no rejection criteria;
- implementation details appear before routing rules;
- reference files are loaded eagerly;
- failure path says only "ask user" without current artifact and next action;
- skill can continue past a human checkpoint without explicit confirmation.

## Review Output

When reviewing a skill, report:

- skill kind;
- trigger overlap risks;
- missing or weak Spec pieces;
- P1/P3 ordering issues;
- contracts to add;
- fixtures to add;
- references to split or defer-load;
- one or two highest-leverage edits.
