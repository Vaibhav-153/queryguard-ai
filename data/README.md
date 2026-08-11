# Data Documentation

This directory contains the datasets and evaluation data used by QueryGuard AI.

The project deliberately separates:

1. the small local database used for the working application and recruiter demo;
2. the manually reviewed evaluation dataset used for repeatable testing;
3. larger optional external benchmarks that are downloaded separately.

No private, confidential, customer, medical, financial, or personally collected user data is required by this project.

---

## Directory Structure

```text
data/
├── README.md
│
├── chinook/
│   ├── Chinook_Sqlite.sql
│   ├── Chinook_Sqlite.sqlite
│   └── LICENSE.md
│
├── evaluation/
│   └── chinook_eval.jsonl
│
└── spider/
    └── .gitkeep