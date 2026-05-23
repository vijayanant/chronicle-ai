import argparse
import sys
import os
import asyncio
import yaml
from pathlib import Path

from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.guardian import GuardianAgent
from chronicle.src.session_memory import SessionLedger
from chronicle.src.providers.base import LLMProvider
from chronicle.src.utils.logging import setup_logging
from chronicle.src.utils.config import AppConfig

def load_config(config_path: str = None):
    """Loads configuration, searching current directory (.chronicle) then default path."""
    paths_to_check = []
    if config_path:
        paths_to_check.append(config_path)
    
    paths_to_check.append(os.path.join(os.getcwd(), ".chronicle", "config.yaml"))
    paths_to_check.append("chronicle/config.yaml")

    for path in paths_to_check:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config at {path}: {e}")
    return {}

def init_workspace():
    """Bootstraps a new Chronicle workspace in the current directory."""
    base_dir = Path(os.getcwd()) / ".chronicle"
    data_dir = base_dir / "data"
    sop_dir = data_dir / "guardians"
    
    print(f"Initializing Chronicle workspace at {base_dir}...")
    sop_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = base_dir / "config.yaml"
    default_config = {
        "blog_root": "", 
        "db_path": ".chronicle/data/lancedb",
        "ledger_path": ".chronicle/data/session_ledger.json",
        "library_path": ".chronicle/data/library/catalog.json",
        "constitution_path": ".chronicle/data/constitution.md",
        "log_path": ".chronicle/data/chronicle.log",
        "provider": "ollama",
        "embedding_model": "nomic-embed-text",
        "reasoning_model": "deepseek-r1:14b",
        "search_limit": 5,
        "search_mode": "hybrid",
        "rrf_k": 60
    }
    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    instr_path = data_dir / "expert_instructions.md"
    instr_path.write_text("# Expert Instructions\n\nAdd your custom personality and mandates here.")
    
    print("\n✅ Chronicle workspace initialized successfully!")
    print(f"👉 ACTION REQUIRED: Open {config_path} and set your 'blog_root' path.")
    print("👉 Then run: chronicle --index")

async def run_audit(guardian, audit_path):
    if not os.path.exists(audit_path):
        print(f"Error: File {audit_path} does not exist.")
        sys.exit(1)
    with open(audit_path, "r") as f:
        draft_text = f.read()
    print(f"Auditing draft: {audit_path}...")
    
    result = await guardian.council.pre_commit_audit_async(draft_text)
    
    if result["status"] == "FAIL":
        print("\n🚨 GUARDIAN INTERCEPT: LOGIC VIOLATION DETECTED 🚨")
        print(f"Reason: {result['reason']}")
    else:
        print("\n✅ GUARDIAN PASS: Draft is logically consistent.")
        print(f"Explorer Notes: {result.get('explorer_notes', 'N/A')}")

