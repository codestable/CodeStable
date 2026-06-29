<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-20-6366F1?style=flat-square" alt="Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## Install

```bash
npx skills add https://github.com/liuzhengdongfortest/CodeStable
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
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Work items (issues / epics) · requirements (needs / constraints / trade-offs)</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How do requirements, constraints, trade-offs get recorded, retrieved, reused?</td></tr>
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

## Design: work items + requirements

Early CodeStable split development into 6 entities and 3 pipelines. In practice that was too many entities and too rigid — feature / issue / refactor are really the same thing (a closeable work item), and requirements / roadmap / architecture all describe the same thing (the current requirements truth). So it collapsed into **work items plus requirements**.

### Work items — things to do that get closed

Bugs, refactors, small features, big needs — they're all "a change to make that gets closed when done," just differing in size and type. They live in `.cs/issues/` or `.cs/epics/`.

- **`cs-plan`** — bridge from `talks/`: small needs become issues directly; larger needs enter epics first and get split into issues
- **`cs-complain`** — when behavior breaks expectations, pin expected/actual/repro/evidence and create a bug issue
- **`cs-design`** — implementation design for a single issue: module ownership, interfaces/data/state, test surface, and execution order
- **`cs-test`** — optional test design for one issue when the user or company requires test cases and execution guidance
- **`cs-do`** — implement from the issue design, verify, and write back the execution record
- **`cs-close`** — close an issue and write durable conclusions back to requirements, notes, facts, or tools
- **`cs-issue`** — one closeable change, tagged `bug` / `refactor` / `feature` / `chore`. Loop: record clearly → locate → fix + verify → close & write back
- **`cs-epics`** — too big for a single issue: settle the architecture in epics first (module split + interface contracts), then break it into a dependency-DAG of issues
- **`cs-audit`** — proactive scanner + reconciliation against requirements, producing a triage list; selected findings become issues

### requirements — human-readable current needs

This is CodeStable's north star: **read it and you know the requirements, constraints, and trade-offs behind the code.** It is not a field table. It should explain, in human language, the background, the rough capability being built, why this path was chosen, which user stories must hold, and which boundaries may vary.

Requirements use progressive disclosure: the entry file starts with an overview and submodule navigation; complex subsystems, substeps, or domain rules move into sibling requirement files. Each child file follows the same explanatory shape: background, what it should provide, key rules, boundaries, and trade-offs.

- **`cs-requirements`** — current need explanations, domain language, key rules, and trade-offs (background / capability / boundaries / why flexibility is needed). No code locations, no historical narrative

### How they mesh

Work items are the increments; requirements is the current requirements truth those increments settle into. **When an issue or epic closes, the graduated constraints, facts, and trade-offs are written back to requirements.** Requirements keeps no history (that lives in closed issues); issues don't describe the standing requirements. The execution discipline (`cs-do`) and notes (`cs-keep`) serve both.

---

## Skill catalog

<table>
<tr><th>Group</th><th>Skill</th><th>Purpose</th></tr>
<tr><td><b>Root entry</b></td><td><code>cs</code></td><td>Unified entry — introduces the system and routes open-ended intents to the right cs-* skill. Call it when you don't know which one fits</td></tr>
<tr><td><b>Onboard</b></td><td><code>cs-onboard</code></td><td>Bring CodeStable into a repo: create or complete the <code>.cs/</code> workspace and base entity directories</td></tr>
<tr><td><b>Discussion entry</b></td><td><code>cs-talk</code></td><td>Discussion + synthesis when ideas are fuzzy: write the result into <code>talks/</code></td></tr>
<tr><td><b>Complaint entry</b></td><td><code>cs-complain</code></td><td>When behavior breaks expectations, pin expected / actual / repro / evidence and create a bug issue</td></tr>
<tr><td><b>Plan entry</b></td><td><code>cs-plan</code></td><td>Read <code>talks/</code>, decide whether to create a direct issue or enter an epic first, then draft the artifact</td></tr>
<tr><td><b>Design entry</b></td><td><code>cs-design</code></td><td>Design the implementation for one issue, writing back module ownership, interfaces/data/state, test surface, and execution order</td></tr>
<tr><td><b>Test entry</b></td><td><code>cs-test</code></td><td>Optional gate: when test design is needed, write test goals, cases, and execution guidance for one issue</td></tr>
<tr><td><b>Execution entry</b></td><td><code>cs-do</code></td><td>Implement from the issue design, verify, and write back the execution record</td></tr>
<tr><td><b>Close entry</b></td><td><code>cs-close</code></td><td>Close an issue and sink durable conclusions into requirements / notes / facts / tools</td></tr>
<tr><td rowspan="3"><b>Work items</b></td><td><code>cs-issue</code></td><td>One closeable change: bug / refactor / small feature / chore, tagged by type</td></tr>
<tr><td><code>cs-epics</code></td><td>Big need: enter epics, settle architecture (module split + interface contracts), then break into dependency issues</td></tr>
<tr><td><code>cs-audit</code></td><td>Proactive scan + reconciliation against requirements, producing candidate changes</td></tr>
<tr><td><b>Requirements</b></td><td><code>cs-requirements</code></td><td>Explain current needs, domain language, key rules, and trade-offs through an overview and submodule files</td></tr>
<tr><td rowspan="3"><b>Support files</b></td><td><code>cs-maketools</code></td><td>Let a human guide AI through an unknown workflow, then sink notes, a facts reference, and optional tools</td></tr>
<tr><td><code>cs-keep</code></td><td>Sink pitfalls / tricks / decisions / exploration into <code>notes/</code> as plain markdown, full-text searchable</td></tr>
<tr><td><code>cs-note</code></td><td>Append one-line startup facts to <code>facts.md</code></td></tr>
<tr><td rowspan="2"><b>Outward docs</b></td><td><code>cs-doc-tutorial</code></td><td>Outward-facing dev / user guides (task-oriented: how to use X to do Y)</td></tr>
<tr><td><code>cs-doc-api</code></td><td>API reference reverse-engineered from source (entry-by-entry, parts lookup)</td></tr>
</table>

---

## Workflow at a glance

CodeStable isn't a single linear pipeline — it's **work items + requirements + event-driven**:

```
═══════════════════════════════════════════════════════════════
 Root entry · routing                          (callable any time)
   cs ──▶ Introduce the system / route open-ended intent to a sub-skill
