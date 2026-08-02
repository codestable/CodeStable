from dispatchboard.display import display_route_label


def test_display_label_trims_without_canonicalizing_visible_text():
    assert display_route_label("  Route_Seven-A  ") == "Route_Seven-A"
    assert display_route_label(" NORTH_wing ") == "NORTH_wing"
