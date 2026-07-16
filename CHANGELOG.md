# Changelog

## Unreleased

- Added Vision Spec as a fourth core information responsibility under `.cs/vision/`, with user-journey-led recursive maps, candidate and mutually exclusive directions, lightweight realization state, and explicit extraction into development slices.
- Added an adaptive Vision action mode: AI helps individual developers organize their product world without forcing every idea into an Epic or Issue.
- Made Issues optional when ongoing management adds value; direct, clear changes and simple bug fixes can now be implemented and verified without creating work-item ceremony.
- Updated Talk, Spec, Complain, Do, Close, quality guidance, templates, initialization, skill metadata, and bilingual documentation to keep Vision, current truth, bounded change, and direct action responsibilities consistent.

## 0.6.0

- Adopted the nine ISO/IEC 25010:2023 product-quality characteristics as CodeStable's shared quality vocabulary without turning them into a compliance checklist.
- Added a quality commitment chain: stable constraints live in project/epic specs, issues select concrete objectives, Design responds to them, Do produces evidence, and Close enforces the selected commitments.
- Updated Talk, Spec, Explore, Complain, Design, Do, Close, issue/spec templates, and public documentation so quality objectives are inherited, risk-driven, explicit, and traceable.
- Kept testability under maintainability and observability as an engineering means rather than a competing top-level quality model.
- Added implementation-economy guidance distilled from Ponytail: minimize only after tracing the real flow, change the correct responsibility once, record bounded simplifications with an upgrade trigger, and leave the smallest useful runnable check.
- Kept repo-wide deletion audits and ungrounded savings scoreboards outside CodeStable's change-scoped model; added thin-adapter and deterministic-copy guidance for portable skills instead.
- Added versionable UI visual specifications: conditional ASCII wireframes for layout, Mermaid for flows and states, explicit current/target/illustrative labels, and screenshots or prototypes as evidence rather than sole truth.
- Defined UI truth placement across Project Spec, Epic Spec, local Issues, Design, Do, and Close without forcing empty UI sections into non-UI work.

## 0.5.0

- Repositioned Explore around **How it works**: trace a trigger through the current system to an observable result before designing a change.
- Added lightweight issue-scoped Explore and full reusable Explore issues, with change-specific impact analysis only when a concrete change exists.
- Made Explore artifacts progressively disclose a one-sentence model, main path, relevant branches, impact, unknowns, and evidence; Design now explains current behavior before proposing the future design.

## 0.4.0

- Removed `.cs/facts.md` from the CodeStable entity model, initialization script, templates, and documentation.
- Moved short startup-critical rules to an existing project `AGENTS.md` or `CLAUDE.md`; reusable background and procedures remain in `.cs/notes/`.
- Relied on agent frameworks to inject `AGENTS.md` / `CLAUDE.md`; CodeStable modes no longer model or proactively read them.
- Added a safe legacy rule: migrate old facts by value and never delete an existing `.cs/facts.md` without explicit confirmation.

## 0.3.0

- Replaced Codex and Claude plugin packaging with the standard `skills/cs/` repository layout.
- Made `npx skills add liuzhengdongfortest/CodeStable` the single installation path.
- Removed marketplace manifests and plugin-specific validation.
- Replaced the plugin package checker with a single-Skill repository checker and local Skills CLI discovery test.

## 0.2.0

- Collapsed the CodeStable LITE plugin into one user-facing `cs` skill with action and principle references loaded on demand.
- Made project spec, epic spec, and issue the core model explained directly in `SKILL.md`, including truth precedence and close-time knowledge promotion.
- Simplified each epic to one authoritative `spec.md`; status, current progress, issue links, blockers, close conditions, and graduation candidates now live together.
- Centralized templates and initialization scripts inside the unified skill, and removed the old `cs-*` installation units.
- Replaced the 150-line document threshold with a judgment-based concision and progressive-disclosure rule.

## 0.1.1

- Refined project and epic spec workflows around developer-facing usage narratives instead of code-layer structure.
- Reworked `cs-spec-explore` into a user-controlled alignment loop that creates exploratory issue workspaces with candidate spec articles.
- Split issue templates by scenario and removed the generic issue template.
- Clarified close behavior so confirmed exploratory articles graduate into project spec according to spec organization rules.

## 0.1.0

- Added the CodeStable LITE plugin distribution under `plugins/codestable-lite/`.
- Packaged the same skill set for Codex and Claude plugin installation.
- Added marketplace metadata and version manifests for release validation.
- Moved root `cs` / `cs-*` skill directories into `plugins/codestable-lite/skills/`.
- Folded `cs-test` into `cs-design`; detailed testing strategy now lives inside implementation design when needed.
