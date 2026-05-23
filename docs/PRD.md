# Chronicle AI Product Requirements Document (PRD)

## 1. Vision
Chronicle AI is a local knowledge engine that acts as a CI/CD pipeline for a writer's historical archive. It ensures narrative continuity and technical accuracy by auditing drafts against past precedents and engineering principles.

## 2. System Architecture
Chronicle AI operates primarily as a local-first validation tool.

*   **Librarian (Local):** Embedded LanceDB providing hybrid search (Vector + Keyword).
*   **Expert Modules (Local):** Specialized logic units (Historian, Peer, etc.) running on local reasoning models to audit content.
*   **Context Layer:** Dual-layer memory consisting of a local index and a version-controlled technical constitution.

## 3. Core Requirements

### 3.1. Knowledge Management
*   **Hybrid Retrieval:** Combine semantic and keyword search for technical precision.
*   **Real-time Sync:** Background file monitoring for incremental index updates.
*   **Portability:** Relative path resolution for cross-environment stability.

### 3.2. Logic & Consistency
*   **Tiered Scoping:** Manage decisions at Global, Series, and Post levels.
*   **Audit Gates:** Structured logic validation for technical drafts, enforcing the Technical Constitution.
*   **Technical Constitution:** Human-readable source of truth for engineering principles.
*   **Manual Verification:** The system empowers the author to run targeted queries and deep audits via CLI commands.

### 3.3. Customizability
*   **Expert Playbooks (SOPs):** Specialized auditing logic for each expert module is externalized into human-editable Markdown files.
*   **Instruction Externalization:** The auditing constraints and personality are manageable via a version-controlled instruction file.

### 3.4. Interoperability
*   **MCP Protocol:** Expose tools and resources via Model Context Protocol for integration with local editors or optional AI agents.

## 4. Technical Stack
*   **Core:** Python 3.10+, LanceDB, Pydantic, PyYAML.
*   **Local AI:** Ollama / MLX (DeepSeek-R1, Nomic-Embed).
*   **Orchestration:** Asyncio-based parallel reasoning.