async def run_main():
    if "--init" in sys.argv:
        init_workspace()
        return

    # Phase 1: Load Configuration
    config_data = load_config()
    config = AppConfig(**config_data) if config_data else AppConfig()
    
    parser = argparse.ArgumentParser(description="Chronicle AI: The Narrative Linter & Prose CI/CD for Technical Content")
    parser.add_argument("--blog-root", default=config.blog_root, help="Root directory of blog posts")
    parser.add_argument("--db-path", default=config.db_path, help="Path to LanceDB")
    parser.add_argument("--index", action="store_true", help="Index the blog directory")
    parser.add_argument("--sync", action="store_true", help="Perform a differential sync of the index")
    parser.add_argument("--query", help="Search the index for a concept or phrase")
    parser.add_argument("--limit", type=int, default=config.search_limit, help="Number of search results to return")
    parser.add_argument("--mode", default=config.search_mode, choices=["hybrid", "vector", "fts"], help="Search mode")
    parser.add_argument("--series", help="Name of the series for scoping or filtering")
    parser.add_argument("--published-only", action="store_true", help="Filter for published posts only (ignore drafts)")

    parser.add_argument("--constitution", action="store_true", help="Generate or update the Technical Constitution")

    parser.add_argument("--audit", help="Path to a draft file to audit")
    parser.add_argument("--dossier", help="Generate a bundled context dossier for cloud auditing")
    parser.add_argument("--history", help="Get a foundational historical briefing for a concept")
    parser.add_argument("--watch", action="store_true", help="Watch the blog root for changes")
    parser.add_argument("--record", nargs=3, metavar=('TOPIC', 'DECISION', 'RATIONALE'), help="Record a design decision")
    parser.add_argument("--scope", default="post", choices=["global", "series", "post"], help="Scope of the decision")
    parser.add_argument("--decisions", action="store_true", help="List recent design decisions")
    parser.add_argument("--series-ledger", action="store_true", help="Generate a narrative ledger for the specified series (requires --series)")
    parser.add_argument("--mcp", action="store_true", help="Start the MCP server for interoperability")
    parser.add_argument("--status", action="store_true", help="Check the health of Chronicle components")
    parser.add_argument("--init", action="store_true", help="Initialize a new workspace")
    
    args = parser.parse_args()
    config.blog_root = args.blog_root
    config.db_path = args.db_path
    setup_logging(log_file=config.log_path)
    
    provider = LLMProvider.get_provider(config.provider)
    indexer = LibrarianIndexer(config=config, provider=provider)
    
    if args.status:
        print("\n--- Chronicle Health Report ---")
        health = indexer.check_health()
        print(f"📡 Provider: {config.provider.upper()}")
        for component, state in health.items():
            status_symbol = "✅" if state else "❌"
            print(f"{status_symbol} {component.capitalize()}: {'Ready' if state else 'FAILED'}")
        print(f"✅ Configuration: Loaded")
        print(f"✅ Technical Constitution: {'Present' if os.path.exists(config.constitution_path) else 'Missing'}")
        return

    if not indexer.check_health()["ollama"] and config.provider == "ollama":
        print("Error: Ollama service is not reachable. Please start Ollama and try again.")
        sys.exit(1)
        
    guardian = GuardianAgent(indexer, config=config, provider=provider)
    ledger = SessionLedger(ledger_path=config.ledger_path)
    
    if args.dossier:
        if not os.path.exists(args.dossier):
            print(f"Error: File {args.dossier} does not exist.")
            sys.exit(1)
        with open(args.dossier, "r") as f:
            draft_text = f.read()
        dossier = await guardian.council.get_audit_dossier(draft_text, ledger)
        import json
        print(json.dumps(dossier, indent=2))
        return

    if args.index:
        print(f"Indexing directory: {config.blog_root}...")
        await indexer.index_directory(config.blog_root)
        print("Indexing complete.")
        
    if args.sync:
        print(f"Syncing directory: {config.blog_root}...")
        await indexer.sync_directory(config.blog_root)
        print("Sync complete.")
        
    if args.constitution:
        await guardian.generate_initial_constitution()

    if args.history:
        print(f"Systems Historian: Briefing on '{args.history}'...")
        brief = await guardian.council.historian.find_historical_context_async(args.history)
        print("\n--- Foundational Briefing ---")
        print(brief)

    if args.record:
        ledger.record_decision(args.record[0], args.record[1], args.record[2], scope=args.scope, series=args.series)
        print(f"Decision recorded ({args.scope}): {args.record[0]}")

    if args.decisions:
        print(f"\n--- Recent Design Decisions (Series: {args.series or 'All'}) ---")
        print(ledger.get_decisions(series=args.series))

    if args.series_ledger:
        if not args.series:
            print("Error: --series-ledger requires a specific --series name.")
            return
        from chronicle.src.series_manager import SeriesManager
        manager = SeriesManager(indexer, provider=provider, model_name=config.reasoning_model)
        print(f"Synthesizing Series Ledger for '{args.series}'...")
        series_ledger = await manager.get_series_ledger(args.series)
        print(f"\n--- Series Ledger: {series_ledger.series_name} ---")
        print(f"Posts Count: {series_ledger.posts_count}")
        print(f"Arc Summary:\n{series_ledger.summary}")
        if series_ledger.open_promises:
            print("\n--- Open Narrative Promises ---")
            for p in series_ledger.open_promises:
                print(f"- From '{p.source_post}': {p.promise_text} (Topic: {p.topic})")
        else:
            print("\n✅ No open narrative promises detected.")

    if args.audit:
        await run_audit(guardian, args.audit)

    if args.watch:
        from chronicle.src.observer import start_watching
        await start_watching(config.blog_root, indexer, guardian)

    if args.mcp:
        from chronicle.src.mcp_server import main as run_mcp
        await run_mcp(blog_root=config.blog_root, db_path=config.db_path)

    if args.query:
        print(f"Searching for: '{args.query}' (mode: {args.mode}, series: {args.series or 'Any'}, published: {args.published_only})...")
        results = await indexer.search(
            args.query, 
            limit=args.limit, 
            mode=args.mode, 
            series=args.series, 
            published_only=args.published_only
        )
        
        if not results:
            print("No relevant results found.")
        else:
            print("\n--- Top Matches ---")
            for i, res in enumerate(results):
                print(f"\n[{i+1}] Source: {res.chunk.source}")
                print(f"Title: {res.chunk.title}")
                print(f"Snippet: {res.chunk.text[:200]}...")
                print(f"Score ({res.mode}): {res.score:.4f}")

    if len(sys.argv) == 1:
        parser.print_help()

def main():
    asyncio.run(run_main())

if __name__ == "__main__":
    main()
