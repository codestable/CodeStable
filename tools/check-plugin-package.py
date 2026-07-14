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
CODESTABLE_SKILL_RE = re.compile(r"^cs(?:-.+)?$")


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
    version_path = root / "VERSION"
    if not version_path.exists():
        findings.append(Finding("VERSION", "VERSION is missing"))
        return None

    version = version_path.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        findings.append(Finding("VERSION", f"VERSION is not semver: {version!r}"))
    return version


def check_changelog(root: Path, version: str | None, findings: list[Finding]) -> None:
    path = root / "CHANGELOG.md"
    if not path.exists():
        findings.append(Finding("CHANGELOG.md", "CHANGELOG.md is missing"))
        return
    if not version:
        return
    text = path.read_text(encoding="utf-8")
    headings = (f"## {version}", f"## [{version}]")
    if not any(heading in text for heading in headings):
        findings.append(Finding("CHANGELOG.md", f"missing changelog section for {version}"))


def check_manifest_versions(root: Path, version: str | None, findings: list[Finding]) -> None:
    manifests = [
        ("plugins/codestable/.codex-plugin/plugin.json", ["version"]),
        ("plugins/codestable/.claude-plugin/plugin.json", ["version"]),
        (".claude-plugin/marketplace.json", ["plugins", 0, "version"]),
        (".agents/plugins/marketplace.json", ["plugins", 0, "version"]),
    ]
    for filename, keys in manifests:
        data, error = read_json(root / filename)
        if error:
            findings.append(Finding(filename, error))
            continue
        value = nested(data, keys)
        if value != version:
            findings.append(Finding(filename, f"{'.'.join(map(str, keys))} must equal VERSION"))


def check_standalone_version(root: Path, version: str | None, findings: list[Finding]) -> None:
    filename = "plugins/codestable/skills/cs-onboard/VERSION"
    path = root / filename
    if not path.is_file():
        findings.append(Finding(filename, "standalone VERSION is missing"))
        return
    standalone_version = path.read_text(encoding="utf-8").strip()
    if standalone_version != version:
        findings.append(Finding(filename, "standalone VERSION must equal VERSION"))


