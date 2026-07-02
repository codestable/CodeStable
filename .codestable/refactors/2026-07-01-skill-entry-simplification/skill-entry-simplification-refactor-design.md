---
doc_type: refactor-design
refactor: 2026-07-01-skill-entry-simplification
status: approved
scope: CodeStable skill entrypoint simplification
summary: Collapse user-facing CodeStable workflows into stable main entries while keeping old stage skills as compatibility entries.
---

# Skill Entry Simplification Refactor Design

## 1. Goal

Simplify the CodeStable skill system from many user-facing stage skills into a smaller set of main workflow entries.

Users should normally call one main skill for a workflow:

- `cs-feat` for feature work
- `cs-issue` for issue fixing
- `cs-refactor` for refactoring
- `cs-docs` for external documentation writing
- `cs-docs-neat` for documentation and memory hygiene
- `cs-epic` for large feature groups
- `cs-code-review` for cross-cutting implementation review
- `cs` only for choosing a main entry

Old stage skills remain available forever as compatibility entries. They must not preserve independent process logic.

## 2. Constraints

- Keep every Markdown file at or below 300 lines.
- When updating skills, also update related skill descriptions and user-facing docs.
- Preserve old skill names so historical users and prompts do not break.
- Do not bulk-migrate historical `.codestable` artifacts.
- Keep `roadmap` as the internal storage/doc_type model for the first `cs-epic` version.
- Do not turn compatibility entries into "please rerun another skill" dead ends; they must continue the current run.

## 3. Decisions From The Design Interview

1. Simplify user-visible entrypoints first; do not force a reduction in physical file count.
2. Keep old stage skills long term, but demote them to compatibility entries.
3. Keep `cs-code-review` as a public cross-cutting gate.
4. Demote `cs-feat-ff` to a compatibility entry for `cs-feat` fastforward mode.
5. Make `cs-issue` the only recommended issue entry; demote `cs-issue-*`.
6. Add `cs-docs` for external documentation writing.
7. Keep `cs-docs-neat` independent; it is a hygiene/sync workflow, not normal doc writing.
8. Add `cs-epic` as the recommended large-demand entry.
9. Keep `cs` as a light router to main entries only.
10. Make `cs-refactor` the only recommended refactor entry; demote `cs-refactor-ff`.
11. Use a uniform compatibility entry template.
12. Compatibility entries load the main protocol file; they do not invoke a second skill command.
13. Compatibility entry `description` should state the workflow/stage intent, not low-level path details.
14. Main entries define `requested_stage` and `requested_mode` semantics.
15. Perform a soft migration: keep old skill names, but move thick rules out of old stage skills.
16. Update user-facing docs and shared conventions; do not rewrite historical artifacts.
17. Main entries are continuous orchestrators with human checkpoints, not unchecked automation.
18. Main entries resume from repository facts first; stage/mode hints are secondary.
19. Add lightweight tests for Markdown line limits, compatibility entries, and skill lists.
20. First implementation includes full rule migration, not just skeletons.
21. `cs-epic` prepares the `/goal` command but does not execute it.
22. User-facing docs use `epic`; internal paths and doc_type may still say `roadmap`.

## 4. Target Shape

### Feature

- Main entry: `cs-feat`
- Compatibility entries: `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff`
- Internal references under `cs-feat/references/`
- `cs-feat` orchestrates design, design review, user approval, implementation, code review, QA, and acceptance.
- `cs-code-review` remains the implementation review authority.

### Issue

- Main entry: `cs-issue`
- Compatibility entries: `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix`
- Internal references under `cs-issue/references/`
- `cs-issue` handles report, analysis, fix, validation, fix note, and code-review handoff.

### Refactor

- Main entry: `cs-refactor`
- Compatibility entry: `cs-refactor-ff`
- Internal references under `cs-refactor/references/`
- `cs-refactor` chooses standard or fastforward mode.
- Fastforward mode is allowed only when behavior is unchanged, scope is small, and tests can self-prove safety.

### Docs

- Main entry: `cs-docs`
- Compatibility entries: `cs-doc-tutorial`, `cs-doc-api`
- Internal references under `cs-docs/references/`
- `cs-docs` covers external tutorial/user-guide and API reference writing only.
- `cs-docs-neat` stays public and independent.

