#!/usr/bin/env python3
"""Sync CodeStable package-owned runtime assets into a repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codestable_runtime import runtime_health, sync_runtime


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--source-skill-dir",
        default=Path(__file__).resolve().parents[1].as_posix(),
        help="cs-onboard skill directory containing gates/, tools/, references/, hooks/",
    )
    parser.add_argument("--plugin-version", default=None, help="Expected CodeStable plugin version")
    parser.add_argument("--force", action="store_true", help="Overwrite dirty managed runtime paths")
    parser.add_argument("--check", action="store_true", help="Only check runtime state, do not sync")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    root = Path(args.root)
    source_skill_dir = Path(args.source_skill_dir)
    result = (
        runtime_health(root, source_skill_dir=source_skill_dir, plugin_version=args.plugin_version)
        if args.check
        else sync_runtime(root, source_skill_dir=source_skill_dir, plugin_version=args.plugin_version, force=args.force)
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"CodeStable runtime: {result['status']}")
        hint = result.get("hint")
        if hint:
            print(f"Hint: {hint}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
