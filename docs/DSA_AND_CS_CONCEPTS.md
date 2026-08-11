# DSA and Computer Science Concepts Used Naturally

## Hash maps / dictionaries

Where: schema lookup, JSON metadata, normalized column mapping.

Why: fast key-based lookup.

Average lookup: O(1).

Alternative: repeated list scanning O(n).

Interview prompt: “Given table schemas by name, how would you retrieve one efficiently?”

## Sets

Where: SQL allowed tables, duplicate token/document frequencies, used sanitized names.

Why: membership/deduplication.

Average membership: O(1).

## Graphs

Relational schema can be modeled as a graph:

- table = node;
- foreign key = edge.

QueryGuard uses one-hop neighbor expansion around retrieved tables.

A production schema-linking feature could use BFS/shortest paths for multi-hop join discovery.

## Ranking / Top-K

Where: schema and document retrieval.

Current implementation scores all candidates and sorts.

For N documents:

- scoring: O(N × query-term work);
- sort: O(N log N).

For small schemas/doc collections this is simpler than ANN infrastructure.

Alternative at large scale: heap top-K O(N log K), or ANN vector index.

## Inverted-index concept

BM25 document frequency behaves like a small information-retrieval index: rare tokens contribute more than common tokens.

Practice problem: build token → document IDs mapping and return documents containing all query terms.

## AST traversal

Where: SQLGlot validator.

The validator walks SQL expression nodes and checks denied node types/tables.

Complexity is roughly O(number of AST nodes).

Practice problem: traverse an expression tree and reject a forbidden operator.

## Caching

Settings are cached with `lru_cache(maxsize=1)` because application environment settings should be constructed once during normal runtime.

Query/document services are not globally cached for arbitrary workspaces to avoid cross-workspace data leakage.

## Filesystem isolation

Workspace ID maps to one directory. This is a simple namespace/isolation pattern.

Production alternatives: object storage prefixes, database tenant IDs, encrypted volumes.

## Database indexes and query planning

SQLite indexes can reduce lookup/join work from scanning many rows to indexed lookup. QueryGuard does not automatically create indexes on uploaded databases because it is read-only. A user can inspect query plans outside the generated workflow if performance matters.

## Serialization

Workspace metadata/chunks/invoice records are serialized to JSON. API models are serialized by Pydantic/FastAPI.

Trade-off: JSON is readable/easy but not efficient for massive document indexes.
