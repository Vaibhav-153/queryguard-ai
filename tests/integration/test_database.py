import sqlite3

import pytest

from queryguard.database.connection import execute_read_only, open_read_only
from queryguard.database.schema import extract_schema


def test_schema_contains_expected_chinook_tables(database_path):
    schema = extract_schema(database_path)
    table_names = {table.name for table in schema}
    assert {"Customer", "Invoice", "Track", "Artist", "Album"} <= table_names


def test_read_only_query_returns_expected_customer_count(database_path):
    result = execute_read_only(database_path, "SELECT COUNT(*) AS count FROM Customer")
    assert result.columns == ["count"]
    assert result.rows == [[59]]


def test_sqlite_connection_rejects_write(database_path):
    with open_read_only(database_path) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM Customer WHERE CustomerId = 1")
