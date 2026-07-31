<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

The methodology in one line: **thin harness, thick context** — write responsibilities for strong models, not step-by-step scripts; retrieve context on demand, never preload it.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/cs--skills-8-6366F1?style=flat-square" alt="CodeStable Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## Install

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

`skills` CLI:

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable
```

If your `skills` CLI does not discover the plugin entity through the marketplace catalog, use the deep-scan fallback:

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable --full-depth
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
npx skills@latest remove \
  cs-audit cs-brainstorm cs-doc-api cs-doc-tutorial cs-docs cs-docs-neat \
  cs-domain cs-feat-accept cs-feat-design cs-feat-design-review cs-feat-ff \
  cs-feat-impl cs-feat-qa cs-feedback cs-goal cs-issue-analyze cs-issue-fix \
  cs-issue-report cs-note cs-refactor-ff cs-req cs-roadmap \
  cs-roadmap-impl-goal cs-roadmap-review \
  -g -y
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

The current `skills` CLI does not automatically remove skills that disappeared from a newer package during `add` or `update`. For a v1.0.4-to-v2.0.0 upgrade, the first command therefore removes the exact 24 retired CodeStable names, then the second installs all 8 v2 skills. Removal is name-based and does not verify the installation source: other names are untouched, but if you maintain a custom or third-party skill under one of these same names, back it up and remove that name from the command first. Future upgrades within the same major need only rerun `add`. For a project-scoped installation, omit `-g` from both commands and run them in that project. Historical v1 project assets (`compound/`, `features/`, and other directories plus old tools) remain untouched, need no per-repository runtime refresh, and stay covered by v2's kickoff retrieval — accumulated knowledge keeps getting read after the upgrade.

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
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>Project docs plus <code>.codestable/</code> project memory (readable by humans and AI)</td></tr>
<tr><td><b>Pain it solves</b></td><td>One agent isn't enough; need coordination to scale</td><td>Software complexity overflows context; tacit knowledge gets lost; requirements drift</td></tr>
<tr><td><b>Role of humans</b></td><td>The less the better — full automation is the ideal</td><td>Human-in-the-loop — the programmer owns the whole; AI is an efficient executor</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)

**Neither direction is wrong.**

If your task is "run an end-to-end automated pipeline with AI" or "have multiple agents debate a plan," the agent-orchestration camp fits better.

If your task is "maintain serious software that iterates over years" or "make sure a requirement written today can still be accurately recalled three months later" — then CodeStable's software-element-centric model fits better.

I built CodeStable because I believe **the chaos of software engineering isn't really about agents not being strong enough — it's about elements not being organized**. No matter how strong the agent, it can't save a project that's lost its requirements, architecture, and history.

---

## Design: thin harness, thick context

The core judgment: **the stronger the model, the more you should write responsibilities instead of steps.** CodeStable does not guard the model with state machines, process gates, or stage artifacts — it ships 8 **thin responsibility contracts** of 30–60 lines each — every skill states exactly three things: what must be achieved, what must not be crossed, and how completion is proven. The route belongs to the model.

Thin rules do not mean no boundaries. What remains are **hard gates**, each decidable in one sentence:

| Flow | Entry | Hard gate |
|------|------|--------|
| **Feature delivery** | `cs-feat` | High-risk designs are persisted to a work doc, pass independent agent review, then user confirmation — never auto-approved; test-first when a setup exists; completion requires verifiable evidence |
| **Issue fixing** | `cs-issue` | No root-cause guessing without a check that clearly turns red; the red check must turn green before claiming the fix |
| **Refactoring** | `cs-refactor` | Equivalence evidence exists before code changes; stop and report the moment behavior would change |
| **Epic delivery** | `cs-epic` | Decomposition passes independent review and user confirmation; one epic doc keeps the full picture; final acceptance is never done on the user's behalf |
| **Independent review** | `cs-review` | Read-only, independent subagent perspective; blocking findings must be resolved, fix-and-rereview capped at 3 rounds before human arbitration |

Engineering judgment does not occupy the always-loaded context: module depth, implementation economy, and debug escalation live in **on-demand references**, read only when the scene calls for them — the thin harness owns reliability, the thick context owns quality.

### The six homes of knowledge

The capture principle: **everything in its place, no archive hall**:

| Home | What it carries |
|------|--------|
| `attention.md` | Project facts read every session, ≤25 entries |
| `lessons/` | One file per pitfall, technique, or research result; traceable evidence required, dedupe-and-merge first |
| Project docs / ADRs | The canonical owner of current facts and structural decisions — CodeStable builds no parallel truth |
| `work/` | Active cross-session tasks, filenames type-prefixed feat-/issue-/refactor-/epic-; ordinary tasks create none |
| git / PR | Execution history |

Completed work docs **graduate before deletion**: the final report must list the graduation destinations — which conclusion went into which project doc, which lesson was distilled, or an explicit "nothing to graduate" — no list, no deletion. When a destination does not exist, the agent proposes one and keeps the doc until the owner decides.

---

## Skill catalog

### Current 8 skills

| Group | Skill | Purpose |
|---|---|---|
| Navigation | `cs` | Clear action requests dispatch to the target skill in the same turn; advice gets a recommendation only; the overview writes no files |
| Onboard | `cs-onboard` | Create the minimal project-memory skeleton for a repository |
| Feature | `cs-feat` | Implement new capability with process strength proportional to risk |
| Issue | `cs-issue` | Fix bugs or broken behavior with red-to-green evidence |
| Refactor | `cs-refactor` | Change structure or performance under behavioral-equivalence evidence |
| Epic | `cs-epic` | Decompose, confirm, and drive multiple items; sub-designs inline-first, standalone only when risk escalates |
| Review | `cs-review` | Independent review in three modes: diff / design / repo audit |
| Memory | `cs-keep` | Capture evidence-backed lessons and project facts with automatic tier selection |

`cs-code-review` is an alias of `cs-review` (forwarding only, no independent rules). See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the full catalog. Call `/cs` when you are unsure which entry fits.

---

## Workflow and project memory

Every entry shares one execution mainline: **understand the relevant facts → act → run proportionate verification → deliver**. Risk is re-judged per request — no persistent lanes, no stage state machines; ordinary tasks produce zero CodeStable artifacts — the diff, test output, and delivery summary are the evidence.

Captured knowledge only has value when it gets read: before acting, every skill greps `lessons/` and project docs by task keywords, and reports the sources of any hits.

After `/cs-onboard`, a new project has only this CodeStable-owned memory:

```text
.codestable/
├── attention.md
├── lessons/
└── work/
```

Skill-specific context and helpers belong to the owning skill. Requirements, domain models, and ADRs stay in the project's own documentation structure — CodeStable builds no parallel truth. See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full boundary.

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

- [x] Simplified the cs skills family: converged on 8 independent thin-harness skills
- [x] v2 dogfood loop in motion: same-turn dispatch, graduation lists, type-prefixed work docs, and the 3-round review cap all landed from real usage feedback
- [ ] Refactor flow needs hardening
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
