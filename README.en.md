<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-16-6366F1?style=flat-square" alt="Skills"/>
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

One command to start working:

```bash
/cs-onboard
```

For daily use, when you don't know which skill fits, call the root entry:

```bash
/cs
```

`cs` reads your intent and tells you which `cs-xxx` to run.

The CodeStable LITE plugin only packages `cs` / `cs-*` skills under `plugins/codestable-lite/skills/`; root-level standalone skill directories are not part of the distribution. The released version lives in `VERSION`, with release notes in `CHANGELOG.md`.

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

Large changes live under `.cs/epics/YYYY/MM/DD/{短语}/`. An epic directory contains `index.md`, `spec.md`, and `plan.md`: orientation, current requirements and architecture considerations, and the scope ready for this planning round. If implementation discovers additions, changes, or reversals, update the same epic spec instead of writing a `changes.md` log.

Issues under an epic close back into the epic spec first. Only when a human confirms the whole epic is done does AI merge the graduated conclusions back into the project spec.

### issues — closeable execution slices

Small bugs, small features, and local chores do not need an epic; they can become independent issues directly. Large needs enter an epic, then get split from the epic spec in batches. An issue carries one verifiable change, not the whole requirement world.

The close rule is simple: independent issue → project spec; exploratory issue → human-confirmed candidate articles merged into project spec according to spec rules; epic issue → epic spec; user-confirmed epic close → project spec.

---

## Skill catalog

<table>
<tr><th>Group</th><th>Skill</th><th>Purpose</th></tr>
<tr><td><b>Root entry</b></td><td><code>cs</code></td><td>Unified entry — introduces the system and routes open-ended intents to the right cs-* skill. Call it when you don't know which one fits</td></tr>
<tr><td><b>Onboard</b></td><td><code>cs-onboard</code></td><td>Bring CodeStable into a repo: create or complete the <code>.cs/</code> workspace and base entity directories</td></tr>
<tr><td><b>Discussion entry</b></td><td><code>cs-talk</code></td><td>Discussion + synthesis when ideas are fuzzy or context is missing: inspect repo context first, then write the result into <code>talks/</code></td></tr>
<tr><td><b>Spec entry</b></td><td><code>cs-spec</code></td><td>Maintain project or epic specs: requirements, architecture considerations, shared language, scope ready for this round, and open questions</td></tr>
<tr><td><b>Complaint entry</b></td><td><code>cs-complain</code></td><td>When behavior breaks expectations, create/update a bug issue, build a feedback loop, diagnose, fix, verify, and write back</td></tr>
<tr><td><b>Plan entry</b></td><td><code>cs-plan</code></td><td>Read <code>talks/</code> or the scope ready in an epic spec, discuss a planning draft first, then create an independent issue, new epic, or epic issue after confirmation</td></tr>
<tr><td><b>Design entry</b></td><td><code>cs-design</code></td><td>Write a tutorial-style implementation design for one issue: functional split, request/data flow, design focus points, boundaries, change route, validation, and detailed test strategy when needed</td></tr>
<tr><td><b>Execution entry</b></td><td><code>cs-do</code></td><td>Implement from the issue design, verify, and write back the execution record</td></tr>
<tr><td><b>Close entry</b></td><td><code>cs-close</code></td><td>Close an issue or epic, sinking conclusions to project/epic specs by ownership, and commit related code plus .cs writebacks</td></tr>
<tr><td><b>System understanding</b></td><td><code>cs-spec-explore</code></td><td>Turn project-spec gaps into exploratory issue workspaces, write discussable candidate articles, then merge on confirmed close</td></tr>
<tr><td rowspan="2"><b>Support files</b></td><td><code>cs-note</code></td><td>Sink pitfalls, tricks, research, and command traps into <code>notes/</code>, or one-line startup facts into <code>facts.md</code></td></tr>
<tr><td><code>cs-maketools</code></td><td>Let a human guide AI through an unknown workflow, then sink notes, a facts reference, and optional tools</td></tr>
<tr><td rowspan="4"><b>Principles</b></td><td><code>cs-how-codedesign</code></td><td>Design module interfaces and capability ownership by making modules deep and placing seams where change is real</td></tr>
<tr><td><code>cs-how-debug</code></td><td>Reproduce, gather evidence, explain the full cause chain from trigger to symptom, then make the smallest fix</td></tr>
<tr><td><code>cs-how-docs</code></td><td>Organize project spec, epic spec, exploratory issues, notes, README, and doc sets as readable knowledge spaces instead of flat content</td></tr>
<tr><td><code>cs-how-great-skills</code></td><td>When writing or reviewing skills, check whether context, principles, and usage boundaries are clear</td></tr>
</table>

---

## Workflow at a glance

CodeStable isn't a single linear pipeline — it's a **project spec + epic spec + issues** loop:

