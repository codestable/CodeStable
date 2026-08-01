from dispatchboard.references import find_job


def test_job_reference_normalizes_query_without_rewriting_storage():
    result = find_job(" job_7 ")

    assert result is not None
    assert result["id"] == "JOB-7"
