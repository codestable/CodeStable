<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-1-6366F1?style=flat-square" alt="Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## Install

Codex plugin marketplace:

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable
codex plugin add codestable-lite@codestable-lite
```

If `codestable-lite` has not merged into the default branch yet, Codex can install from that branch directly:

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable --ref codestable-lite
codex plugin add codestable-lite@codestable-lite
```

For local development, Codex can also add a local marketplace path:

```bash
codex plugin marketplace add D:\playground\CodeStable
codex plugin add codestable-lite@codestable-lite
```

Claude plugin marketplace:

```text
/plugin marketplace add liuzhengdongfortest/CodeStable
/plugin install codestable-lite@codestable-lite
```

Note: Claude remote marketplaces read `.claude-plugin/marketplace.json` from the GitHub repository's default branch. If `codestable-lite` still lives only on a non-default branch, test it from a local checkout first:

```bash
git clone -b codestable-lite git@github.com:liuzhengdongfortest/CodeStable.git CodeStable-LITE
```

```text
/plugin marketplace add ./CodeStable-LITE
/plugin install codestable-lite@codestable-lite
```

You can also use the skills CLI:

```bash
npx skills@latest add liuzhengdongfortest/CodeStable
```

Use the single entry to onboard a project:

```bash
/cs onboard CodeStable in this project
```

Use that same entry for requirements, specs, bugs, issue implementation, closing, and knowledge capture:

```bash
/cs
```

`cs` determines whether the current knowledge belongs to the project spec, an epic spec, or an issue, loads the relevant internal rules, and executes the work currently authorized.

The CodeStable LITE plugin packages one skill at `plugins/codestable-lite/skills/cs/`; action rules, design principles, templates, and scripts load progressively inside it. The released version lives in `VERSION`, with release notes in `CHANGELOG.md`.

## Upgrade

After a new release, check `CHANGELOG.md` for the version change, then refresh through the entry you installed from.

Before publishing to Claude users, `.claude-plugin/marketplace.json`, `plugins/codestable-lite/`, and `VERSION` must be on the repository's default branch, or the LITE package should move to a separate repository whose default branch is LITE.

Codex plugin marketplace:

```bash
codex plugin marketplace upgrade codestable-lite
codex plugin add codestable-lite@codestable-lite
```

Claude plugin marketplace:

```text
/plugin marketplace update
/plugin update codestable-lite@codestable-lite
```

skills CLI:

```bash
npx skills@latest update
```

---

## Why

