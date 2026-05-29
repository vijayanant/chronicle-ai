import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from chronicle.src.recommender import LinkRecommender
from chronicle.src.utils.config import AppConfig
from chronicle.src.models import SearchResult, DocumentChunk

@pytest.mark.asyncio
async def test_recommend_links(tmp_path):
    # 1. Setup mock content directory
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    
    # Draft post (post-a) which already links to post-b
    post_a = content_dir / "post-a.md"
    post_a.write_text(
        "---\n"
        "title: Post A\n"
        "---\n"
        "This is draft A which has a link to [Post B](post-b.md)."
    )
    
    # Existing post (post-b)
    post_b = content_dir / "post-b.md"
    post_b.touch()

    # Existing post (post-c)
    post_c = content_dir / "post-c.md"
    post_c.touch()

    config = AppConfig(content_root=str(content_dir))
    
    # 2. Mock LibrarianIndexer and search result
    indexer = MagicMock()
    
    # We want indexer.search to return chunks representing post-b (already linked)
    # and post-c (not linked yet), and post-a (itself).
    chunk_a = DocumentChunk(
        id="a_0",
        text="This is draft A",
        source="post-a.md",
        title="Post A",
        slug="post-a",
        content_hash="hash1",
        file_hash="filehash1"
    )
    chunk_b = DocumentChunk(
        id="b_0",
        text="Content of B",
        source="post-b.md",
        title="Post B",
        slug="post-b",
        content_hash="hash2",
        file_hash="filehash2"
    )
    chunk_c = DocumentChunk(
        id="c_0",
        text="Content of C",
        source="post-c.md",
        title="Post C",
        slug="post-c",
        content_hash="hash3",
        file_hash="filehash3"
    )

    indexer.search = AsyncMock(return_value=[
        SearchResult(chunk=chunk_a, score=0.9, mode="hybrid"),
        SearchResult(chunk=chunk_b, score=0.8, mode="hybrid"),
        SearchResult(chunk=chunk_c, score=0.7, mode="hybrid")
    ])

    recommender = LinkRecommender(config, indexer)
    
    # 3. Get recommendations for post-a.md
    recommendations = await recommender.recommend_links(str(post_a), limit=5)
    
    # 4. Assertions
    assert len(recommendations) == 1
    assert recommendations[0]["file"] == "post-c.md"
    assert recommendations[0]["title"] == "Post C"
    assert recommendations[0]["similarity_score"] == 0.7
