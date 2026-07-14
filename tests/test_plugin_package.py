from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/check-plugin-package.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_plugin_package", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = load_checker()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def init_git(repo: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.PIPE)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git(repo)
    (repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (repo / "plugins/codestable/skills/cs-onboard").mkdir(parents=True)
    (repo / "plugins/codestable/skills/cs-onboard/VERSION").write_text("0.1.0\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## 0.1.0\n\n- Initial plugin package.\n", encoding="utf-8")
    (repo / ".gitignore").write_text(
        "/.claude/\n"
        "/dist/\n"
        "__pycache__\n"
        "*.pyc\n"
        ".DS_Store\n",
        encoding="utf-8",
    )
    write_json(
        repo / ".agents/plugins/marketplace.json",
        {
            "name": "codestable",
            "plugins": [
                {
                    "name": "codestable",
                    "version": "0.1.0",
                    "source": {"source": "local", "path": "./plugins/codestable"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "development",
                    "interface": {"displayName": "CodeStable"},
                }
            ]
        },
    )
    write_json(
        repo / ".claude-plugin/marketplace.json",
        {
            "name": "codestable",
            "description": "CodeStable AI coding workflow skills.",
            "owner": {"name": "CodeStable"},
            "plugins": [{"name": "codestable", "version": "0.1.0", "source": "./plugins/codestable"}],
        },
    )
    write_json(
        repo / "plugins/codestable/.codex-plugin/plugin.json",
        {"name": "codestable", "version": "0.1.0", "skills": "./skills/"},
    )
    write_json(
        repo / "plugins/codestable/.claude-plugin/plugin.json",
        {"name": "codestable", "version": "0.1.0", "author": {"name": "CodeStable"}},
    )
    for skill in ["cs", "cs-feat", "cs-onboard"]:
        skill_dir = repo / "plugins/codestable/skills" / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
    for readme in ["README.md", "README.en.md"]:
        (repo / readme).write_text(
            "\n".join(
                [
                    "codex plugin marketplace add codestable/CodeStable",
                    "codex plugin add codestable@codestable",
                    "codex plugin marketplace upgrade codestable",
                    "/plugin marketplace update",
                    "/plugin update codestable@codestable",
                    "npx skills@latest add codestable/CodeStable/plugins/codestable",
                    "npx skills@latest add codestable/CodeStable/plugins/codestable --skill '*' -g",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return repo


def messages(findings: list[object]) -> list[str]:
    return [finding.message for finding in findings]


def test_valid_plugin_package_passes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    assert checker.check_repo(repo) == []


def test_missing_version_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "VERSION").unlink()

    findings = checker.check_repo(repo)

    assert "VERSION is missing" in messages(findings)


def test_missing_changelog_version_section_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## 0.0.9\n\n- Older.\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("missing changelog section for 0.1.0" in message for message in messages(findings))


def test_invalid_manifest_contract_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_json(repo / "plugins/codestable/.codex-plugin/plugin.json", {"version": "0.1.0", "skills": "./bad/"})

    findings = checker.check_repo(repo)

    assert any("skills must equal './skills/'" in message for message in messages(findings))


def test_codex_catalog_contract_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_json(
        repo / ".agents/plugins/marketplace.json",
        {
            "name": "wrong",
            "plugins": [
                {
                    "name": "codestable",
                    "version": "0.1.0",
                    "source": {"source": "local", "path": "./wrong"},
                    "policy": {"installation": "BLOCKED", "authentication": "NEVER"},
                    "category": "",
                    "interface": {},
                }
            ]
        },
    )

    findings = checker.check_repo(repo)
    finding_messages = messages(findings)

    assert "name must equal 'codestable'" in finding_messages
    assert any("source must equal {'source': 'local', 'path': './plugins/codestable'}" in message for message in finding_messages)
    assert any("policy.installation must equal 'AVAILABLE'" in message for message in finding_messages)
    assert any("policy.authentication must equal 'ON_INSTALL'" in message for message in finding_messages)
    assert "plugins.0.category is required" in finding_messages
    assert "plugins.0.interface.displayName is required" in finding_messages


def test_claude_marketplace_source_contract_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_json(
        repo / ".claude-plugin/marketplace.json",
        {
            "name": "wrong",
            "description": "",
            "owner": {},
            "plugins": [{"name": "codestable", "version": "0.1.0", "source": "./wrong"}],
        },
    )

    findings = checker.check_repo(repo)
    finding_messages = messages(findings)

    assert "name must equal 'codestable'" in finding_messages
    assert "owner.name must equal 'CodeStable'" in finding_messages
    assert any("description must equal" in message for message in finding_messages)
    assert any("source must equal './plugins/codestable'" in message for message in finding_messages)


def test_manifest_version_mismatch_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    write_json(
        repo / "plugins/codestable/.claude-plugin/plugin.json",
        {"name": "codestable", "version": "0.2.0"},
    )

    findings = checker.check_repo(repo)

    assert any("version must equal VERSION" in message for message in messages(findings))


def test_standalone_skill_version_missing_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "plugins/codestable/skills/cs-onboard/VERSION").unlink()

    findings = checker.check_repo(repo)

    assert any("standalone VERSION is missing" in message for message in messages(findings))


def test_standalone_skill_version_mismatch_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "plugins/codestable/skills/cs-onboard/VERSION").write_text("0.2.0\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("standalone VERSION must equal VERSION" in message for message in messages(findings))


def test_codex_marketplace_version_mismatch_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    marketplace = json.loads((repo / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    marketplace["plugins"][0]["version"] = "0.2.0"
    write_json(repo / ".agents/plugins/marketplace.json", marketplace)

    findings = checker.check_repo(repo)

    assert any(
        finding.path == ".agents/plugins/marketplace.json" and "version must equal VERSION" in finding.message
        for finding in findings
    )


def test_root_cs_skill_residue_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    root_skill = repo / "cs-onboard"
    root_skill.mkdir()
    (root_skill / "SKILL.md").write_text("---\nname: cs-onboard\n---\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("root cs* skill entry" in message for message in messages(findings))


def test_root_standalone_skill_residue_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    root_skill = repo / "other-skill"
    root_skill.mkdir()
    (root_skill / "SKILL.md").write_text("---\nname: other-skill\n---\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("root standalone skill entry" in message for message in messages(findings))


def test_skill_reference_spelling_conflict_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    skill_dir = repo / "plugins/codestable/skills/cs-feat"
    (skill_dir / "reference").mkdir()
    (skill_dir / "references").mkdir()

    findings = checker.check_repo(repo)

    assert any("must not contain both reference/ and references/" in message for message in messages(findings))


def test_skill_reference_directory_spelling_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    skill_dir = repo / "plugins/codestable/skills/cs-feat"
    (skill_dir / "reference").mkdir()

    findings = checker.check_repo(repo)

    assert any("must use references/, not reference/" in message for message in messages(findings))


def test_nested_references_directory_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    nested = repo / "plugins/codestable/skills/cs-feat/references/design/references"
    nested.mkdir(parents=True)

    findings = checker.check_repo(repo)

    assert any("nested references/ directories are not allowed" in message for message in messages(findings))


def test_non_cs_skill_and_generated_artifacts_fail(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    extra_skill = repo / "plugins/codestable/skills/other-skill"
    extra_skill.mkdir()
    (extra_skill / "SKILL.md").write_text("---\nname: other-skill\n---\n", encoding="utf-8")
    cache_dir = repo / "plugins/codestable/__pycache__"
    cache_dir.mkdir()
    (cache_dir / "x.pyc").write_bytes(b"cache")
    (repo / "plugins/codestable/.pytest_cache").mkdir()
    (repo / "dist").mkdir()

    findings = checker.check_repo(repo)
    finding_messages = messages(findings)

    assert any("non cs* skill" in message for message in finding_messages)
    assert any("generated or cache artifact" in message for message in finding_messages)
    assert any("temporary dist output" in message for message in finding_messages)


def test_ignored_install_asset_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / ".gitignore").write_text("plugins/\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("install asset is ignored" in message for message in messages(findings))


def test_ignored_codestable_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / ".gitignore").write_text(".codestable/\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert ".codestable must not be ignored" in messages(findings)


def test_readme_commands_stay_current(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("codex plugin install codestable\n", encoding="utf-8")

    findings = checker.check_repo(repo)
    finding_messages = messages(findings)

    assert "obsolete documented command: codex plugin install codestable" in finding_messages
    assert any("missing documented command: codex plugin add codestable@codestable" in message for message in finding_messages)


def test_readme_rejects_unqualified_claude_update_command(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("/plugin update codestable\n", encoding="utf-8")

    findings = checker.check_repo(repo)
    finding_messages = messages(findings)

    assert "obsolete documented command: /plugin update codestable" in finding_messages
    assert any("missing documented command: /plugin update codestable@codestable" in message for message in finding_messages)


def test_readme_rejects_unsafe_bare_skills_update(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    for filename in ("README.md", "README.en.md"):
        path = repo / filename
        path.write_text(path.read_text(encoding="utf-8") + "npx skills@latest update\n", encoding="utf-8")

    findings = checker.check_repo(repo)

    assert any("unsafe documented command: npx skills@latest update" in message for message in messages(findings))
