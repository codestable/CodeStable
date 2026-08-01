from dispatchboard.route_sequence import next_route_number


def test_route_sequence_never_reuses_active_or_retired_numbers():
    assert next_route_number([3, 5], [6, 13]) == 14
    assert next_route_number([], [9]) == 10
    assert next_route_number([], []) == 1
