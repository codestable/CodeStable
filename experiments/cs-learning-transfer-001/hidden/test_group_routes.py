from dispatchboard.grouping import group_routes


def test_route_grouping_keeps_its_sorted_deduplicated_behavior():
    events = [
        {"id": "r1", "group": "B", "value": 1},
        {"id": "r2", "group": "B", "value": 2},
        {"id": "r1", "group": "A", "value": 3},
        {"id": "r3", "group": "A", "value": 4},
    ]

    groups = group_routes(events)

    assert [key for key, _ in groups] == ["A", "B"]
    assert [row["id"] for row in groups[0][1]] == ["r1", "r3"]
    assert groups[0][1][0]["value"] == 3
    assert [row["id"] for _, rows in groups for row in rows].count("r1") == 1
