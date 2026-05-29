import pytest
import os
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.utils.config import AppConfig
from chronicle.src.providers.ollama import OllamaProvider

@pytest.mark.smoke
def test_real_ollama_connectivity():
    """Verifies that we can actually talk to the local Ollama service."""
    provider = OllamaProvider()
    assert provider.check_health() is True

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_real_embedding_generation():
    """Verifies that the local embedding model is loaded and working."""
    provider = OllamaProvider()
    embedding = await provider.embed_async("test text", "nomic-embed-text")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert isinstance(embedding[0], float)

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_real_lancedb_and_hybrid_search(tmp_path):
    """Verifies end-to-end indexing and retrieval with the real DB engine."""
    # 1. Setup a clean, real environment
    blog_root = tmp_path / "blog"
    blog_root.mkdir()
    (blog_root / "test.md").write_text("---\ntitle: Real Test\n---\nSuccession Ritual is a specific term.")
    
    db_path = tmp_path / "db"
    config = AppConfig(
        content_root=str(blog_root),
        db_path=str(db_path),
        search_mode="hybrid"
    )
    
    # 2. Run real indexing
    indexer = LibrarianIndexer(config=config)
    await indexer.index_directory(str(blog_root))
    
    # 3. Perform real hybrid search
    results = await indexer.search("Succession Ritual")
    
    # 4. Assert
    assert len(results) > 0
    assert "Real Test" in results[0].chunk.title
    assert results[0].mode == "hybrid"
