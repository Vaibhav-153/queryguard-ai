import pytest

from queryguard.governance.validator import validate_sql

ALLOWED = {"customer", "invoice", "track", "artist", "genre"}

@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM Customer",
        "UPDATE Customer SET FirstName='x'",
        "DROP TABLE Customer",
        "CREATE TABLE Evil(id INTEGER)",
        "PRAGMA table_info(Customer)",
        "ATTACH DATABASE '/tmp/x.db' AS x",
    ],
)
def test_destructive_or_administrative_sql_is_blocked(sql):
    result = validate_sql(sql, ALLOWED)
    assert result.is_safe is False


def test_multiple_statements_are_blocked():
    result = validate_sql("SELECT * FROM Customer; DELETE FROM Customer", ALLOWED)
    assert result.is_safe is False


def test_unapproved_table_is_blocked():
    result = validate_sql("SELECT * FROM Secrets", ALLOWED)
    assert result.is_safe is False
    assert "Secrets" in result.errors[0]


def test_safe_join_is_allowed():
    result = validate_sql(
        "SELECT c.CustomerId, SUM(i.Total) FROM Customer c JOIN Invoice i ON i.CustomerId=c.CustomerId GROUP BY c.CustomerId",
        ALLOWED,
    )
    assert result.is_safe is True
    assert set(result.tables) == {"Customer", "Invoice"}


def test_cte_is_allowed_without_treating_cte_alias_as_database_table():
    result = validate_sql(
        "WITH totals AS (SELECT CustomerId, SUM(Total) AS revenue FROM Invoice GROUP BY CustomerId) SELECT c.CustomerId, t.revenue FROM Customer c JOIN totals t ON t.CustomerId=c.CustomerId",
        ALLOWED,
    )
    assert result.is_safe is True
