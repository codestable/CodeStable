<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-13-6366F1?style=flat-square" alt="Skills"/>
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
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Change axis (issue / epic) · State axis (context)</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How do requirements, constraints, trade-offs get recorded, retrieved, reused?</td></tr>
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>The <code>.codestable/</code> file tree + optional GitHub issues (readable by both humans and AI)</td></tr>
<tr><td><b>Pain it solves</b></td><td>One agent isn't enough; need coordination to scale</td><td>Software complexity overflows context; tacit knowledge gets lost; requirements drift</td></tr>
<tr><td><b>Role of humans</b></td><td>The less the better — full automation is the ideal</td><td>Human-in-the-loop — the programmer owns the whole; AI is an efficient executor</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)

**Neither direction is wrong.**

If your task is "run an end-to-end automated pipeline with AI" or "have multiple agents debate a plan," the agent-orchestration camp fits better.

If your task is "maintain serious software that iterates over years" or "make sure a requirement written today can still be accurately recalled three months later" — then CodeStable's software-element-centric model fits better.

I built CodeStable because I believe **the chaos of software engineering isn't really about agents not being strong enough — it's about elements not being organized**. No matter how strong the agent, it can't save a project that's lost its requirements, trade-offs, and history.

---

## Design: two orthogonal axes

Early CodeStable split development into 6 entities and 3 pipelines. In practice that was too many entities and too rigid — feature / issue / refactor are really the same thing (a closeable change), and requirements / roadmap / architecture all describe the same thing (the current state). So it collapsed into **two orthogonal axes**.

### Change axis — things to do that get closed

Bugs, refactors, small features, big needs — they're all "a change to make that gets closed when done," just differing in size and type. They live as GitHub issues or locally (pick one at onboard).

- **`cs-issue`** — one closeable change, tagged `bug` / `refactor` / `feature` / `chore`. Loop: record clearly → locate → fix + verify → close & write back
- **`cs-epic`** — too big for a single issue: settle the architecture first (module split + interface contracts), then break it into a dependency-DAG of sub-issues
- **`cs-audit`** — proactive scanner + reconciliation against context, producing a triage list; selected findings become issues

### State axis — what it is now, and why

This is CodeStable's north star: **read it and you know the code's requirements and trade-offs.** It only records what the code itself can't show — why this, why not that, the rejected alternatives, which axis varies. Code says "what it does," context fills in "why"; together they're the full picture, neither repeating the other.

- **`cs-context`** — domain glossary + rationale notes (happy path / boundaries / why flexibility is needed). No code locations, no historical narrative

### How the axes mesh

The change axis is the increment; the state axis is the current truth those increments integrate to. **When an issue / epic closes, the graduated trade-offs are written back to context.** Context keeps no history (that lives in closed issues); issues don't describe the standing state. The coding discipline (`cs-code`) and knowledge sink (`cs-keep`) cut across both axes.

---

## Skill catalog

<table>
<tr><th>Group</th><th>Skill</th><th>Purpose</th></tr>
<tr><td><b>Root entry</b></td><td><code>cs</code></td><td>Unified entry — introduces the system and routes open-ended intents to the right cs-* skill. Call it when you don't know which one fits</td></tr>
<tr><td><b>Onboard</b></td><td><code>cs-onboard</code></td><td>Bring CodeStable into a repo: skeleton + distribute shared assets + pick change-axis carrier (GitHub / local) + migrate old docs</td></tr>
<tr><td rowspan="4"><b>Change axis</b></td><td><code>cs-issue</code></td><td>One closeable change: bug / refactor / small feature / chore, tagged by type</td></tr>
<tr><td><code>cs-epic</code></td><td>Big need: settle architecture (module split + interface contracts), then break into dependency sub-issues</td></tr>
<tr><td><code>cs-audit</code></td><td>Proactive scan + reconciliation against context, producing candidate changes</td></tr>
<tr><td><code>cs-code</code></td><td>Coding discipline: write only what's needed now, stop the moment you drift (cross-cutting, used in any hands-on work)</td></tr>
<tr><td><b>State axis</b></td><td><code>cs-context</code></td><td>Domain glossary + rationale notes (happy path / boundaries / why flexibility is needed)</td></tr>
<tr><td><b>Discussion entry</b></td><td><code>cs-clarify</code></td><td>Discussion + triage when ideas are fuzzy: route to writing directly or to cs-epic</td></tr>
<tr><td rowspan="3"><b>Cross-cut & periphery</b></td><td><code>cs-keep</code></td><td>Sink pitfalls / tricks / decisions / exploration into <code>compound/</code> as plain markdown, full-text searchable</td></tr>
<tr><td><code>cs-note</code></td><td>Append one-line startup must-knows to <code>attention.md</code></td></tr>
<tr><td><code>cs-convention</code></td><td>Maintain the system's shared conventions, distributed as <code>.codestable/convention.md</code></td></tr>
<tr><td rowspan="2"><b>Outward docs</b></td><td><code>cs-doc-tutorial</code></td><td>Outward-facing dev / user guides (task-oriented: how to use X to do Y)</td></tr>
<tr><td><code>cs-doc-api</code></td><td>API reference reverse-engineered from source (entry-by-entry, parts lookup)</td></tr>
</table>

