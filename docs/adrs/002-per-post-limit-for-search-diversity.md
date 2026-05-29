# ADR-002: Per-Post Chunk Limit for Search Result Diversity

## Status
Accepted

## Context
When searching the knowledge base (which is segmented into text chunks), longer posts with high matching density often dominate the top query results. For example, a single comprehensive essay on TDD might occupy all 5 slots of a limit-5 search, hiding other canonical or shorter posts that also cover TDD from different perspectives.

While this behavior is correct for deep context retrieval (Ideation), it creates a suboptimal experience for discovery tasks like internal link-building (Drafting), where the user/agent wants a diverse set of *distinct* posts to reference.

## Decision
We will introduce a `per_post_limit` parameter to both the query API and the CLI configurations.
- `per_post_limit` specifies the maximum number of chunks from the same source file that can be included in the search results.
- If `per_post_limit` is set (e.g., `1`), the indexer will filter out duplicate sources from the candidates.
- To prevent result starvation when filtering is active, the query layer will pull a larger candidate pool from the database before performing post-level deduplication.

## Consequences
- **Positive:** Enables the caller to explicitly choose between deep context retrieval (unlimited chunks per post) and diverse link discovery (e.g. 1 chunk per post).
- **Positive:** Exposes the parameter through CLI flags (`--per-post-limit`) and Pydantic configuration (`per_post_limit`).
- **Neutral:** Adds a processing step in the Python engine (`_apply_per_post_limit`) after database retrieval.
