# Data Directory

This repository contains only public demo/evaluation data. Runtime user uploads are stored temporarily under `data/workspaces/` and are Git-ignored.

## Layout

```text
data/
├── chinook/                  # bundled public SQLite demo + upstream licenses
├── evaluation/               # small project evaluation sets
├── spider/                   # optional downloaded benchmark; not committed
└── workspaces/               # runtime uploads; not committed
```

## Chinook

Version: `v1.4.5`.

Upstream: https://github.com/lerocha/chinook-database

License: MIT. See the license files in `data/chinook/`.

Verified smoke checks:

```text
Customers: 59
Tracks: 3503
Total invoice revenue: 2328.60
```

Repository LF-normalized SQL SHA-256:

```text
caf31d698a4a79c628215b552dfe6575e71be052ae02b8f18e763498f55f5d44
```

Rebuild:

```bash
python scripts/setup_chinook.py
queryguard-verify
```

## Evaluation sets

- `chinook_eval.jsonl`: 15 structured-data questions.
- `synthetic_document_chunks.jsonl`: hand-authored document evidence.
- `synthetic_document_eval.jsonl`: 8 retrieval questions.
- `synthetic_invoice_eval.jsonl`: 3 simple invoice extraction examples.

The synthetic files are regression/evaluation aids created for this project; they are not representative real-world benchmarks.

## Spider

Spider is optional and separately licensed. It is deliberately not bundled.

```bash
python -m pip install gdown
python scripts/download_spider.py
```

Check current upstream documentation before use: https://yale-lily.github.io/spider

## Privacy

Never commit personal uploaded databases/documents/invoices. `data/workspaces/` is temporary and ignored by Git.
