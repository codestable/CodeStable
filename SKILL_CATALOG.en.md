# CodeStable v2 Skill Catalog

v2 ships exactly 8 skills. Each is an independent installation unit and does not depend on sibling
skill files or a centralized onboard runtime.

## Current Entries

| Group | Skill | Responsibility |
|---|---|---|
| Navigation | `cs` | Clear action requests dispatch to the target skill in the same turn; advice gets a recommendation only; the overview writes no files |
| Onboarding | `cs-onboard` | Create minimal project memory and explain a lossless v1 upgrade |
| Feature | `cs-feat` | Implement new capability; scale design confirmation and independent review with risk |
| Issue | `cs-issue` | Fix bugs or broken existing behavior with red-to-green evidence |
| Refactor | `cs-refactor` | Change structure or performance under verifiable behavioral equivalence |
| Epic | `cs-epic` | Decompose, confirm, and drive multiple deliverable items over time |
| Review | `cs-review` | Read-only leaf executor for one change, design, module, or repository review |
| Memory | `cs-keep` | Store evidence-backed frequent facts or reusable lessons in project memory |

`cs-code-review` ships as the single compatibility alias of `cs-review` (the carried-over v1 name; forwarding only, no independent rules).

## Retired v1.0.4 Entries

The following 24 names are retired and not shipped in v2. No compatibility shims are installed.
Upgrading preserves historical project artifacts; it only removes these triggers from the new skill
package.

| v1 names | v2 approach |
|---|---|
| `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff` | Use `cs-feat`; risk and repository facts determine execution strength |
| `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix` | Use `cs-issue` |
| `cs-refactor-ff` | Use `cs-refactor` |
| `cs-audit` | Use the audit mode of `cs-review` |
| `cs-goal`, `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal` | Use `cs-epic` for large initiatives; ordinary cross-session work uses one work document |
| `cs-brainstorm`, `cs-domain`, `cs-req` | Clarify within `cs-feat` / `cs-epic`; update project docs or ADRs directly |
| `cs-docs`, `cs-docs-neat`, `cs-doc-api`, `cs-doc-tutorial` | Update docs as part of the owning development task, or request a standalone documentation edit directly |
| `cs-note` | Use `cs-keep` |
| `cs-feedback` | Store project lessons with `cs-keep`; submit product feedback through the repository issue process |

Call `cs` when the mapping is unclear. See
[WORKFLOW.en.md](./WORKFLOW.en.md#v1-upgrade-boundary) for v1 project-asset preservation.
