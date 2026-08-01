from dispatchboard.patches import patch_route


def test_route_patch_uses_project_partial_update_semantics():
    original = {
        "label": "North",
        "note": "seasonal",
        "priority": 5,
        "enabled": True,
    }
    result = patch_route(
        original,
        {"label": "", "note": None, "priority": 0, "enabled": False},
    )

    assert result == {"label": "North", "priority": 0, "enabled": False}
    assert original["note"] == "seasonal"
