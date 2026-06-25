<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-27-6366F1?style=flat-square" alt="CodeStable Skills"/>
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

> **What gets orchestrated isn't agents — it's the lifecycle of the software itself.** The entities at the center are **the elements that make up software**: every requirement, every architectural decision, every feature, every bug, every constraint left in history.

<table>
<tr><th></th><th>Agent-orchestration camp</th><th>CodeStable</th></tr>
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Requirement / Architecture / Feature / Issue / Decision</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How do requirements, constraints, decisions get recorded, retrieved, reused?</td></tr>
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>The <code>codestable/</code> file tree in your project (readable by both humans and AI)</td></tr>
<tr><td><b>Pain it solves</b></td><td>One agent isn't enough; need coordination to scale</td><td>Software complexity overflows context; tacit knowledge gets lost; requirements drift</td></tr>
<tr><td><b>Role of humans</b></td><td>The less the better — full automation is the ideal</td><td>Human-in-the-loop — the programmer owns the whole; AI is an efficient executor</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)

**Neither direction is wrong.**

If your task is "run an end-to-end automated pipeline with AI" or "have multiple agents debate a plan," the agent-orchestration camp fits better.

If your task is "maintain serious software that iterates over years" or "make sure a requirement written today can still be accurately recalled three months later" — then CodeStable's software-element-centric model fits better.

I built CodeStable because I believe **the chaos of software engineering isn't really about agents not being strong enough — it's about elements not being organized**. No matter how strong the agent, it can't save a project that's lost its requirements, architecture, and history.

---

## Design: entities + flows

CodeStable models real coding work as a set of **entities** and **flows**.

### Entities

| Entity | Slug | What it does |
|------|------|--------|
| **Requirement** | requirements | User stories + domain glossary (CONTEXT.md) + architecture decisions (ADRs). The escape hatch — when code rots, you can throw it all out and let AI regenerate from these |
| **Roadmap** | roadmap | "I want a permission system" — too big to throw at AI as a feature; cut it into a roadmap and advance step by step |
| **Goal** | goals | Bounded start/end: write a start report, then let AI iterate autonomously on implementation/validation, with subagent functional acceptance before completion |
| **Feature** | feature | The actual engineering execution. Human and AI collaborate, jointly responsible for design / implementation / acceptance |
| **Issue** | issue | The bug list after release. AI and human solve it together |
| **Refactor** | refactor | Cleanup process when code rots (beta) |
| **Compound** | compound | The compounding-engineering knowledge base — pitfalls, tricks, investigation notes |

### Flows

| Flow | Key skill chain | Notes |
|------|------------|------|
| **Feature delivery** | `cs-feat` → `cs-feat-design` → `cs-feat-design-review` → `cs-feat-impl` → `cs-code-review` → `cs-feat-qa` → `cs-feat-accept` | Think it through → design review → step-by-step coding → code review → QA → acceptance |
| **Goal achievement** | `cs-goal` | Bounded start/end → interview/grill + start report → autonomous implement/validate/iterate → subagent functional acceptance before completion |
| **Issue fixing** | `cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix` → `cs-code-review` | Tell AI what's wrong → AI finds the root cause → AI fixes precisely → independent review before commit |
| **Refactoring** | `cs-refactor` (beta) → `cs-code-review` | Architectural rot doesn't happen overnight. AI assists, but **humans refactor**. Still iterating — feedback welcome |

`cs-code-review` is the cross-cutting quality gate at the tail of every execution flow, before commit — feature, fast path, issue fixing, and refactoring all route their pre-commit diff review through it. At a phase or milestone boundary, use `cs-docs-neat` to reconcile `.codestable/`, README/docs, `CLAUDE.md` / `AGENTS.md`, and agent memory so docs do not drift from code.

> Strong branch protection: `cs-onboard` can optionally release the `codestable-ai-branch-guard` hook, which blocks AI from implementing directly on `main`/`master` and forces a worktree. See the "branch protection hook" section in `cs-onboard`.

---

## Skill catalog

