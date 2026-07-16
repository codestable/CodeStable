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

Install with the Skills CLI:

```bash
npx skills add liuzhengdongfortest/CodeStable
```

Installation is project-local by default. Add `-g` to make it available across projects:

```bash
npx skills add liuzhengdongfortest/CodeStable -g
```

For local development, verify discovery from the repository root:

```bash
npx skills add . --list
```

Use the single entry to onboard a project:

```bash
/cs onboard CodeStable in this project
```

Use that same entry for vision shaping, requirements, specs, direct changes, managed issues, closing, and knowledge capture:

```bash
/cs
```

`cs` first determines whether the user is asking, imagining, discussing, or authorizing action, then uses a vision spec, project spec, epic spec, or issue only when it adds value. CodeStable changes the agent's judgment; it does not force the user through a fixed workflow.

The repository distributes one Skill at `skills/cs/`; action rules, design principles, templates, and scripts load progressively inside it. The released version lives in `VERSION`, with release notes in `CHANGELOG.md`.

## Upgrade

After a new release, check `CHANGELOG.md`, then update the installed `cs` Skill:

```bash
npx skills update cs
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
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Vision spec · project spec · epic spec · issues</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How do the software's target world, current truth, change lines, and closeable work get organized and evolved?</td></tr>
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

## Design: vision spec + project spec + epic spec + issues when useful

CodeStable separates four responsibilities: the target application world, current project truth, bounded evolving changes, and closeable work that is worth managing over time. They are not stages every request must pass through.

### vision spec — the target application world

The vision spec lives in `.cs/vision/`. It lets an individual developer externalize the product in their head: how users eventually get results, which capability areas make up the application, which imaginative ideas and mutually exclusive directions remain open, and which areas are planned, under construction, or real.

Vision is a recursively expandable product map. Each `index.md` leads with user journeys and uses the capability landscape as a secondary view. The agent does more than transcribe: it helps place, divide, connect, and challenge ideas. Vision is not a roadmap or task board; detailed delivery state remains in epics and issues.

### project spec — the mainline truth

The project spec lives in `.cs/spec/`. It tells a new developer what the project currently is, which capabilities and boundaries already hold, how the architecture expands, and where shared language lives. The target future belongs in Vision; Project Spec keeps stable current truth.

Shared language belongs in the nearest `index.md` where it applies, not in a separate domain hierarchy. A spec does not record change logs; it explains why the current design, boundaries, and trade-offs stand.

### epic spec — a large-change line

Large changes live in `.cs/epics/YYYY/MM/DD/{短语}/spec.md`. An epic may extract a slice from Vision or begin from a current problem. Its `spec.md` is the single authority for status, current requirements, architecture considerations, direct slices and issue links, blockers, close conditions, and graduation candidates.

Issues under an epic close back into the epic spec first. Only when a human confirms the whole epic is done does AI merge the graduated conclusions back into the project spec.

### issues — closeable work when ongoing management helps

Use an issue when a change has scope trade-offs, needs multiple rounds or sessions, needs handoff and history, or the user explicitly wants tracking. A small, clear, one-session bug, feature, or chore can be changed and verified directly. Even an epic creates issues only when the continuing record pays for itself.

The close rule is simple: independent issue → Project Spec; exploratory issue → confirmed stable understanding in Project Spec; epic issue → Epic Spec; user-confirmed epic close → Project Spec plus realization state and links in the source Vision.

## How quality follows a change

CodeStable uses the nine product-quality characteristics from [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) as a shared vocabulary: functional suitability, performance efficiency, compatibility, interaction capability, reliability, security, maintainability, flexibility, and safety. This is an engineering decision model, not a claim of ISO compliance or certification.

```text
Target quality directions in Vision
                    ↓ extract and confirm
Stable quality constraints in Project / Epic Spec
                    ↓ inherit
Risk discovery in Talk / Explore / Complain
                    ↓ select
Issue objectives / necessary boundaries for a direct change
                    ↓ realize
