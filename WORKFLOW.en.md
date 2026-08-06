# CodeStable v2 Workflow and Project Structure

## Workflow

CodeStable v2 consists of eight independently installed thin-harness skills and a project-memory
loop. `cs` classifies whether the user wants execution, discussion first, advice, or an overview.
Explicit action dispatches in the same turn by default; a discussion-first request converges in the
current session and hands off under existing authorization; advice only recommends, and a request
without a task gets an overview.

```text
unsure which entry    -> cs
discuss / align first -> cs -> cs-feat / cs-issue / cs-epic
onboard / v1 upgrade  -> cs-onboard
diagnose / investigate -> cs-issue (no product diff; no change review)
new capability -> cs-feat
authorized repair of bug / performance regression / broken behavior -> cs-issue
equivalent refactor -> cs-refactor
large initiative      -> cs-epic -> cs-feat / cs-issue / cs-refactor
independent review / audit -> cs-review
lessons and memory    -> cs-keep
```

### In-session discussion and handoff

- Explicit action dispatches in the same turn by default. Only when the user explicitly asks to discuss first
  does that request override the default. Discuss may also start when repository facts still cannot identify the
  action type or owning skill and a product decision would materially change whether the flow documents or edits
  code. Once the owning skill is known, its own intake refines goals, boundaries, and acceptance.
- Discussion exists only in the current session. The agent investigates facts available from the repository,
  asks one real owner decision at a time, and tests shared language with concrete scenarios and boundaries.
  It does not create a discussion work cursor or transcript. Unresolved discussion is not recoverable across sessions.
- When handoff-ready, the in-memory packet carries the target entry, original request, goal or expected behavior,
  scope, non-goals, acceptance, verified repository facts and sources, owner decisions, unresolved risks, and
  asset pointers. With existing execution authorization, it hands off in the same turn to `cs-feat`, `cs-issue`,
  or `cs-epic` and must not ask whether to continue. Discussion itself creates no authorization. The handoff does
  not expand authorization or replace the owning skill's review, verification, or owner gates.
- Raw questions, answers, unresolved discussion, and candidate branches are not persisted. Stable terms graduate
  to the project's existing canonical terminology home. A structural choice becomes an ADR only when it is hard
  to reverse, surprising without context, and the result of a real trade-off. The owning skill graduates task
  contracts, permanent Epics, attention, and lessons under existing rules; no parallel truth is invented. When no
  canonical home exists, ask the owner to choose one.
- Outside the three confirmed handoff targets, outcomes use `cs`'s existing Execute / Advise rules and receive no
  duplicate-confirmation privilege. When only discussion is authorized, `cs` returns the confirmed conclusions
  and recommends `cs-keep` or the owning skill for asset graduation.

### Shared Language

Shared language is a conditional design discipline, not a fixed phase for every task:

- Ordinary changes that reuse existing unambiguous terms add no artifact, question, or gate. It activates only when a new or overloaded term or a neighboring concept boundary can change goals, behavior, ownership, factual
  authority, lifecycle, contracts, or acceptance.
- A Feature requires local semantic clarity: a canonical name, tight definition, excluded meaning, and one boundary scenario keep implementation, API, schema, docs, and tests aligned.
- An Epic requires conceptual-system clarity: cross-concept relationships, authority, and invariants live in the permanent Epic and form part of Route Clear.
- The agent verifies repository facts; product meaning and concept boundaries enter HITL after facts, options, and trade-offs are explicit. This is not a new owner gate and does not offload researchable facts.
- Stable domain terms use existing canonical domain docs; architecture roles stay in the current design. Without a home, definitions stay in the task packet or permanent Epic with a suggested destination that does not block
  delivery and does not automatically create `CONTEXT.md` or a parallel glossary.
- Design / contract review checks define-before-use, one meaning per term, and scenario consistency, but cannot prove owner understanding. A post-review terminology question that exposes a contract-level mismatch means the
  candidate is not clear; explaining an implementation detail alone does not reopen design.

Task type determines the engineering method; actual risk determines assurance strength:

```text
Execution flow = minimum complete loop + the least assurance required by each unexcluded risk
```

Independent review is not a default step. Each risk adds only the assurance directly required by that risk.

