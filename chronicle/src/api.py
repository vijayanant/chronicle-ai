from pathlib import Path
from typing import List, Dict, Any, Optional
import os

from .utils.config import AppConfig
from .indexer import LibrarianIndexer
from .series_manager import SeriesManager
from .linter import ProseLinter, LintIssue
from .session_memory import SessionLedger
from .providers.base import LLMProvider
from .models import SearchResult, SeriesLedger
from .graph import BlogGraph
from .recommender import LinkRecommender

def get_unique_series(config: AppConfig) -> List[str]:
    """Retrieves all unique series tags currently indexed in the database."""
    indexer = LibrarianIndexer(config)
    if not indexer.store._table_exists():
        return []
    df = indexer.store.get_table().to_pandas()
    if "series" in df.columns:
        return sorted(list(df["series"].explode().dropna().unique()))
    return []

async def get_series_ledger_api(config: AppConfig, series_name: str) -> SeriesLedger:
    """Synthesizes the series ledger (narrative arc and promises) using the reasoning model."""
    provider = LLMProvider.get_provider(config.provider)
    indexer = LibrarianIndexer(config, provider=provider)
    manager = SeriesManager(indexer, provider=provider, model_name=config.reasoning_model)
    return await manager.get_series_ledger(series_name)

async def search_blog_api(
    config: AppConfig,
    query: str,
    limit: Optional[int] = None,
    mode: Optional[str] = None,
    series: Optional[str] = None,
    include_drafts: bool = False,
    per_post_limit: Optional[int] = None
) -> List[SearchResult]:
    """Performs a semantic/keyword search across the corpus."""
    provider = LLMProvider.get_provider(config.provider)
    indexer = LibrarianIndexer(config, provider=provider)
    return await indexer.search(
        query,
        limit=limit,
        mode=mode,
        series=series,
        published_only=not include_drafts,
        per_post_limit=per_post_limit
    )

def lint_files_api(config: AppConfig, target_path: str, include_drafts: bool = False) -> Dict[str, List[LintIssue]]:
    """
    Lints a targeted file or directory.
    Returns a dictionary mapping absolute file paths to their respective list of LintIssues.
    """
    linter = ProseLinter(config)
    path_to_lint = Path(target_path).resolve()
    if not path_to_lint.exists():
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    is_single_file = path_to_lint.is_file()
    if is_single_file:
        files = [path_to_lint]
    else:
        files = sorted([p for p in path_to_lint.glob("**/*.md") if p.name != "_index.md"])

    results = {}
    for p in files:
        include_drafts_for_file = True if is_single_file else include_drafts
        issues = linter.lint_file(str(p), include_drafts=include_drafts_for_file)
        if issues:
            results[str(p)] = issues
    return results

def get_decisions_api(config: AppConfig, series: Optional[str] = None) -> str:
    """Retrieves design decisions logged in the session ledger."""
    ledger = SessionLedger(ledger_path=config.ledger_path)
    return ledger.get_decisions(series=series)

def record_decision_api(
    config: AppConfig,
    topic: str,
    decision: str,
    rationale: str,
    scope: str = "post",
    series: Optional[str] = None
) -> None:
    """Records a new design decision to the session ledger."""
    ledger = SessionLedger(ledger_path=config.ledger_path)
    ledger.record_decision(topic, decision, rationale, scope=scope, series=series)

def get_link_graph_api(config: AppConfig, include_drafts: bool = False) -> Dict[str, Any]:
    """Builds the blog link graph and returns the graph nodes, edges, metrics, and skipped targets."""
    analyzer = BlogGraph(config)
    g, skipped = analyzer.build_graph(include_drafts=include_drafts)
    metrics = analyzer.get_metrics()
    
    nodes = [{"id": node, "title": g.nodes[node].get("title", node)} for node in g.nodes]
    edges = [{"source": u, "target": v} for u, v in g.edges]
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": metrics,
        "skipped_targets": skipped
    }

async def suggest_internal_links_api(
    config: AppConfig,
    file_path: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Suggests internal links for a targeted draft file based on semantic search."""
    recommender = LinkRecommender(config, LibrarianIndexer(config))
    return await recommender.recommend_links(file_path, limit=limit)
