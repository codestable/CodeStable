# CodeStable Roadmap

**English** · [中文](./ROADMAP.md)

CodeStable is not trying to accumulate process. As models and hosts improve, constraints that no longer add reliability should be removed.

[CHANGELOG.md](./CHANGELOG.md) is the source for shipped facts. This document tracks ongoing direction and does not replace release notes.

## Completed

- [x] Reduced the 32 v1 entries to 8 independent thin-harness skills.
- [x] Established one canonical skill source shared by Codex, Claude, and `skills` CLI distribution.
- [x] Replaced distributed project runtime with `attention.md`, `lessons/`, and `work/`; new projects create only minimal memory.
- [x] Made `cs` support same-turn explicit action, current-session discussion, and handoff after alignment.
- [x] Established the two-layer Epic model with a permanent document, temporary execution cursor, and three owner gates.
- [x] Evaluated routing and process contracts through fixtures and real-agent comparisons.

## Near Term

- [ ] Expand outcome evaluation across multi-item Epics, long-running recovery, and cross-model consistency.
- [ ] Harden `cs-refactor`, especially behavioral-equivalence evidence and performance refactors.
- [ ] Increase real-environment coverage for installation, upgrades, and release regression.
- [ ] Use real project feedback to remove repeated confirmation, low-value artifacts, and obsolete constraints.

## Long-Term Test

These signals should remove process instead of adding wrappers:

- models reliably establish and explain evidence for a task class;
- hosts reliably provide equivalent isolation, review, or recovery;
- a rule adds text and waiting without reducing failure probability;
- the project already has a better canonical mechanism for the same fact.

Issues with real development constraints, failures, and reproducible evidence are welcome. They should shape this roadmap more than abstract feature requests.

Return to the [README](./README.en.md).