Before selecting the minimum complete loop, perform one silent, bounded check against the goal and the
paths, symbols, trust boundaries, and effects outside the codebase that the change is expected to or actually
does touch. This check creates no itemized report or artifact. If a risk still cannot be ruled out after the
least-cost targeted check, treat it as present or continue targeted diagnosis until it can be decided; not noticing a risk is not a valid reason to lower assurance. Size is
only evidence about impact: line count, file count, prose versus code, and task kind do not replace semantic risk.

Add only the assurance directly required by each risk fact:

- An uncertain goal, root cause, or implementation direction, or a real trade-off that changes the result -> targeted diagnosis, a question, or design; obtain owner confirmation when the owner must choose.
- A change that breaks compatibility or changes a public contract used by multiple consumers -> contract confirmation, matching contract tests, and canonical documentation; add independent review when compatibility
  or consumer impact remains uncertain.
- A change that changes authorization, security, privacy, or another trust boundary -> targeted threat/security evidence and independent review; obtain confirmation when the owner's authorization boundary changes.
- A change that changes persisted data, schema, or a migration path -> compatibility/migration verification, applicable backup and rollback/recovery evidence, and independent review; confirm destructive or irreversible work.
- A change that changes concurrency, ordering, or consistency semantics -> matching race/order verification and independent review; confirm when the semantics involve a trade-off.
- A change that creates an irreversible effect outside the codebase -> confirm before execution, provide applicable dry-run, idempotency, compensation, or recovery evidence, and add independent review.
- Work that addresses a performance regression or changes a performance-sensitive path -> targeted profiling, a baseline, or a before/after comparison; add independent review only when SLO, cost, or propagation is material
  or uncertain.
- A change that has broad impact or can propagate failure across modules -> expand to affected regression checks; add a full suite or independent review only when consumer/failure scope remains uncertain or failure cost is high.

When the user says “flow is too heavy / this is only a small change / documentation exceeds the code,” this triggers
a reassessment of risk and assurance, not an unconditional bypass of safety gates. Stop adding artifacts and
recalculate; keep a gate only by naming the concrete risk that prevents lowering it. Continuity needs are not risk
gates: cross-session work, multi-agent handoff, or an explicit request for a durable record adds only one temporary
work cursor. Ordinary work uses the lowest-cost authoritative targeted verification and does not automatically stack
a full suite, browser smoke, or independent review.

- `cs-feat` starts with the minimum complete loop and adds assurance only for the risk facts above;
  it asks for confirmation only when an owner choice is required.
- `cs-issue` first establishes a repeatable failure signal for the user's actual symptom. A diagnosis-only request leaves
  zero product changes and reports a confirmed root cause, falsifiable hypothesis, or insufficient evidence; once repair
  is authorized, the same signal must go from red to green.
- `cs-refactor` establishes equivalence evidence first and keeps verification green after each step; once all steps are
  done it runs a regression covering affected call sites and modules, and only a full suite is added when an independent
  risk requires it.
- A performance regression or anomalous slowdown enters `cs-issue`; without an existing failure, proactive optimization
  under behavioral equivalence remains in `cs-refactor`.
- `cs-epic` keeps approved delivery contracts in a permanent Epic document and active execution in
  a temporary work cursor. Decomposition, contract changes, and overall acceptance each cross an owner gate.
- When independent review is needed, the outer workflow creates the reviewer. That reviewer runs
  `cs-review` once per round and does not create another agent before returning a result. Each independent
  review stage starts with one fresh reviewer. Reviewer independence means independence from the implementer,
  not amnesia about its own prior review.
- A review stage is defined by one review purpose. Design review, change review, contract review, and Epic final acceptance are
  separate stages. Only re-review driven by fixes for that stage's findings remains in the same stage and reuses
  its reviewer lineage; a changed review purpose starts a new stage.
- Before creating a reviewer, the current workflow discovers the subagent creation and management
  capabilities callable in the current session. It first follows explicit creation-method/model
  constraints in project context. After meeting the review quality floor, it prefers an agent
  heterogeneous to the implementer and explicitly selects the strongest stable model. Reviewer creation
  methods prefer managed structured delegation, then a host subagent. A bounded local agent CLI is only a fallback.
  When no qualified heterogeneous candidate exists, fall back to the strongest stable homogeneous model;
  never rely on a default model. A PATH executable scan is not capability discovery. Exact backend and model
  constraints belong to project context, not to a shipped skill. Record the final creation method, agent/model,
  and fallback reason in the task packet.
