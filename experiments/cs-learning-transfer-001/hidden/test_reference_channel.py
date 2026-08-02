from dispatchboard.references import find_channel


def test_channel_reference_reuses_the_diagnosed_lookup_method():
    result = find_channel(" channel_7 ")

    assert result is not None
    assert result["id"] == "Channel-7"
