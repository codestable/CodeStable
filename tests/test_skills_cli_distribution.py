from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "plugins/codestable"
RUN_E2E = os.environ.get("CODESTABLE_RUN_SKILLS_CLI_E2E") == "1"
CLI_COMMAND = os.environ.get("CODESTABLE_SKILLS_CLI")
LEGACY_INVENTORY = ROOT / "tests/fixtures/skills-cli/legacy-cs-inventory.json"
SKILLS_CLI_1_5_17_PRIORITY_PREFIXES = (
    "",
    "skills/",
    "skills/.curated/",
    "skills/.experimental/",
    "skills/.system/",
    ".agents/skills/",
    ".claude/skills/",
    ".cline/skills/",
    ".codebuddy/skills/",
    ".codex/skills/",
    ".commandcode/skills/",
    ".continue/skills/",
    ".github/skills/",
    ".goose/skills/",
    ".iflow/skills/",
    ".junie/skills/",
    ".kilocode/skills/",
    ".kiro/skills/",
    ".mux/skills/",
    ".neovate/skills/",
    ".opencode/skills/",
    ".openhands/skills/",
    ".pi/skills/",
    ".qoder/skills/",
    ".roo/skills/",
    ".trae/skills/",
    ".windsurf/skills/",
    ".zcode/skills/",
    ".zencoder/skills/",
)


def package_skill_names(package_root: Path) -> set[str]:
    manifest = json.loads((package_root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    skills_dir = package_root / manifest["skills"]
    return {
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def skill_md_paths(root: Path) -> set[str]:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    return {
        path
        for path in tracked
        if path and Path(path).name.lower() == "skill.md"
    }


def skills_cli_1_5_17_priority_discovery(root: Path, subpath: str | None = None) -> set[str]:
    paths = skill_md_paths(root)
    prefix = f"{subpath.rstrip('/')}" + "/" if subpath else ""
    filtered = {
        path
        for path in paths
        if not prefix or path.startswith(prefix) or path == f"{prefix}SKILL.md"
    }
    if not filtered:
        return set()

    discovered: set[str] = set()
    lower_paths = {path.lower() for path in filtered}
    for priority_prefix in SKILLS_CLI_1_5_17_PRIORITY_PREFIXES:
        full_prefix = f"{prefix}{priority_prefix}"
        for path in filtered:
            if not path.startswith(full_prefix):
                continue
            rest = path[len(full_prefix) :]
            parts = rest.split("/")
            if rest.lower() == "skill.md" or (len(parts) == 2 and parts[1].lower() == "skill.md"):
                discovered.add(path)
            elif priority_prefix and len(parts) == 3 and parts[2].lower() == "skill.md":
                parent_skill = f"{full_prefix}{parts[0]}/SKILL.md".lower()
                if parent_skill not in lower_paths:
                    discovered.add(path)
    if discovered:
        return discovered
    return {path for path in filtered if len(path.split("/")) <= 6}


def skills_cli_1_5_17_deleted_skills(
    locked_paths: dict[str, str], discovered_paths: set[str]
) -> set[str]:
    return {
        name
        for name, skill_path in locked_paths.items()
        if skill_path not in discovered_paths
    }


def installed_skill_names(home: Path) -> set[str]:
    skills_dir = home / ".agents/skills"
    if not skills_dir.is_dir():
        return set()
    return {
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def test_skills_cli_package_root_contains_complete_cs_family() -> None:
    names = package_skill_names(PACKAGE_ROOT)

    assert names
    assert all(name == "cs" or name.startswith("cs-") for name in names)
    assert {"cs", "cs-onboard", "cs-feat", "cs-issue", "cs-goal"} <= names


def test_repo_root_update_discovery_misses_plugin_but_package_root_is_complete() -> None:
    names = package_skill_names(PACKAGE_ROOT)
    canonical_paths = {f"plugins/codestable/skills/{name}/SKILL.md" for name in names}

    root_discovery = skills_cli_1_5_17_priority_discovery(ROOT)
    package_discovery = skills_cli_1_5_17_priority_discovery(ROOT, "plugins/codestable")

    assert root_discovery == {
        ".claude/skills/build-cs-skill/SKILL.md",
        ".claude/skills/eval-cs-skill/SKILL.md",
    }
    assert root_discovery.isdisjoint(canonical_paths)
    assert package_discovery == canonical_paths


def test_update_deletion_detection_preserves_complete_package_siblings() -> None:
    legacy = json.loads(LEGACY_INVENTORY.read_text(encoding="utf-8"))
    legacy_names = set(legacy["skills"])
    current_names = package_skill_names(PACKAGE_ROOT)
    locked_paths = {
        name: f"plugins/codestable/skills/{name}/SKILL.md"
        for name in current_names
    }
    root_discovery = skills_cli_1_5_17_priority_discovery(ROOT)
    package_discovery = skills_cli_1_5_17_priority_discovery(ROOT, "plugins/codestable")

    deleted_from_root = skills_cli_1_5_17_deleted_skills(locked_paths, root_discovery)
    deleted_from_package = skills_cli_1_5_17_deleted_skills(locked_paths, package_discovery)

    assert legacy_names <= current_names
    assert deleted_from_root == current_names
    assert deleted_from_package == set()


@pytest.mark.skipif(
    not RUN_E2E or not CLI_COMMAND,
    reason="set CODESTABLE_RUN_SKILLS_CLI_E2E=1 and CODESTABLE_SKILLS_CLI for a real CLI E2E",
)
def test_full_package_reinstall_preserves_sibling_skills(tmp_path: Path) -> None:
    source = tmp_path / "source/codestable"
    shutil.copytree(PACKAGE_ROOT, source)
    home = tmp_path / "home"
    state = tmp_path / "state"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_STATE_HOME": str(state),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        }
    )
    unrelated_source = tmp_path / "unrelated/third-party-probe"
    unrelated_source.mkdir(parents=True)
    (unrelated_source / "SKILL.md").write_text(
        "---\nname: third-party-probe\ndescription: E2E preservation probe.\n---\n\n# Probe\n",
        encoding="utf-8",
    )
    unrelated_command = [
        *shlex.split(CLI_COMMAND),
        "add",
        str(unrelated_source),
        "-g",
        "-a",
        "codex",
        "-y",
        "--copy",
    ]
    command = [
        *shlex.split(CLI_COMMAND),
        "add",
        str(source),
        "-g",
        "-a",
        "codex",
        "-s",
        "*",
        "-y",
        "--copy",
    ]

    subprocess.run(
        unrelated_command,
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert "third-party-probe" in installed_skill_names(home)

    subprocess.run(command, cwd=tmp_path, env=env, check=True, capture_output=True, text=True, timeout=120)
    expected = package_skill_names(source)
    before = installed_skill_names(home)
    assert expected <= before

    skill_md = source / "skills/cs/SKILL.md"
    skill_md.write_text(skill_md.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    subprocess.run(command, cwd=tmp_path, env=env, check=True, capture_output=True, text=True, timeout=120)

    after = installed_skill_names(home)
    assert expected <= after
    assert "third-party-probe" in after