- Before dispatch, the outer workflow must freeze an explicit review target: prefer a staged diff or
  explicit range/patch for diff review; design review may freeze an existing repository design document
  or verbatim design text + SHA-256 in the task packet; audit freezes a commit plus scope. With the packet
  form, the first round sends the text and hash verbatim, and the reviewer reviews that text as the target;
  a finding-driven follow-up carries the latest full text, previous and current hashes, and repair summary.
  It does not move that target or its worktree until the reviewer returns; a changed target invalidates the round.
- `cs-review` is a read-only leaf executor for change, module, or repository review. The outer
  workflow owns fixes and any later review round.
- With blocking findings or important findings not explicitly accepted by the user, do not commit the
  current candidate or create a formal milestone. After finding-driven fixes, rerun verification, freeze a
  new complete target, and continue through a follow-up in the same reviewer's same session. The re-review
  examines the complete current candidate and the repair delta, classifies prior findings as resolved or
  unresolved, and reports new findings; it cannot be a checklist-only pass.
- A review stage allows at most three completed rounds with terminal reports. Replacing a reviewer does not reset that count.
  Replace one only when the original run/session fails or cannot be recovered, capability is insufficient,
  the target, scope, design, or core path changes materially, the reviewer says it can no longer judge
  independently, or the owner requests a second opinion. A replacement starts fresh. Complete the selected
  assurance first. A review gate is required only when review was actually triggered, and a formal semantic
  milestone also requires existing commit authorization; a WIP/checkpoint exists only for recovery or an isolated
  baseline and does not mean approval.
- With `continuous` or `per-item`, an Epic allows only one `current_item` at a time. This is a serialization constraint, not a per-item owner gate.
  Under the continuous policy, an ordinary item milestone advances automatically; it must not ask whether
  to continue to the next item or return as a terminal result. Per-item pauses require an explicit owner policy
  or a real gate. Under `parallel`, the main workflow stays the sole orchestrator and cursor writer, advancing dependency-independent items concurrently and serializing integration and milestones.
- A healthy running reviewer remains bound to its run and target.
  When Awaiting carries the same queryable run identity and remains active, keep waiting;
  discovering a better creation method later does not justify cancellation, duplicate creation, or parallel
  dispatch. Only terminal failure without a report, an unrecoverable run identity, a capability mismatch,
  or target invalidation fails the delegation; it does not consume a review round. The outer workflow diagnoses
  before a bounded retry, creation-method switch, or escalation; it never blindly resends the task.
- `cs-keep` compresses frequently needed facts into attention, stages experience without a stronger owner as
  lessons, and graduates it to mechanical guards, project docs, or ADRs.

Ordinary work creates no stage artifacts. The diff, test output, and delivery report are the evidence.
Create one work document only for cross-session work, multi-agent handoff, or an explicit request for
a durable record; remove it when complete unless the owner asks to retain it.

## Project-Local Continuous Learning

- Each task skill observes silently during the task. Read-repair performs one bounded, lowest-cost targeted check
  against existing code, tests, or canonical docs; it must not run broad tests or repeat reproductions solely to
  verify a lesson. If that check is insufficient, it skips the lesson without blocking the task. It reports
  `lesson hit: {path} ({status}); check: {fact}; impact: {plan_or_check}` only when current facts hold and the
  lesson changes the plan or verification, or explicitly rules out a concrete, plausible wrong path; keyword
  overlap alone is not reuse.
- A crystallization candidate exists only in the current session. Ordinary work shows at most one candidate and
  stays quiet without a strong signal. Epic items add no pause: each may place one deduplicated candidate in the
  existing cursor evidence, and the final graduation list handles them together.
- The lesson lifecycle is observed / validated / retired. A new lesson starts observed and reaches validated only
  after successful use in an independent later task that records the lesson-caused plan or verification change,
  or the concrete plausible wrong path it ruled out, together with the task's passing acceptance evidence. It
  becomes retired when facts contradict it, its scope expires, or a stronger owner exists.
- Read-repair permits only narrow state maintenance on an existing matched lesson; stable validated hits create
  no file churn. New lessons still require explicit authorization, as do rule/scope rewrites, promotion, deletion,
  and cross-project sharing; none may be inferred from task-execution authorization.
