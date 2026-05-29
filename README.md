# Chronicle AI
### The Narrative Linter for Technical Content

Chronicle AI is a local-first intelligence layer designed to maintain **Intent Persistence** across your technical writing. Unlike generic AI assistants that generate text, Chronicle AI works like a **compiler for your engineering philosophy**—ensuring every draft you write is grounded in your 5-year history and audited for architectural integrity.

It transforms your personal archive from a static repo into an active **CI/CD pipeline for your prose**, acting as an adversarial auditor that guards against topical drift and "AI-speak" fluff. The author retains full control, invoking manual CLI commands to verify logic before publishing.

---

## 1. Setup & Installation

### Step A: Global Installation
To use the `chronicle` command across all your blog projects, clone the repository and install the engine:

```bash
# Clone the repository
git clone https://github.com/vijayanant/chronicle-ai.git
cd chronicle-ai

# Install the engine globally
uv tool install .
```

> **Tip:** If you plan to contribute or customize the Guardian playbooks, use an editable install: `uv tool install --editable .`

### Step B: Local Workspace Initialization
Navigate to your Hugo blog root and bootstrap the local intelligence layer:

```bash
# 1. Initialize the .chronicle directory
chronicle --init

# 2. Configure your blog path
# Open .chronicle/config.yaml and set your 'content_root' path.

# 3. Build the initial local index
chronicle --index

# 4. Verify everything is ready
chronicle --status
```

---

## 2. Verification & Testing

To verify that your environment is correctly configured for the "Sovereign Intelligence" engine, run the included test suite:

```bash
# Run the core logic tests
pytest tests/

# Run the 'smoke' tests (requires local Ollama)
pytest -m smoke tests/
```

Chronicle uses a **Research -> Strategy -> Execution** loop. Before pushing changes, ensure all tests pass to maintain the system's logical integrity.

---

## 2. The Auditing Pipeline

Chronicle AI is designed for manual, proactive invocation by the author to verify content integrity.

1.  **Contextual Verification:** Run searches against your local history to ensure new definitions align with past precedents.
2.  **Thematic Anchoring:** The system checks the Session Ledger to flag deviations from established design decisions.
3.  **Adversarial Audits:** Pass a draft through the local engine to detect logic gaps, contradictions, or violations of your Technical Constitution.

---

## 3. Core CLI Commands (Manual Verification)

| Command | Purpose |
| :--- | :--- |
| `chronicle --audit file.md` | Deep local audit of a technical draft against your Constitution. |
| `chronicle --query "term"` | Search history with conceptual and keyword matching to verify past definitions. |
| `chronicle --series "Name"` | Filter search results to a specific series. |
| `chronicle --series "Name" --series-ledger` | Generate a narrative summary and track promises for a series. |
| `chronicle --history "concept"`| Retrieve your historical, first-principles definition of a concept. |
| `chronicle --record topic choice why` | Manually log a new design decision to the ledger. |
| `chronicle --status` | Check the health of local components. |

---

## 4. Expert Modules (The Council)
Chronicle AI evaluates your writing through specialized logical lenses during an audit:

*   **Systems Historian:** Enforces that concepts are anchored in first principles.
*   **Sovereign Explorer:** Defends architectural and decentralized values.
*   **Master Craftsman:** Verifies technical discipline (TDD, Types) in code examples.
*   **Strategist:** Ensures pragmatic shipping trade-offs are acknowledged.
*   **Cartographer:** Checks narrative and series continuity.
*   **Hugo Master:** Audits build performance and metadata SEO.
*   **Adversarial Peer:** Identifies logic gaps, contradictions, and removes fluff.

---
