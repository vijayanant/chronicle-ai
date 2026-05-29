import yaml
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    """Centralized configuration model for Chronicle."""
    content_root: str = Field("")
    db_path: str = Field(".chronicle/data/lancedb")
    table_name: str = Field("blog_chunks")
    ledger_path: str = Field(".chronicle/data/session_ledger.json")
    library_path: str = Field(".chronicle/data/library/catalog.json")
    constitution_path: str = Field(".chronicle/data/constitution.md")
    sop_dir: str = Field(".chronicle/data/guardians")
    log_path: str = Field(".chronicle/data/chronicle.log")
    
    provider: str = Field("ollama")
    embedding_model: str = Field("nomic-embed-text")
    reasoning_model: str = Field("deepseek-r1:14b")
    
    constitution_seed_topics: List[str] = Field(default_factory=lambda: ["Sovereign Web", "Engineering Principles", "Test-Driven Development", "Modular Design"])
    
    search_limit: int = Field(5)
    search_mode: str = Field("hybrid")
    per_post_limit: Optional[int] = Field(None)
    rrf_k: int = Field(60)
    required_frontmatter_fields: List[str] = Field(default_factory=lambda: ["title"])
    frontmatter_field_types: Dict[str, str] = Field(default_factory=lambda: {"draft": "bool"})
    
    chunk_size: int = Field(1200)
    chunk_overlap: int = Field(200)

    @classmethod
    def from_yaml(cls, path: str = ".chronicle/config.yaml") -> 'AppConfig':
        if not os.path.exists(path):
            return cls()
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
            return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