<table>
<tr><th>Group</th><th>Skill</th><th>Purpose</th></tr>
<tr><td><b>Root entry</b></td><td><code>cs</code></td><td>Unified entry — introduces the system and routes open-ended intents to the right cs-* skill. Call it when you don't know which one fits</td></tr>
<tr><td><b>Onboard</b></td><td><code>cs-onboard</code></td><td>Bring CodeStable into a new repo or one with scattered docs</td></tr>
<tr><td rowspan="2"><b>Requirement & domain</b></td><td><code>cs-req</code></td><td>Curate / accumulate capability vision docs</td></tr>
<tr><td><code>cs-domain</code></td><td>Maintain <code>requirements/CONTEXT.md</code> glossary + <code>requirements/adrs/</code> architecture decisions (3-criteria gate + Nygard 4 sections) + single/multi context topology</td></tr>
<tr><td><b>Roadmap</b></td><td><code>cs-roadmap</code></td><td>Up-front planning for a big chunk of work: high-level design + interface contracts + sub-feature breakdown</td></tr>
<tr><td><b>Discussion entry</b></td><td><code>cs-brainstorm</code></td><td>Triage when ideas are still fuzzy: route to design / continue in a feature / hand off to roadmap</td></tr>
<tr><td><b>Goal</b></td><td><code>cs-goal</code></td><td>Bounded start/end: write a start report, let AI iterate autonomously, with subagent functional acceptance before completion</td></tr>
<tr><td rowspan="6"><b>Feature flow</b></td><td><code>cs-feat</code></td><td>Sub-flow entry for new features</td></tr>
<tr><td><code>cs-feat-design</code></td><td>Draft <code>{slug}-design.md</code> as the single input for what follows</td></tr>
<tr><td><code>cs-feat-impl</code></td><td>Code in the order the design lays out</td></tr>
<tr><td><code>cs-code-review</code></td><td>Cross-cutting read-only code review gate before commit; produces <code>{slug}-review.md</code></td></tr>
<tr><td><code>cs-feat-accept</code></td><td>Verify implementation against the design layer by layer; close the loop</td></tr>
<tr><td><code>cs-feat-ff</code></td><td>Ultra-light lane: no design, no phases, AI just does it</td></tr>
<tr><td rowspan="4"><b>Issue flow</b></td><td><code>cs-issue</code></td><td>Sub-flow entry for issue fixing</td></tr>
<tr><td><code>cs-issue-report</code></td><td>Turn the problem in your head into a reproducible, traceable report</td></tr>
<tr><td><code>cs-issue-analyze</code></td><td>Find root cause, assess fix risk, propose options</td></tr>
<tr><td><code>cs-issue-fix</code></td><td>Targeted fix + verification + write fix-note</td></tr>
<tr><td rowspan="2"><b>Refactor flow</b></td><td><code>cs-refactor</code></td><td>(beta) Main refactor flow</td></tr>
<tr><td><code>cs-refactor-ff</code></td><td>(beta) Light refactor lane</td></tr>
<tr><td><b>Knowledge sink</b></td><td><code>cs-keep</code></td><td>Sink pitfalls / tricks / decisions / exploration into <code>compound/</code> as plain markdown, searched via grep</td></tr>
<tr><td rowspan="2"><b>Outward docs</b></td><td><code>cs-doc-tutorial</code></td><td>Outward-facing dev / user guides (task-oriented: how to use X to do Y)</td></tr>
<tr><td><code>cs-doc-api</code></td><td>API reference reverse-engineered from source (entry-by-entry, parts lookup)</td></tr>
</table>

See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the full catalog. In daily use, call `/cs` when you are unsure; it routes your intent to the right skill.

---

## Workflow at a glance

CodeStable's skills are **layered + event-driven**: root routing, onboard, long-lived archives, roadmap planning, feature / issue / refactor execution flows, and cross-cut knowledge sinking.

