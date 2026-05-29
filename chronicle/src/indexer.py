import os
import hashlib
import frontmatter
import lancedb
import pandas as pd
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date as dt_date

from .models import DocumentChunk, SearchResult
from .providers.base import LLMProvider
from .providers.ollama import OllamaProvider
from .utils.paths import PathResolver
from .utils.config import AppConfig
from .utils.logging import get_logger
from .utils.chunker import Chunker

logger = get_logger()

class VectorStore:
    """Handles all LanceDB interactions, FTS, and RRF logic."""
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = lancedb.connect(config.db_path)
        self.table_name = config.table_name

    def _table_exists(self) -> bool:
        try:
            res = self.db.list_tables()
            # Handle both ListTablesResponse (new) and list of strings (old)
            if hasattr(res, 'tables'):
                return self.table_name in res.tables
            return self.table_name in res
        except:
            return False

    def get_table(self):
        return self.db.open_table(self.table_name)

    def create_table(self, data: pd.DataFrame):
        self.db.create_table(self.table_name, data=data)

    def overwrite_table(self, data: pd.DataFrame):
        self.get_table().add(data, mode="overwrite")

    def upsert_chunks(self, df: pd.DataFrame):
        self.get_table().add(df)

    def delete_by_source(self, rel_path: str):
        if self._table_exists():
            self.get_table().delete(f"source = '{rel_path}'")

    def create_fts_index(self):
        if self._table_exists():
            table = self.get_table()
            table.create_fts_index("text", replace=True)

