# ADR-004: Shared Argument Scoping via --include-drafts

## Status
Accepted & Implemented

## Context
As Chronicle grew, subcommands handled published vs. draft content filters in diverging ways. For example:
1. `search` default-searched all posts (drafts and published) and used a `--published-only` flag to restrict scope.
2. `lint` had no draft filtering, validating all files recursively in a directory. This caused errors for draft files that were missing required metadata or links (which is expected for work-in-progress content).

This lack of consistency meant that:
- Search results were polluted with unfinished thoughts from stale drafts.
- Linting the entire content directory failed due to incomplete drafts, even though the user only cared about validating the published corpus before deploying.
- Relative link checks failed on drafts since static site generators (like Hugo) exclude drafts from the build directory.

## Decision
We refactored the scoping rules to prioritize **published posts by default**, using an opt-in **`--include-drafts`** flag to include drafts:

1. **Shared Subparser:** Created a shared `common_parser` that subparsers (like `search` and `lint`) inherit.
2. **Default Scoping:** All corpus-wide operations (like searching the index or linting a directory) default to published posts only.
3. **Opt-in Scoping:** The user must pass `--include-drafts` to include draft posts.
4. **Explicit Targets:** If a single file path is explicitly targeted (e.g., `chronicle lint content/posts/my-new-draft.md`), it is always linted regardless of its draft status, since the author has directly targeted it for feedback.

## Consequences
- **Positive:** Consistent argument syntax and behavior across all subcommands.
- **Positive:** Drastically reduces noise during global operations (search, linting).
- **Positive:** Aligns default behavior with static site compilers (e.g. Hugo), which exclude drafts from production builds.
- **Positive:** Avoids build-target link failures on drafts.
