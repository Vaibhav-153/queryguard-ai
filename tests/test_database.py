import sqlite3

import pytest

from queryguard.database import DatabaseError, execute_read_only, extract_schema


def test_schema_contains_expected_tables(demo_db):
    schema = extract_schema(demo_db)
    names = {table.name for table in schema}
    assert names == {"Customer", "Invoice", "Track"}
    invoice = next(table for table in schema if table.name == "Invoice")
    assert any(fk.target_table == "Customer" for fk in invoice.foreign_keys)


def test_read_only_query_executes(demo_db):
    result = execute_read_only(demo_db, "SELECT COUNT(*) AS total FROM Customer")
    assert result.columns == ["total"]
    assert result.rows == [[6]]
    assert result.truncated is False


def test_write_query_is_rejected_by_read_only_connection(demo_db):
    with pytest.raises(DatabaseError):
        execute_read_only(demo_db, "DELETE FROM Customer")
    with sqlite3.connect(demo_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM Customer").fetchone()[0] == 6


def test_result_limit_is_applied(demo_db):
    result = execute_read_only(demo_db, "SELECT * FROM Track ORDER BY TrackId", max_rows=3)
    assert result.row_count == 3
    assert result.truncated is True