Design decisions → Do evidence → Close check and write-back
```

- The nine characteristics are a risk lens, not a nine-row “met / not applicable” checklist.
- Vision may preserve target quality directions, but a development slice confirms them again. An issue selects only objectives that change its design or acceptance.
- Relevant spec constraints are inherited automatically. The agent identifies ordinary engineering risks; users decide thresholds, material cost, compatibility policy, and conflicts between objectives.
- Selection creates a commitment: Design responds to every objective, Do produces evidence, and Close passes only when that evidence is sufficient.
- A direct change does not create a formal quality checklist, but it still obeys relevant specs, explicit user requirements, security, data protection, accessibility, and necessary verification.
- Testability remains a maintainability subcharacteristic. Observability remains an engineering means that supports reliability, analysability, and evidence instead of becoming a competing quality model.

## How implementation stays economical

CodeStable tightens “write less code” into a **minimum sufficient change**: understand the real trigger-to-result path first, then try no new behavior, deletion or narrower scope, reuse in the correct owner, the standard library, native platform features, and installed dependencies before writing new code. A small diff beside the symptom is not small if the responsibility belongs elsewhere.

- Do not prepay for imagined futures with single-implementation interfaces, unset configuration, forwarding wrappers, or unnecessary dependencies.
- When a deliberately simple solution has a capacity, environment, or algorithmic ceiling, record that ceiling, the observable upgrade trigger, and the layer to replace. Do not build the future before the trigger, and do not hide an already-triggered limit as “later.”
- Leave at least one smallest useful runnable check for non-trivial logic, preferably through an existing test entry point instead of a new framework.
- Trust-boundary validation, data-loss prevention, security, accessibility, dangerous-action safeguards, explicit user requirements, and selected quality objectives are not optimization targets.
- Without a real comparison baseline, report what was removed or avoided; do not invent LOC, cost, or time savings.

## How UI specs use visuals

When spatial relationships, information hierarchy, or multi-state interaction affect the meaning of a UI requirement, CodeStable keeps a versionable visual specification in Vision or the relevant spec. Projects without relevant UI, and simple copy or styling changes, do not keep empty visual sections.

- ASCII wireframes express layout, regions, hierarchy, and major controls; Mermaid expresses navigation flows or state transitions.
- Vision Spec shows the target application experience and candidate directions across epics. Project Spec shows the stable current interface; Epic Spec shows the bounded target change; an Issue stays local; Design maps the contract to implementation.
- Adjacent annotations identify the role and entry point, interaction and key states, stable constraints, and merely illustrative details. A diagram/text conflict must be resolved before implementation.
- Screenshots, high-fidelity designs, and prototypes may serve as visual evidence, but not as the only specification. A wireframe clarifies an interaction objective; it does not replace runnable behavior or accessibility evidence.

---

## Skill catalog

The repository distributes one `cs` Skill. Users no longer choose among a catalog of skill names; `cs` first identifies what the user wants now, then loads the relevant internal mode:

| Intent | What `cs` does internally |
|---|---|
| First-time setup | Create or complete the `.cs/` skeleton without silently migrating old requirements |
| Imagining the whole application | Help the user shape a navigable product map under `.cs/vision/` without forcing immediate delivery |
| Fuzzy local idea or planning | Inspect context, clarify the real problem, then directly change, update Vision, create an issue / epic, or continue exploring |
| Spec change | Maintain the project spec or the epic's single `spec.md` |
| Behavior breaks expectations | Diagnose, fix, and verify through a feedback loop; direct for simple bugs, managed by issue when tracking helps |
| Clear change | Implement when authorized; write back to an issue when one exists, and do not invent one otherwise |
| How the system works is unclear | Trace trigger to result with lightweight Explore; promote to a full exploratory issue when complex or reusable |
| Reusable knowledge | Write notes, agent instructions, or tools; learn unknown workflows under human guidance |

Action rules and principles for code design, debugging, documentation, and skill design live under `cs/references/` and load only when the current situation needs them.

---

## How the structure evolves

CodeStable is not a linear pipeline. Four information responsibilities collaborate only when useful:

```text
Vision Spec ──extract target slice──> Epic Spec ──issues as useful──> Issues
     │                                │                              │
     │                                └──close and graduate──────────┤
     │                                                               ↓
     └──target world                              Project Spec (current reality)

Small clear change ──implement and verify directly──> Project Spec (only if current truth changes)
```

**How to read this diagram:**

- **Vision is the target world; Project Spec is current reality** — their difference is an intentional product gap, not a precedence conflict
- **Epic Spec is a bounded change line** — it may extract from Vision, graduates into Project Spec, and updates Vision's realization links at close
- **Issues are optional ongoing records** — use them when tracking helps; implement and verify small clear changes directly
- **Support files are the flywheel**: any work item that surfaces something worth keeping triggers a sink; the next round of work reads it back — the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs` onboards the project, a `.cs/` directory appears at the project root — the aggregate root for specs, work items, and knowledge artifacts.

