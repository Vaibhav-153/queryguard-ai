import fitz

from queryguard.ingestion.pdf_loader import extract_pdf_units


def test_pdf_loader_keeps_page_number(tmp_path):
    path = tmp_path / "report.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Revenue increased during the year.")
    document.save(path)
    document.close()

    units, warnings = extract_pdf_units(path)
    assert warnings == []
    assert units[0].locator == "Page 1"
    assert "Revenue increased" in units[0].text
