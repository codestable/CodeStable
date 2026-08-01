#!/usr/bin/env python3
"""Deterministic mutations used only by learning-transfer preflight and hooks."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def _write(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def apply_stale_reference_policy(repo: Path) -> None:
    _write(repo, "dispatchboard/references.py", _references("naive", opaque_v2=True))
    attention = repo / ".codestable/attention.md"
    attention_text = attention.read_text(encoding="utf-8")
    policy = (
        "- `reference_policy: opaque-v2`：业务引用按存储值精确匹配；不得 trim、casefold "
        "或互换 `_` / `-`，返回值保留存储 spelling。\n"
    )
    if policy not in attention_text:
        attention.write_text(attention_text.rstrip() + "\n" + policy, encoding="utf-8")
    _write(
        repo,
        "tests/test_references.py",
        '''
        from dispatchboard.references import find_job, find_route


        def test_job_reference_uses_opaque_v2_policy():
            assert find_job("JOB-7")["id"] == "JOB-7"
            assert find_job(" job-7 ") is None
            assert find_job("job-7") is None
            assert find_job("JOB_7") is None


        def test_exact_route_reference_remains_available():
            assert find_route("Route_7")["id"] == "Route_7"
        ''',
    )


def _patch_body(kind: str) -> str:
    if kind == "old":
        return """
        if value == "":
            continue
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
        """
    if kind == "truthy":
        return """
        if value:
            result[key] = value
        """
    raise ValueError(kind)


def _patch_function(name: str, kind: str) -> str:
    body = "\n".join(f"        {line}" for line in dedent(_patch_body(kind)).strip().splitlines())
    return f'''def {name}(record: dict, changes: dict) -> dict:
    result = record.copy()
    for key, value in changes.items():
{body}
    return result
'''


def _patches(mode: str) -> str:
    job_kind = "old"
    route_kind = "old" if mode == "golden" else "truthy"
    return f'''"""Partial-update helpers for dispatchboard records."""

{_patch_function("patch_job", job_kind)}

{_patch_function("patch_route", route_kind)}
'''


def _post_a_patch() -> str:
    return f'''"""Partial-update helpers for dispatchboard records."""

{_patch_function("patch_job", "old")}

def patch_route(route: dict, changes: dict) -> dict:
    raise NotImplementedError("patch_route is not implemented")
'''


def _job_sequence() -> str:
    return '''
    """Job number allocation."""


    def next_job_number(active_numbers: list[int], retired_numbers: list[int]) -> int:
        return max([*active_numbers, *retired_numbers], default=0) + 1
    '''


def _sequence(mode: str) -> str:
    expression = (
        "max([*active_numbers, *retired_numbers], default=0) + 1"
        if mode == "golden"
        else "max(active_numbers, default=0) + 1"
    )
    return f'''"""Route number allocation."""


def next_route_number(active_numbers: list[int], retired_numbers: list[int]) -> int:
    return {expression}
'''


def _grouping(mode: str) -> str:
    if mode == "naive":
        return '''
        """Event grouping helpers."""


        def _group_events(events: list[dict]) -> list[tuple[str, list[dict]]]:
            groups: dict[str, list[dict]] = {}
            for event in events:
                groups.setdefault(event["group"], []).append(event)
            return list(groups.items())


        def group_jobs(events: list[dict]) -> list[tuple[str, list[dict]]]:
            return _group_events(events)


        def group_routes(events: list[dict]) -> list[tuple[str, list[dict]]]:
            return _group_events(events)
        '''
    return '''
    """Event grouping helpers."""


    def _group_events(
        events: list[dict], *, deduplicate: bool = False, sort_keys: bool = False
    ) -> list[tuple[str, list[dict]]]:
        selected = list({event["id"]: event for event in events}.values()) if deduplicate else events
        groups: dict[str, list[dict]] = {}
        for event in selected:
            groups.setdefault(event["group"], []).append(event)
        items = list(groups.items())
        return sorted(items) if sort_keys else items


    def group_jobs(events: list[dict]) -> list[tuple[str, list[dict]]]:
        return _group_events(events)


    def group_routes(events: list[dict]) -> list[tuple[str, list[dict]]]:
        return _group_events(events, deduplicate=True, sort_keys=True)
    '''


def _display(mode: str) -> str:
    expression = (
        "value.strip()"
        if mode == "golden"
        else 'value.strip().replace("_", "-").casefold()'
    )
    return f'''"""Display-only formatting helpers."""


def display_route_label(value: str) -> str:
    return {expression}
'''


def _references(mode: str, *, opaque_v2: bool = False) -> str:
    if opaque_v2:
        policy = "opaque-v2"
        job_body = "return JOBS.get(reference)"
        channel_body = "return CHANNELS.get(reference)"
        route_body = (
            "return ROUTES.get(reference)"
            if mode == "golden"
            else "wanted = canonical_ref(reference)\n"
            "    return next((item for key, item in ROUTES.items() "
            "if canonical_ref(key) == wanted), None)"
        )
    else:
        policy = "canonical-v1"
        job_body = (
            "wanted = canonical_ref(reference)\n"
            "    return next((item for key, item in JOBS.items() "
            "if canonical_ref(key) == wanted), None)"
        )
        channel_body = (
            "wanted = canonical_ref(reference)\n"
            "    return next((item for key, item in CHANNELS.items() "
            "if canonical_ref(key) == wanted), None)"
            if mode == "golden"
            else "return CHANNELS.get(reference)"
        )
        route_body = (
            "wanted = canonical_ref(reference)\n"
            "    return next((item for key, item in ROUTES.items() "
            "if canonical_ref(key) == wanted), None)"
        )
    return f'''"""Reference lookup policies."""

REFERENCE_POLICY = "{policy}"
JOBS = {{"JOB-7": {{"id": "JOB-7", "title": "Pack"}}}}
CHANNELS = {{"Channel-7": {{"id": "Channel-7", "title": "North"}}}}
ROUTES = {{"Route_7": {{"id": "Route_7", "title": "Primary"}}}}


def canonical_ref(value: str) -> str:
    return value.strip().replace("_", "-").casefold()


def find_job(reference: str) -> dict | None:
    {job_body}


def find_channel(reference: str) -> dict | None:
    {channel_body}


def find_route(reference: str) -> dict | None:
    {route_body}
'''


def apply_preflight(repo: Path, scenario: str, mode: str) -> None:
    if mode not in {"naive", "golden"}:
        raise ValueError(mode)
    if scenario == "patch":
        _write(repo, "dispatchboard/patches.py", _patches(mode))
    elif scenario == "sequence":
        _write(repo, "dispatchboard/job_sequence.py", _job_sequence())
        _write(repo, "dispatchboard/route_sequence.py", _sequence(mode))
    elif scenario == "reference":
        _write(repo, "dispatchboard/references.py", _references(mode))
    elif scenario == "epic-sequence":
        _write(repo, "dispatchboard/job_sequence.py", _job_sequence())
        _write(repo, "dispatchboard/route_sequence.py", _sequence(mode))
        cursor = repo / ".codestable/work/epic-sequence-rollout.md"
        cursor_text = cursor.read_text(encoding="utf-8").replace("- [ ] SEQ-A", "- [x] SEQ-A")
        cursor.write_text(
            cursor_text.rstrip()
            + "\n\n- 晶化候选：实现 sibling allocator 前先盘点全部 persisted history sources，并建立 single snapshot。\n",
            encoding="utf-8",
        )
    elif scenario == "grouping":
        _write(repo, "dispatchboard/grouping.py", _grouping(mode))
    elif scenario == "display":
        _write(repo, "dispatchboard/patches.py", _post_a_patch())
        _write(repo, "dispatchboard/display.py", _display(mode))
    elif scenario == "stale-reference-v2":
        apply_stale_reference_policy(repo)
        _write(repo, "dispatchboard/references.py", _references(mode, opaque_v2=True))
    else:
        raise ValueError(scenario)
