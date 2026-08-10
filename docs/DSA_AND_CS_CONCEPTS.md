# DSA and computer-science concepts

| Concept | Where it appears | Why | Complexity | Alternative |
|---|---|---|---|---|
| Hash set | allowed table names | O(1) average membership check | O(1) average lookup, O(n) space | list would be O(n) lookup |
| Hash map | table name -> schema | fast schema expansion | O(1) average lookup | repeated linear scan |
| Graph | foreign-key relationships | tables are nodes, FKs are edges | one-hop expansion O(V+E) worst case | no expansion/full schema |
| Inverted statistics | lexical retrieval | document frequency/idf | build O(total tokens) | library TF-IDF |
| Top-K ranking | schema retrieval | retain relevant tables | current sort O(n log n) | heap O(n log k) at larger n |
| Vector dot product | semantic retrieval | cosine after normalization | O(nd) | ANN index |
| AST traversal | SQL validation | structural safety checks | O(number of AST nodes) | regex is less reliable |
| Database index | Chinook foreign keys | faster joins | DB-dependent | full scans |
| Progress callback | query timeout | bounded execution | callback every N VM ops | database-native statement timeout |

## Practice questions

1. Change retrieval ranking from full sort to a heap and explain when it becomes useful.
2. Model Chinook foreign keys as an adjacency list and find all tables within two hops.
3. Explain why a set is preferable to a list for table allowlist membership.
4. Given n schema documents with d-dimensional embeddings, compare exact cosine search with ANN indexing.
5. Walk a simple SQL AST and collect all referenced physical tables while ignoring CTE aliases.
