# Invoice Intelligence Pipeline

## Goal

Invoices contain both structured values (vendor, date, tax, total) and unstructured wording (payment terms, notes). QueryGuard keeps both forms instead of choosing only “PDF chat” or only “table extraction.”

## Supported inputs

- text/scanned PDF;
- PNG/JPG/JPEG (requires OCR);
- XLSX;
- CSV.

## Flow

```text
Invoice files
   ↓
file-specific extraction
   ↓
InvoiceRecord objects
   ↓
manual-review flags
   ↓
invoices.sqlite
   ↓
normal governed Text-to-SQL
```

For PDF/image invoices, raw extracted text also becomes document chunks for evidence Q&A.

## `InvoiceRecord`

Current normalized fields:

```text
source_file
invoice_number
vendor
invoice_date
due_date
currency
subtotal
tax
total
needs_review
notes
raw_text
```

`raw_text` is kept in JSON/evidence but is not inserted into the analytics SQLite table.

## PDF/image extraction

The baseline parser uses visible labels and regex patterns such as:

- `Invoice No:`;
- `Invoice Number:`;
- `Invoice Date:`;
- `Subtotal:`;
- `GST` / `VAT` / `Tax`;
- `Grand Total` / `Amount Due` / `Invoice Total`.

Currency is detected from common codes/symbols.

This is deliberately transparent and conservative.

## Spreadsheet invoice extraction

Column names are normalized and matched against aliases:

```text
invoice_no / invoice_number / invoice_id
vendor / supplier / seller
date / invoice_date
total / amount_due / invoice_total
```

A sheet without a recognizable total column is skipped with a warning. If no usable invoice sheet remains, ingestion fails instead of inventing values.

## Manual review

A record is flagged when important fields such as invoice number or total are missing.

This lets the UI say:

```text
28 records extracted; 3 require review
```

rather than quietly treating extraction as perfect.

## Analytics questions

Because normalized fields are in SQLite, questions can use the existing governed SQL path:

- Which vendor received the most money?
- What is total spend by currency?
- How many invoices need review?
- Show monthly invoice totals (when dates are standardized enough).

A real LLM provider is required for arbitrary questions; demo mode only has fixed Chinook SQL rules.

## Text questions

If raw invoice text exists, document retrieval can answer questions such as:

- What payment terms are stated on a specific invoice?
- Does an invoice mention a purchase order?

## Evaluation

```bash
python scripts/evaluate_invoice_extraction.py
```

The included three-example synthetic set currently produces 1.000 exact match over its six expected fields per example. This result is intentionally labeled **synthetic** and must not be reported as real-world invoice accuracy.

## Production evolution

A stronger invoice system could add:

- OCR confidence;
- vendor-specific layouts;
- line-item extraction;
- layout-aware document models;
- LLM JSON extraction with schema validation;
- duplicate invoice detection;
- human correction UI;
- a labeled real invoice benchmark.
