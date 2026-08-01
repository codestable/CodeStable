"""learning-transfer lesson oracle 的严格 schema 与迁移契约。"""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/skills/eval-cs-skill/scripts"
EXPERIMENT = ROOT / "experiments/cs-learning-transfer-001"
SEED_BUILDER = ROOT / "experiments/seeds/dispatchboard-learning/build-seed.py"
sys.path.insert(0, str(SCRIPTS))

from scorers.learning_transfer import (  # noqa: E402
    validate_lesson_transition,
    validate_observed_lesson,
)


VALID_LESSON = """---
status: observed
scope: reference lookup
date: 2026-08-02
---
规则：修改 sibling lookup 前同时核对 storage 与 query normalization。
适用 / 不适用：适用于引用查找；已有 canonical owner 时停止。
证据：tests/test_references.py。
候选归宿：project-doc
"""


def _write_lesson(
    repo: Path,
    text: str = VALID_LESSON,
    relative: str = ".codestable/lessons/2026-08-02-reference-lookup.md",
) -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _validate(repo: Path, paths: list[str] | None = None) -> dict:
    return validate_observed_lesson(
        repo,
        required_concepts=["storage", "query normalization"],
        paths=paths,
    )


def test_observed_lesson_accepts_the_exact_schema(tmp_path: Path) -> None:
    _write_lesson(tmp_path)

    result = _validate(tmp_path)

    assert result == {
        "ok": True,
        "path": ".codestable/lessons/2026-08-02-reference-lookup.md",
        "errors": [],
    }


@pytest.mark.parametrize(
    "mutated",
    [
        VALID_LESSON.replace("date: 2026-08-02", "date: 2026-08-02\nowner: docs"),
        VALID_LESSON.replace("scope: reference lookup", "scope: first\nscope: second"),
        VALID_LESSON.replace("status: observed", "status: [observed]"),
        VALID_LESSON.replace("scope: reference lookup", "scope: 7"),
        VALID_LESSON.replace("date: 2026-08-02", "date: [2026-08-02]"),
    ],
    ids=[
        "extra-frontmatter-key",
        "duplicate-frontmatter-key",
        "status-wrong-type",
        "scope-wrong-type",
        "date-wrong-type",
    ],
)
def test_observed_lesson_rejects_non_exact_frontmatter(
    tmp_path: Path,
    mutated: str,
) -> None:
    _write_lesson(tmp_path, mutated)

    assert _validate(tmp_path)["ok"] is False


@pytest.mark.parametrize(
    "mutated",
    [
        VALID_LESSON.replace(
            "规则：修改 sibling lookup 前同时核对 storage 与 query normalization。\n",
            "规则：修改 sibling lookup 前同时核对 storage 与 query normalization。\n"
            "规则：不要改 display spelling。\n",
        ),
        VALID_LESSON.replace(
            "候选归宿：project-doc\n",
            "候选归宿：project-doc\n额外说明：不可进入 oracle。\n",
        ),
        VALID_LESSON.replace("适用 / 不适用：适用于引用查找；已有 canonical owner 时停止。", "适用 / 不适用："),
        VALID_LESSON.replace("候选归宿：project-doc", "候选归宿：wiki"),
        VALID_LESSON.replace(
            "证据：tests/test_references.py。",
            "证据：tests/a.py；tests/b.py；tests/c.py；tests/d.py。",
        ),
    ],
    ids=[
        "duplicate-body-field",
        "hidden-extra-body-line",
        "empty-body-value",
        "unknown-candidate-home",
        "too-many-evidence-items",
    ],
)
def test_observed_lesson_rejects_non_exact_body(
    tmp_path: Path,
    mutated: str,
) -> None:
    _write_lesson(tmp_path, mutated)

    assert _validate(tmp_path)["ok"] is False


