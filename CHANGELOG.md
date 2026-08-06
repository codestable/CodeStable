# Changelog

## 2.0.2

- Added the owner-gated `item_progression: parallel` policy to `cs-epic`: the main workflow stays the
  sole orchestrator and cursor writer, workers execute dependency-independent items in host-provided
  isolated workspaces, and integration is serialized without advancing mainline history until per-item
  re-verification passes (protocol in `references/parallel-execution.md`).
- Scoped the skill-coupling rule to file-level dependencies; mentioning or routing to another skill by
  name remains allowed.

## 2.0.1

- Replaced task-shape workflow tiers with minimum sufficient assurance selected from unexcluded risks.
- Added pre-approval Epic route discovery with a document-owned route map, derived frontier, and explicit HITL decisions.
- Added conditional shared-language alignment for Feature and Epic design without introducing a mandatory glossary or new gate.
- Removed stale experiments for retired v1 skill entries and tightened experiment-to-skill consistency checks.

## 2.0.0

- Reduced the shipped package from the 32 skills in v1.0.4 to 8 thin-harness skills: `cs`,
  `cs-onboard`, `cs-feat`, `cs-issue`, `cs-refactor`, `cs-review`, `cs-epic`, and `cs-keep`.
- Renamed `cs-code-review` to `cs-review` — it now reviews designs and runs audits, not only code.
  `cs-code-review` ships as the single thin compatibility alias (forwarding only), the one exception
  to the no-shim rule below.
- Retired the other 24 v1 entry names without compatibility shims. A one-time exact-name removal is
  required before the `skills` CLI full-package reinstall because that CLI does not prune removed
  package members. Removal is name-based, so same-name custom skills require an explicit backup.
- Replaced distributed project runtime assets with minimal project memory: `attention.md`, `lessons/`,
  and `work/`. Existing v1 artifacts remain untouched and searchable, but v2 does not execute or
  refresh legacy tools, gates, hooks, references, or manifests.
- Reworked `build-cs-skill` around `thin harness, thick context`, direct semantic tests, explicit rule
  ownership, context plans, and continuous compression; frontmatter `contracts` are no longer used.
- Separated frozen v1 experiment fixtures from the active v2 contract and added v1.0.4-to-v2
  distribution, architecture, and documentation coverage.

## 1.0.4

- Hardened CodeStable workflow contracts across Epic dependency admission, Goal authorization, checkpoint resume, independent review, runtime safety, and release gates.

## 1.0.3

- Added the `cs-feedback` evidence pipeline for collecting local Codex and Claude session context, triaging incidents, and producing privacy-safe public issue previews.
- Added candidate-only fixture conversion in the shipped plugin and fail-closed regression fixture promotion in the repository evaluation tooling.
- Hardened current-session discovery, trigger cutoffs, provider-aware tool pairing, public redaction, and upload confirmation gates.

## 1.0.2

- Hardened runtime upgrades: versionless or mismatched manifests now require synchronization, while `/cs-onboard --mode refresh-runtime` refreshes package-owned assets without overwriting dirty managed paths.
- Updated the root `cs` router so action requests dispatch to the target skill in the current run, while advice and overview requests remain non-executing.
- Synchronized Codex and Claude marketplace versions and documented complete-plugin plus per-repository upgrade steps.

## 1.0.1

- CodeStable skill simplification release.

## 1.0.0

- Simplified CodeStable skill entrypoints around main workflow skills and compatibility wrappers.
- Added `cs-feat`, `cs-epic`, and `cs-docs` main entries with explicit `--stage` / `--mode` argument semantics.
- Added long-running goal driver semantics for feature and epic flows, including `/goal` fallback instructions.
- Added workflow scenario coverage and Paseo-agent verification evidence for changed skill workflows.
- Documented partial status for earlier state-machine and manual dogfood reports.

## 0.1.0

- Added the committed CodeStable plugin distribution structure under `plugins/codestable/`.
- Moved CodeStable `cs` / `cs-*` skills to `plugins/codestable/skills/` as the canonical skill source.
- Added Codex and Claude marketplace manifests for local repository installation.
- Added marketplace metadata required by Codex and Claude CLI validation.
- Documented upgrade commands for Codex, Claude, and `skills` CLI users.
- Removed the root-level `browser-bridge` standalone skill from this distribution branch.
