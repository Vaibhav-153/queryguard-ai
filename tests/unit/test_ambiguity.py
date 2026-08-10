from queryguard.analysis.ambiguity import detect_ambiguity


def test_clear_question_is_not_ambiguous():
    result = detect_ambiguity("Show the top 5 customers by revenue")
    assert result.ambiguous is False


def test_vague_ranking_requires_metric():
    result = detect_ambiguity("Who are the best customers?")
    assert result.ambiguous is True
    assert result.reason == "ranking_metric_missing"


def test_recent_requires_time_window():
    result = detect_ambiguity("Show recent invoices")
    assert result.ambiguous is True
    assert result.reason == "time_window_missing"