```
═══════════════════════════════════════════════════════════════════════
 Root entry · routing                              (callable any time)
───────────────────────────────────────────────────────────────────────
   cs ──▶ Introduce the system / route open-ended intent to a sub-skill
          (does nothing itself — only triages and points)
═══════════════════════════════════════════════════════════════════════
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        (not onboarded)  (onboarded)    (just want to learn)
         go to phase 0   jump to L1~4 / cross-cut    quick read
              │
              ▼
═══════════════════════════════════════════════════════════════════════
 Phase 0 · Onboard                            (runs once per project)
───────────────────────────────────────────────────────────────────────
   cs-onboard ──▶ Generate codestable/ skeleton + release reference/, tools/
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 1 · Long-lived archive ("what the system looks like now")
───────────────────────────────────────────────────────────────────────
   cs-req     ──▶ codestable/requirements/{slug}.md       capability vision
   cs-domain  ──▶ codestable/requirements/CONTEXT.md      domain glossary
                  codestable/requirements/adrs/NNN-*.md   ADRs (3-criteria gate)
                  CONTEXT-MAP.md present → nest per bounded context
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 2 · Planning ("how we plan to deliver this big thing next")
───────────────────────────────────────────────────────────────────────
   cs-roadmap ──▶ codestable/roadmap/{slug}/
                  Turn "I want X" into a complete up-front plan:
                    ① High-level design — module / component split
                    ② Architectural detail — interface contracts
                    ③ Sub-features      — broken into executable units
                  ② is a hard input for feature-design
                  (Small needs skip this layer and go straight to L3)
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Discussion entry (optional · enter when fuzzy, route after triage)
───────────────────────────────────────────────────────────────────────
                          ┌── case 1 clear enough ──▶ cs-feat-design
   cs-brainstorm ────────▶┼── case 2 small + decided ─▶ feature flow
                          └── case 3 big with one word ─▶ cs-roadmap
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 3 · Execution flows (pick one per event type)
───────────────────────────────────────────────────────────────────────

  ▸ Event: new capability                                      ┌──────────┐
       cs-feat-design ─▶ cs-feat-impl ─▶ cs-code-review ─▶     │ features │
                                         cs-feat-qa ─▶ cs-feat-accept │ /YYYY-…/ │
       cs-feat-ff     ──(light lane, skips design/accept)─▶     └──────────┘

  ▸ Event: fix a defect                                         ┌──────────┐
       cs-issue-report ─▶ cs-issue-analyze ─▶ cs-issue-fix ─▶   │  issues  │
                                              cs-code-review    │ /YYYY-…/ │
                                                                └──────────┘

  ▸ Event: code rot (beta)                                      ┌──────────┐
       cs-refactor / cs-refactor-ff ─▶ cs-code-review            │refactors │
                                                                 │ /YYYY-…/ │
                                                                 └──────────┘
═══════════════════════════════════════════════════════════════════════
                              │
                ▼ trigger any time something is worth recording ▼
═══════════════════════════════════════════════════════════════════════
 Cross-cut · Knowledge sink (compounding engineering)
───────────────────────────────────────────────────────────────────────
   cs-keep ──▶ codestable/compound/YYYY-MM-DD-{slug}.md
                  plain markdown, no frontmatter, grep to search
                   ↑
          Next cs-feat-design / cs-issue-analyze
          greps compound/ so experience is reused
═══════════════════════════════════════════════════════════════════════
```

**How to read this diagram:**

- **Vertical = layers**, not strict time order — Layer 1 is refreshed repeatedly, Layer 2 is only entered for big needs
- **Layer 3 is event-driven**: new need → feature flow, bug → issue flow, rot → refactor flow
- **Cross-cut is the flywheel**: any flow can trigger a sink when something is worth keeping; the next round of work reads it back. This is the physical implementation of CodeStable's "compounding"

`cs-code-review` is the cross-cutting quality gate at the tail of the feature / issue / refactor execution flows, before commit. See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full diagram.

---

## Runtime structure

After `/cs-onboard`, a `.codestable/` directory appears at your project root as the aggregate root for requirements, architecture, roadmap, goals, features, issues, refactors, audits, compound, tools, hooks, and reference.

