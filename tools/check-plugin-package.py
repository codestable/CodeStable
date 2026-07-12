#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
DESCRIPTION = "CodeStable LITE software lifecycle skill."


@dataclass(frozen=True)
class Finding:
    path: str
    message: str


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "file is missing"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"


def nested(data: Any, keys: list[Any]) -> Any:
    current = data
    for key in keys:
        if isinstance(key, int):
            if not isinstance(current, list) or len(current) <= key:
                return None
            current = current[key]
        else:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
    return current


def is_git_ignored(root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", rel(path, root)],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def check_version(root: Path, findings: list[Finding]) -> str | None:
    path = root / "VERSION"
    if not path.exists():
        findings.append(Finding("VERSION", "VERSION is missing"))
        return None
    version = path.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        findings.append(Finding("VERSION", f"VERSION is not semver: {version!r}"))
    return version


def check_changelog(root: Path, version: str | None, findings: list[Finding]) -> None:
    path = root / "CHANGELOG.md"
    if not path.exists():
        findings.append(Finding("CHANGELOG.md", "CHANGELOG.md is missing"))
        return
    if version and f"## {version}" not in path.read_text(encoding="utf-8"):
        findings.append(Finding("CHANGELOG.md", f"missing changelog section for {version}"))


def check_json_contracts(root: Path, version: str | None, findings: list[Finding]) -> None:
    checks = [
        ("plugins/codestable-lite/.codex-plugin/plugin.json", ["name"], "codestable-lite"),
        ("plugins/codestable-lite/.codex-plugin/plugin.json", ["version"], version),
        ("plugins/codestable-lite/.codex-plugin/plugin.json", ["description"], DESCRIPTION),
        ("plugins/codestable-lite/.codex-plugin/plugin.json", ["skills"], "./skills/"),
        ("plugins/codestable-lite/.claude-plugin/plugin.json", ["name"], "codestable-lite"),
        ("plugins/codestable-lite/.claude-plugin/plugin.json", ["version"], version),
        ("plugins/codestable-lite/.claude-plugin/plugin.json", ["description"], DESCRIPTION),
        ("plugins/codestable-lite/.claude-plugin/plugin.json", ["author", "name"], "CodeStable"),
        (".agents/plugins/marketplace.json", ["name"], "codestable-lite"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "name"], "codestable-lite"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "version"], version),
        (".agents/plugins/marketplace.json", ["plugins", 0, "description"], DESCRIPTION),
        (".agents/plugins/marketplace.json", ["plugins", 0, "source"], {"source": "local", "path": "./plugins/codestable-lite"}),
        (".agents/plugins/marketplace.json", ["plugins", 0, "policy", "installation"], "AVAILABLE"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "policy", "authentication"], "ON_INSTALL"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "category"], "development"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "interface", "displayName"], "CodeStable LITE"),
        (".claude-plugin/marketplace.json", ["name"], "codestable-lite"),
        (".claude-plugin/marketplace.json", ["description"], DESCRIPTION),
        (".claude-plugin/marketplace.json", ["owner", "name"], "CodeStable"),
        (".claude-plugin/marketplace.json", ["plugins", 0, "name"], "codestable-lite"),
        (".claude-plugin/marketplace.json", ["plugins", 0, "version"], version),
        (".claude-plugin/marketplace.json", ["plugins", 0, "description"], DESCRIPTION),
        (".claude-plugin/marketplace.json", ["plugins", 0, "source"], "./plugins/codestable-lite"),
    ]
    cache: dict[str, Any | None] = {}
    for filename, keys, expected in checks:
        if filename not in cache:
            data, error = read_json(root / filename)
            if error:
                findings.append(Finding(filename, error))
                cache[filename] = None
                continue
            cache[filename] = data
        value = nested(cache[filename], keys)
        if value != expected:
            findings.append(Finding(filename, f"{'.'.join(map(str, keys))} must equal {expected!r}"))


