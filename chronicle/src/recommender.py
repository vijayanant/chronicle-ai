from pathlib import Path
from typing import List, Dict, Any, Optional
import frontmatter

from .utils.config import AppConfig
from .utils.logging import get_logger
from .indexer import LibrarianIndexer
from .graph import BlogGraph

logger = get_logger()

class LinkRecommender:
    def __init__(self, config: AppConfig, indexer: LibrarianIndexer):
        self.config = config
        self.indexer = indexer
        self.graph_analyzer = BlogGraph(config)

    async def recommend_links(self, file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Analyzes a draft file and recommends existing indexed articles to link to.
        Filters out the draft file itself and any posts already linked in the draft.
        """
        p = Path(file_path).resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Draft file not found: {file_path}")

        # 1. Parse draft content and frontmatter
        try:
            content = p.read_text(encoding="utf-8")
            post = frontmatter.loads(content)
        except Exception as e:
            logger.error(f"Error reading/parsing draft {file_path}: {e}")
            raise

        # 2. Extract existing links from the draft content to filter them out later
        raw_hrefs = self.graph_analyzer._extract_hrefs(post.content)
        existing_links = set()
        for href in raw_hrefs:
            resolved = self.graph_analyzer._normalize_target(href, p)
            if resolved:
                existing_links.add(resolved)

        # Get relative path of the draft itself relative to content_root
        content_root = Path(self.config.content_root).resolve()
        try:
            draft_rel = str(p.relative_to(content_root)).replace("\\", "/")
        except ValueError:
            draft_rel = p.name  # Fallback if outside content root

        # 3. Construct a query string from metadata and start of content
        title = post.get("title", "")
        description = post.get("description", "")
        tags = post.get("tags", [])
        if isinstance(tags, list):
            tags_str = " ".join(tags)
        else:
            tags_str = str(tags)

        # Get first 200 words of the content
        words = post.content.split()
        snippet = " ".join(words[:200])

        query = f"Title: {title}. Description: {description}. Tags: {tags_str}. Content: {snippet}"
        
        # 4. Search the index. We search with limit * 4 to ensure enough candidates after filtering.
        raw_results = await self.indexer.search(
            query,
            limit=limit * 4,
            mode="hybrid",
            published_only=False
        )

        # 5. Group and filter search results by source file
        recommendations = []
        seen_files = set()

        for res in raw_results:
            source_file = res.chunk.source.replace("\\", "/")
            
            # Skip if it is the draft itself, already linked, or already seen
            if source_file == draft_rel:
                continue
            if source_file in existing_links:
                continue
            if source_file in seen_files:
                continue

            seen_files.add(source_file)
            
            recommendations.append({
                "file": source_file,
                "title": res.chunk.title,
                "similarity_score": round(float(res.score), 4),
                "snippet": res.chunk.text
            })

            if len(recommendations) >= limit:
                break

        return recommendations