```
your-project/
├── .cs/
│   ├── talks/                # Discussion synthesis (written only after confirmation)
│   │   └── YYYY/MM/DD/{短语}.md
│   ├── vision/               # Vision spec: target application world
│   │       ├── index.md
│   │       └── ...           # Recursive product map led by user journeys
│   ├── spec/                 # Project spec: mainline truth
│   │       ├── index.md
│   │       └── ...           # Recursive reading path; each layer may have its own index.md
│   │
│   ├── issues/               # Closeable work items, sharded by creation date
│   │   ├── YYYY/MM/DD/{status}-{短语}.md   # ordinary issues
│   │   └── YYYY/MM/DD/{status}-{短语}/     # full Explore: index + trigger-to-result path articles
│   ├── epics/                # Large-change lines
│   │   └── YYYY/MM/DD/{短语}/
│   │       └── spec.md       # Single authority: spec, direct slices, issues, blockers, close conditions
│   │
│   ├── notes/                # Knowledge notes, plain markdown, full-text search
│   │   └── YYYY/MM/DD/{短语}.md
│   │
│   └── tools/                # Shared scripts captured after a workflow is proven
│
└── (other project files)
```

**Key points:**

- Specs, work items, and knowledge artifacts aggregate under `.cs/`, so "how did we handle that change last time" is three seconds away
- `vision/` holds the target application world, candidates, and mutually exclusive directions; AI helps organize the map and writes only after user confirmation
- `spec/` is the project spec, organizing mainline requirements, architecture considerations, shared language, and reading paths for a developer entering the project
- `epics/` are large-change lines; at close they graduate into Project Spec and check realization state and links in their source Vision
- Small clear changes can be implemented and verified without an issue; use issues when complexity, risk, multiple sessions, or history make them valuable
- Before changing code, trace how a trigger produces its result; keep the lightweight model in current context or the target issue, and promote to full Explore only when it crosses unclear boundaries or deserves reuse
- A full Explore `index.md` carries the one-sentence model, boundary, and reading path; path articles progressively reveal the main flow, responsibilities, data, state, relevant branches, and evidence
- On close, stable How-it-works knowledge graduates progressively into project spec; change-specific impact stays in the target issue, while evidence and excluded interpretations remain in the Explore issue
- Talks and notes default to `YYYY/MM/DD/{短语}.md` date shards, epics use `YYYY/MM/DD/{短语}/` workspaces, ordinary issues use `YYYY/MM/DD/{status}-{短语}.md`, and exploratory issues use `YYYY/MM/DD/{status}-{短语}/` workspaces; search recursively under each area
- `notes/` is the knowledge notes area — plain markdown, no frontmatter, full-text searchable. `cs` decides whether daily "remember this" work belongs in notes or project agent instructions
- Human-guided unknown workflows become `notes/`; add a one-line reference to `AGENTS.md` or `CLAUDE.md` only when the workflow is a stable prerequisite for related work, and produce `tools/` only when automation is stable
- The agent framework injects root instruction files automatically, so `cs` neither reads them proactively nor models them under `.cs/`; prefer an existing `AGENTS.md` for cross-agent rules and `CLAUDE.md` for Claude-only rules
- Keep Markdown appropriately concise without a universal line limit; preserve the complete core structure, background, principles, and contracts in the main narrative, and progressively disclose only details that are scenario-specific or obstruct the reading flow

### Hard constraint

> CodeStable has one installed `cs` unit. Its core structure and shared boundaries live in `SKILL.md`; scenario-specific action rules and principles live in that same skill's `references/`, with templates and scripts in the same package.
>
> `SKILL.md` must say when to read each reference. It must not hide core contracts or load every scenario at once. The target application world belongs in `.cs/vision/`, stable project truth in `.cs/spec/`, reusable knowledge in `.cs/notes/`, and short startup rules directly in `AGENTS.md` or `CLAUDE.md`.

Before switching internal modes, `cs` first decides whether the user is asking, imagining, discussing, or authorizing action. It reuses a known vision, project spec, epic spec, or issue when current, and confirms the target file's latest version before writing.

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

- [ ] Keep refining Vision shaping and extraction into development slices
- [ ] Keep refining adaptive choice between direct change, Issue, and Epic
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
