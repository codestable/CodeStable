<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-32-6366F1?style=flat-square" alt="CodeStable Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## Install

Codex plugin marketplace:

```bash
codex plugin marketplace add liuzhengdongfortest/CodeStable
codex plugin add codestable@codestable
```

Claude plugin marketplace:

```text
/plugin marketplace add liuzhengdongfortest/CodeStable
/plugin install codestable@codestable
```

`skills` CLI:

```bash
npx skills@latest add liuzhengdongfortest/CodeStable
```

If your `skills` CLI does not discover the plugin entity through the marketplace catalog, use the deep-scan fallback:

```bash
npx skills@latest add liuzhengdongfortest/CodeStable --full-depth
```

The CodeStable plugin only packages `cs` / `cs-*` skills under `plugins/codestable/skills/`; the repository root no longer keeps standalone skill directories.

## Upgrade

After a new release, check `CHANGELOG.md` for the version changes, then refresh through the entry point you used to install.

Codex plugin marketplace:

```bash
codex plugin marketplace upgrade codestable
codex plugin add codestable@codestable
```

The current Codex CLI has no separate `plugin update` subcommand; `marketplace upgrade` refreshes the Git marketplace snapshot, and `plugin add` installs the current version from that refreshed snapshot.

Claude plugin marketplace:

```text
/plugin marketplace update
/plugin update codestable@codestable
```

Restart Claude Code after updating so the new plugin version is applied.

`skills` CLI:

```bash
npx skills@latest update
```

If an older installer did not record the source, rerun the `npx skills@latest add liuzhengdongfortest/CodeStable` install command above. Upgrade the complete CodeStable plugin rather than replacing only the root `cs` skill; runtime refresh also requires the matching `cs-onboard` skill and its tools. After the global plugin upgrade, explicitly run `/cs-onboard --mode refresh-runtime` in every onboarded project to refresh and verify its repo-local runtime immediately. If you skip the command, the next CodeStable preflight compares `.codestable/runtime-manifest.json` with the current plugin version and refreshes automatically when the manifest is missing, the version or runtime capabilities do not match, and managed paths are clean; it does not scan repositories in the background. `managed-paths-dirty`, a repository that is not onboarded, or an incomplete skeleton stops the refresh instead of forcing an overwrite.

One command to start working:

```bash
/cs-onboard
```

For daily use, when you don't know which skill fits, call the root entry:

```bash
/cs
```

`cs` classifies whether you want execution, advice, or an overview. Action requests dispatch to the target skill in the current run; advice requests only recommend. Ambiguous requests get one focused question.

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
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>The <code>.codestable/</code> file tree in your project (readable by both humans and AI)</td></tr>
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
| **Requirement** | requirements | User stories + domain glossary (CONTEXT.md) + architecture decisions (ADRs). The escape hatch when code rots |
| **Epic** | epic | Large demand entry such as "I want a permission system"; user-facing docs call it epic while v1 still stores internal artifacts under `.codestable/roadmap/` |
| **Goal** | goals | Bounded start/end: write a start report, then let AI iterate autonomously with subagent functional acceptance before completion |
| **Feature** | feature | Engineering execution where human and AI share responsibility for design, implementation, QA, and acceptance |
| **Issue** | issue | Bug records and fixes after something should already work |
| **Refactor** | refactor | Behavior-preserving cleanup when code rots (beta) |
| **Compound** | compound | The compounding-engineering knowledge base: pitfalls, tricks, decisions, and investigation notes |

### Flows

| Flow | Recommended main entry | Notes |
|------|------------|------|
| **Feature delivery** | `cs-feat` | End-to-end design → design review → user gate → long-range goal run of implementation → `cs-code-review` → QA → acceptance |
| **Epic delivery** | `cs-epic` | Plan a large demand, review it, design child features, prepare a goal package, then dispatch a visible goal driver (print `/goal` as fallback) |
| **Goal achievement** | `cs-goal` | Bounded start/end → interview/grill + start report → autonomous implement/validate/iterate → subagent functional acceptance |
| **Issue fixing** | `cs-issue` | End-to-end report → analyze → fix → `cs-code-review` |
| **Refactoring** | `cs-refactor` | Behavior-preserving cleanup; standard or fastforward mode, followed by `cs-code-review` |
| **External docs** | `cs-docs` | Developer guides, user guides, and API references; hygiene stays in `cs-docs-neat` |

`cs-code-review` is the cross-cutting quality gate at the tail of execution flows, before commit. At a phase or milestone boundary, use `cs-docs-neat` to reconcile `.codestable/`, README/docs, `CLAUDE.md` / `AGENTS.md`, and agent memory so docs do not drift from code.

