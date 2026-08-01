import ast
import inspect

import dispatchboard.grouping as grouping


def test_group_jobs_refactor_preserves_first_seen_order_and_duplicates():
    events = [
        {"id": "e1", "group": "B", "value": 1},
        {"id": "e1", "group": "B", "value": 2},
        {"id": "e2", "group": "A", "value": 3},
    ]

    groups = grouping.group_jobs(events)

    implementation = ast.parse(inspect.getsource(grouping.group_jobs))
    assert not any(isinstance(node, ast.For) for node in ast.walk(implementation))
    assert any(isinstance(node, ast.Call) for node in ast.walk(implementation))
    assert [key for key, _ in groups] == ["B", "A"]
    assert [row["value"] for row in groups[0][1]] == [1, 2]
