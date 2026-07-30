# CodeStable Skill Catalog

v2 ships 8 skills: a thin layer of engineering discipline plus a project-memory loop. Ordinary tasks produce zero CodeStable artifacts — the diff and tests are the evidence; cross-session work keeps exactly one work document.

| Skill | Purpose |
|---|---|
| `cs` | System overview and entry recommendation; explains only, never starts a workflow |
| `cs-onboard` | Create the minimal `.codestable/` skeleton (attention / lessons / work); v1 legacy is preserved untouched |
| `cs-feat` | New features and changes; risk-escalation signals require a design confirmation first |
| `cs-issue` | Bug fixing; no root-cause guessing without a verification that clearly turns red |
| `cs-refactor` | Behavior-preserving refactoring; equivalence verification before touching code |
| `cs-code-review` | Independent code review; diff review by default, repo-wide audit on request |
| `cs-epic` | Large-requirement decomposition and long-running delivery via one epic document |
| `cs-keep` | Distill experience into attention / lessons; every entry needs traceable evidence |

## v1 legacy entries

The v1 stage skills and long-tail entries (`cs-feat-design`, `cs-issue-fix`, `cs-goal`, `cs-brainstorm`, `cs-docs`, `cs-domain`, `cs-req`, `cs-audit`, `cs-note`, `cs-feedback`, the `cs-roadmap` family, etc.) have been removed: design and requirement clarification are built-in steps of `cs-feat` / `cs-epic`, auditing is a mode of `cs-code-review`, knowledge capture goes through `cs-keep`, and docs/ADRs are produced by the work that needs them. All v1 artifacts and knowledge in existing projects remain untouched and grep-discoverable.
