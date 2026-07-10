# CodeStable Skill Catalog

Main entries accept optional stage / mode flags (for example `/cs-feat --stage qa`, `/cs-refactor --mode fastforward`, `/cs-docs --mode api auth-endpoints`). Flags are only intent hints; repository facts always win, bare arguments always describe the task, and no-argument calls recover or route from repository facts plus the user's words.

## Recommended Main Entries

| Group | Skill | Purpose |
|---|---|---|
| Root | `cs` | Action requests dispatch to the target skill in the current run; advice requests only recommend. |
| Onboarding | `cs-onboard` | Install CodeStable into a new or previously informal repository |
| Requirements and domain | `cs-req` | Capture capability intent documents |
| Requirements and domain | `cs-domain` | Maintain domain terms, ADRs, and context topology |
| Epic | `cs-epic` | Large-demand entry: planning, review, child feature design, goal package, and visible driver dispatch |
| Goal | `cs-goal` | Autonomous iteration from a defined start state to accepted end state |
| Brainstorm | `cs-brainstorm` | Triage unclear ideas into feature, epic, or brainstorm notes |
| Feature flow | `cs-feat` | End-to-end feature entry: design, review, goal package, impl, code review, QA, accept |
| Issue flow | `cs-issue` | End-to-end issue entry: report, analyze, fix, review |
| Refactor flow | `cs-refactor` | Behavior-preserving refactor entry with standard and fastforward modes |
| Cross-cutting review | `cs-code-review` | Read-only implementation review gate |
| Audit | `cs-audit` | Scan for bugs, security, performance, maintainability, and architecture drift |
| Feedback | `cs-feedback` | Capture CodeStable skill usage problems, collect local history, and prepare a GitHub issue |
| Knowledge | `cs-keep` | Capture lessons, tricks, decisions, and research in `.codestable/compound/` |
| Knowledge | `cs-note` | Append short startup-critical notes to `.codestable/attention.md` |
| External docs | `cs-docs` | Write or update developer guides, user guides, and API references |
| Docs hygiene | `cs-docs-neat` | Sync `.codestable/`, README/docs, agent entry files, and memory |

## Long-Term Compatibility Entries

These skill names remain usable, but they only enter the corresponding main workflow and do not maintain independent rules.

| Compatibility group | Skills | Enters |
|---|---|---|
| Feature | `cs-feat-design`, `cs-feat-design-review`, `cs-feat-impl`, `cs-feat-qa`, `cs-feat-accept`, `cs-feat-ff` | Matching `cs-feat` stage or mode |
| Issue | `cs-issue-report`, `cs-issue-analyze`, `cs-issue-fix` | Matching `cs-issue` stage |
| Refactor | `cs-refactor-ff` | `cs-refactor` fastforward mode |
| Docs | `cs-doc-tutorial`, `cs-doc-api` | `cs-docs` tutorial / api mode |
| Epic | `cs-roadmap`, `cs-roadmap-review`, `cs-roadmap-impl-goal` | `cs-epic` planning / review / goal-package stage |
