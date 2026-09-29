from queryguard.sql_guard import validate_sql

ALLOWED = {"customer", "invoice", "track"}


def test_safe_select_passes():
    result = validate_sql("SELECT CustomerId FROM Customer LIMIT 2", ALLOWED)
    assert result.is_safe
    assert "Customer" in result.tables


def test_cte_over_allowed_table_passes():
    result = validate_sql(
        "WITH totals AS (SELECT CustomerId, SUM(Total) total FROM Invoice GROUP BY CustomerId) "
        "SELECT * FROM totals",
        ALLOWED,
    )
    assert result.is_safe
    assert "Invoice" in result.tables


def test_destructive_statement_is_blocked():
    result = validate_sql("DELETE FROM Customer", ALLOWED)
    assert not result.is_safe


def test_multiple_statements_are_blocked():
    result = validate_sql("SELECT * FROM Customer; SELECT * FROM Track", ALLOWED)
    assert not result.is_safe


def test_unknown_table_is_blocked():
    result = validate_sql("SELECT * FROM Secrets", ALLOWED)
    assert not result.is_safe
    assert "Secrets" in " ".join(result.errors)
