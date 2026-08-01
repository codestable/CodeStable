# CodeStable v2 Workflow and Project Structure

## Workflow

CodeStable v2 consists of eight independently installed thin-harness skills and a project-memory
loop. `cs` classifies what the user wants right now: clear action requests dispatch to the target
skill in the same turn and continue executing; advice requests get a recommendation only; with no
request it presents the overview.

```text
unsure which entry    -> cs
onboard / v1 upgrade  -> cs-onboard
new capability        -> cs-feat ---------\
bug / broken behavior -> cs-issue ----------> cs-review (high risk or on demand)
equivalent refactor   -> cs-refactor ------/
large initiative      -> cs-epic -> cs-feat / cs-issue / cs-refactor
lessons and memory    -> cs-keep
```

Execution strength follows risk:

- `cs-feat` normally understands, implements, and verifies directly. Public contracts, data,
  authorization, concurrency, or real design tradeoffs require owner confirmation first.
- `cs-issue` establishes a reliably failing check before changing code, then proves it turns green.
- `cs-refactor` establishes equivalence evidence first and keeps verification green after each step.
- `cs-epic` keeps approved delivery contracts in a permanent Epic document and active execution in
  a temporary work cursor. Decomposition, contract changes, and overall acceptance each cross an owner gate.
- When independent review is needed, the outer workflow creates the reviewer. That reviewer runs
  `cs-review` once and does not create another agent before returning a result.
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
  explicit range/patch for diff review, freeze the document version for design review, and freeze a
  commit plus scope for audit. It does not move that target or its worktree until the reviewer returns;
  a changed target invalidates the round.
- `cs-review` is a read-only leaf executor for change, module, or repository review. The outer
  workflow owns fixes and any later review round.
- With blocking findings or important findings not explicitly accepted by the user, do not commit the
  current candidate or create a formal milestone. After fixes, verify, freeze a new target, and use a
  fresh reviewer. A formal semantic milestone requires the review gate plus existing commit authorization;
  a WIP/checkpoint exists only for recovery or an isolated baseline and does not mean approval.
- An Epic advances one confirmed item at a time. Start the next item only after the current one reaches
  its milestone. Without commit authorization, deliver the checkpoint for an owner decision instead
  of accumulating multiple items in one diff.
- A healthy running reviewer remains bound to its run and target.
  When Awaiting carries the same queryable run identity and remains active, keep waiting;
  discovering a better creation method later does not justify cancellation, duplicate creation, or parallel
  dispatch. Only terminal failure without a report, an unrecoverable run identity, a capability mismatch,
  or target invalidation fails the delegation; it does not consume a review round. The outer workflow diagnoses
  before a bounded retry, creation-method switch, or escalation; it never blindly resends the task.
- `cs-keep` compresses frequently needed facts into attention and reusable experience into lessons.

Ordinary work creates no stage artifacts. The diff, test output, and delivery report are the evidence.
Create one work document only for cross-session work, multi-agent handoff, or an explicit request for
a durable record; remove it when complete unless the owner asks to retain it.

## Epic Lifecycle

An Epic separates durable product intent from temporary execution state and keeps one fact owner:

- The **permanent Epic document** reuses an existing Epic, RFC, or initiative home when the project
  has one. Otherwise, create `.codestable/epics/{slug}.md` on demand for the first Epic;
  `cs-onboard` does not precreate `.codestable/epics/`. This document alone owns the starting point,
  goals, scope, non-goals, acceptance criteria, approved items with stable IDs/dependencies/acceptance
  points, key decisions, final delivery index, overall acceptance, residual risks, and durable `status`.
- The **temporary execution cursor** at `.codestable/work/epic-{slug}.md` stores only the permanent
  document pointer, `approved_revision`, execution `phase`, current item ID, per-ID progress, next action,
  `blocked_by`, temporary decisions, and evidence/commit pointers. It must not duplicate goals,
  acceptance criteria, item definitions, or final conclusions. After owner confirmation, the full
  permanent-document SHA-256 fixes the approved revision. The active permanent document stays frozen;
  routine progress changes only the cursor.

An Epic retains three owner gates:

1. The current outer workflow first creates a fresh reviewer for design review of the proposed
   decomposition. After findings are handled, the owner confirms goals, boundaries, acceptance, and
   item contracts before execution starts.
2. Changes to goals, scope, non-goals, acceptance, item membership/definitions, or major risks update
   the permanent document and require a fresh review plus owner reconfirmation. In-boundary technical
   choices and ordering adjustments that do not change dependencies or acceptance add no gate.
3. After every item and integration verification complete, the cursor enters acceptance. The current
   outer workflow creates a fresh reviewer for a final acceptance review against the latest owner-approved
   criteria. Passing that gate does not replace the owner's final acceptance.

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
