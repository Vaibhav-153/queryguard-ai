import zipfile

import pytest

from queryguard.ingestion.common import IngestionError, safe_filename, validate_office_archive


def test_safe_filename_removes_user_paths():
    assert safe_filename("../../private/report.pdf") == "report.pdf"
    assert safe_filename(r"..\\private\\report.pdf") == "private_report.pdf"


def test_office_archive_rejects_large_uncompressed_content(tmp_path):
    archive = tmp_path / "large.xlsx"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("xl/worksheets/sheet1.xml", "x" * 2048)

    with pytest.raises(IngestionError, match="safety limit"):
        validate_office_archive(archive, max_uncompressed_bytes=1024)