def check_skill_layout(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / "plugins/codestable-lite/skills"
    if not skills_dir.is_dir():
        findings.append(Finding("plugins/codestable-lite/skills", "canonical skills directory is missing"))
        return

    skill_dirs = [path for path in sorted(skills_dir.iterdir()) if path.is_dir()]
    skill_names = [path.name for path in skill_dirs]
    if skill_names != ["cs"]:
        findings.append(Finding("plugins/codestable-lite/skills", f"must contain exactly the cs skill, found {skill_names!r}"))
    cs_skill = skills_dir / "cs" / "SKILL.md"
    if not cs_skill.is_file():
        findings.append(Finding(rel(cs_skill, root), "skill is missing SKILL.md"))

    for path in sorted(root.iterdir()):
        if path.name in {"plugins", "asset", "tools", "tests"}:
            continue
        if path.is_dir() and (path / "SKILL.md").is_file():
            findings.append(Finding(path.name, "root standalone skill entry must be moved under plugins/codestable-lite/skills"))


def check_install_assets(root: Path, findings: list[Finding]) -> None:
    assets = [
        root / ".agents/plugins/marketplace.json",
        root / ".claude-plugin/marketplace.json",
        root / "plugins/codestable-lite/.codex-plugin/plugin.json",
        root / "plugins/codestable-lite/.claude-plugin/plugin.json",
        root / "plugins/codestable-lite/skills/cs/SKILL.md",
        root / "plugins/codestable-lite/skills/cs/agents/openai.yaml",
        root / "plugins/codestable-lite/skills/cs/scripts/init_codestable.py",
    ]
    skill_root = root / "plugins/codestable-lite/skills/cs"
    assets.extend(
        skill_root / "references" / filename
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
    assets.extend(
        skill_root / "templates/entities" / filename
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
    for path in assets:
        if not path.exists():
            findings.append(Finding(rel(path, root), "install asset is missing"))
        elif is_git_ignored(root, path):
            findings.append(Finding(rel(path, root), "install asset is ignored by .gitignore"))
    if (root / "dist").exists():
        findings.append(Finding("dist", "temporary dist output must not be present in the package tree"))


def check_readme_commands(root: Path, findings: list[Finding]) -> None:
    required = [
        "codex plugin marketplace add liuzhengdongfortest/CodeStable",
        "codex plugin add codestable-lite@codestable-lite",
        "codex plugin marketplace add liuzhengdongfortest/CodeStable --ref codestable-lite",
        "codex plugin marketplace add D:\\playground\\CodeStable",
        "codex plugin marketplace upgrade codestable-lite",
        "/plugin marketplace add liuzhengdongfortest/CodeStable",
        "/plugin marketplace update",
        "/plugin update codestable-lite@codestable-lite",
        "npx skills@latest add liuzhengdongfortest/CodeStable",
        "npx skills@latest update",
    ]
    for filename in ["README.md", "README.en.md"]:
        path = root / filename
        if not path.exists():
            findings.append(Finding(filename, "README file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for command in required:
            if command not in text:
                findings.append(Finding(filename, f"missing documented command: {command}"))
        for obsolete in ["codex plugin install codestable", "codex plugin install codestable-lite"]:
            if obsolete in text:
                findings.append(Finding(filename, f"obsolete documented command: {obsolete}"))


def check_repo(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    version = check_version(root, findings)
    check_changelog(root, version, findings)
    check_json_contracts(root, version, findings)
    check_skill_layout(root, findings)
    check_install_assets(root, findings)
    check_readme_commands(root, findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the committed codestable-lite plugin package.")
    parser.add_argument("--root", default=".", help="Repository root to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable findings.")
    args = parser.parse_args()
    findings = check_repo(Path(args.root))
    if args.json:
        print(json.dumps({"ok": not findings, "findings": [finding.__dict__ for finding in findings]}, indent=2))
    elif findings:
        print("Plugin package check failed:")
        for finding in findings:
            print(f"- {finding.path}: {finding.message}")
    else:
        print("Plugin package check passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
