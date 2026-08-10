# Data documentation

## Bundled dataset: Chinook 1.4.5

Source: https://github.com/lerocha/chinook-database
Official release used: v1.4.5
License: MIT (upstream license applies to Chinook files)

Bundled files:
- `chinook/Chinook_Sqlite.sql` - official SQL creation/population script.
- `chinook/Chinook_Sqlite.sqlite` - generated locally from that script.

Checksums produced during project build:
- SQL SHA-256: `fdcb271b3e9c840216b09168752bddca973ed3917b40e49b603b15831114aea1`
- SQLite SHA-256: `79df86ebd5c45f009ed35dbb19757cac4f9afb393352e3d2ffe128a60a2ea718`

The upstream project describes the database as a digital media store. Customer and employee records are fictitious/manual sample records and sales information is generated sample data. Do not treat it as representative production customer behavior.

## Custom evaluation set

`evaluation/chinook_eval.jsonl` contains manually written natural-language questions and executable gold SQL for the bundled Chinook database. It is for engineering evaluation and regression testing; it is not a statistically representative user study.

## Spider 1.0

Spider is not committed into this repository because it is much larger and has its own CC BY-SA 4.0 licensing/provenance. Use `python scripts/download_spider.py` after installing `gdown`, or download it from the official Yale page and place it under `data/spider/`.

Never mix Spider tuning examples into the final held-out evaluation split.
