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
- `cs-epic` maintains one work document for items, dependencies, and acceptance. The owner confirms
  decomposition and boundary changes.
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

## Project Memory

`/cs-onboard` creates this minimal skeleton for a new project:

```text
.codestable/
├── attention.md    # a small set of facts needed every session, at most 25 entries
├── lessons/        # one Markdown file per reusable lesson, searched by keyword
└── work/           # active cross-session work, filenames carry a type prefix feat-/issue-/refactor-/epic-, removed on completion
```

Skill-specific context and helpers belong to the owning skill's `references/` and `scripts/`.
Project facts belong in the structure above or the project's existing docs and ADRs. A skill does not
read sibling skill files or depend on a centralized onboard runtime. Worktree, branch, and agent
backend policy remain host- or owner-controlled.

## v1 Upgrade Boundary

v2 does not migrate or clean historical v1 project directories. Existing requirements, roadmap,
features, issues, compound knowledge, tools, gates, hooks, and manifests remain untouched. New skills
may search those artifacts for project knowledge, but they do not execute the old runtime or produce
new v1 stage artifacts.

The 32 skills in v1.0.4 converge to eight in v2. The other 24 entries are retired and are not installed
with v2. See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the complete mapping.
