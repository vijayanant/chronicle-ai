# Chronicle AI Strategic Roadmap: From Prototype to Sovereign Engine

This document outlines the evolutionary path for Chronicle AI, transforming it from a local-first RAG prototype into a production-grade narrative compiler for technical content.

---

## 1. Core Philosophy: The Sovereign Intelligence Layer
The goal is to maintain intent persistence. While compute can be hybrid, the identity (Index) and history (Ledger) must remain under the author's physical control.

- **Data Sovereignty:** LanceDB and Ledger always reside on the user's local disk.
- **Compute Agnostic:** Decouple the "Guardians" from specific local hardware.
- **Adversarial by Design:** Prioritize technical accuracy and narrative continuity over fluency and sycophancy.

---

## 2. Tier 1: Production Infrastructure (The Solid Layer)

### 2.1 Hybrid Sovereign Architecture
Move from hardcoded Ollama dependencies to a provider-agnostic interface (using LiteLLM or similar).
- Allow users to toggle between local (Ollama) for privacy and cloud (Claude/GPT) for speed or low-power machines.
- Ensure the Librarian (Data) never leaves the machine, regardless of where the reasoning (Compute) happens.

### 2.2 Modern Packaging
Remove the DevOps requirement for installation.
- **Tauri-based Desktop App:** A lightweight Rust-based wrapper for managing the local environment.
- **One-Click Bootstrap:** Automated Ollama detection and indexing initialization.

---

## 3. Tier 2: The Narrative Linter (The User Experience)

### 3.1 IDE Integration (VS Code / Obsidian)
Bloggers primarily use an editor rather than a CLI.
- **MCP Server Expansion:** Fully implement the Model Context Protocol to provide real-time Guardian feedback in VS Code.
- **"Squiggly" Auditing:** Flag AI-speak, logical gaps, or tone drift directly in Markdown files as the user types.

### 3.2 The Visual Ledger
Transform ledger.json from a text file into a decision timeline.
- A GUI to see every major architectural and editorial choice made over the blog's history.
- Ability to revert or deprioritize past decisions to manage topical evolution.

---

## 4. Tier 3: Advanced Intelligence (The Expert Council)

### 4.1 Series Handoff Hooks
Implement chronicle --handoff "{series_name}".
- Automatically retrieves the synthesis of the last post and the stated next steps.
- Ensures the next post starts with narrative alignment.

### 4.2 The "Voice Vector" Meter
Quantify the author's tone using vector analysis of sentence length, vocabulary, and reading level.
- Flag drafts that are out of character or too generic.

### 4.3 Auto-Anchor Mapping
A tool that scans a draft and suggests internal links based on conceptual matches in the Librarian.
