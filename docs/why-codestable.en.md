# Why CodeStable

**English** · [中文](./why-codestable.md)

## The Starting Point

CodeStable began with a concrete problem: AI can produce code quickly, while an evolving project keeps losing boundaries, decisions, and context.

A repeated failure often means not that the model cannot code, but that the project failed to organize what it already knew.

Putting more prompts into a session does not solve this. Context expires, conversations end, and implicit agreements drift.

Serious engineering needs current code, product contracts, historical decisions, and verification evidence to remain discoverable in later work.

## A Different Problem from Agent Orchestration

Agent orchestration asks who should work, how agents form teams, and how tasks move between them. CodeStable asks which durable elements make up the software and how those elements are confirmed, verified, preserved, and reused.

| | Agent Orchestration | CodeStable |
|---|---|---|
| Core entity | Agent, role, team | Feature, Issue, Epic, Decision, Evidence |
| Main question | How do agents collaborate and relay work? | How do software boundaries, decisions, and knowledge remain valid? |
| State home | Sessions, queues, message buses | Code, project docs, and minimal project memory |
| Human role | Choose the level of automation | Own product boundaries and final acceptance |

![The different focus of agent orchestration and CodeStable](../asset/CodeStableVSAgent.png)

The two directions can coexist. A host may organize one agent or many; CodeStable only constrains the software task's responsibility, boundaries, evidence, and knowledge homes.

## thin harness, thick context

The stronger the model, the more it should receive responsibilities instead of step-by-step scripts.

CodeStable skills are thin: they state what must be achieved, what must not be crossed, and how completion is proven.

They do not force every task through one set of stages or use a permanent state machine to replace local engineering judgment.

Task type determines the engineering method; actual risk determines assurance strength:

```text
Execution flow = minimum complete loop + the least assurance required by each unexcluded risk
```

Independent review is not a default step. Each risk adds only the assurance directly required by that risk.

Context should be thick but loaded only when needed. The current task retrieves project facts, adjacent implementation, historical lessons, and engineering guidance by keyword and situation instead of preloading a manual into every session.

## Human in the Loop Is Not Approval at Every Step

Human involvement should not mean repeatedly clicking “continue.” Explicit actions should execute directly, and ordinary steps should advance without ceremony.

The owner is needed when a product contract changes, a major risk is accepted, a hard-to-reverse choice is made, or the whole delivery is accepted. Verification, independent review, and owner gates should all be proportionate to risk.

This division makes AI an efficient executor while preserving the programmer's responsibility for software that remains observable, controllable, and evolvable.

## Project Knowledge Is an Engineering Asset

Domain terms, requirements, architecture decisions, failed approaches, and acceptance evidence should not live only in chat. Copying all of them into a new archive, however, creates another source of drift.

CodeStable keeps one canonical owner for each fact: stable product facts return to project docs, structural
trade-offs enter ADRs, and experience without a stronger owner is staged in lessons.

A shared language follows the same rule. It activates only when terminology ambiguity can change behavior or a route:
a Feature converges local semantics, an Epic converges concept relationships, and existing project domain docs keep
owning stable definitions instead of having every task copy a glossary.

Session-critical facts enter attention, and durable Epic contracts enter permanent Epic documents.

A large initiative whose route is still unclear must not masquerade as a complete plan. The permanent Epic document
itself is the route map: decision dependencies derive the frontier, the agent resolves facts, and only product
judgment or real trade-offs enter HITL. Only when the route is clear, reviewable, and executable does an execution
agent take over. Exploration and the final route share one factual owner rather than a separate issue map.

Only active cross-session state uses a temporary work cursor. Ordinary work relies on the diff, test output, and delivery summary as evidence and creates no extra stage documents.

## Experience Evolves Through Verification

Experience is not an activity log. CodeStable silently recognizes crystallization moments that truly change a
plan, root cause, or verification, or explicitly rules out a concrete, plausible wrong path. It keeps a candidate
only when it has evidence, applies beyond the exact diff, and has no stronger owner. Without a strong signal,
completion gains no extra ritual.

A lesson is staging, not a permanent archive. An independent later task validates it; changed facts retire it;
and mechanizable failures move into tests or checkers. The project accumulates methods that reduce failure instead
of an ever-growing set of prose rules.

## Deliberate Non-Goals

- No agent teams, role queues, or automatic relay system.
- No parallel requirements, domain-model, or ADR truth beside the project's own structure.
- No large set of stages, templates, or runtime gates designed to contain strong models.
- No promise of full autonomy; owners still make consequential product decisions.
- No cross-session recovery promise for unresolved discussion.

## How It Evolves

CodeStable is not trying to accumulate process. When model capability, host capability, or simpler evidence reliably replaces a constraint, that constraint should disappear.

See the [roadmap](../ROADMAP.en.md) for current direction, the [changelog](../CHANGELOG.md) for shipped changes, and the [workflow](../WORKFLOW.en.md) for the runtime contract.
