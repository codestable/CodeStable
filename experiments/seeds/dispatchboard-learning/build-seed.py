#!/usr/bin/env python3
"""构建 learning-transfer 实验使用的可复现 dispatchboard seed。"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


FILES = {
    "pyproject.toml": """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "dispatchboard"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
""",
    "dispatchboard/__init__.py": "",
    "dispatchboard/patches.py": '''"""Partial-update helpers for dispatchboard records."""


def patch_job(job: dict, changes: dict) -> dict:
    raise NotImplementedError("patch_job is not implemented")


def patch_route(route: dict, changes: dict) -> dict:
    raise NotImplementedError("patch_route is not implemented")
''',
    "dispatchboard/references.py": '''"""Reference lookup policies."""

REFERENCE_POLICY = "canonical-v1"
JOBS = {"JOB-7": {"id": "JOB-7", "title": "Pack"}}
CHANNELS = {"Channel-7": {"id": "Channel-7", "title": "North"}}
ROUTES = {
    "Route_7": {"id": "Route_7", "title": "Primary"},
}


def canonical_ref(value: str) -> str:
    return value.strip().replace("_", "-").casefold()


def find_job(reference: str) -> dict | None:
    return JOBS.get(reference)


def find_channel(reference: str) -> dict | None:
    return CHANNELS.get(reference)


def find_route(reference: str) -> dict | None:
    wanted = canonical_ref(reference)
    return next((item for key, item in ROUTES.items() if canonical_ref(key) == wanted), None)
''',
    "dispatchboard/grouping.py": '''"""Event grouping helpers."""


def group_jobs(events: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for event in events:
        groups.setdefault(event["group"], []).append(event)
    return list(groups.items())


def group_routes(events: list[dict]) -> list[tuple[str, list[dict]]]:
    unique = {event["id"]: event for event in events}
    groups: dict[str, list[dict]] = {}
    for event in unique.values():
        groups.setdefault(event["group"], []).append(event)
    return sorted(groups.items())
''',
    "dispatchboard/display.py": '''"""Display-only formatting helpers."""


def display_route_label(value: str) -> str:
    raise NotImplementedError("display_route_label is not implemented")
''',
    "dispatchboard/job_sequence.py": '''"""Job number allocation."""


def next_job_number(active_numbers: list[int], retired_numbers: list[int]) -> int:
    return max(active_numbers, default=0) + 1
''',
    "dispatchboard/route_sequence.py": '''"""Route number allocation."""


def next_route_number(active_numbers: list[int], retired_numbers: list[int]) -> int:
    return max(active_numbers, default=0) + 1
''',
    "tests/test_references.py": '''from dispatchboard.references import find_job, find_route


def test_route_reference_uses_v1_canonical_policy():
    assert find_route(" route-7 ")["id"] == "Route_7"


def test_exact_job_reference_remains_available():
    assert find_job("JOB-7")["id"] == "JOB-7"
''',
    "tests/test_grouping.py": '''from dispatchboard.grouping import group_jobs, group_routes


def test_unique_events_group_by_first_seen_key():
    events = [{"id": "e1", "group": "B"}, {"id": "e2", "group": "A"}]
    assert [key for key, _ in group_jobs(events)] == ["B", "A"]
    assert {key for key, _ in group_routes(events)} == {"A", "B"}
''',
    "tests/test_sequences.py": '''from dispatchboard.job_sequence import next_job_number
from dispatchboard.route_sequence import next_route_number


def test_sequence_advances_past_active_numbers():
    assert next_job_number([2, 7], []) == 8
    assert next_route_number([3, 5], []) == 6
''',
    ".codestable/attention.md": """# Attention

## 项目事实

- Python 验证使用 `python3 -m pytest -q`。
""",
}

EPIC = """---
status: active
created: 2026-08-02
work: ../work/epic-sequence-rollout.md
---

# Sequence rollout

## 目标

为 job 与 route 交付不会碰撞既有历史记录的编号分配能力。

## 子项契约

- `SEQ-A`：实现 job 编号分配并覆盖项目已有历史记录；验证通过后完成。
- `SEQ-B`：依赖 `SEQ-A`；为 route 交付同类编号分配能力。

## 验收

新分配编号不得与任何已持久化历史记录冲突；没有历史记录时从 1 开始。
"""

CURSOR = """---
epic: ../epics/sequence-rollout.md
phase: executing
approved_revision: {approved_revision}
current_item: SEQ-A
next_action: execute the approved current item
blocked_by: null
item_progression: per-item
milestone_commit: manual
remote_publish: manual
---

## 子项进度

- [ ] SEQ-A
- [ ] SEQ-B

## 临时决策与证据
"""


def _run(command: list[str], cwd: Path) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "dispatchboard-dev",
        "GIT_AUTHOR_EMAIL": "dev@dispatchboard.invalid",
        "GIT_COMMITTER_NAME": "dispatchboard-dev",
        "GIT_COMMITTER_EMAIL": "dev@dispatchboard.invalid",
        "GIT_AUTHOR_DATE": "2026-08-02T09:00:00+08:00",
        "GIT_COMMITTER_DATE": "2026-08-02T09:00:00+08:00",
    }
    subprocess.run(command, cwd=cwd, env=env, check=True, capture_output=True, text=True)


def build(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"拒绝构建：{out} 已存在且非空")
    out.mkdir(parents=True, exist_ok=True)
    for relative, content in FILES.items():
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    epic = out / ".codestable/epics/sequence-rollout.md"
    epic.parent.mkdir(parents=True, exist_ok=True)
    epic.write_text(EPIC, encoding="utf-8")
    approved = hashlib.sha256(epic.read_bytes()).hexdigest()
    cursor = out / ".codestable/work/epic-sequence-rollout.md"
    cursor.parent.mkdir(parents=True, exist_ok=True)
    cursor.write_text(CURSOR.format(approved_revision=approved), encoding="utf-8")
    _run(["git", "init", "-q", "-b", "main"], out)
    _run(["git", "add", "-A"], out)
    _run(["git", "commit", "-q", "-m", "seed dispatchboard learning scenarios"], out)


def verify() -> int:
    with tempfile.TemporaryDirectory(prefix="dispatchboard-learning-") as tmp:
        repo = Path(tmp) / "repo"
        build(repo)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=repo,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
        )
        epic = repo / ".codestable/epics/sequence-rollout.md"
        cursor = repo / ".codestable/work/epic-sequence-rollout.md"
        approved = hashlib.sha256(epic.read_bytes()).hexdigest()
        return result.returncode if approved in cursor.read_text(encoding="utf-8") else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return verify()
    if not args.out:
        parser.error("--out 或 --verify 必选其一")
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
