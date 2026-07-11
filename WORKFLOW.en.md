# CodeStable Workflow and Runtime Structure

## Workflow Layers

CodeStable is layered and event-driven. Daily use should start from main entries, not stage skill names.

The root `cs` entry classifies intake mode first. Action requests dispatch to the target skill in the current run; advice requests only recommend. Overview requests do not start downstream workflows, and ambiguous requests stop for one focused question.

The main-entry relationships are:

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-epic
    │   └── internally uses the roadmap storage model and goal package
    ├── cs-goal
    ├── cs-brainstorm
    ├── cs-feat -> cs-code-review
    ├── cs-issue -> cs-code-review
    ├── cs-refactor -> cs-code-review
    ├── cs-docs
    ├── cs-feedback
    └── cs-keep / cs-note / cs-docs-neat
```

The vertical layout is layering, not strict time order. Long-lived records are refreshed repeatedly; `cs-epic` is only for large demands and still writes `.codestable/roadmap/` in the first version; `cs-goal` is the autonomous goal workflow.

The event entries are `cs-feat` for new capability, `cs-issue` for bugs, `cs-refactor` for behavior-preserving cleanup, and `cs-docs` for outward documentation. `cs-code-review` remains the cross-cutting implementation review gate.

The knowledge and feedback loop remains cross-cutting: `cs-keep` compounds knowledge; explicit `cs-feedback` calls produce local-private incidents/triage and require separate preview confirmation before upload; `cs-docs-neat` handles milestone hygiene.

Old stage skills remain long-term compatibility entries:

- Feature: `cs-feat-design` / `cs-feat-design-review` / `cs-feat-impl` / `cs-feat-qa` / `cs-feat-accept` / `cs-feat-ff`
- Issue: `cs-issue-report` / `cs-issue-analyze` / `cs-issue-fix`
- Refactor: `cs-refactor-ff`
- Docs: `cs-doc-tutorial` / `cs-doc-api`
- Epic: `cs-roadmap` / `cs-roadmap-review` / `cs-roadmap-impl-goal`

## Runtime Structure

After `/cs-onboard`, the project root contains `.codestable/`:

```text
.codestable/
├── requirements/        # requirements + domain model
├── roadmap/             # internal storage model for epic
├── goals/
├── features/
├── issues/
├── refactors/
├── audits/
├── brainstorms/
├── feedback/
├── compound/
├── tools/
└── reference/
```

Key constraints:

- `requirements/` stores long-lived current-state facts and the domain model.
- `roadmap/` remains the internal planning layer used by `cs-epic`; user-facing docs call it epic, but historical paths/doc_type are not migrated yet.
- `features/`, `issues/`, and `refactors/` use `YYYY-MM-DD-{slug}/` directories.
- `compound/` is the only knowledge compounding directory, written by `cs-keep`.
- `reference/` is released by `cs-onboard`; shared workflow conventions are read from project-local `.codestable/reference/`.
