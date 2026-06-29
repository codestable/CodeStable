#!/usr/bin/env python3
"""Run checklist dod.commands and report real exit codes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import gate_result, load_yaml, main_exit, parse_args, repo_root, run_command


def collect_commands(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    # Authoritative schema: top-level `dod.commands` (cs-feat-design reference §"DoD
    # Contract" — `dod` is a top-level checklist key alongside `steps`/`checks`).
    top_dod = checklist.get("dod") or {}
    for command in top_dod.get("commands", []) or []:
        commands.append(command)
    # Backward-compat: also accept step-level `dod.commands`.
    for step in checklist.get("steps", []) or []:
        dod = step.get("dod") or {}
        for command in dod.get("commands", []) or []:
            commands.append(command)
    return commands


def main() -> None:
    parser = parse_args("Run explicit checklist dod.commands using real subprocess exit codes.")
    parser.add_argument("--checklist", required=True, help="Path to checklist YAML")
    parser.add_argument("--only", action="append", default=[], help="Run only this command id; repeatable")
    parser.add_argument("--stage", default="implementation.before_review")
    args = parser.parse_args()

    checklist_path = Path(args.checklist)
    if not checklist_path.exists():
        result = gate_result("dod-runner", args.stage, "blocked", [f"checklist not found: {checklist_path}"])
        main_exit(result, args.json_out)

    checklist = load_yaml(checklist_path)
    commands = collect_commands(checklist)
    if args.only:
        requested = set(args.only)
        commands = [command for command in commands if command.get("id") in requested]
    if not commands:
        result = gate_result("dod-runner", args.stage, "skipped", warnings=["no matching dod.commands found"])
        main_exit(result, args.json_out)

    root = repo_root()
    evidence = []
    blocking = []
    warnings = []
    for command in commands:
        run = run_command(str(command.get("command", "")), root)
        run["id"] = command.get("id")
        run["core"] = bool(command.get("core"))
        run["failure_handling"] = command.get("failure_handling")
        evidence.append(run)
        if run["exit_code"] != 0 and run["core"]:
            blocking.append(f"{command.get('id')}: command failed with exit {run['exit_code']}")
        elif run["exit_code"] != 0:
            warnings.append(f"{command.get('id')}: non-core command failed with exit {run['exit_code']}")

    status = "failed" if blocking else "passed"
    result = gate_result("dod-runner", args.stage, status, blocking, warnings, evidence)
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
