import sqlite3
from contextlib import closing

import pandas as pd

from queryguard.ingestion.spreadsheet_loader import spreadsheet_to_sqlite


def test_csv_is_converted_to_sqlite(tmp_path):
    source = tmp_path / "sales.csv"
    pd.DataFrame(
        {
            "Customer": ["A", "B"],
            "Revenue": [10.0, 20.0],
        }
    ).to_csv(source, index=False)

    database = tmp_path / "sales.sqlite"
    result = spreadsheet_to_sqlite(
        source,
        database,
        max_office_uncompressed_bytes=10 * 1024 * 1024,
    )

    assert result.table_rows == {"sales": 2}
    with closing(sqlite3.connect(database)) as connection:
        count = connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    assert count == 2
