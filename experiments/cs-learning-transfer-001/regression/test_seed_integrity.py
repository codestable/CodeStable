from dispatchboard.grouping import group_jobs
from dispatchboard.job_sequence import next_job_number
from dispatchboard.references import find_channel, find_job
from dispatchboard.route_sequence import next_route_number


def test_unrelated_seed_contracts_remain_available():
    events = [
        {"id": "e1", "group": "B"},
        {"id": "e2", "group": "A"},
    ]

    assert find_job("JOB-7")["id"] == "JOB-7"
    assert find_channel("Channel-7")["id"] == "Channel-7"
    assert [key for key, _ in group_jobs(events)] == ["B", "A"]
    assert next_job_number([2, 7], []) == 8
    assert next_route_number([3, 5], []) == 6
