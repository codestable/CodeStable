# Changelog

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