- Put mechanical guards first: when an in-scope test, checker, lint, type, or helper can prevent recurrence, do
  not write a duplicate lesson. Experience converges on one canonical owner and does not save transcripts,
  per-hit logs, or background telemetry.

## Epic Lifecycle

An Epic separates durable product intent from temporary execution state and keeps one fact owner:

When the route is still unclear during `proposed + planning`, `cs-epic` performs pre-approval route discovery:

- The permanent Epic document is the only route document; during proposed, the permanent Epic document itself is the route map.
  Precisely stated route questions go under Decisions pending with a readable name, `AFK|HITL`, dependencies, and
  a resolution method. The frontier is derived only from pending decisions whose dependencies are resolved; it is
  not stored as another state or list. Route-level fog that cannot yet be stated precisely goes under Still unclear.
  This does not add issues, a separate map artifact, or a third state system.
- The agent resolves AFK facts. Only product judgment, user preference, external authority, or a real trade-off
  enters HITL. The agent first supplies facts, options and trade-offs, a recommendation, and the route impact, but
  must not answer a HITL question for the owner or treat silence as a choice. Only one HITL frontier decision is
  presented at a time. HITL is not a new owner gate and does not approve the Epic. No unresolved HITL node may
  remain at route clear. A still-valid HITL node must be explicitly resolved by the owner or moved out of scope with
  the owner's explicit confirmation; the agent must not unilaterally declare it out of scope or invalid; a prerequisite
  involving external authority or side effects still requires separate permission or confirmation.
- A resolved node moves from Decisions pending to key decisions; newly visible fog becomes a decision, and work
  outside the destination becomes a non-goal before the frontier is derived again. Decision questions are not
  copied one-for-one into execution items. The work cursor keeps only the current frontier decision name, next
  action, blockers, and evidence pointers; before the route is clear, `current_item` stays `null`.
- The route is clear, reviewable, and executable only when remaining unknowns cannot change goals, scope,
  non-goals, acceptance, item boundaries, dependencies, or major risks, and stable-ID item contracts name the
  owning skill, dependencies, and acceptance. Route clear is not a new owner gate; the complete proposed Epic
  then enters the existing design review and first owner confirmation.
- Skip route discovery when the route is already clear, only one local technical unknown remains, or the only
  reason is high risk, file count, or cross-session continuity. The relevant owning skill handles local design
  and assurance.

- The **permanent Epic document** reuses an existing Epic, RFC, or initiative home when the project
  has one. Otherwise, create `.codestable/epics/{slug}.md` on demand for the first Epic;
  `cs-onboard` does not precreate `.codestable/epics/`. This document alone owns the starting point,
  goals, scope, non-goals, acceptance criteria, approved items with stable IDs/dependencies/acceptance
  points, key decisions, final delivery index, overall acceptance, residual risks, and durable `status`.
- The **temporary execution cursor** at `.codestable/work/epic-{slug}.md` stores only the permanent
  document pointer, `approved_revision`, execution `phase`, current item ID, per-ID progress, next action,
  `blocked_by`, `item_progression`, `milestone_commit`, `remote_publish`, the `active_items` recovery records under `parallel`, temporary decisions, and
  evidence/commit pointers. It must not duplicate goals, acceptance criteria, item definitions, or final
  conclusions. After owner confirmation, the full permanent-document SHA-256 fixes the approved revision.
  The active permanent document stays frozen; routine progress and execution policies change only the cursor.

An Epic retains three owner gates:

1. The current outer workflow first creates a fresh reviewer for design review of the proposed
   decomposition. After findings are handled and re-reviewed in the same lineage, the owner confirms goals,
   boundaries, acceptance, and item contracts before execution starts.
2. During execution, after the permanent document has been approved, changes to goals, scope, non-goals,
   acceptance, item membership/definitions, or major risks update the permanent document. These contract changes
   start a separate contract-review stage with a fresh reviewer and require owner reconfirmation. In-boundary
   technical choices and ordering adjustments that do not change dependencies or acceptance add no gate.
3. After every item and integration verification complete, the cursor enters acceptance. Final acceptance is
   a separate review stage: the current outer workflow starts a new fresh-reviewer lineage instead of reusing an
   item, design-review, or contract-review lineage, and reviews against the latest owner-approved criteria. Passing that gate does
   not replace the owner's final acceptance.

