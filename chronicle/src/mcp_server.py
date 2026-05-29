import asyncio
from typing import List, Optional, Dict, Any
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .indexer import LibrarianIndexer
from .guardian import GuardianAgent
from .session_memory import SessionLedger
from .utils.config import AppConfig
from . import api

# Initialize the MCP Server
server = Server("chronicle")

# Dependency containers
indexer: Optional[LibrarianIndexer] = None
guardian: Optional[GuardianAgent] = None
ledger: Optional[SessionLedger] = None
config: Optional[AppConfig] = None

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """Exposes the Technical Constitution as a read-only resource."""
    return [
        types.Resource(
            uri="chronicle://data/constitution",
            name="Technical Constitution",
            description="The version-controlled engineering principles for the blog.",
            mimeType="text/markdown",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Reads the content of a Chronicle resource."""
    if uri == "chronicle://data/constitution":
        return guardian.council.constitution_path.read_text()
    raise ValueError(f"Resource not found: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Lists the available Chronicle intelligence tools."""
    return [
        types.Tool(
            name="search_blog",
            description="Semantically search the 5-year blog history. Supports series and draft filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term or phrase"},
                    "limit": {"type": "number", "description": "Number of results to return", "default": 3},
                    "series": {"type": "string", "description": "Optional: Filter results to a specific series name"},
                    "include_drafts": {"type": "boolean", "description": "Optional: Include draft posts in search", "default": False},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_series",
            description="List all unique series tags currently indexed in the blog.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_series_ledger",
            description="Synthesize the ledger (narrative arc and open promises) for a series.",
            inputSchema={
                "type": "object",
                "properties": {
                    "series_name": {"type": "string", "description": "The name of the series to summarize"},
                },
                "required": ["series_name"],
            }
        ),
        types.Tool(
            name="lint_files",
            description="Run metadata schema linting checks on a targeted file or directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_path": {"type": "string", "description": "The file or directory path to check"},
                    "include_drafts": {"type": "boolean", "description": "Whether to include drafts in directory checks", "default": False},
                },
                "required": ["target_path"],
            }
        ),
        types.Tool(
            name="get_decisions",
            description="Retrieve recorded engineering design decisions from the ledger.",
            inputSchema={
                "type": "object",
                "properties": {
                    "series": {"type": "string", "description": "Optional series name to filter decisions"}
                }
            }
        ),
        types.Tool(
            name="audit_draft",
            description="Audit a technical draft against the Constitution and Series Ledger.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The raw markdown text to audit"},
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="get_historical_brief",
            description="Get a foundational briefing for a technical concept anchored in first principles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {"type": "string", "description": "The concept to research"},
                },
                "required": ["concept"],
            },
        ),
        types.Tool(
            name="get_audit_dossier",
            description="Generate a bundled context dossier for high-speed cloud auditing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The draft text to audit"},
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="get_link_graph",
            description="Build the blog's link graph and retrieve topological metrics, orphans, and broken links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_drafts": {"type": "boolean", "description": "Optional: Include draft posts in the graph", "default": False},
                }
            }
        ),
        types.Tool(
            name="suggest_internal_links",
            description="Suggest semantically relevant internal posts to link to from a targeted draft file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The file path of the draft to analyze"},
                    "limit": {"type": "integer", "description": "Optional: Max recommendations to return", "default": 5}
                },
                "required": ["file_path"]
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> List[types.Content]:
    """Executes a Chronicle tool call."""
    if name == "search_blog":
        query = arguments.get("query")
        limit = int(arguments.get("limit", 3))
        series = arguments.get("series")
        include_drafts = arguments.get("include_drafts", False)
        
        results = await api.search_blog_api(
            config, query, limit=limit, series=series, include_drafts=include_drafts
        )
        
        output = []
        for r in results:
            text = f"Title: {r.chunk.title}\nSource: {r.chunk.source}\nSnippet: {r.chunk.text}\n"
            output.append(types.TextContent(type="text", text=text))
        return output

    elif name == "list_series":
        series_list = api.get_unique_series(config)
        import json
        return [types.TextContent(type="text", text=json.dumps(series_list, indent=2))]

    elif name == "get_series_ledger":
        series_name = arguments.get("series_name")
        ledger = await api.get_series_ledger_api(config, series_name)
        
        report = f"SERIES: {ledger.series_name}\n"
        report += f"POSTS COUNT: {ledger.posts_count}\n"
        report += f"SUMMARY:\n{ledger.summary}\n"
        report += "\nOPEN PROMISES:\n"
        for p in ledger.open_promises:
            report += f"- From '{p.source_post}': {p.promise_text} (Topic: {p.topic})\n"
        return [types.TextContent(type="text", text=report)]

    elif name == "lint_files":
        target_path = arguments.get("target_path")
        include_drafts = arguments.get("include_drafts", False)
        
        try:
            lint_results = api.lint_files_api(config, target_path, include_drafts=include_drafts)
            
            # Format report
            if not lint_results:
                report = "✅ Prose Lint PASS: No issues found."
            else:
                report = "🚨 Prose Lint FAILED:\n"
                for filepath, issues in lint_results.items():
                    report += f"\n{filepath}:\n"
                    for i in issues:
                        line_str = f"Line {i.line}: " if i.line else ""
                        report += f"  [{i.severity}] {i.category.upper()} | {line_str}{i.message}\n"
            return [types.TextContent(type="text", text=report)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e}")]

    elif name == "get_decisions":
        series = arguments.get("series")
        decisions = api.get_decisions_api(config, series=series)
        return [types.TextContent(type="text", text=decisions)]

    elif name == "audit_draft":
        text = arguments.get("text")
        result = await guardian.council.pre_commit_audit_async(text)
        
        status = "✅ PASS" if result["status"] == "PASS" else "🚨 FAIL"
        report = f"STATUS: {status}\nREASON: {result['reason']}\nEXPLORER NOTES: {result.get('explorer_notes', '')}"
        return [types.TextContent(type="text", text=report)]

    elif name == "get_historical_brief":
        concept = arguments.get("concept")
        brief = await guardian.council.historian.find_historical_context_async(concept)
        return [types.TextContent(type="text", text=brief)]

    elif name == "get_audit_dossier":
        text = arguments.get("text")
        dossier = await guardian.council.get_audit_dossier(text, ledger)
        import json
        return [types.TextContent(type="text", text=json.dumps(dossier, indent=2))]

    elif name == "get_link_graph":
        include_drafts = arguments.get("include_drafts", False) if arguments else False
        graph_data = api.get_link_graph_api(config, include_drafts=include_drafts)
        import json
        return [types.TextContent(type="text", text=json.dumps(graph_data, indent=2))]

    elif name == "suggest_internal_links":
        file_path = arguments.get("file_path")
        limit = int(arguments.get("limit", 5))
        recommendations = await api.suggest_internal_links_api(config, file_path, limit=limit)
        import json
        return [types.TextContent(type="text", text=json.dumps(recommendations, indent=2))]

    raise ValueError(f"Unknown tool: {name}")

async def main(content_root: str, db_path: str):
    global indexer, guardian, ledger, config
    
    # Standard config load
    config = AppConfig.from_yaml()
    config.content_root = content_root
    config.db_path = db_path
    
    # Initialize core logic
    indexer = LibrarianIndexer(config=config)
    guardian = GuardianAgent(indexer, config=config)
    ledger = SessionLedger(ledger_path=config.ledger_path)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_server):
        await server.run(
            read_stream,
            write_server,
            InitializationOptions(
                server_name="chronicle",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