═══════════════════════════════════════════════════════════════
                          │
        ┌─────────────────┼─────────────────┐
   (not onboarded)     (idea fuzzy)        (onboarded)
   cs-onboard          cs-talk ─▶ cs-plan ─▶ cs-design ─▶ cs-test? ─▶ cs-do ─▶ cs-close  go to work items / requirements
   skeleton            synthesize talks → create items → design issue → optional tests → execute → close and sink
                       cs-complain ─▶ create a bug issue when behavior drifts
═══════════════════════════════════════════════════════════════
 Work items · things to do that get closed   (.cs/issues/ or .cs/epics/)
───────────────────────────────────────────────────────────────
   cs-plan   ──▶ from talks: create a direct issue, or enter an epic then split issues
   cs-complain ─▶ when behavior breaks expectations, create a closeable bug issue
   cs-design ──▶ design one issue's implementation (modules / interfaces / data / tests)
   cs-test   ──▶ optional test design (goals / cases / levels / test-first)
   cs-do     ──▶ implement, verify, and write back the execution record
   cs-close  ──▶ close the issue and sink durable conclusions into long-lived entities
   cs-issue  ──▶ one closeable change (bug / refactor / small feature / chore)
   cs-epics  ──▶ big need: enter epics → settle architecture → break into issues
   cs-audit  ──▶ proactive scan + reconcile requirements → candidate issues
        │   coding via cs-do (stop the moment you drift)
        ▼   on close, write graduated trade-offs back ▼