@pytest.mark.parametrize(
    ("relative", "text"),
    [
        (
            ".codestable/lessons/2026-08-03-reference-lookup.md",
            VALID_LESSON,
        ),
        (
            ".codestable/lessons/2026-02-30-reference-lookup.md",
            VALID_LESSON.replace("date: 2026-08-02", "date: '2026-02-30'"),
        ),
        (
            ".codestable/lessons/2026-08-02-Reference_lookup.md",
            VALID_LESSON,
        ),
        (
            ".codestable/lessons/2026-08-02-abcdefghijklmnopqrstuvwxyz12345.md",
            VALID_LESSON,
        ),
        (
            ".codestable/other/2026-08-02-reference-lookup.md",
            VALID_LESSON,
        ),
    ],
    ids=[
        "date-mismatch",
        "invalid-calendar-date",
        "invalid-slug-characters",
        "slug-too-long",
        "wrong-home",
    ],
)
def test_observed_lesson_rejects_invalid_path_or_date(
    tmp_path: Path,
    relative: str,
    text: str,
) -> None:
    _write_lesson(tmp_path, text, relative)

    assert _validate(tmp_path, paths=[relative])["ok"] is False


def test_observed_lesson_rejects_escape_and_symlink_paths(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-lesson.md"
    outside.write_text(VALID_LESSON, encoding="utf-8")
    assert _validate(tmp_path, paths=["../outside-lesson.md"])["ok"] is False

    target = tmp_path / "target.md"
    target.write_text(VALID_LESSON, encoding="utf-8")
    link = tmp_path / ".codestable/lessons/2026-08-02-reference-lookup.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    assert _validate(tmp_path)["ok"] is False


def _transition_lessons() -> tuple[str, str]:
    after = VALID_LESSON.replace("status: observed", "status: validated").replace(
        "证据：tests/test_references.py。",
        "证据：tests/test_references.py。；tests/test_channel_references.py。",
    )
    return VALID_LESSON, after


def test_lesson_transition_accepts_exactly_one_appended_evidence_item() -> None:
    before, after = _transition_lessons()

    assert validate_lesson_transition(before, after) == {"ok": True, "errors": []}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda before, after: after.replace(
            "tests/test_channel_references.py。",
            "tests/test_channel_references.py。；tests/test_route_references.py。",
        ),
        lambda before, after: after.replace(
            "tests/test_references.py。；tests/test_channel_references.py。",
            "tests/test_channel_references.py。；tests/test_references.py。",
        ),
        lambda before, after: after.replace(
            "tests/test_references.py。；",
            "tests/test_references_v2.py。；",
        ),
        lambda before, after: after.replace(
            "候选归宿：project-doc\n",
            "候选归宿：project-doc\n隐藏正文：不允许。\n",
        ),
        lambda before, after: after.replace(
            "tests/test_channel_references.py。",
            "已再次验证。",
        ),
        lambda before, after: after.replace(
            "tests/test_channel_references.py。",
            "验证通过 1/1。",
        ),
    ],
    ids=[
        "append-two",
        "reorder-old-evidence",
        "rewrite-old-evidence",
        "hidden-body-change",
        "new-evidence-without-pointer",
        "numeric-fraction-is-not-a-pointer",
    ],
)
def test_lesson_transition_rejects_non_incremental_changes(mutation) -> None:
    before, after = _transition_lessons()

    result = validate_lesson_transition(before, mutation(before, after))

    assert result["ok"] is False


def test_retirement_marker_must_be_in_the_new_evidence_item() -> None:
    before = VALID_LESSON.replace("status: observed", "status: validated").replace(
        "证据：tests/test_references.py。",
        "证据：tests/test_references.py canonical owner 已确认。",
    )
    after = before.replace("status: validated", "status: retired").replace(
        "证据：tests/test_references.py canonical owner 已确认。",
        "证据：tests/test_references.py canonical owner 已确认。；tests/test_policy.py。",
    )

    result = validate_lesson_transition(before, after)

    assert result["ok"] is False
    assert "退役原因" in result["errors"]


