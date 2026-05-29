# ADR-005: AI Agent Integration as an SDK Client (Information Hiding)

## Status
Accepted

## Context
During interactive sessions, the AI client was executing custom Python scripts importing low-level components (like LanceDB, pandas, or raw files) to query unique series or build custom mappings. 

While this direct scripting gives the client infinite flexibility, it represents a severe leak of implementation details (violating David Parnas's principle of Information Hiding):
1. **High Coupling:** The AI agent becomes tightly coupled to internal storage layouts, vector databases (LanceDB), and column names.
2. **Split-Brain Risk:** If the CLI linter and the AI IDE assistant use different logic to parse or query data, inconsistencies will arise.
3. **Lack of Safety:** Generating and running arbitrary system scripts raises security and sandbox hazards.

## Decision
We will enforce a strict **3-Tier Architecture** for Chronicle:

1. **Tier 1: Core Engine (`chronicle/src/*`)** -> Handles database connections, indexing algorithms, and filesystem observers.
2. **Tier 2: Facade SDK (`chronicle/api.py` or high-level facades)** -> A stable, well-typed Python API that encapsulates complex queries.
3. **Tier 3A: CLI Interface (`main.py`)** -> Translates command-line arguments to SDK calls.
4. **Tier 3B: MCP Server (`mcp_server.py`)** -> Translates JSON-RPC tool calls from the AI to the exact same SDK calls.

The AI agent will interact with the codebase exclusively through high-level SDK tools (e.g. `list_series()`, `get_series_ledger()`, `lint_files()`) mirrored on the MCP server, hiding database and file details.

## Consequences
- **Positive:** Decouples the AI client from internal storage refactoring.
- **Positive:** Ensures complete logic alignment between the CI/CD pipeline (running CLI) and the interactive assistant (running MCP).
- **Positive:** Minimal security footprint; AI actions are constrained to a predefined, safe API.