---

## Skill catalog

### Recommended main entries

| Group | Skill | Purpose |
|---|---|---|
| Root | `cs` | Action requests dispatch to the target skill in the current run; advice requests only recommend. |
| Onboard | `cs-onboard` | Install CodeStable into a repository |
| Requirements & domain | `cs-req` / `cs-domain` | Capture capability intent, domain terms, ADRs, and context topology |
| Epic | `cs-epic` | Large demand planning, review, child feature design, and goal package |
| Brainstorm | `cs-brainstorm` | Triage fuzzy ideas into feature, epic, or brainstorm notes |
| Goal | `cs-goal` | Autonomous iteration from a bounded start state to acceptance |
| Feature | `cs-feat` | End-to-end feature workflow |
| Issue | `cs-issue` | End-to-end issue workflow |
| Refactor | `cs-refactor` | Behavior-preserving refactor workflow |
| Review | `cs-code-review` | Cross-cutting read-only implementation review gate |
| Audit | `cs-audit` | Scan for bugs, security, performance, maintainability, and architecture drift |
| Feedback | `cs-feedback` | Explicitly capture current-session incidents/triage; upload only after preview confirmation |
| Knowledge | `cs-keep` / `cs-note` | Capture durable knowledge or short startup-critical notes |
| External docs | `cs-docs` | Developer guides, user guides, and API references |
| Docs hygiene | `cs-docs-neat` | Sync `.codestable/`, README/docs, agent entries, and memory |

### Long-term compatibility entries

Old skill names remain usable but only enter the corresponding main workflow:

- Feature: `cs-feat-design` / `cs-feat-design-review` / `cs-feat-impl` / `cs-feat-qa` / `cs-feat-accept` / `cs-feat-ff`
- Issue: `cs-issue-report` / `cs-issue-analyze` / `cs-issue-fix`
- Refactor: `cs-refactor-ff`
- Docs: `cs-doc-tutorial` / `cs-doc-api`
- Epic: `cs-roadmap` / `cs-roadmap-review` / `cs-roadmap-impl-goal`

See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the full catalog. In daily use, call `/cs` when you are unsure.

---

## Workflow at a glance

CodeStable is layered and event-driven:

```text
cs
└── cs-onboard
    ├── cs-req / cs-domain
    ├── cs-epic          # user-facing epic; internally still roadmap storage
    ├── cs-goal
    ├── cs-brainstorm
    ├── cs-feat     -> cs-code-review
    ├── cs-issue    -> cs-code-review
    ├── cs-refactor -> cs-code-review
    ├── cs-docs
    ├── cs-feedback
    └── cs-keep / cs-note / cs-docs-neat
```

How to read it:

- `cs` classifies the intake mode before the target. Action requests dispatch to the target skill in the current run; advice requests only recommend. It never routes users to deprecated stage skills.
- `cs-feat`, `cs-issue`, and `cs-refactor` resume from repository facts. `cs-issue` and `cs-refactor` stop at review, blocking, or user-confirmation checkpoints; `cs-feat` stops only at the design gate, then runs impl, review, QA, and accept long-range via a visible goal driver.
- `cs-epic` prepares planning and goal packages, then dispatches a visible goal driver; v1 still writes `.codestable/roadmap/`.
- `cs-code-review` is the cross-cutting gate; `cs-docs-neat` handles hygiene; `cs-docs` writes outward docs.
- `cs-feedback` explicitly captures a local-private current-session evidence package; public issue upload remains separately confirmed.
- Old stage skills are long-term compatibility entries for historical users.

See [WORKFLOW.en.md](./WORKFLOW.en.md) for the compact diagram.

---

## Runtime structure

After `/cs-onboard`, project artifacts aggregate under `.codestable/`. Python tool scripts run from the installed `cs-onboard` skill package instead of being copied into each repo.

```text
.codestable/
├── attention.md
├── requirements/  roadmap/  goals/
├── features/  issues/  refactors/
├── audits/  brainstorms/  feedback/  compound/
├── gates/
└── reference/
```

`requirements/` is the long-lived archive, `roadmap/` is planning, dated work-item directories bundle one workflow, and `compound/` is the single knowledge sink. A skill is an independent install unit: cross-skill references must be released by `cs-onboard` into project-local `.codestable/reference/`, never read from a sibling skill package. See [WORKFLOW.en.md](./WORKFLOW.en.md) for the directory contract.

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
