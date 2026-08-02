# CodeStable Upgrade Guide

**English** · [中文](./UPGRADE.md)

Read [CHANGELOG.md](./CHANGELOG.md) first, then refresh through the entry point you originally used.

Do not treat `npx skills@latest update` as a complete upgrade: the external CLI's update discovery is not equivalent to plugin installation discovery and may remove sibling skills.

## Codex Plugin

```bash
codex plugin marketplace upgrade codestable
codex plugin add codestable@codestable
```

Codex currently has no separate `plugin update` subcommand. The first command refreshes the marketplace Git snapshot; the second installs the current version from that snapshot.

## Claude Plugin

```text
/plugin marketplace update
/plugin update codestable@codestable
```

Restart Claude Code after updating so the new plugin version is applied.

## `skills` CLI

For an upgrade within the same major, reinstall the complete package from its package root:

```bash
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

For a project-scoped installation, omit `-g` and run the command inside that project. Do not switch to bare `update`; package-root `add` is what discovers the complete skill set through the plugin manifest.

## Upgrade from v1.0.4 to v2

v2 reduces 32 entries to 8 primary skills and keeps only `cs-code-review` as a compatibility alias.

The current `skills` CLI does not prune names removed from a newer package during `add`, so the first upgrade must remove exactly 24 retired entries:

```bash
npx skills@latest remove \
  cs-audit cs-brainstorm cs-doc-api cs-doc-tutorial cs-docs cs-docs-neat \
  cs-domain cs-feat-accept cs-feat-design cs-feat-design-review cs-feat-ff \
  cs-feat-impl cs-feat-qa cs-feedback cs-goal cs-issue-analyze cs-issue-fix \
  cs-issue-report cs-note cs-refactor-ff cs-req cs-roadmap \
  cs-roadmap-impl-goal cs-roadmap-review \
  -g -y
npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g
```

Removal is name-based and does not verify the installation source. Names outside this list are untouched. If you maintain a custom or third-party skill under one of these names, back it up and remove that name from the command first.

For a project-scoped v1 installation, omit `-g` from both commands and run them in the project.

## Project Assets Are Not Migrated

An upgrade does not delete historical v1 project assets, bulk-migrate them, or rewrite them in place.

Existing requirements, features, issues, retrospectives, and lessons remain where they are. This guide does not duplicate their runtime policy.

Old tools, gates, hooks, references, and manifests also remain in place, but v2 neither runs nor refreshes the old runtime. A skill-package upgrade requires no per-repository runtime installation.

The retrieval and write policy remains owned by [WORKFLOW.en.md](./WORKFLOW.en.md#v1-upgrade-boundary). See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md#retired-v104-entries) for the complete old-to-v2 entry mapping.

## Post-Upgrade Check

- Call `/cs` and confirm the root entry is available.
- `/cs-onboard` should maintain only minimal project memory and must not overwrite existing project docs.
- With the `skills` CLI, confirm all 8 primary skills plus the `cs-code-review` compatibility alias are installed.
- When reporting an installation difference, include the installation entry point and version.

Return to the [README](./README.en.md).