def _build_seed(repo: Path) -> None:
    subprocess.run(
        [sys.executable, str(SEED_BUILDER), "--out", str(repo)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _apply_asset(script: str, repo: Path) -> None:
    subprocess.run(
        [sys.executable, str(EXPERIMENT / script), str(repo)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _references(repo: Path) -> dict:
    return runpy.run_path(str(repo / "dispatchboard/references.py"))


def test_fixture_candidates_do_not_copy_canonical_owner_contracts(tmp_path: Path) -> None:
    issue = json.loads(
        (EXPERIMENT / "fixtures/positive/lt-issue-reference.json").read_text(encoding="utf-8")
    )["scenario"]
    epic = json.loads(
        (EXPERIMENT / "fixtures/positive/lt-epic-sequence.json").read_text(encoding="utf-8")
    )["scenario"]
    stale = json.loads(
        (EXPERIMENT / "fixtures/stale/lt-stale-reference-v2.json").read_text(encoding="utf-8")
    )["scenario"]

    assert issue["candidate"]["required_concepts"] == [
        "storage",
        "query",
        "normalization",
        "display spelling",
    ]
    assert "canonical policy" in issue["a"]["request"]
    assert stale["candidate"]["required_concepts"] == issue["candidate"]["required_concepts"]
    assert epic["candidate"]["required_concepts"] == [
        "persisted history sources",
        "single snapshot",
        "sibling allocator",
    ]

    repo = tmp_path / "seed"
    _build_seed(repo)
    attention = (repo / ".codestable/attention.md").read_text(encoding="utf-8")
    epic_body = (repo / ".codestable/epics/sequence-rollout.md").read_text(
        encoding="utf-8"
    ).split("# Sequence rollout", 1)[1]
    assert "reference_policy" not in attention
    assert "active" not in epic_body
    assert "retired" not in epic_body
    assert "max" not in epic_body


def test_reference_preflight_separates_naive_and_golden_siblings(tmp_path: Path) -> None:
    naive = tmp_path / "naive"
    golden = tmp_path / "golden"
    _build_seed(naive)
    _build_seed(golden)
    _apply_asset("preflight/issue-reference-naive.py", naive)
    _apply_asset("preflight/issue-reference-golden.py", golden)

    naive_refs = _references(naive)
    golden_refs = _references(golden)
    assert naive_refs["find_job"](" job_7 ")["id"] == "JOB-7"
    assert golden_refs["find_job"](" job_7 ")["id"] == "JOB-7"
    assert naive_refs["find_channel"](" channel_7 ") is None
    assert golden_refs["find_channel"](" channel_7 ")["id"] == "Channel-7"


def test_stale_hook_migrates_a_side_before_leaving_the_sibling_stale(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _build_seed(repo)
    _apply_asset("preflight/issue-reference-golden.py", repo)
    lesson = repo / ".codestable/lessons/2026-08-02-reference-lookup.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text(VALID_LESSON, encoding="utf-8")
    lesson_before = lesson.read_bytes()

    _apply_asset("hooks/stale-reference-opaque-v2.py", repo)

    refs = _references(repo)
    assert refs["REFERENCE_POLICY"] == "opaque-v2"
    assert refs["find_job"]("JOB-7")["id"] == "JOB-7"
    assert refs["find_job"](" job_7 ") is None
    assert refs["find_job"]("job-7") is None
    assert refs["find_job"]("JOB_7") is None
    assert refs["find_route"](" route-7 ")["id"] == "Route_7"
    assert "reference_policy: opaque-v2" in (
        repo / ".codestable/attention.md"
    ).read_text(encoding="utf-8")
    public_test = (repo / "tests/test_references.py").read_text(encoding="utf-8")
    assert "test_job_reference_uses_opaque_v2_policy" in public_test
    assert "test_route_reference_uses_v1_canonical_policy" not in public_test
    assert lesson.read_bytes() == lesson_before
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_stale_preflight_requires_all_opaque_variants_to_be_distinct(tmp_path: Path) -> None:
    naive = tmp_path / "naive"
    golden = tmp_path / "golden"
    _build_seed(naive)
    _build_seed(golden)
    _apply_asset("preflight/stale-reference-v2-naive.py", naive)
    _apply_asset("preflight/stale-reference-v2-golden.py", golden)

    naive_refs = _references(naive)
    golden_refs = _references(golden)
    variants = [" route_7 ", "route_7", "Route-7"]
    assert all(naive_refs["find_route"](value) is not None for value in variants)
    assert all(golden_refs["find_route"](value) is None for value in variants)
    assert golden_refs["find_route"]("Route_7")["id"] == "Route_7"
