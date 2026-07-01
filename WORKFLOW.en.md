# CodeStable Workflow and Runtime Structure

## Workflow Layers

CodeStable skills are layered and event-driven:

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-roadmap
    │   ├── cs-roadmap-review
    │   └── cs-roadmap-impl-goal
    ├── cs-goal
    ├── cs-feat-design -> cs-feat-design-review -> cs-feat-impl -> cs-code-review -> cs-feat-qa -> cs-feat-accept
    ├── cs-issue-report -> cs-issue-analyze -> cs-issue-fix -> cs-code-review
    ├── cs-refactor / cs-refactor-ff -> cs-code-review
    └── cs-keep / cs-note / cs-docs-neat
```

Vertical means layers, not strict time order. Long-lived archives are refreshed repeatedly; the roadmap layer is entered for large needs, and `cs-goal` is the goal-driven autonomous iteration entry that, given a start point and desired end state, iterates until accepted. Execution is event-driven: new capability goes to feature flow, bugs go to issue flow, and code rot goes to refactor flow; `cs-code-review` is the cross-cutting code review gate that all of feature / issue / refactor pass through to produce `{slug}-review.md`. The cross-cut layer is the knowledge flywheel: any flow sinks reusable experience into compound via `cs-keep`.
`cs-docs-neat` is the phase-close cleanup skill: it reconciles `.codestable/`, README/docs, `CLAUDE.md` / `AGENTS.md`, and agent memory without adding a new archive document type.

## Runtime Structure

After `/cs-onboard`, the project root gets `.codestable/`:

```text
.codestable/
├── requirements/        # requirement docs + domain model: CONTEXT.md glossary + adrs/ ADRs
├── roadmap/
├── goals/
├── features/
├── issues/
├── refactors/
├── audits/
├── brainstorms/
├── compound/
├── tools/
└── reference/
```

Key constraints:

- `requirements/` is a long-lived archive of current state: it holds requirement/capability docs as well as the cs-domain domain model — the `CONTEXT.md` glossary and `adrs/` decision records (split into `CONTEXT-MAP.md` plus per-context subdirectories under multi-context).
- `roadmap/` is the planning layer for large needs; `goals/` holds cs-goal start / iteration / acceptance artifacts.
- `features/`, `issues/`, and `refactors/` use `YYYY-MM-DD-{slug}/` to group one workflow run; `audits/` and `brainstorms/` likewise hold audit and brainstorm artifacts.
- `compound/` is the single knowledge sink; `cs-keep` writes pitfalls / tricks / decisions / research there as plain markdown files retrieved via grep.
- `reference/` is released by `cs-onboard`; cross-skill shared docs must go through project-local `.codestable/reference/`, not direct references to another skill package.
