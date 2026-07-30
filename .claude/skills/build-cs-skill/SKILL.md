---
name: build-cs-skill
description: "CodeStable skill authoring and evolution protocol. Use when creating, refactoring, simplifying, or reviewing cs-* skills under plugins/codestable/skills or .claude/skills. Produces a thin harness, an explicit context plan, evidence gates, and an optional agent collaboration contract. Do not use for product implementation; use eval-cs-skill only for measured experiment loops."
---

# build-cs-skill

## Purpose

Build the smallest always-loaded control surface that lets an agent select relevant context, respect
hard gates, collaborate safely, and leave recoverable evidence. `SKILL.md` is the **thin harness**;
references and repository facts are **thick context**. Thick means decision-useful, not large.

Specify responsibility, authority, context selection, evidence, and stop conditions. Leave safe
implementation choices to the executing agent.

## Scope And References

Targets are `plugins/codestable/skills/<skill-name>/` or `.claude/skills/<local-skill-name>/`.

Load only the reference needed for the current decision:

- `references/cs-skill-spec-standard.md`: contract definitions, typed decisions, recovery, and output semantics.
- `references/cs-skill-quality-gates.md`: review algorithm for placement, context, evolution, runtime alignment, and validation safety.
- `references/cs-skill-fixture-patterns.md`: risky routing, checkpoint, failure, compatibility, or
  forbidden-action scenarios.

## Spec

```haskell
data SkillKind
  = OperatorSkill | WorkflowSkill | MethodologySkill | CompatibilityShim | ReferenceDoc

data SkillShape = NoActiveSkill | ThinOperator | ContextualWorkflow | ToolBackedWorkflow
                | ShimSkill | ReferenceSkill
data ProcessProtocol = WorkflowProtocol | DomainProtocol | LifecycleProtocol
                     | OperationProtocol | AlgorithmProtocol | ShimRoute | ReferenceOnly
data RulePlacement = Harness | StageContext | ProjectContext | DeterministicGate | Remove

selectSkillShape :: SkillKind -> SkillSource -> SkillShape
selectSkillShape kind source | not (independentSkillNeeded kind source) = NoActiveSkill
selectSkillShape kind source =
  case kind of
    ReferenceDoc      -> ReferenceSkill
    CompatibilityShim -> ShimSkill
    OperatorSkill     -> ThinOperator
    WorkflowSkill
      | deterministicRouter source -> ToolBackedWorkflow
      | otherwise                  -> ContextualWorkflow
    MethodologySkill  -> ContextualWorkflow

selectProcessProtocol :: SkillKind -> SkillSource -> ProcessProtocol
selectProcessProtocol kind source =
  case kind of
    WorkflowSkill
      | lifecycleDriven source -> LifecycleProtocol
      | otherwise              -> WorkflowProtocol
    OperatorSkill
      | algorithmic source -> AlgorithmProtocol
      | otherwise          -> OperationProtocol
    MethodologySkill  -> DomainProtocol
    CompatibilityShim -> ShimRoute
    ReferenceDoc      -> ReferenceOnly

placeRule :: Rule -> RulePlacement
placeRule r
  | mechanizable r                                    = DeterministicGate
  | nonMechanizableSafety r                           = Harness
  | projectSpecific r                                 = ProjectContext
  | stageSpecific r                                   = StageContext
  | everyInvocationNeeds r && changesDecisionOrGate r = Harness
  | otherwise                                         = Remove

buildContextPlan :: SkillShape -> [PlacedRule] -> ContextPlan
buildThinHarness :: SkillShape -> ResponsibilityContract -> ContextPlan -> Markdown
```

## Build Protocol

### 1. Establish scope and responsibility

Read the target and relevant repository design facts; inspect git status and preserve unrelated edits.
State the one outcome the skill owns, its authority boundary, completion evidence, and unsafe stop
conditions. Authoring itself does not require project preflight. A generated skill adds preflight only
when its behavior depends on project setup, repository facts, artifact writes, or recovery.

If there is no independent installable responsibility, or an existing skill/reference/tool owns it,
select `NoActiveSkill`. A retired v1 CodeStable name also selects `NoActiveSkill`; migration prose is
not an instruction to recreate a compatibility shim. Use `ReferenceSkill` only when knowledge has an
independent distribution contract.

### 2. Choose the minimum shape

Classify before writing; do not default to a full protocol refactor. Use `ThinOperator` for one
action/artifact, `ContextualWorkflow` for staged or recoverable work, and `ToolBackedWorkflow` when a
deterministic router/gate owns fragile choices. `ShimSkill` contains only a canonical target and
preset, and is allowed only when a newly accepted distribution contract explicitly ships that alias.
`ReferenceSkill` contains knowledge without an invented workflow.

