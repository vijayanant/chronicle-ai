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
from chronicle.src import api

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
    import shutil
    base_dir = Path(os.getcwd()) / ".chronicle"
    data_dir = base_dir / "data"
    sop_dir = data_dir / "guardians"
    
    print(f"Initializing Chronicle workspace at {base_dir}...")
    sop_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy packaged default playbooks to workspace
    pkg_sop_dir = Path(__file__).parent / "data" / "guardians"
    if pkg_sop_dir.exists():
        for file in pkg_sop_dir.glob("*.md"):
            shutil.copy(file, sop_dir)
    
    config_path = base_dir / "config.yaml"
    default_config = {
        "content_root": "", 
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
    print(f"👉 ACTION REQUIRED: Open {config_path} and set your 'content_root' path.")
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
    # Phase 1: Load Configuration
    config_data = load_config()
    config = AppConfig(**config_data) if config_data else AppConfig()
    
    parser = argparse.ArgumentParser(description="Chronicle AI: The Narrative Linter & Prose CI/CD for Technical Content")
    parser.add_argument("--content-root", default=config.content_root, help="Root directory of content files")
    parser.add_argument("--db-path", default=config.db_path, help="Path to LanceDB")
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")
    
    # Common parent parser for options shared across multiple subcommands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--include-drafts", action="store_true", help="Include draft posts in the command scope")
    
    # status subcommand
    subparsers.add_parser("status", help="Check the health of Chronicle components")
    
    # index subcommand
    index_parser = subparsers.add_parser("index", help="Index content directory")
    index_parser.add_argument("--rebuild", action="store_true", help="Perform a full rebuild instead of a sync")
    
    # search subcommand
    search_parser = subparsers.add_parser("search", parents=[common_parser], help="Search the index for a concept or phrase")
    search_parser.add_argument("query", help="Query string")
    search_parser.add_argument("--limit", type=int, default=config.search_limit, help="Number of search results to return")
    search_parser.add_argument("--per-post-limit", type=int, default=config.per_post_limit, help="Max chunks from the same post to return")
    search_parser.add_argument("--mode", default=config.search_mode, choices=["hybrid", "vector", "fts"], help="Search mode")
    search_parser.add_argument("--series", help="Name of the series for scoping or filtering")

    # ledger subcommand group
    ledger_parser = subparsers.add_parser("ledger", help="Manage design decisions and narrative promises")
    ledger_subparsers = ledger_parser.add_subparsers(dest="ledger_command", required=True)
    
    show_parser = ledger_subparsers.add_parser("show", help="Show decisions and promises")
    show_parser.add_argument("--series", help="Filter by series name")
    show_parser.add_argument("--promises-only", action="store_true", help="Synthesize series narrative promises instead of listing decisions")
    
    record_parser = ledger_subparsers.add_parser("record", help="Record a design decision")
    record_parser.add_argument("topic", help="The topic of the decision")
    record_parser.add_argument("decision", help="The decision chosen")
    record_parser.add_argument("rationale", help="The rationale for the choice")
    record_parser.add_argument("--scope", default="post", choices=["global", "series", "post"], help="Scope of the decision")
    record_parser.add_argument("--series", help="Filter by series name")

    # lint subcommand
    lint_parser = subparsers.add_parser("lint", parents=[common_parser], help="Perform deterministic syntax and link checks on a draft or directory")
    lint_parser.add_argument("file_path", nargs="?", default=None, help="Path to draft file or directory to lint")

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit a draft file")
    audit_parser.add_argument("file_path", help="Path to draft file to audit")
    audit_parser.add_argument("--dossier", action="store_true", help="Generate bundled context dossier instead of running local audit")
    
    # constitution subcommand
    subparsers.add_parser("constitution", help="Generate or update the Technical Constitution")
    
    # history subcommand
    history_parser = subparsers.add_parser("history", help="Get historical briefing")
    history_parser.add_argument("concept", help="Concept to research")
    
    # watch subcommand
    subparsers.add_parser("watch", help="Watch content root for changes")
    
    # graph subcommand
    subparsers.add_parser("graph", parents=[common_parser], help="Analyze internal links and print topological graph metrics")
    
    # suggest-links subcommand
    suggest_links_parser = subparsers.add_parser("suggest-links", help="Suggest internal links for a targeted draft file based on semantic search")
    suggest_links_parser.add_argument("file_path", help="Path to the draft file to analyze")
    suggest_links_parser.add_argument("--limit", type=int, default=5, help="Maximum number of link suggestions to return")
    
    # handoff subcommand
    handoff_parser = subparsers.add_parser("handoff", help="Analyze series progression gaps and suggest logical follow-up topics")
    handoff_parser.add_argument("series_name", help="The name of the series to analyze")
    
    # mcp subcommand
    subparsers.add_parser("mcp", help="Start the MCP server")

    # Parse arguments
    args = parser.parse_args()
    config.content_root = args.content_root
    config.db_path = args.db_path
    setup_logging(log_file=config.log_path)
    
    provider = LLMProvider.get_provider(config.provider)
    indexer = LibrarianIndexer(config=config, provider=provider)
    
    if args.command == "status":
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
    
    if args.command == "index":
        if args.rebuild:
            print(f"Indexing directory (rebuild): {config.content_root}...")
            await indexer.index_directory(config.content_root)
            print("Indexing complete.")
        else:
            print(f"Syncing directory (differential): {config.content_root}...")
            await indexer.sync_directory(config.content_root)
            print("Sync complete.")
            
    elif args.command == "search":
        published_only = not args.include_drafts
        print(f"Searching for: '{args.query}' (mode: {args.mode}, series: {args.series or 'Any'}, published: {published_only}, per-post-limit: {args.per_post_limit})...")
        results = await api.search_blog_api(
            config,
            args.query,
            limit=args.limit,
            mode=args.mode,
            series=args.series,
            include_drafts=args.include_drafts,
            per_post_limit=args.per_post_limit
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
                
    elif args.command == "ledger":
        if args.ledger_command == "show":
            if args.promises_only:
                if not args.series:
                    print("Error: --promises-only requires a specific --series name.")
                    return
                print(f"Synthesizing Series Ledger for '{args.series}'...")
                series_ledger = await api.get_series_ledger_api(config, args.series)
                print(f"\n--- Series Ledger: {series_ledger.series_name} ---")
                print(f"Posts Count: {series_ledger.posts_count}")
                print(f"Arc Summary:\n{series_ledger.summary}")
                if series_ledger.open_promises:
                    print("\n--- Open Narrative Promises ---")
                    for p in series_ledger.open_promises:
                        print(f"- From '{p.source_post}': {p.promise_text} (Topic: {p.topic})")
                else:
                    print("\n✅ No open narrative promises detected.")
            else:
                print(f"\n--- Recent Design Decisions (Series: {args.series or 'All'}) ---")
                print(api.get_decisions_api(config, series=args.series))
                
        elif args.ledger_command == "record":
            api.record_decision_api(config, args.topic, args.decision, args.rationale, scope=args.scope, series=args.series)
            print(f"Decision recorded ({args.scope}): {args.topic}")
            
    elif args.command == "audit":
        if args.dossier:
            if not os.path.exists(args.file_path):
                print(f"Error: File {args.file_path} does not exist.")
                sys.exit(1)
            with open(args.file_path, "r") as f:
                draft_text = f.read()
            dossier = await guardian.council.get_audit_dossier(draft_text, ledger)
            import json
            print(json.dumps(dossier, indent=2))
        else:
            await run_audit(guardian, args.file_path)
            
    elif args.command == "lint":
        path_to_lint = args.file_path or config.content_root
        if not path_to_lint:
            print("Error: No file or directory specified to lint, and 'content_root' is not configured.")
            sys.exit(1)
            
        try:
            lint_results = api.lint_files_api(config, path_to_lint, include_drafts=args.include_drafts)
            
            if not lint_results:
                print(f"✅ Prose Lint PASS: All checked files are compliant.")
            else:
                total_errors = sum(sum(1 for i in issues if i.severity == "ERROR") for issues in lint_results.values())
                total_warnings = sum(sum(1 for i in issues if i.severity == "WARNING") for issues in lint_results.values())
                print(f"\n🚨 Prose Lint FAILED: Found {total_errors} error(s) and {total_warnings} warning(s) across {len(lint_results)} file(s):")
                for filepath, issues in lint_results.items():
                    rel_path = os.path.relpath(filepath, os.getcwd())
                    print(f"\n{rel_path}:")
                    for i in issues:
                        line_str = f"Line {i.line}: " if i.line else ""
                        print(f"  [{i.severity}] {i.category.upper()} | {line_str}{i.message}")
                if total_errors > 0:
                    sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif args.command == "constitution":
        await guardian.generate_initial_constitution()
        
    elif args.command == "history":
        print(f"Systems Historian: Briefing on '{args.concept}'...")
        brief = await guardian.council.historian.find_historical_context_async(args.concept)
        print("\n--- Foundational Briefing ---")
        print(brief)
        
    elif args.command == "graph":
        print(f"Building link graph for: {config.content_root}...")
        graph_data = api.get_link_graph_api(config, include_drafts=args.include_drafts)
        metrics = graph_data["metrics"]
        
        print("\n=== CHRONICLE LINK GRAPH STATUS ===")
        print(f"Total Posts:          {metrics['total_posts']}")
        print(f"Total Internal Links: {metrics['total_links']}")
        print(f"Link Density:         {metrics['density']} links/post")
        
        if metrics["orphans"]:
            print(f"\n🚨 ORPHAN POSTS ({len(metrics['orphans'])} post(s) with 0 incoming links):")
            for o in metrics["orphans"]:
                print(f"  - {o}")
        else:
            print("\n✅ No orphan posts detected. All pages have incoming links.")
            
        if graph_data["skipped_targets"]:
            print(f"\n⚠️ BROKEN INTERNAL LINKS ({len(graph_data['skipped_targets'])}):")
            for skipped in sorted(list(set(graph_data["skipped_targets"]))):
                print(f"  - {skipped}")
                
    elif args.command == "suggest-links":
        print(f"Analyzing draft '{args.file_path}' for link recommendations...")
        try:
            recommendations = await api.suggest_internal_links_api(config, args.file_path, limit=args.limit)
            if not recommendations:
                print("\n✅ No link recommendations found or file is already well-linked.")
            else:
                print(f"\n💡 Found {len(recommendations)} recommended internal link(s) to add:")
                for r in recommendations:
                    print(f"\n🔗 {r['title']} ({r['file']})")
                    print(f"   Similarity: {r['similarity_score']}")
                    print(f"   Context: \"...{r['snippet'].strip()}...\"")
        except Exception as e:
            print(f"Error suggesting links: {e}")
            
    elif args.command == "handoff":
        print(f"Analyzing progression of series '{args.series_name}' for logical gaps and follow-ups...")
        try:
            brief = await api.get_series_handoff_api(config, args.series_name)
            print(f"\n=== CHRONICLE SERIES HANDOFF: {brief.series_name} ===")
            print(f"Last Post: {brief.last_post_title}")
            
            if brief.logical_gaps:
                print("\n🚨 IDENTIFIED LOGICAL GAPS & UNADDRESSED TRADE-OFFS:")
                for gap in brief.logical_gaps:
                    print(f"  - {gap}")
            else:
                print("\n✅ No logical gaps identified in the progression.")
                
            if brief.follow_ups:
                print("\n💡 SUGGESTED DEEP FOLLOW-UP ARTICLES:")
                for i, f in enumerate(brief.follow_ups, 1):
                    print(f"\n{i}. Topic: {f.title}")
                    print(f"   Why:   {f.rationale}")
                    print(f"   Hook:  \"{f.transition_hook}\"")
            else:
                print("\n❌ No follow-up recommendations could be generated.")
        except Exception as e:
            print(f"Error generating handoff brief: {e}")
            
    elif args.command == "watch":
        from chronicle.src.observer import start_watching
        await start_watching(config.content_root, indexer, guardian)
        
    elif args.command == "mcp":
        from chronicle.src.mcp_server import main as run_mcp
        await run_mcp(content_root=config.content_root, db_path=config.db_path)

def main():
    asyncio.run(run_main())

if __name__ == "__main__":
    main()
