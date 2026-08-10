from queryguard.evaluation.metrics import result_match, table_recall_at_k


def test_result_match_ignores_order_when_requested():
    assert result_match(["x"], [[2], [1]], ["x"], [[1], [2]], False)


def test_result_match_respects_order():
    assert not result_match(["x"], [[2], [1]], ["x"], [[1], [2]], True)


def test_table_recall_at_k():
    assert table_recall_at_k(["Customer", "Invoice", "Track"], ["Customer", "Invoice"], 2) == 1.0