---

## Workflow at a glance

CodeStable isn't a single linear pipeline — it's **two axes + event-driven**:

```
═══════════════════════════════════════════════════════════════
 Root entry · routing                          (callable any time)
   cs ──▶ Introduce the system / route open-ended intent to a sub-skill
═══════════════════════════════════════════════════════════════
                          │
        ┌─────────────────┼─────────────────┐
   (not onboarded)     (idea fuzzy)       (onboarded)
   cs-onboard          cs-clarify          go to the axes
   skeleton + carrier  discuss + triage
═══════════════════════════════════════════════════════════════
 Change axis · things to do that get closed  (GitHub issue or local)
───────────────────────────────────────────────────────────────
   cs-issue  ──▶ one closeable change (bug / refactor / small feature / chore)
   cs-epic   ──▶ big need: settle architecture → break into sub-issues
   cs-audit  ──▶ proactive scan + reconcile context → candidate issues
        │   coding via cs-code (stop the moment you drift)
        ▼   on close, write graduated trade-offs back ▼
═══════════════════════════════════════════════════════════════
 State axis · what it is now, and why         (.codestable/context/)
───────────────────────────────────────────────────────────────
   cs-context ──▶ domain glossary + rationale notes
                  (happy path / boundaries / why flexibility is needed)
                  north star: read it and you know the requirements & trade-offs
═══════════════════════════════════════════════════════════════
            ▼ any time something is worth recording ▼
 Cross-cut · knowledge sink (compounding engineering)
   cs-keep ──▶ .codestable/compound/    plain markdown, full-text search
   cs-note ──▶ .codestable/attention.md  one-line startup must-knows
═══════════════════════════════════════════════════════════════
```

**How to read this diagram:**

- **The two axes are orthogonal**, not a time order — open new changes any time; the state axis is refreshed as changes close
- **Change is the increment, state is the integral**: when an issue / epic closes, the graduated trade-offs are written back to context
- **Cross-cut is the flywheel**: any change that surfaces something worth keeping triggers a sink; the next round of work reads it back — the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs-onboard`, a `.codestable/` directory appears at your project root — the aggregate root for all local artifacts and the only workspace each skill reads/writes at runtime.

```
your-project/
├── .codestable/
│   ├── attention.md          # Startup must-reads + change-axis carrier (github / local)
│   ├── convention.md         # Shared conventions (distributed by onboard, don't hand-edit)
│   │
│   ├── context/              # State axis (cs-context)
│   │   ├── CONTEXT.md        # Domain glossary (lazy)
│   │   ├── CONTEXT-MAP.md    # Multi-context topology entry (multi-context only)
│   │   └── {slug}.md         # Rationale notes, one per area
│   │
│   ├── issues/  epics/       # Change axis — only in local-carrier mode
│   │   └── YYYY-MM-DD-{slug}/ # (in github mode, issues/epics live on GitHub)
│   │
│   ├── compound/             # Knowledge sink, plain markdown, full-text search (cs-keep)
│   │   └── YYYY-MM-DD-{slug}.md
│   │
│   ├── clarify/              # Big-need clarification notes (cs-clarify, lazy)
│   ├── tools/                # Cross-workflow shared scripts (released by onboard)
│   └── reference/            # Shared reference docs (released by onboard)
│       ├── system-overview.md
│       ├── maintainer-notes.md
│       └── tools.md
│
└── (in github-carrier mode, the change axis lives on GitHub; local keeps only context / compound)
```

**Key points:**

- All local artifacts aggregate under `.codestable/`, so "how did we handle that change last time" is three seconds away
- `context/` is the **state axis** (glossary + rationale notes), describing only the current truth with no historical narrative; history lives in closed issues
- **The change-axis carrier is one of two**: GitHub issues (native closeable entities) or local `issues/ epics/`, chosen at onboard and recorded in `attention.md`
- `compound/` is the knowledge sink — plain markdown, no frontmatter, full-text searchable. Easy to write, easy to find
- `convention.md` / `reference/` are distributed by `cs-onboard` from the skill package; to change shared conventions go through `cs-convention`, and new projects pick up the new version on onboard

### Hard constraint

> A skill is an independent install unit. At runtime, **each skill can only see files inside its own package**. References like `B-skill/reference/xxx.md` written in skill A's SKILL.md are **simply unreachable** at runtime.
>
> Cross-skill shared conventions must go through the "working project" layer: the source of truth lives in `cs-convention` (at `cs-onboard/reference/convention.md`), `cs-onboard` distributes it to the project's `.codestable/convention.md`, and other skills read it via the project-relative path.

To change shared conventions, go through `cs-convention`; new projects pick them up at onboard time, and existing projects re-run `cs-onboard` to sync.

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

- [ ] Polish the GitHub change-axis carrier (`gh` integration)
- [ ] Harden `cs-audit`'s reconciliation against context
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
