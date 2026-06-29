from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "cs-onboard/tools"
DOD_RUNNER = TOOLS_DIR / "codestable-dod-runner.py"


def run_dod(tmp_path: Path, checklist_yaml: str) -> dict:
    repo = tmp_path / "proj"
    (repo / ".codestable").mkdir(parents=True, exist_ok=True)  # repo_root() marker
    checklist = repo / "checklist.yaml"
    checklist.write_text(checklist_yaml, encoding="utf-8")
    out = repo / "dod-results.json"
    subprocess.run(
        [sys.executable, str(DOD_RUNNER), "--checklist", str(checklist), "--json-out", str(out)],
        cwd=repo,
        text=True,
        capture_output=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": __import__("os").environ.get("PATH", "")},
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_top_level_dod_commands_are_run(tmp_path: Path) -> None:
    """Regression: top-level `dod.commands` (the authoritative schema) must be
    executed, not skipped."""
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
dod:
  commands:
    - id: CMD-001
      command: "true"
      core: true
    - id: CMD-002
      command: "false"
      core: true
""",
    )
    assert data["status"] == "failed"  # CMD-002 (core) exits non-zero
    assert {e["id"] for e in data["evidence"]} == {"CMD-001", "CMD-002"}


def test_step_level_dod_commands_still_supported(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
    dod:
      commands:
        - id: S-1
          command: "true"
          core: true
""",
    )
    assert data["status"] == "passed"
    assert [e["id"] for e in data["evidence"]] == ["S-1"]


def test_top_and_step_level_merge(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
dod:
  commands:
    - id: TOP-1
      command: "true"
      core: true
steps:
  - action: a
    status: done
    dod:
      commands:
        - id: STEP-1
          command: "true"
          core: true
""",
    )
    assert data["status"] == "passed"
    assert {e["id"] for e in data["evidence"]} == {"TOP-1", "STEP-1"}


def test_non_core_failure_is_warning_not_block(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
dod:
  commands:
    - id: NC-1
      command: "false"
      core: false
""",
    )
    assert data["status"] == "passed"
    assert any("NC-1" in w for w in data["warnings"])


def test_no_commands_is_skipped(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
""",
    )
    assert data["status"] == "skipped"
