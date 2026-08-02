from dispatchboard.patches import patch_job


def test_patch_job_distinguishes_omit_clear_and_falsey_values():
    original = {
        "title": "Pack",
        "note": "fragile",
        "attempts": 3,
        "enabled": True,
    }
    result = patch_job(
        original,
        {"title": "", "note": None, "attempts": 0, "enabled": False},
    )

    assert result == {"title": "Pack", "attempts": 0, "enabled": False}
    assert original["note"] == "fragile"
