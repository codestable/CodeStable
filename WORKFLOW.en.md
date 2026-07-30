# CodeStable Workflow and Runtime Structure

## Design principle: thin harness, thick context

Rules stay minimal: skills carry engineering experience (when to do what, and why) plus a few hard gates — no process state machines. The route belongs to the model; state is recovered from repository facts. Context is retrieved on demand: before acting, grep the project's accumulated knowledge by task keywords and report the sources of any hits.

## Workflow

```text
cs (overview)
cs-onboard (skeleton)
cs-feat / cs-issue / cs-refactor (event entries) ──> cs-code-review (independent review: designs and changes by default, trivial edits may skip)
cs-epic (large-requirement decomposition, sub-items go through event entries)
cs-keep (wrap-up distillation; every entry has a built-in recommendation moment)
```

All entries share one execution mainline: **understand the relevant facts → act → run proportionate verification → deliver the result**. Risk is re-judged per request from current facts — no persistent lanes. Escalation signals (public contracts / data / permissions / real trade-offs / large diffs / explicit user request) require design alignment before acting: the proposal passes an independent agent design review (fix-and-rereview capped at 2 rounds; beyond that, escalate with the disagreement) and is then confirmed by the user. Design and final-acceptance confirmations must never be auto-approved by the model; completed changes get an independent review by default; claiming completion requires verifiable evidence.

## Persistence

Ordinary tasks produce zero CodeStable artifacts — the git diff, test output, and delivery summary are the evidence.

```text
.codestable/
├── attention.md    # project facts to read every session, ≤25 entries
├── lessons/        # distilled experience, one markdown file per lesson, grep-searchable
└── work/           # active cross-session tasks only, one doc per task (goal/context/boundaries/evidence/acceptance/status-and-open-items), compressed and deleted on completion
```

Lesson discipline: never write without traceable evidence; grep for same-domain entries first and merge instead of duplicating; a soft cap of ~50 lessons forces consolidation before addition.

## v1 compatibility

v1 artifacts in existing projects (`requirements/`, `roadmap/`, `features/`, `issues/`, `compound/`, `reference/`, `tools/`, etc.) are kept read-only — never migrated or deleted; legacy knowledge stays covered by the same grep retrieval. v1 gates and runtime tools are no longer invoked by skills.
