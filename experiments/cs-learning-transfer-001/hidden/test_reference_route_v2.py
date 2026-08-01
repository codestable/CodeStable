from dispatchboard.references import REFERENCE_POLICY, find_route


def test_opaque_v2_route_reference_requires_exact_storage_spelling():
    assert REFERENCE_POLICY == "opaque-v2"
    assert find_route("Route_7")["id"] == "Route_7"
    assert find_route(" route_7 ") is None
    assert find_route("route_7") is None
    assert find_route("Route-7") is None
