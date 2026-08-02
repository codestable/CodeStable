<div align="center">

# CodeStable

**English** · [中文](./README.md)

**Keep boundaries, evidence, and memory intact as AI coding projects evolve.**

<p><img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/> <img src="https://img.shields.io/badge/cs--skills-8-6366F1?style=flat-square" alt="CodeStable Skills"/> <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/></p>
</div>

CodeStable offers lightweight skill contracts for serious software. It does not orchestrate agent teams and does not create a second documentation system. Models act within boundaries, prove results, and return knowledge to existing homes.

## 30-Second Model

```text
User intent
   ↓
cs: execute directly / discuss in this session / advise
   ↓
feat · issue · refactor · epic
   ↓
proportionate verification + necessary review / owner gates
   ↓ code results + the project's canonical knowledge
```

Explicit actions dispatch in the same turn by default; they do not acquire a discussion gate first.

Requests to discuss first converge in the current session and hand off in the same turn.

`cs` aligns facts, language, and boundaries; with existing execution authorization it enters `cs-feat`, `cs-issue`, or `cs-epic`. Discussion itself grants no authorization.

Discussion creates no work cursor or transcript. Unresolved discussion is not recoverable across sessions. Advice requests only advise, and an overview writes no files.

## Start in 5 Minutes

### Install

Codex plugin marketplace:

```bash
codex plugin marketplace add codestable/CodeStable
codex plugin add codestable@codestable
```

Claude plugin marketplace:

```text
/plugin marketplace add codestable/CodeStable
/plugin install codestable@codestable
```

`skills` CLI (v1 users must first follow the [upgrade guide](./UPGRADE.en.md#upgrade-from-v104-to-v2) to remove the 24 retired entries, then install v2):

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable
```

If the catalog misses the plugin entity, use `npx skills@latest add codestable/CodeStable/plugins/codestable --full-depth` as the deep-scan fallback.

### Onboard a Project

Run `/cs-onboard` from the repository root. It creates only the minimal project-memory skeleton and does not take over documentation, worktree, or branch policy.

### Start Working

When you are unsure which entry fits, call `/cs`; you can also call the owning skill directly. v2 ships 8 skills:

| Skill | Purpose |
|---|---|
| `cs` | Route explicit actions, in-session discussion, advice, and system overview |
| `cs-onboard` | Create the minimal project-memory skeleton |
| `cs-feat` | Implement new capability or change existing behavior |
| `cs-issue` | Fix bugs or broken behavior with red-to-green evidence |
| `cs-refactor` | Change structure or performance under equivalence evidence |
| `cs-epic` | Decompose and advance multiple deliverable items under confirmed policies |
| `cs-review` | Read-only leaf executor; one review, with no child agent |
| `cs-keep` | Manage evidence-backed project facts, lesson lifecycle, and canonical homes |

`cs-code-review` is a compatibility alias of `cs-review`. It only forwards and contains no independent rules.

## Three Principles

### 1. thin harness, thick context

CodeStable writes responsibilities for strong models, not step-by-step scripts. Skills constrain goals, hard boundaries, and evidence; models choose paths from repository facts and load guidance on demand.

Thin means no permanent state machine or stage-artifact micromanagement, not no gates.

### 2. Evidence before conclusions

Feature work gets design and verification proportionate to risk; bug fixes go red to green; refactors establish equivalence first. The outer flow creates read-only reviewers.

Humans enter for product-contract changes, major risk, and overall acceptance, not every mechanical step.

### 3. One fact, one canonical owner

Project docs, ADRs, code, and domain documents keep their facts. CodeStable adds only a few session facts, lessons, and active cursors, never a parallel archive.

The owning skill returns conclusions to one home; if none exists, it asks the owner to choose.

## Project Memory

`/cs-onboard` creates:

```text
.codestable/
├── attention.md
├── lessons/
└── work/
```

- `attention.md` holds the small set of project facts needed every session, capped at 25 entries.
- `lessons/` keeps one lesson per file, evolves it through observed / validated / retired, and deduplicates before writing.
- `work/` exists only for active cross-session work, multi-agent handoff, or an explicitly requested durable record.

CodeStable recognizes crystallization moments while working: it observes silently and shows at most one evidence-backed candidate at ordinary completion.

Mechanizable failures go to tests or checkers first. New lessons still require explicit authorization; later sessions validate or retire them after checking current facts.

Ordinary work creates no CodeStable stage docs; the diff, tests, and delivery summary are the evidence. Discussion does not enter `work/`; only stable conclusions graduate through the owning skill to a canonical home.

### The Two-Layer Epic Model

Large initiatives separate durable contracts from temporary execution state. A permanent Epic document owns goals, scope, acceptance, approved items, key decisions, and final delivery.

A temporary work cursor keeps only its pointer, approved revision, progress, policies, and evidence.

An Epic reuses an existing Epic, RFC, or initiative home when available and creates `.codestable/epics/` only on demand. The temporary cursor is deleted at completion; the permanent document remains.

See [WORKFLOW.en.md](./WORKFLOW.en.md) for owner gates, recovery, and terminal rules.

## Fit

CodeStable fits best when:

- software will evolve for months or years;
- later sessions, models, or developers must recover historical constraints accurately;
- AI should execute efficiently while humans retain product boundaries and final acceptance;
- the team values verifiable results, independent review, and reusable knowledge.

It is not:

- a multi-agent team orchestrator or automatic relay platform;
- a process engine that forces every task through one pipeline;
- a replacement for existing project docs, ADRs, issues, or pull requests;
- a necessary dependency for a disposable prototype with no maintenance horizon.

CodeStable can coexist with agent-orchestration tools. It owns task boundaries, evidence, and memory, not how the host organizes agents.

For multi-agent collaboration or independent review by a heterogeneous agent inside a CodeStable flow, use
[cs-agent](https://github.com/codestable/cs-agent-mcp) alongside CodeStable.

## Go Deeper

- [Full workflow and project structure](./WORKFLOW.en.md)
- [Responsibilities of all 8 skills and retired-entry mappings](./SKILL_CATALOG.en.md)
- [Installation upgrades and the v1 project boundary](./UPGRADE.en.md)
- [Why CodeStable exists](./docs/why-codestable.en.md)
- [Roadmap](./ROADMAP.en.md)
- [Version changes](./CHANGELOG.md)

<div align="center">

MIT License · Authors [@liuzhengdong](https://github.com/liuzhengdong), [@dafang](https://github.com/dafang), Codex, and Claude

</div>