```
═══════════════════════════════════════════════════════════════
 Root entry · routing                          (callable any time)
   cs ──▶ Introduce the system / route open-ended intent to a sub-skill
═══════════════════════════════════════════════════════════════
                          │
        ┌─────────────────┼─────────────────┐
   (not onboarded)     (idea fuzzy)        (spec needs update)       (onboarded)
   cs-onboard          cs-talk ─────┐      cs-spec ─────┐           cs-plan ─▶ cs-design ─▶ cs-do ─▶ cs-close
   skeleton            context + talks│      project/epic│           confirm draft, create items → design → execute/verify → sink by owner
                                    └───────────────┴────────────▶ independent issue / epic / epic issue
                       cs-complain ─▶ diagnose and fix behavior drift through a bug issue
═══════════════════════════════════════════════════════════════
 spec · current truth and change lines       (.cs/spec/ and .cs/epics/)
───────────────────────────────────────────────────────────────
   project spec ─▶ what the project is / where it goes / capability map / architecture map / shared language / reading path
   epic spec    ─▶ what the big change changes / why this design / scope ready this round / open questions
   cs-spec      ─▶ maintain project or epic spec; write considerations, not change logs
   cs-plan      ─▶ from talks or epic spec: discuss a planning draft, then create independent issue / new epic / this round's epic issues after confirmation
═══════════════════════════════════════════════════════════════
 issues · closeable execution slices         (.cs/issues/)
───────────────────────────────────────────────────────────────
   cs-complain ─▶ when behavior breaks expectations, feedback loop → diagnosis → fix/verify → bug issue writeback
   cs-design ──▶ design one issue's implementation (functional split / request-data flow / design focus points / boundaries / change route / validation; detailed test strategy when needed)
   cs-do     ──▶ implement, verify, and write back the execution record
   cs-close  ──▶ independent issue → project spec; epic issue → epic spec; epic close → project spec
   cs-spec-explore ─▶ exploratory issue workspace: candidate articles → human-confirmed close → project spec
═══════════════════════════════════════════════════════════════
            ▼ any time something is worth recording ▼
 Support files · knowledge sink (compounding engineering)
   cs-note ──▶ .cs/notes/ or .cs/facts.md
   cs-maketools ─▶ human-guided unknown workflow → notes + facts reference + optional tools
═══════════════════════════════════════════════════════════════
```

**How to read this diagram:**

- **Project spec is the mainline, epic spec is a change line** — large-change churn stays in the epic until it graduates
- **Issues can be independent or epic-owned**: small bugs/features go direct; large needs split from epic specs in batches
- **Support files are the flywheel**: any work item that surfaces something worth keeping triggers a sink; the next round of work reads it back — the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs-onboard`, a `.cs/` directory appears at your project root — the aggregate root for all local artifacts and the only workspace each skill reads/writes at runtime.

```
your-project/
├── .cs/
│   ├── facts.md              # Startup facts
│   ├── talks/                # Discussion synthesis (cs-talk, lazy)
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── spec/                 # Project spec: mainline truth (cs-spec)
│   │       ├── index.md
│   │       └── ...           # Recursive reading path; each layer may have its own index.md
│   │
│   ├── issues/               # Closeable work items, sharded by creation date
│   │   ├── YYYY/MM/DD/{status}-{短语}.md   # ordinary issues
│   │   └── YYYY/MM/DD/{status}-{短语}/     # exploratory issue workspaces
│   ├── epics/                # Large-change lines
│   │   └── YYYY/MM/DD/{短语}/
│   │       ├── index.md      # Epic orientation, state, and issue list
│   │       ├── spec.md       # Epic requirements, architecture considerations, shared language
│   │       └── plan.md       # Scope ready this round and issue list
│   │
│   ├── notes/                # Knowledge notes, plain markdown, full-text search (cs-note)
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # Cross-workflow shared scripts (added by cs-maketools as needed)
│
└── (work items stay under .cs/ by default so humans and AI can both read and edit them)
```

**Key points:**

- All local artifacts aggregate under `.cs/`, so "how did we handle that change last time" is three seconds away
- `spec/` is the project spec, organizing mainline requirements, architecture considerations, shared language, and reading paths for a developer entering the project
- `epics/` are large-change lines; each epic spec carries additions, changes, and reversals until the epic closes and graduates back into the project spec
- `issues/` can carry exploratory work; candidate articles, user corrections, and evidence stay in the issue workspace for discussion, then merge into project spec according to spec rules after human-confirmed close
- Talks and notes default to `YYYY/MM/DD/{短语}.md` date shards, epics use `YYYY/MM/DD/{短语}/` workspaces, ordinary issues use `YYYY/MM/DD/{status}-{短语}.md`, and exploratory issues use `YYYY/MM/DD/{status}-{短语}/` workspaces; search recursively under each area
- `notes/` is the knowledge notes area — plain markdown, no frontmatter, full-text searchable. Daily "remember this" work goes through `cs-note`
- `cs-maketools` turns human-guided unknown workflows into `notes/`, adds a `facts.md` reference, and only writes `tools/` when automation is stable
- When one Markdown file exceeds 150 lines, split by progressive disclosure into same-directory resources instead of hard-compressing the entry file

### Hard constraint

> A skill is an independent install unit. At runtime, **each skill can only see files inside its own package**. References like `B-skill/reference/xxx.md` written in skill A's SKILL.md are **simply unreachable** at runtime.
>
> Do not solve cross-skill system rules by making skills reference each other's files. `cs` is only a guide; action skills must describe their own artifact contracts and boundaries. Sink project-specific stable knowledge into `.cs/spec/`, `.cs/notes/`, and `.cs/facts.md`.

Each cs action skill should reuse the current context first: if `facts.md`, project spec, epic spec, or the target issue has already been read and shows no sign of change, do not mechanically reread it. Read again only when context is missing, likely stale, needed for exact citation/write-back, or a new local slice is required. Before writing, always confirm the current version of the target issue, `.cs` file, or code file.

To change system rules, update the relevant skills' own instructions and templates; project-specific stable needs and operating knowledge belong in the matching `.cs/` entities.

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
