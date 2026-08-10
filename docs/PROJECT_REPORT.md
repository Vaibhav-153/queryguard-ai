# Project report

## Problem

People often know the business question they want answered but not the relational schema or SQL needed to answer it. A direct LLM-to-database design is unsafe and can return convincing wrong answers. QueryGuard treats SQL generation as an untrusted proposal that must pass deterministic controls before execution.

## Implemented workflow

Natural language -> ambiguity check -> schema retrieval -> local LLM SQL -> AST policy -> read-only SQLite -> verified rows -> presentation metadata.

## Advanced differentiators

### 1. Schema retrieval

Problem: full-schema prompts become noisy and costly as schemas grow.

Implementation: explainable lexical baseline plus optional Sentence Transformer embeddings. Direct table mentions receive a transparent boost; Top-K relevance is measured separately from SQL generation.

Evidence currently measured on 15 custom Chinook questions:
- Recall@1: 0.800
- Recall@3: 0.967
- Recall@5: 0.967

### 2. AST-based governance

Problem: prompts cannot guarantee safe SQL.

Implementation: SQLGlot parses the generated statement. The validator requires one SELECT-style root, blocks destructive/administrative AST nodes, checks physical tables against the live schema allowlist, and correctly excludes CTE aliases. SQLite then provides a second read-only boundary.

### 3. Ambiguity + bounded repair

Problem: an LLM can silently guess what “best” or “recent” means and can loop indefinitely when trying to self-correct.

Implementation: selected ambiguity patterns request clarification; ordinary generation errors may trigger one repair attempt; security violations never trigger repair.

## Data

The demo uses Chinook 1.4.5 from the official upstream project. The repository includes its SQL script and a generated SQLite database with recorded checksums. A 15-question custom evaluation set contains gold executable SQL.

Spider 1.0 is optional for cross-domain evaluation and remains separately downloaded/licensed.

## Verified build results

Measured in the artifact-build environment:
- Chinook SQL source downloaded from official v1.4.5 path;
- SQLite built successfully;
- customer count = 59;
- track count = 3,503;
- unit/integration tests not requiring SQLGlot passed;
- lexical retrieval metrics above were generated and saved.

Full SQLGlot/Ollama end-to-end metrics are deliberately marked not tested in this environment because the runtime package index did not provide SQLGlot and no Ollama model was installed. GitHub CI is configured to install normal project dependencies and execute those tests.

## Limitations

A syntactically valid, safe query can still encode the wrong business meaning. The ambiguity detector is not a general semantic judge. A small public demo database does not represent enterprise data governance. Model benchmarks can be contaminated by pretraining. Production rollout therefore requires human review for important decisions and stronger authorization controls.
