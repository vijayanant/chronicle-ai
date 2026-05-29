# ADR-003: Structured CLI Subcommands

## Status
Proposed (Pending implementation of Step 1)

## Context
Chronicle AI started as a small, flat command-line script. As features were added (health checks, index syncing, database querying, ledger writing, pre-commit auditing, and systems historian lookups), the command-line flags multiplied at the top level.

This flat structure leads to:
1. Cluttered `--help` outputs.
2. Fragile parsing rules where options are mutually exclusive (e.g. `--record` requires three arguments, but other actions like `--status` require none).
3. Poor discoverability of the tools mapped to the author's writing lifecycle.

## Decision
We will refactor the command line interface to use a **structured subcommand verb tree** (e.g., `chronicle init`, `chronicle status`, `chronicle search`, `chronicle ledger [show|record]`, `chronicle audit`).

The parser will utilize `argparse` subparsers. This ensures:
- Commands are explicitly mapped to verbs.
- Each subcommand has its own specific options and flags.
- We improve output formatting and help messages for each individual tool.

## Consequences
- **Positive:** Standardizes Chronicle's CLI to match mature engineering toolkits (like `git`, `docker`, `poetry`).
- **Positive:** Simplifies CLI argument verification and error reporting.
- **Negative:** Introduces breaking changes for any existing automated script wrappers relying on the old flat flag syntax.