```
your-project/
├── codestable/
│   ├── requirements/                     # Requirement + domain model (cs-req / cs-domain co-maintain)
│   │   ├── VISION.md                     # Capability index
│   │   ├── {slug}.md                     # One file per capability, flat (no grouping)
│   │   ├── CONTEXT.md                    # Domain glossary (cs-domain, lazy)
│   │   ├── CONTEXT-MAP.md                # Multi-context topology (only for multi-context projects)
│   │   ├── adrs/                         # Architecture decisions (cs-domain, lazy)
│   │   │   └── NNN-{slug}.md             # Nygard 4 sections + status machine
│   │   └── {ctx}/                        # Bounded-context subdir (only multi-context)
│   │       ├── CONTEXT.md
│   │       ├── adrs/
│   │       └── {capability}.md
│   │
│   ├── roadmap/                          # Roadmaps ("how we plan to walk next")
│   │   └── {slug}/
│   │       ├── {slug}-roadmap.md         # Main doc: background / breakdown / sequencing
│   │       ├── {slug}-items.yaml         # Machine-readable sub-feature list, acceptance writes status back
│   │       └── drafts/                   # Optional: drafts / research
│   │
│   ├── features/                         # Feature flow aggregate root
│   │   └── YYYY-MM-DD-{slug}/            # One directory per feature
│   │       ├── {slug}-brainstorm.md      # Optional (cs-brainstorm output)
│   │       ├── {slug}-design.md          # Design (cs-feat-design)
│   │       ├── {slug}-checklist.yaml     # Progress checklist (impl runs it, accept writes back)
│   │       └── {slug}-acceptance.md      # Acceptance report (cs-feat-accept)
│   │
│   ├── issues/                           # Issue flow aggregate root
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-report.md          # Issue report
│   │       ├── {slug}-analysis.md        # Root-cause analysis (only when non-obvious)
│   │       └── {slug}-fix-note.md        # Fix record
│   │
│   ├── refactors/                        # Refactor flow aggregate root (beta)
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-scan.md
│   │       ├── {slug}-refactor-design.md
│   │       ├── {slug}-checklist.yaml
│   │       └── {slug}-apply-notes.md
│   │
│   ├── compound/                         # Knowledge sink (compounding engineering), unified directory
│   │   └── YYYY-MM-DD-{slug}.md
│   │       # plain markdown, no frontmatter, grep to search (cs-keep)
│   │
│   ├── tools/                            # Cross-workflow shared scripts (released by onboard)
│   └── reference/                        # Shared reference docs (released by onboard)
│       ├── shared-conventions.md         # Cross-skill conventions / paths / metadata
│       ├── system-overview.md            # CodeStable system overview + scenario routing
│       └── ...
│
└── AGENTS.md                             # At project root, not under codestable/
```

**Key points:**

- All artifacts aggregate under `codestable/`, so "how did we handle that feature / bug last time" is three seconds away
- `requirements/` is the **long-lived archive** (capability vision + domain glossary CONTEXT.md + decisions adrs/); `roadmap/` is the **planning layer** (what's next) — deliberately separated
- `features/` `issues/` `refactors/` use `YYYY-MM-DD-{slug}/` to bundle all related specs in one directory, no crossing
- `compound/` is the **single** knowledge sink directory — plain markdown, no frontmatter, searched via `grep -r`. Easy to write, easy to find
- `reference/` is copied in by `cs-onboard` from the skill package; to change shared conventions, edit the templates under `cs-onboard/reference/` — new projects pick up the new version on onboard

### Hard constraint

> A skill is an independent install unit. At runtime, **each skill can only see files inside its own package**. References like `B-skill/reference/xxx.md` written in skill A's SKILL.md are **simply unreachable** at runtime.
>
> Cross-skill shared references must go through the "working project" layer: `cs-onboard` copies them from the skill package to the project's `codestable/reference/`, and other skills read them via the project-relative path.

To change shared conventions, edit the templates under `cs-onboard/reference/`; new projects pick them up at onboard time. See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full directory model and cross-skill reference constraints.

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

- [ ] Refactor flow needs hardening (`cs-refactor` is still beta)
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