The first gate determines item progression, milestone commit, and remote publication policies once. Approving
the decomposition does not itself grant version-control authorization. Store those policies in the work cursor
and reuse them on recovery; only missing or invalid values pause once for repair. An owner-explicit policy change
updates only the cursor, not the approved hash. `milestone_commit: manual` requires
`item_progression: per-item` and `remote_publish: manual`; `remote_publish: each-milestone` requires
`milestone_commit: authorized`; `item_progression: parallel` requires `milestone_commit: authorized`.

With `item_progression: continuous`, after a non-final item completes, choose the first incomplete item in
permanent-document order whose dependencies are satisfied and continue in the same entrusted workflow. An
ordinary item completion is not an owner gate; the workflow must not ask whether to continue to the next item
or return that completion as terminal. With `per-item`, pause under the recorded per-item checkpoint policy.
Owning-skill gates, important findings requiring owner acceptance, real blockers, new authorization, and the
final owner gate may still pause execution. With `parallel`, workers execute dependency-independent items in host-provided isolated workspaces while the main workflow remains the sole cursor writer and serializes integration: it merges each delivery without advancing mainline history, re-verifies on the merged result, and only then creates the semantic milestone; when isolation or every qualified worker-creation capability is unavailable, execution degrades to serial within the session without changing the recorded policy, and parallel execution adds no owner gate (see `references/parallel-execution.md` in `cs-epic`).

With `remote_publish: each-milestone`, publish after every semantic commit using the branch/remote policy
already selected by the project, host, or owner. With `final`, publish once after integration verification and
the final acceptance review pass, before requesting the owner's final acceptance. With `manual`, the agent does
not publish remotely. An unspecified branch/remote or a publication failure records a blocker and pauses; the
agent neither chooses a policy nor continues silently.

After owner acceptance, complete the permanent Epic's final scope, key decisions, delivery index,
acceptance evidence, and residual risks; then set `accepted`, remove its work pointer, and delete the Epic
and child-item cursors. Never delete the permanent Epic document. Finish `superseded` and `cancelled`
states idempotently without resuming execution or creating a duplicate Epic. Do not restore the `cs-goal`
entry, goal package, `state.yaml`, per-iteration reports, or legacy runtime gates.

## Project Memory

`/cs-onboard` creates this minimal skeleton for a new project:

```text
.codestable/
├── attention.md    # a small set of facts needed every session, at most 25 entries
├── lessons/        # one Markdown file per reusable lesson, searched by keyword
└── work/           # active cross-session work, filenames carry a type prefix feat-/issue-/refactor-/epic-, removed on completion
```

Skill-specific context and helpers belong to the owning skill's `references/` and `scripts/`.
Project facts belong in the structure above, an on-demand permanent Epic home, or the project's existing
docs and ADRs. A skill does not read sibling skill files or depend on a centralized onboard runtime.
Worktree, branch, and agent backend policy remain host- or owner-controlled.

## v1 Upgrade Boundary

v2 does not migrate or clean historical v1 project directories. `.codestable/roadmap/`,
`.codestable/features/`, `.codestable/issues/`, `.codestable/refactors/`, `.codestable/goals/`,
`.codestable/compound/`, `.codestable/audits/`, `.codestable/brainstorms/`, and
`.codestable/feedback/` are read-only historical knowledge sources. The four owning task skills
(`cs-feat`, `cs-issue`, `cs-refactor`, and `cs-epic`) cover all nine by task keyword and cite matching
source paths. Other skills retrieve only historical sources explicitly named by their own contracts;
for example, `cs-keep` reads `compound/` for deduplication. No skill may generate into, rewrite in place,
or bulk-migrate these v1 sources.

An existing `.codestable/requirements/` may be maintained only when `.codestable/attention.md` explicitly
records it as the canonical requirement location. When the owner first selects it, record that project fact
in attention before maintenance. Without that explicit record it remains read-only historical knowledge,
and v2 does not create the directory by default. New projects keep requirements in their own documentation
structure; when no canonical home exists, ask the owner to choose one and record it in attention. Until then,
keep stable contracts in the permanent Epic. `reference/`, `tools/`, `gates/`, `hooks/`, and
`runtime-manifest.json` remain only for legacy compatibility; v2 does not execute the old runtime.

The 32 skills in v1.0.4 converge to eight in v2. The other 24 entries are retired and are not installed
with v2. See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the complete mapping.
