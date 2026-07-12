#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class Finding:
    path: str
    message: str


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_git_ignored(root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", rel(path, root)],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def check_version(root: Path, findings: list[Finding]) -> None:
    version_file = root / "VERSION"
    changelog = root / "CHANGELOG.md"
    if not version_file.is_file():
        findings.append(Finding("VERSION", "file is missing"))
        return

    version = version_file.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        findings.append(Finding("VERSION", f"not valid semver: {version!r}"))
    if not changelog.is_file():
        findings.append(Finding("CHANGELOG.md", "file is missing"))
    elif f"## {version}" not in changelog.read_text(encoding="utf-8"):
        findings.append(Finding("CHANGELOG.md", f"missing version section {version}"))


def required_skill_files(root: Path) -> list[Path]:
    skill = root / "skills/cs"
    files = [
        skill / "SKILL.md",
        skill / "agents/openai.yaml",
        skill / "scripts/init_codestable.py",
    ]
    files.extend(
        skill / "references" / filename
        for filename in [
            "close.md",
            "code-design.md",
            "complain.md",
            "debug.md",
            "design.md",
            "do.md",
            "docs.md",
            "explore.md",
            "great-skills.md",
            "maketools.md",
            "note.md",
            "onboard.md",
            "spec.md",
            "talk.md",
        ]
    )
    files.extend(
        skill / "templates/entities" / filename
        for filename in [
            "bug-issue.md",
            "chore-issue.md",
            "epic-spec.md",
            "explore-article.md",
            "explore-index.md",
            "facts.md",
            "feature-issue.md",
            "notes.md",
            "project-spec-index.md",
            "refactor-issue.md",
            "spec-section-index.md",
            "talk.md",
            "tool.md",
        ]
    )
    return files


def check_skill_layout(root: Path, findings: list[Finding]) -> None:
    skills = root / "skills"
    if not skills.is_dir():
        findings.append(Finding("skills", "directory is missing"))
        return

    skill_dirs = sorted(path.name for path in skills.iterdir() if path.is_dir())
    if skill_dirs != ["cs"]:
        findings.append(Finding("skills", f"must contain exactly the cs skill, found {skill_dirs!r}"))

    for path in required_skill_files(root):
        if not path.is_file():
            findings.append(Finding(rel(path, root), "required skill file is missing"))
        elif is_git_ignored(root, path):
            findings.append(Finding(rel(path, root), "required skill file is git-ignored"))

    for obsolete in ["plugins", ".agents/plugins", ".claude-plugin"]:
        if (root / obsolete).exists():
            findings.append(Finding(obsolete, "obsolete plugin wrapper must not exist"))


def check_readmes(root: Path, findings: list[Finding]) -> None:
    required = [
        "npx skills add liuzhengdongfortest/CodeStable",
        "npx skills add . --list",
        "npx skills update cs",
    ]
    obsolete = [
        "codex plugin",
        "/plugin ",
        "plugins/codestable-lite",
        ".claude-plugin",
        "marketplace",
    ]
    for filename in ["README.md", "README.en.md"]:
        path = root / filename
        if not path.is_file():
            findings.append(Finding(filename, "file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for command in required:
            if command not in text:
                findings.append(Finding(filename, f"missing documented command: {command}"))
        for marker in obsolete:
            if marker in text:
                findings.append(Finding(filename, f"obsolete plugin documentation remains: {marker}"))


def check_repo(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    check_version(root, findings)
    check_skill_layout(root, findings)
    check_readmes(root, findings)
    if (root / "dist").exists():
        findings.append(Finding("dist", "temporary distribution output must not be committed"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the CodeStable single-skill repository.")
    parser.add_argument("--root", default=".", help="Repository root to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable findings.")
    args = parser.parse_args()
    findings = check_repo(Path(args.root))
    if args.json:
        print(json.dumps({"ok": not findings, "findings": [finding.__dict__ for finding in findings]}, indent=2))
    elif findings:
        print("Skill repository check failed:")
        for finding in findings:
            print(f"- {finding.path}: {finding.message}")
    else:
        print("Skill repository check passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
