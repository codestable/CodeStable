"""M3 release：bump_version / adapt_extracted_skill / regression。tmp 隔离，不碰真实仓库。"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
sys.path.insert(0, str(SCRIPTS))

import adapt_extracted_skill as adapt_mod   # noqa: E402
import bump_version as bump_mod             # noqa: E402
import regression as reg_mod                # noqa: E402

EXPERIMENT = ROOT / "experiments/cs-code-review-001"


# ---- bump_version ----

def _mk_repo(tmp_path):
    (tmp_path / "plugins/codestable/.codex-plugin").mkdir(parents=True)
    (tmp_path / "plugins/codestable/.claude-plugin").mkdir(parents=True)
    (tmp_path / "plugins/codestable/skills/cs-onboard").mkdir(parents=True)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".agents/plugins").mkdir(parents=True)
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (tmp_path / "plugins/codestable/skills/cs-onboard/VERSION").write_text(
        "1.0.0\n", encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0.0\n\n- init\n", encoding="utf-8")
    for rel in ("plugins/codestable/.codex-plugin/plugin.json",
                "plugins/codestable/.claude-plugin/plugin.json"):
        (tmp_path / rel).write_text(json.dumps({"name": "codestable", "version": "1.0.0"}), encoding="utf-8")
    for rel in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        (tmp_path / rel).write_text(json.dumps({"plugins": [{"version": "1.0.0"}]}), encoding="utf-8")
    return tmp_path


def test_bump_version_syncs_all(tmp_path):
    repo = _mk_repo(tmp_path)
    bump_mod.bump(repo, "1.1.0", "eval-cs-skill release")
    assert (repo / "VERSION").read_text().strip() == "1.1.0"
    assert (repo / "plugins/codestable/skills/cs-onboard/VERSION").read_text().strip() == "1.1.0"
    assert json.loads((repo / "plugins/codestable/.codex-plugin/plugin.json").read_text())["version"] == "1.1.0"
    assert json.loads((repo / ".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"] == "1.1.0"
    assert json.loads((repo / ".agents/plugins/marketplace.json").read_text())["plugins"][0]["version"] == "1.1.0"
    assert "## 1.1.0" in (repo / "CHANGELOG.md").read_text()


def test_bump_rejects_non_semver(tmp_path):
    assert bump_mod.main(["--to", "not-semver", "--root", str(_mk_repo(tmp_path))]) == 2


# ---- adapt_extracted_skill ----

def _mk_draft(tmp_path, skill_lines=10):
    d = tmp_path / "draft"
    (d / "reference").mkdir(parents=True)
    (d / "inventory").mkdir()
    (d / "templates").mkdir()
    (d / "scripts").mkdir()
    (d / "SKILL.md").write_text("# skill 🚀✨\n" + "\n".join(f"line {i}" for i in range(skill_lines)), encoding="utf-8")
    (d / "README.md").write_text("readme", encoding="utf-8")
    (d / "reference/patterns.md").write_text("# patterns", encoding="utf-8")
    (d / "inventory/inventory.json").write_text("{}", encoding="utf-8")
    (d / "templates/t.md").write_text("tmpl", encoding="utf-8")
    (d / "scripts/x.py").write_text("print(1)", encoding="utf-8")
    return d


def test_adapt_produces_compliant_structure(tmp_path):
    draft = _mk_draft(tmp_path)
    target = tmp_path / "out"
    adapt_mod.adapt(draft, target)
    assert (target / "references").is_dir()                       # 复数
    assert not (target / "reference").exists()                    # 无单数
    assert (target / "references/patterns/protocol.md").is_file() # file→子目录/protocol
    assert (target / "references/templates/support/t.md").is_file()
    assert not (target / "README.md").exists()                    # 丢 README
    assert not (target / "inventory").exists()                    # 丢 inventory
    assert (target / "scripts/x.py").is_file()                    # 保留 scripts
    assert "🚀" not in (target / "SKILL.md").read_text(encoding="utf-8")  # 去 emoji


def test_adapt_enforces_line_limit(tmp_path):
    draft = _mk_draft(tmp_path, skill_lines=400)
    target = tmp_path / "out"
    adapt_mod.adapt(draft, target)
    assert len((target / "SKILL.md").read_text().splitlines()) <= adapt_mod.MAX_SKILL_LINES + 1
    assert (target / "references/overview/protocol.md").is_file()


# ---- regression ----

def test_regression_verdict():
    assert reg_mod.verdict([0.5] * 5, [0.9] * 5) == "improved"
    assert reg_mod.verdict([0.9] * 5, [0.5] * 5) == "regressed"
    assert reg_mod.verdict([0.7] * 5, [0.7] * 5) == "inconclusive"


def test_regression_record_then_compare(tmp_path):
    dst = tmp_path / "exp"
    shutil.copytree(EXPERIMENT, dst, ignore=shutil.ignore_patterns("artifacts", "iteration-*.md", "results.md"))
    assert reg_mod.main(["--experiment", str(dst), "--n", "3", "--record-baseline"]) == 0
    # 相同 candidate 对比 → 不 regressed → exit 0
    assert reg_mod.main(["--experiment", str(dst), "--n", "3"]) == 0