### Epic

- Main entry: `cs-epic`
- Compatibility entries: `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal`
- Internal references under `cs-epic/references/`
- `cs-epic` plans the epic, reviews it, designs child features, prepares the goal execution package, and prints the `/goal` command.
- Storage remains `.codestable/roadmap/{slug}/` for now.

## 5. Compatibility Entry Contract

Each compatibility `SKILL.md` should be short and follow the same pattern:

```markdown
---
name: {old-skill}
description: {Workflow} compatibility entry. Old calls are preserved; execution enters {main-skill} {stage/mode}.
---

# {old-skill}

This skill is a long-term compatibility entry for `{main-skill}`.
It does not maintain independent workflow rules.

Entry intent: `{requested_stage: ...}` or `{requested_mode: ...}`

Execution rules:
1. Load the registered `{main-skill}` skill by skill name as the authoritative main protocol; do not use sibling-directory relative paths as the primary mechanism.
2. Continue this run under that main protocol with the entry intent above.
3. Do not ask the user to rerun `{main-skill}`.
4. If the runtime cannot load the main protocol, stop and report that the compatibility entry cannot continue.
```

Exact wording can vary slightly for `cs-roadmap*` because `cs-epic` is a different name from the historical storage model.

## 6. Main Entry Contract

Each main entry `SKILL.md` should contain:

- Purpose and user-facing workflow boundary
- Supported `requested_stage` values
- Supported `requested_mode` values
- Repository-facts-first resume rules
- Human checkpoints
- Reference loading map
- Completion criteria
- Compatibility entry list

Thick stage details should live in reference files, not in the main `SKILL.md`.

## 7. Implementation Steps

1. Create or revise main entry reference files for feature, issue, refactor, docs, and epic.
2. Rewrite old stage skill files into compatibility entries.
3. Add `cs-docs` and `cs-epic` skill directories.
4. Update `README.md`, `WORKFLOW.md`, `SKILL_CATALOG.md`, and English mirrors when present.
5. Update `plugins/codestable/skills/cs-onboard/references/shared-conventions.md`.
6. Update skill-name allowlists and package checks.
7. Add tests for line limits, compatibility entry shape, and new main entries.
8. Run targeted tests, then the full available test suite.

## 8. Risks

- Rules can be lost during migration if a stage skill is thinned before its content is copied into references.
- Cross-references can drift if README, catalog, workflow, and shared conventions are not updated together.
- `cs-epic` naming can confuse users if docs imply `epic` and `roadmap` are separate concepts.
- Compatibility entries can become unusable if they tell users to manually call the main entry instead of continuing the current run.

## 9. Acceptance Criteria

- Main documentation recommends main entries, not stage skills.
- Compatibility entries remain discoverable but are clearly labeled as compatibility entries.
- No Markdown file exceeds 300 lines.
- New main entries `cs-docs` and `cs-epic` are included in package validation.
- Old stage skill names remain present.
- Thick workflow rules exist under main entry references.
- Tests cover the migration invariants above.

## 10. Amendments (2026-07-02)

Long-range execution supersedes parts of decisions 17 and 21:

1. `cs-feat` keeps one human checkpoint at the design gate. After the user approves the design, it generates a single-feature goal package and runs implementation, code review, QA, and acceptance long-range; ordinary stage blockers are fixed inside the goal loop, and only goal handoff conditions stop for the user.
2. `cs-epic` and `cs-feat` first try to dispatch a **visible Task agent goal driver** (Paseo subagent preferred, then host-native Task/Agent with user-visible run id/status/logs/cancel). Dispatch preconditions include the driver being able to launch independent Task agent reviewers in its own runtime. If no visible or capable driver exists, they print the fenced `/goal` command for the user to paste; they never run the long-range loop silently in the main thread (`cs-epic`) and never auto-execute slash commands.
3. Per-feature user-wait checkpoints convert to written reports/state/evidence in goal mode; design-gate confirmations, contract/scope changes, blocked independent reviewers, and repeated failures still hand off to the user.
