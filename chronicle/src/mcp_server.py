import asyncio
from typing import List, Optional, Dict, Any
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .indexer import LibrarianIndexer
from .guardian import GuardianAgent
from .session_memory import SessionLedger

# Initialize the MCP Server
server = Server("chronicle")

# Dependency containers
indexer: Optional[LibrarianIndexer] = None
guardian: Optional[GuardianAgent] = None
ledger: Optional[SessionLedger] = None

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
                    "published_only": {"type": "boolean", "description": "Optional: Filter for only published posts (ignore drafts)", "default": False},
                },
                "required": ["query"],
            },
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
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> List[types.Content]:
    """Executes a Chronicle tool call."""
    if name == "search_blog":
        query = arguments.get("query")
        limit = int(arguments.get("limit", 3))
        series = arguments.get("series")
        published_only = arguments.get("published_only", False)
        
        results = await indexer.search(query, limit=limit, series=series, published_only=published_only)
        
        output = []
        for r in results:
            text = f"Title: {r.chunk.title}\nSource: {r.chunk.source}\nSnippet: {r.chunk.text}\n"
            output.append(types.TextContent(type="text", text=text))
        return output

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

    raise ValueError(f"Unknown tool: {name}")

async def main(content_root: str, db_path: str):
    global indexer, guardian, ledger
    
    # Standard config load
    from .utils.config import AppConfig
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