═══════════════════════════════════════════════════════════════
 requirements · needs, constraints, trade-offs (.cs/requirements/)
───────────────────────────────────────────────────────────────
   cs-requirements ──▶ overview + submodule explanations + domain language + trade-offs
                       (background / capability / key rules / boundaries)
                       north star: read it and you know the requirements & trade-offs
═══════════════════════════════════════════════════════════════
            ▼ any time something is worth recording ▼
 Support files · knowledge sink (compounding engineering)
   cs-maketools ─▶ human-guided unknown workflow → notes + facts reference + optional tools
   cs-keep ──▶ .cs/notes/       plain markdown, full-text search
   cs-note ──▶ .cs/facts.md  one-line startup facts
═══════════════════════════════════════════════════════════════
```

**How to read this diagram:**

- **Work items and requirements are not a time order** — open new work any time; requirements is refreshed as work items close
- **Work items are the increments, requirements is the sediment**: when an issue or epic closes, the graduated trade-offs are written back to requirements
- **Support files are the flywheel**: any work item that surfaces something worth keeping triggers a sink; the next round of work reads it back — the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs-onboard`, a `.cs/` directory appears at your project root — the aggregate root for all local artifacts and the only workspace each skill reads/writes at runtime.

```
your-project/
├── .cs/
│   ├── facts.md              # Startup facts
│   ├── talks/                # Discussion synthesis (cs-talk, lazy)
│   │
│   ├── issues/               # Small work items, sharded by creation year/month
│   │   └── YYYY/MM/{slug}.md
│   ├── epics/                # Large work-item planning
│   │   └── YYYY-MM-DD-{slug}.md
│   │
│   ├── requirements/         # Current needs, constraints, and trade-offs (cs-requirements)
│   │   ├── REQUIREMENTS.md   # Entry point (lazy)
│   │   ├── REQUIREMENTS-MAP.md # Multi-requirements topology entry (large projects only)
│   │   └── {slug}.md         # One area per file
│   │
│   ├── notes/                # Knowledge notes, plain markdown, full-text search (cs-keep)
│   │   └── YYYY-MM-DD-{slug}.md
│   │
│   └── tools/                # Cross-workflow shared scripts (added by cs-maketools as needed)
│
└── (work items stay under .cs/ by default so humans and AI can both read and edit them)
```

**Key points:**

- All local artifacts aggregate under `.cs/`, so "how did we handle that change last time" is three seconds away
- `requirements/` explains current needs, constraints, domain language, and trade-offs in human language; the entry file gives the overview, while details are progressively disclosed through submodule files; history lives in closed issues
- Issues default to local `issues/YYYY/MM/{slug}.md`, avoiding too many files in one directory; search recursively under `issues/`
- `notes/` is the knowledge notes area — plain markdown, no frontmatter, full-text searchable. Easy to write, easy to find
- `cs-maketools` turns human-guided unknown workflows into `notes/`, adds a `facts.md` reference, and only writes `tools/` when automation is stable
- When one Markdown file exceeds 150 lines, split by progressive disclosure into same-directory resources instead of hard-compressing the entry file

### Hard constraint

> A skill is an independent install unit. At runtime, **each skill can only see files inside its own package**. References like `B-skill/reference/xxx.md` written in skill A's SKILL.md are **simply unreachable** at runtime.
>
> Do not solve cross-skill system rules by making skills reference each other's files. Keep system rules inside the `cs` skill, or sink project-specific stable knowledge into `.cs/requirements/`, `.cs/notes/`, and `.cs/facts.md`.

Each cs action skill first checks the `cs` skill: reuse it if it has already been read in the current conversation or execution context; otherwise read it once to load the entity and skill boundaries.

To change system rules, update the `cs` skill and its references/templates; project-specific stable needs and operating knowledge belong in the matching `.cs/` entities.

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
- [ ] Harden `cs-audit`'s reconciliation against requirements
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
