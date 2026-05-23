from pydantic import BaseModel, Field
from typing import List, Optional

class ReferenceDocument(BaseModel):
    """Represents a seminal paper or book in the Historian's Library."""
    id: str = Field(..., description="Unique ID (e.g., bibtex key or shortname)")
    title: str
    authors: List[str]
    year: int
    abstract: str = Field(..., description="A 1-paragraph summary of the key thesis")
    why_it_matters: str = Field(..., description="The specific reason this is an 'Anchor' for the blog")
    file_path: Optional[str] = Field(None, description="Path to PDF in workspace if available")
    tags: List[str] = Field(default_factory=list)