Use high freedom for safe implementation choices, medium for preferred patterns, and low only for
fragile operations or invariant-sensitive ordering.

### 3. Place every rule once

Inventory current and proposed rules before editing. Record each rule's source, affected decision,
frequency, and `RulePlacement`; then apply `placeRule`.

- Mechanizable safety and repeated transformations -> script, hook, or gate.
- Stage methods, templates, and examples -> stage reference.
- Project facts, ADRs, and learnings -> repository CodeStable artifacts.
- Every-invocation decisions and non-mechanizable hard gates -> harness.
- Generic advice, duplicated rationale, stale prose, and behavior-neutral steps -> remove.

Information must have one canonical home. Do not retain the same route, gate, or method in both the
harness and a prose reference.

### 4. Build the context plan before the harness

Call `buildContextPlan` before writing the body. For every context source state when to load it, why
it matters, how freshness is checked, when enough context has been gathered, and how an already
loaded fact is reused.

Entry context is the minimum needed for a safe next action. After selection, load one stage protocol
and only relevant facts/support. Do not preload every reference, ADR, note, or source file.

### 5. Write the thin harness

Write the runtime kernel in this order: trigger/frontmatter, responsibility, context contract,
decision contract when needed, hard gates, collaboration when needed, and done/failure.

Target review thresholds: 30-80 body lines for an operator, 60-120 for a workflow front door, and at
most 40 for a shim. Exceeding them requires another placement pass and an explicit reason, not truncation.

Do not include long rationale, historical narrative, broad checklists, templates, or ordinary coding
steps in the harness. Preserve a compact `## Operation`, `## Workflow`, or `## Lifecycle` only when
it helps a fresh agent orient from entry to recoverable exit.

### 6. Add collaboration only when useful

Delegate only bounded work that has explicit ownership and an independent completion check. Do not
pre-script provider-specific roles or a fixed agent count.

Use this packet contract:

```text
contextPacket = goal + relevantContext + scopeOwnership + boundaries + evidence + returnContract
mainAgentOwnsIntegration = true
```

The delegated agent chooses its route. The main agent owns integration, conflict handling, final
verification, and durable state. Worktree/branch policy remains host-owned.

### 7. Preserve hard contracts

#### Haskell Contract Gate

Use Haskell only for a real closed decision, transition, lifecycle, or invariant. Prompt-routed
workflows keep one compact decision truth and no parallel prose router. Audit every stage checkpoint
against the canonical main entry's tagged resume domain; persist `Awaiting` state, reason, and run
identity. A locally closed stage type is insufficient.

#### Runtime Alignment Gate

For `ToolBackedWorkflow`, state the tool contract, invariant boundaries, outcomes, and failure
behavior without copying its branch table. Align persisted schema, normalization, terminal
precedence, and outcomes across harness, runtime, references, and tests.

Each skill remains independently installable: do not require sibling skill files or a centralized
onboard runtime. Skill-specific context and deterministic helpers belong to the owning skill's
`references/` and `scripts/`. Project context belongs in `.codestable/attention.md`,
`.codestable/lessons/`, `.codestable/work/`, or the project's existing docs and ADRs. A v2 skill may
search useful v1 artifacts, but must not execute their tools or treat them as current distribution
surfaces. Shims stay thin. Branch/worktree policy and agent backends remain host-owned.

### 8. Compress, validate, and finish

For continuous evolution, feed every new lesson back through `placeRule`; never treat it as permission
to append prose. Replace obsolete rules, move specialized knowledge to context, and run a whole-file
deletion pass. Additive-only evolution is a failure mode.

Update related skills, shared references, tests, and ADR wording when the changed contract crosses
those boundaries. Do not add changelog or migration narrative to the runtime skill.

Load `references/cs-skill-quality-gates.md` and create a validation plan. Apply its `Regression Ladder`,
`Live Host Safety Gate`, and family coverage as applicable. Structural contracts do not replace
scenario or real runtime conformance tests.

Run relevant repository tests and `git diff --check`. Use `eval-cs-skill` only when the request
explicitly includes a measured multi-model experiment or when release policy requires one.

## Failure Behavior

Return `NeedsHuman` when the target/output is ambiguous, overlapping edits cannot be preserved,
authority boundaries conflict, required context cannot be identified, or the proposed compression
would remove a recovery/safety contract. Report the current target, blocker, preserved files, and
safe next action.

## Output Contract

Report:

- target skill path and `SkillShape`;
- one-sentence responsibility and selected freedom;
- rule placements: kept in harness, moved to stage/project context, mechanized, or removed;
- context plan and collaboration contract, or why none is needed;
- files changed;
- validation results and skipped layers;
- unresolved maintainer decisions and the next concrete action.

Distinguish actual edits from recommendations. Do not claim success from line reduction alone; the
result must remain safe, recoverable, and usable by a fresh agent without chat history.
