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
bug / broken behavior -> cs-issue ----------> cs-code-review (high risk or on demand)
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
- `cs-code-review` is an independent read-only review and also handles module or repository audits.
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
└── work/           # active cross-session work, removed on completion
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