class LibrarianIndexer:
    """Natively Asynchronous Indexer Orchestrator."""
    
    def __init__(self, config: AppConfig, provider: Optional[LLMProvider] = None):
        self.config = config
        self.store = VectorStore(config)
        self.provider = provider or LLMProvider.get_provider(config.provider, config=config)
        self.resolver = PathResolver(config.content_root)

    def check_health(self) -> Dict[str, Any]:
        return {
            self.config.provider: self.provider.check_health(),
            "database": self.store._table_exists(),
            "content_root": os.path.exists(self.config.content_root)
        }

    def _calculate_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    async def _get_embedding(self, text: str, is_query: bool = False) -> List[float]:
        prefix = "search_query: " if is_query else "search_document: "
        return await self.provider.embed_async(f"{prefix}{text}", self.config.embedding_model)

    async def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parses a file and prepares chunks with CLEAN separation of Vector vs Metadata Payloads."""
        with open(file_path, "rb") as f:
            raw_content = f.read()
        
        post = frontmatter.loads(raw_content.decode("utf-8"))
        meta = post.metadata
        
        # 1. Metadata Payload Extraction
        title = meta.get("title", "Untitled")
        slug = meta.get("slug", Path(file_path).stem)
        description = meta.get("description", "")
        series = meta.get("series", [])
        if isinstance(series, str): series = [series]
        series_order = meta.get("series_order")
        tags = meta.get("tags", [])
        draft = meta.get("draft", False)
        
        # Date Normalization
        raw_date = meta.get("date")
        date = None
        if isinstance(raw_date, datetime):
            date = raw_date
        elif isinstance(raw_date, dt_date):
            date = datetime.combine(raw_date, datetime.min.time())
        elif isinstance(raw_date, str):
            try:
                date = datetime.fromisoformat(raw_date)
            except:
                pass
        if date and date.tzinfo:
            date = date.replace(tzinfo=None)
            
        rel_source = self.resolver.to_relative(file_path)
        file_hash = hashlib.sha256(raw_content).hexdigest()
        
        # 2. Vector Payload Generation (Pure Prose/Code)
        chunks = Chunker.chunk(
            post.content, 
            window_size=self.config.chunk_size, 
            overlap=self.config.chunk_overlap
        )
        if not chunks:
            chunks = [{"text": f"Metadata for {title}", "type": "frontmatter"}]
            
        # We NO LONGER prepend metadata to the vector payload to avoid 'Metadata Dilution'.
        # We embed the RAW chunk text only.
        embedding_tasks = [
            self._get_embedding(c["text"], is_query=False)
            for c in chunks
        ]
        vectors = await asyncio.gather(*embedding_tasks)
        
        return [{
            "id": f"{slug}_{i}",
            "vector": v,
            "text": chunks[i]["text"], # Vector Payload
            "source": rel_source,      # Metadata Payload starts here...
            "title": title,
            "slug": slug,
            "description": description,
            "date": date,
            "series": series,
            "series_order": series_order,
            "tags": tags,
            "draft": draft,
            "chunk_type": chunks[i]["type"],
            "content_hash": hashlib.sha256(chunks[i]["text"].encode()).hexdigest(),
            "file_hash": file_hash
        } for i, v in enumerate(vectors)]

    async def index_directory(self, content_dir: str):
        pathlist = [p for p in Path(content_dir).glob('**/*.md') if p.name != "_index.md"]
        logger.info(f"Indexing {len(pathlist)} files...")
        
        semaphore = asyncio.Semaphore(10)
        async def worker(p):
            async with semaphore:
                try:
                    logger.info(f"Indexing: {self.resolver.to_relative(str(p))}")
                    return await self.process_file(str(p))
                except Exception as e:
                    logger.error(f"Error {p}: {e}")
                    return []

        results = await asyncio.gather(*(worker(p) for p in pathlist))
        all_data = [chunk for file_results in results for chunk in file_results]

        if all_data:
            df = pd.DataFrame(all_data)
            if self.store._table_exists():
                self.store.overwrite_table(df)
            else:
                self.store.create_table(df)
            self.store.create_fts_index()

    async def sync_directory(self, content_dir: str):
        if not self.store._table_exists():
            return await self.index_directory(content_dir)

        existing_df = self.store.get_table().to_pandas()
        indexed_files = existing_df.groupby('source')['file_hash'].first().to_dict()
        
        pathlist = [p for p in Path(content_dir).glob('**/*.md') if p.name != "_index.md"]
        stats = {"updated": 0, "new": 0, "deleted": 0, "skipped": 0}
        on_disk = set()

        async def sync_worker(p):
            abs_p = str(p)
            rel_p = self.resolver.to_relative(abs_p)
            on_disk.add(rel_p)
            cur_hash = hashlib.sha256(open(abs_p, "rb").read()).hexdigest()
            
            if rel_p in indexed_files:
                if indexed_files[rel_p] != cur_hash:
                    logger.info(f"Sync (Update): {rel_p}")
                    self.store.delete_by_source(rel_p)
                    stats["updated"] += 1
                    return await self.process_file(abs_p)
                stats["skipped"] += 1
                return []
            else:
                logger.info(f"Sync (New):    {rel_p}")
                stats["new"] += 1
                return await self.process_file(abs_p)

        results = await asyncio.gather(*(sync_worker(p) for p in pathlist))
        new_data = [chunk for res in results for chunk in res]
        
        # Deletions
        for rel_p in indexed_files:
            if rel_p not in on_disk:
                logger.info(f"Sync (Delete): {rel_p}")
                self.store.delete_by_source(rel_p)
                stats["deleted"] += 1

        if new_data:
            self.store.upsert_chunks(pd.DataFrame(new_data))
        
        logger.info(f"Sync Complete: {stats}")
        if new_data or stats["deleted"] > 0:
            self.store.create_fts_index()

    async def index_file(self, file_path: str):
        """Indexes or re-indexes a single file."""
        logger.info(f"Indexing file: {file_path}")
        chunks_data = await self.process_file(file_path)
        if chunks_data:
            df = pd.DataFrame(chunks_data)
            # Remove old chunks for this source first
            rel_path = self.resolver.to_relative(file_path)
            self.store.delete_by_source(rel_path)
            self.store.upsert_chunks(df)
            self.store.create_fts_index()

    async def delete_file(self, file_path: str):
        """Removes a file from the index."""
        rel_path = self.resolver.to_relative(file_path)
        logger.info(f"Deleting source from index: {rel_path}")
        self.store.delete_by_source(rel_path)
        self.store.create_fts_index()

    async def search(self, query: str, limit: Optional[int] = None, mode: Optional[str] = None,
                     series: Optional[str] = None, published_only: bool = False,
                     per_post_limit: Optional[int] = None) -> List[SearchResult]:
        """Async Search with High-Precision Metadata Filtering."""
        if not self.store._table_exists():
            logger.warning("Search failed: Table does not exist.")
            return []
            
        search_limit = limit or self.config.search_limit
        active_per_post_limit = per_post_limit if per_post_limit is not None else self.config.per_post_limit
        search_mode = mode or self.config.search_mode
        table = self.store.get_table()
        
        # Build Filter Query
        filters = []
        if series:
            filters.append(f"array_contains(series, '{series}')")
        if published_only:
            filters.append("draft = false")
        
        filter_query = " AND ".join(filters) if filters else None
        
        if search_mode == "fts":
            q = table.search(query)
            if filter_query: q = q.where(filter_query)
            db_limit = search_limit * 5 if active_per_post_limit else search_limit
            raw = q.limit(db_limit).to_list()
            results = [self._to_result(r, "fts") for r in raw]
            return self._apply_per_post_limit(results, active_per_post_limit)[:search_limit]
        
        vec = await self._get_embedding(query, is_query=True)
        if search_mode == "vector":
            q = table.search(vec)
            if filter_query: q = q.where(filter_query)
            db_limit = search_limit * 5 if active_per_post_limit else search_limit
            raw = q.limit(db_limit).to_list()
            results = [self._to_result(r, "vector") for r in raw]
            return self._apply_per_post_limit(results, active_per_post_limit)[:search_limit]
        
        # Hybrid RRF with Filtering
        try:
            pool_size = 50
            v_q = table.search(vec)
            f_q = table.search(query)
            if filter_query:
                v_q = v_q.where(filter_query)
                f_q = f_q.where(filter_query)
                
            v_res = v_q.limit(pool_size).to_list()
            f_res = f_q.limit(pool_size).to_list()
            
            k, scores, docs = self.config.rrf_k, {}, {}
            for rank, d in enumerate(v_res, 1):
                key = (d['source'], d['content_hash'])
                scores[key] = scores.get(key, 0) + (1 / (k + rank))
                docs[key] = d
            for rank, d in enumerate(f_res, 1):
                key = (d['source'], d['content_hash'])
                scores[key] = scores.get(key, 0) + (1 / (k + rank))
                docs[key] = d
                
            sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            results = [self._to_result(docs[key], "hybrid", scores[key]) for key in sorted_keys]
            return self._apply_per_post_limit(results, active_per_post_limit)[:search_limit]
        except Exception as e:
            logger.error(f"Hybrid Fail: {e}")
            q = table.search(vec)
            if filter_query: q = q.where(filter_query)
            db_limit = search_limit * 5 if active_per_post_limit else search_limit
            raw = q.limit(db_limit).to_list()
            results = [self._to_result(r, "vector") for r in raw]
            return self._apply_per_post_limit(results, active_per_post_limit)[:search_limit]

    def _apply_per_post_limit(self, results: List[SearchResult], per_post_limit: Optional[int]) -> List[SearchResult]:
        if not per_post_limit:
            return results
        filtered = []
        counts = {}
        for r in results:
            source = r.chunk.source
            if counts.get(source, 0) < per_post_limit:
                filtered.append(r)
                counts[source] = counts.get(source, 0) + 1
        return filtered

    def _to_result(self, raw: Dict[str, Any], mode: str, score: Optional[float] = None) -> SearchResult:
        data = {k: v for k, v in raw.items() if not k.startswith('_') and k != 'vector'}
        return SearchResult(
            chunk=DocumentChunk(**data),
            score=score or (raw.get('_distance') or raw.get('_score') or 0.0),
            mode=mode
        )
