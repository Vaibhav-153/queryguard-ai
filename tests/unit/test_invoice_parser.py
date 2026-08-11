from queryguard.invoices.parser import parse_invoice_text


def test_invoice_text_parser_extracts_common_fields():
    text = """
    Acme Supplies Pvt Ltd
    Invoice No: INV-1042
    Invoice Date: 2026-08-01
    Subtotal: $100.00
    Tax: $18.00
    Grand Total: $118.00
    """
    record = parse_invoice_text("invoice.pdf", text)
    assert record.invoice_number == "INV-1042"
    assert record.vendor == "Acme Supplies Pvt Ltd"
    assert record.currency == "USD"
    assert record.subtotal == 100.0
    assert record.tax == 18.0
    assert record.total == 118.0
    assert record.needs_review is False