def check_catalog_contracts(root: Path, findings: list[Finding]) -> None:
    checks = [
        (".agents/plugins/marketplace.json", ["name"], "codestable"),
        (
            ".agents/plugins/marketplace.json",
            ["plugins", 0, "source"],
            {"source": "local", "path": "./plugins/codestable"},
        ),
        (".agents/plugins/marketplace.json", ["plugins", 0, "policy", "installation"], "AVAILABLE"),
        (".agents/plugins/marketplace.json", ["plugins", 0, "policy", "authentication"], "ON_INSTALL"),
        (".claude-plugin/marketplace.json", ["name"], "codestable"),
        (".claude-plugin/marketplace.json", ["owner", "name"], "CodeStable"),
        (".claude-plugin/marketplace.json", ["description"], "CodeStable AI coding workflow skills."),
        (".claude-plugin/marketplace.json", ["plugins", 0, "source"], "./plugins/codestable"),
        ("plugins/codestable/.claude-plugin/plugin.json", ["author", "name"], "CodeStable"),
        ("plugins/codestable/.codex-plugin/plugin.json", ["skills"], "./skills/"),
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
        data = cache[filename]
        if data is None:
            continue
        value = nested(data, keys)
        if value != expected:
            findings.append(Finding(filename, f"{'.'.join(map(str, keys))} must equal {expected!r}"))

    codex_marketplace = cache.get(".agents/plugins/marketplace.json")
    if codex_marketplace is not None:
        if not nested(codex_marketplace, ["plugins", 0, "category"]):
            findings.append(Finding(".agents/plugins/marketplace.json", "plugins.0.category is required"))
        if not nested(codex_marketplace, ["plugins", 0, "interface", "displayName"]):
            findings.append(Finding(".agents/plugins/marketplace.json", "plugins.0.interface.displayName is required"))


def check_skill_layout(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / "plugins/codestable/skills"
    if not skills_dir.is_dir():
        findings.append(Finding("plugins/codestable/skills", "canonical skills directory is missing"))
        return

    skill_dirs = [path for path in sorted(skills_dir.iterdir()) if path.is_dir()]
    if not skill_dirs:
        findings.append(Finding("plugins/codestable/skills", "no skills found"))

    for path in skill_dirs:
        if not CODESTABLE_SKILL_RE.match(path.name):
            findings.append(Finding(rel(path, root), "non cs* skill found in CodeStable plugin"))
        if not (path / "SKILL.md").is_file():
            findings.append(Finding(rel(path, root), "skill is missing SKILL.md"))

    for path in sorted(root.iterdir()):
        if CODESTABLE_SKILL_RE.match(path.name) and (path.is_dir() or path.is_symlink()):
            findings.append(Finding(path.name, "root cs* skill entry must be moved under plugins/codestable/skills"))
        elif path.is_dir() and (path / "SKILL.md").is_file():
            findings.append(Finding(path.name, "root standalone skill entry must be removed from this distribution branch"))


def check_reference_directory_spellings(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / "plugins/codestable/skills"
    if not skills_dir.is_dir():
        return

    directories = [skills_dir, *[path for path in sorted(skills_dir.rglob("*")) if path.is_dir()]]
    for directory in directories:
        if (directory / "reference").is_dir() and (directory / "references").is_dir():
            findings.append(Finding(rel(directory, root), "must not contain both reference/ and references/"))
        if directory.name == "reference":
            findings.append(Finding(rel(directory, root), "skill package directory must use references/, not reference/"))
        if directory.name == "references":
            parts = directory.relative_to(skills_dir).parts
            if len(parts) != 2 or parts[1] != "references":
                findings.append(Finding(rel(directory, root), "nested references/ directories are not allowed; use support/"))


def check_ignored_assets(root: Path, findings: list[Finding]) -> None:
    assets = [
        root / ".agents/plugins/marketplace.json",
        root / ".claude-plugin/marketplace.json",
        root / "plugins/codestable/.codex-plugin/plugin.json",
        root / "plugins/codestable/.claude-plugin/plugin.json",
        root / "plugins/codestable/skills/cs/SKILL.md",
    ]
    for path in assets:
        if not path.exists():
            findings.append(Finding(rel(path, root), "install asset is missing"))
        elif is_git_ignored(root, path):
            findings.append(Finding(rel(path, root), "install asset is ignored by .gitignore"))


def check_codestable_not_ignored(root: Path, findings: list[Finding]) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", ".codestable/attention.md"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        findings.append(Finding(".gitignore", ".codestable must not be ignored"))


def check_generated_exclusions(root: Path, findings: list[Finding]) -> None:
    blocked = {".DS_Store", ".pytest_cache"}
    scan_roots = [root / "plugins/codestable"]
    if (root / "dist").exists():
        findings.append(Finding("dist", "temporary dist output must not be present in the package tree"))
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            name = path.name
            if name == "__pycache__" or name in blocked or path.suffix == ".pyc" or name == "dist":
                findings.append(Finding(rel(path, root), "generated or cache artifact found in plugin entity"))


def check_readme_commands(root: Path, findings: list[Finding]) -> None:
    required = [
        "codex plugin marketplace add codestable/CodeStable",
        "codex plugin add codestable@codestable",
        "codex plugin marketplace upgrade codestable",
        "/plugin marketplace update",
        "/plugin update codestable@codestable",
    ]
    forbidden = ["codex plugin install codestable"]
    required_lines = [
        "npx skills@latest add codestable/CodeStable/plugins/codestable",
        "npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g",
    ]
    forbidden_lines = ["/plugin update codestable", "npx skills@latest update"]
    for filename in ["README.md", "README.en.md"]:
        path = root / filename
        if not path.exists():
            findings.append(Finding(filename, "README file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for command in required:
            if command not in text:
                findings.append(Finding(filename, f"missing documented command: {command}"))
        for command in forbidden:
            if command in text:
                findings.append(Finding(filename, f"obsolete documented command: {command}"))
        lines = {line.strip() for line in text.splitlines()}
        for command in required_lines:
            if command not in lines:
                findings.append(Finding(filename, f"missing documented command: {command}"))
        for command in forbidden_lines:
            if command in lines:
                prefix = "unsafe" if command == "npx skills@latest update" else "obsolete"
                findings.append(Finding(filename, f"{prefix} documented command: {command}"))


def check_repo(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    version = check_version(root, findings)
    check_changelog(root, version, findings)
    check_manifest_versions(root, version, findings)
    check_standalone_version(root, version, findings)
    check_catalog_contracts(root, findings)
    check_skill_layout(root, findings)
    check_reference_directory_spellings(root, findings)
    check_ignored_assets(root, findings)
    check_codestable_not_ignored(root, findings)
    check_generated_exclusions(root, findings)
    check_readme_commands(root, findings)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the committed CodeStable plugin package.")
    parser.add_argument("--root", default=".", help="Repository root to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable findings.")
    args = parser.parse_args(argv)

    root = Path(args.root)
    findings = check_repo(root)
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
