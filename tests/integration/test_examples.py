from pathlib import Path

from queryguard.ingestion.document_loader import extract_document_units
from queryguard.ingestion.spreadsheet_loader import spreadsheet_to_sqlite
from queryguard.invoices.parser import parse_invoice_file

EXAMPLES = Path("examples")
OFFICE_LIMIT = 120 * 1024 * 1024


def test_sample_sales_csv_can_build_a_workspace_database(tmp_path):
    result = spreadsheet_to_sqlite(
        EXAMPLES / "sample_sales.csv",
        tmp_path / "sales.sqlite",
        max_office_uncompressed_bytes=OFFICE_LIMIT,
    )

    assert result.table_rows == {"sample_sales": 5}


def test_sample_document_files_preserve_evidence_units():
    expected_minimums = {
        "sample_policy.pdf": 2,
        "sample_handbook.docx": 2,
        "sample_briefing.pptx": 2,
    }

    for filename, minimum in expected_minimums.items():
        units, warnings = extract_document_units(
            EXAMPLES / filename,
            max_uncompressed_bytes=OFFICE_LIMIT,
        )
        assert len(units) >= minimum
        assert warnings == []


def test_sample_invoice_csv_is_parseable():
    records, units, warnings = parse_invoice_file(
        EXAMPLES / "sample_invoices.csv",
        max_office_uncompressed_bytes=OFFICE_LIMIT,
    )

    assert len(records) == 3
    assert records[0].invoice_number == "INV-1001"
    assert records[0].total == 132.0
    assert units == []
    assert warnings == []
