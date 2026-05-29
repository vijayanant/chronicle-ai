# ADR-001: Pivot to Narrative CI/CD for Engineering Teams

## Status
Accepted

## Context
Chronicle AI began as a "Blogging Assistant" designed to help an individual author maintain technical consistency across a personal archive of Markdown posts. Through a successful architectural spike, it was validated as a high-precision "Logic Compiler" for prose, utilizing Hybrid Search (Vector + FTS) and a Council of Guardians (Specialized LLM Audits).

However, the "Assistant" framing is limited. It implies passive generation rather than active verification. Furthermore, engineering teams face a larger, more critical problem: **Architectural Intent Decay**. Design decisions made in ADRs, Technical Specs, and READMEs are often forgotten or violated as the team grows, leading to documentation rot and architectural drift.

## Decision
We will reposition Chronicle AI from a "Blogging Assistant" to a **"Narrative CI/CD for Engineering Intent."**

The tool will be refactored to support general engineering repositories, moving beyond the blog-specific "Hugo" constraints. The core identity will shift from "Helping you write" to **"Enforcing your invariants."**

### Key Refinements:
1.  **Generalization:** Rename `blog_root` to `content_root` to support any documentation folder.
2.  **Constraint Enforcement:** Position the `--audit` feature as a hard gate (e.g., pre-commit hooks) rather than an optional chat.
3.  **The Symbolic Bridge:** Establish a roadmap to connect Prose (What we said) to Code (What we did) via symbolic indexing.

## Consequences
- **Positive:** Opens a much larger "market" of users (engineering teams, CTOs, Architects).
- **Positive:** Encourages more rigorous internal dogfooding (using Chronicle to audit Chronicle).
- **Neutral:** Requires removing some Hugo-specific optimizations (like strict frontmatter requirements) in favor of more flexible Markdown parsing.
- **Negative:** Increases the "Complexity Tax" for initialization, as users must now define their own "Technical Constitution" earlier in the process.
