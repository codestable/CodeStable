# Changelog

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
