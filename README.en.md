<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

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
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

The bare `skills` CLI `update` currently uses different discovery rules for plugin manifests and generic directories, so it can misclassify existing sibling skills as deleted. Upgrade with the full-package reinstall command above instead. It synchronizes every `cs*` skill from `plugins/codestable`; for a project-scoped install, omit `-g` and run it in that project. Since v2, all rules live in the skill package itself — there are no runtime assets inside projects to refresh, so upgrading the plugin is the whole procedure.

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

| Entity | Carrier | What it does |
|------|------|--------|
| **Attention** | `attention.md` | Project facts read every session, ≤25 entries |
| **Lessons** | `lessons/` | The compounding knowledge base: pitfalls, good practices, investigation notes — one markdown file per lesson, grep-searchable, every entry backed by traceable evidence (`cs-keep`) |
| **Active work** | `work/` | The single state document for cross-session / handoff / epic tasks (goal / context / boundaries / evidence / acceptance / status-and-open-items), compressed and deleted on completion |

Ordinary tasks produce no CodeStable entities at all — the git diff, test output, and delivery summary are the evidence.

### Flows

| Flow | Entry | Hard gate |
|------|------|--------|
| **Feature delivery** | `cs-feat` | On risk escalation the design passes independent agent review, then user confirmation — never auto-approved; test-first when a test setup exists; completion requires verifiable evidence |
| **Issue fixing** | `cs-issue` | No root-cause guessing without a verification that clearly turns red; the red verification must turn green before claiming the fix |
| **Refactoring** | `cs-refactor` | Equivalence verification exists before code changes; stop and report the moment behavior would change |
| **Epic delivery** | `cs-epic` | Decomposition is user-confirmed before execution; one epic document keeps the full picture; final acceptance is never done on the user's behalf |
| **Independent review** | `cs-code-review` | Read-only; independent subagent perspective; designs and changes reviewed by default; blocking findings must be resolved, fix-and-rereview capped at 2 rounds before human arbitration |

Every flow shares one mainline: understand the relevant facts → act → run proportionate verification → deliver. Risk is re-judged per request — no persistent lanes, no stage state machines.

---

## Skill catalog

v2 ships 8 skills — a thin layer of engineering discipline plus a project-memory loop (thin harness, thick context):

| Skill | Purpose |
|---|---|
| `cs` | System overview and entry recommendation; explains only, never starts a workflow |
| `cs-onboard` | Create the minimal `.codestable/` skeleton; v1 legacy preserved untouched |
| `cs-feat` | New features and changes; on risk escalation the design passes independent review, then user confirmation |
| `cs-issue` | Bug fixing; no root-cause guessing without a red verification |
| `cs-refactor` | Behavior-preserving refactoring; equivalence verification first |
| `cs-code-review` | Independent review: diff / design / repo-audit modes |
| `cs-epic` | Large-requirement decomposition and long-running delivery |
| `cs-keep` | Distill experience; traceable evidence required |

The v1 stage skills and long-tail entries (design/impl/qa stage skills, `cs-goal`, `cs-brainstorm`, the `cs-docs` family, `cs-domain`, `cs-req`, `cs-audit`, `cs-note`, `cs-feedback`, the `cs-roadmap` family) have been folded into the table above. See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the full catalog. In daily use, call `/cs` when you are unsure.

---

## Workflow and runtime

Every entry shares one execution mainline: **understand the relevant facts → act → run proportionate verification → deliver**. Risk is re-judged per request from current facts — no persistent lanes, no stage state machines. Before acting, grep the project's accumulated knowledge (including v1 legacy) by task keywords and report the sources of hits. Design and acceptance confirmations are never auto-approved by the model.

`/cs-onboard` creates a minimal `.codestable/`: `attention.md` (read every session, ≤25 entries), `lessons/` (one file per lesson, grep-searchable), and `work/` (active cross-session tasks, compressed and deleted on completion). Ordinary tasks produce zero artifacts; there are no gates, no runtime tools, and no references copied into projects. v1 artifacts in existing projects are kept read-only and stay grep-discoverable.

See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full contract.

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

- [x] v2 thin-harness rewrite: 32 skills consolidated into 8 thin responsibility contracts (~24k lines → ~340 lines), all state machines / gates / stage artifacts removed; ordinary tasks produce zero artifacts; knowledge unified into attention + lessons + work
- [ ] Refactor flow needs hardening
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