I was building a new harness agent ([MA](https://github.com/liuzhengdongfortest/MA)) — vibe-coding at first, just writing designs and requirements while AI wrote the code. It carried most features, until Codex repeatedly failed on a problem I thought was simple, making the same mistake in the same place. That's when I knew the project needed a workflow to keep moving.

I surveyed OpenSpec, SuperPowers, Oh-My-OpenAgent — none felt right:

- **OpenSpec** — too thin, no compounding, specs too abstract for humans to read
- **SuperPowers** — no process discipline, you never know which one to use
- **Oh-My-OpenAgent** — too heavy, philosophically treats "human intervention = failure"

CodeStable's goal is **to solve real software implementation and coding problems for serious engineering** — not to coin a new term or chase trends.

---

## The core difference: what gets orchestrated

Mainstream AI coding frameworks — Superpowers, CCW, Oh-My-OpenAgent — are all doing **the same thing**:

> **Orchestrating agents better.** Get them to team up, collaborate, brainstorm, run pipelines, hand off automatically. The entity at the center is always the **Agent**.

CodeStable goes the **other way**:

> **What gets orchestrated isn't agents — it's the lifecycle of the software itself.** The entities at the center are **the elements that make up software**: every change, every trade-off, every rejected alternative, every constraint left in history.

<table>
<tr><th></th><th>Agent-orchestration camp</th><th>CodeStable</th></tr>
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Project spec · epic spec · issues</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How does the software's current truth, change lines, and closeable work get organized, advanced, and sunk?</td></tr>
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>The <code>.cs/</code> file tree (readable by both humans and AI)</td></tr>
<tr><td><b>Pain it solves</b></td><td>One agent isn't enough; need coordination to scale</td><td>Software complexity overflows context; tacit knowledge gets lost; requirements drift</td></tr>
<tr><td><b>Role of humans</b></td><td>The less the better — full automation is the ideal</td><td>Human-in-the-loop — the programmer owns the whole; AI is an efficient executor</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)

**Neither direction is wrong.**

If your task is "run an end-to-end automated pipeline with AI" or "have multiple agents debate a plan," the agent-orchestration camp fits better.

If your task is "maintain serious software that iterates over years" or "make sure a requirement written today can still be accurately recalled three months later" — then CodeStable's software-element-centric model fits better.

I built CodeStable because I believe **the chaos of software engineering isn't really about agents not being strong enough — it's about elements not being organized**. No matter how strong the agent, it can't save a project that's lost its requirements, trade-offs, and history.

---

## Design: project spec + epic spec + issues

Early CodeStable split development into 6 entities and 3 pipelines. After further compression, the core is three things: the project mainline truth, large-change lines, and closeable execution slices.

### project spec — the mainline truth

The project spec lives in `.cs/spec/`. It is written for a developer entering the project for the first time: what the project is, where it is going, how requirements expand, how architecture expands, and where shared language lives. It is a tree, not a two-level directory; each `index.md` gives orientation first, then points to child documents.

Shared language belongs in the nearest `index.md` where it applies, not in a separate domain hierarchy. A spec does not record change logs; it explains why the current design, boundaries, and trade-offs stand.

### epic spec — a large-change line

Large changes live in `.cs/epics/YYYY/MM/DD/{短语}/spec.md`. That file is the epic's single authoritative entry and carries status, current requirements, architecture considerations, ready scope, issue links, blockers, close conditions, and graduation candidates. If implementation discovers additions, changes, or reversals, update the same epic spec instead of splitting truth across `index.md`, `plan.md`, or a `changes.md` log.

Issues under an epic close back into the epic spec first. Only when a human confirms the whole epic is done does AI merge the graduated conclusions back into the project spec.

### issues — closeable execution slices

Small bugs, small features, and local chores do not need an epic; they can become independent issues directly. Large needs enter an epic, then get split from the epic spec in batches. An issue carries one verifiable change, not the whole requirement world.

The close rule is simple: independent issue → project spec; exploratory issue → human-confirmed candidate articles merged into project spec according to spec rules; epic issue → epic spec; user-confirmed epic close → project spec.

---

## Skill catalog

The plugin has one `cs` skill. Users no longer choose among a catalog of skill names; `cs` first identifies the knowledge layer, then loads the relevant internal mode:

| Intent | What `cs` does internally |
|---|---|
| First-time setup | Create or complete the `.cs/` skeleton without silently migrating old requirements |
| Fuzzy idea or planning | Inspect context, clarify the real problem, then create an independent issue, exploratory issue, or epic only after confirmation |
| Spec change | Maintain the project spec or the epic's single `spec.md` |
| Behavior breaks expectations | Create a bug issue and use a feedback loop to diagnose, fix, and verify |
| Clear issue | Design, implement, and verify as needed; close and commit only when the user asks for wrap-up |
| Unknown system area | Develop candidate articles inside an exploratory issue, then graduate confirmed knowledge into the project spec |
| Reusable knowledge | Write notes, facts, or tools; learn unknown workflows under human guidance |

Action rules and principles for code design, debugging, documentation, and skill design live under `cs/references/` and load only when the current situation needs them.

---

## How the structure evolves

CodeStable isn't a single linear pipeline — it's a **project spec + epic spec + issues** loop:

```text
Project Spec ──small, clear change──> Issue ──close writeback──> Project Spec
     │
     └──large, unstable change──> Epic Spec ──in batches──> Issues
                                      ↑                    │
                                      └──evidence and learning

Epic close ──graduated conclusions──> Project Spec
```

**How to read this diagram:**

- **Project spec is the mainline, epic spec is a change line** — large-change churn stays in the epic until it graduates
- **Issues can be independent or epic-owned**: small bugs/features go direct; large needs split from epic specs in batches
- **Support files are the flywheel**: any work item that surfaces something worth keeping triggers a sink; the next round of work reads it back — the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs` onboards the project, a `.cs/` directory appears at the project root — the aggregate root for local artifacts and the workspace the unified skill reads and writes.

```
your-project/
├── .cs/
│   ├── facts.md              # Startup facts
│   ├── talks/                # Discussion synthesis (written only after confirmation)
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── spec/                 # Project spec: mainline truth
│   │       ├── index.md
│   │       └── ...           # Recursive reading path; each layer may have its own index.md
│   │
│   ├── issues/               # Closeable work items, sharded by creation date
│   │   ├── YYYY/MM/DD/{status}-{短语}.md   # ordinary issues
│   │   └── YYYY/MM/DD/{status}-{短语}/     # exploratory issue workspaces
│   ├── epics/                # Large-change lines
│   │   └── YYYY/MM/DD/{短语}/
│   │       └── spec.md       # Single authority: spec, progress, issues, blockers, close conditions
│   │
│   ├── notes/                # Knowledge notes, plain markdown, full-text search
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # Shared scripts captured after a workflow is proven
│
└── (work items stay under .cs/ by default so humans and AI can both read and edit them)
```

**Key points:**

- All local artifacts aggregate under `.cs/`, so "how did we handle that change last time" is three seconds away
- `spec/` is the project spec, organizing mainline requirements, architecture considerations, shared language, and reading paths for a developer entering the project
- `epics/` are large-change lines; each epic spec carries additions, changes, and reversals until the epic closes and graduates back into the project spec
- `issues/` can carry exploratory work; candidate articles, user corrections, and evidence stay in the issue workspace for discussion, then merge into project spec according to spec rules after human-confirmed close
- Talks and notes default to `YYYY/MM/DD/{短语}.md` date shards, epics use `YYYY/MM/DD/{短语}/` workspaces, ordinary issues use `YYYY/MM/DD/{status}-{短语}.md`, and exploratory issues use `YYYY/MM/DD/{status}-{短语}/` workspaces; search recursively under each area
- `notes/` is the knowledge notes area — plain markdown, no frontmatter, full-text searchable. `cs` decides whether daily "remember this" work belongs in notes or facts
- Human-guided unknown workflows become `notes/`, add a `facts.md` reference, and only produce `tools/` when automation is stable
- Keep Markdown appropriately concise without a universal line limit; preserve the complete core structure, background, principles, and contracts in the main narrative, and progressively disclose only details that are scenario-specific or obstruct the reading flow

### Hard constraint

> CodeStable has one installed `cs` unit. Its core structure and shared boundaries live in `SKILL.md`; scenario-specific action rules and principles live in that same skill's `references/`, with templates and scripts in the same package.
>
> `SKILL.md` must say when to read each reference. It must not hide core contracts or load every scenario at once. Project-specific stable knowledge still belongs in `.cs/spec/`, `.cs/notes/`, and `.cs/facts.md`.

Before `cs` switches internal action modes, it should reuse the current context first: if `facts.md`, project spec, epic spec, or the target issue has already been read and shows no sign of change, do not mechanically reread it. Read again only when context is missing, likely stale, needed for exact citation/write-back, or a new local slice is required. Before writing, always confirm the current version of the target issue, `.cs` file, or code file.

To change system rules, update `cs/SKILL.md`, the relevant reference, and its templates together; project-specific stable needs and operating knowledge belong in the matching `.cs/` entities.

---

## Design philosophy

CodeStable takes the **opposite** philosophy from OMO:

- OMO says: any human intervention is a failure signal
- CodeStable says: **the programmer is in the loop of software coding** — you may not understand the black-box implementation, but you must own the whole, and dive in when needed

Software architecture must be **evolvable**, **observable**, **controllable**.

This may matter less as AI gets stronger, but **right now this makes programmers comfortable in reality** — and that's the value.

CodeStable is modeled for real-world development scenarios, aiming to handle common dev problems through a closed-loop system. **Most existing frameworks model around AI, not around humans.** I think their authors have strong AI-driving skills but aren't seriously building software — they lack the basic ability to organize requirements and design, and they lack respect for code implementation.

---

## Roadmap

CodeStable adapts to model capability. If a future model nails a module reliably, that module gets removed.

- [ ] Polish the local work-item flow
- [ ] Polish the handoff from spec clarification to planning
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
