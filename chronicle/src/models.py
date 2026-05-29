from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class DocumentChunk(BaseModel):
    """Represents a single chunk of a blog post for indexing."""
    id: str = Field(..., description="Unique ID for the chunk (e.g., hash or uuid)")
    text: str = Field(..., description="The raw markdown text of the chunk")
    source: str = Field(..., description="Blog-root relative path to the source markdown file")
    title: str = Field(..., description="Title of the post from frontmatter")
    slug: str = Field(..., description="Slug of the post")
    description: Optional[str] = Field(None, description="Short summary from frontmatter")
    date: Optional[datetime] = Field(None, description="Publication date")
    series: Optional[List[str]] = Field(default_factory=list, description="Series name(s)")
    series_order: Optional[int] = Field(None, description="Order within a series")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the post")
    draft: bool = Field(False, description="True if the post is a draft")
    chunk_type: str = Field("prose", description="Type of chunk: prose, code, header, frontmatter")
    content_hash: str = Field(..., description="SHA-256 hash of the chunk content")
    file_hash: str = Field(..., description="SHA-256 hash of the entire source file")

class SearchResult(BaseModel):
    """Represents a result returned from the Librarian search."""
    chunk: DocumentChunk
    score: float = Field(..., description="Hybrid RRF score or Vector distance")
    mode: str = Field("hybrid", description="Search mode used (hybrid, vector, fts)")

class NarrativePromise(BaseModel):
    """Represents a commitment made in a past post to explore a topic later."""
    source_post: str
    promise_text: str
    topic: str
    status: str = Field("open", description="open, fulfilled, or abandoned")
    
class SeriesLedger(BaseModel):
    """A high-level summary of an entire series."""
    series_name: str
    posts_count: int
    last_updated: datetime
    summary: str
    key_logic_invariants: List[str] = Field(default_factory=list, description="Core technical rules established in this series")
    open_promises: List[NarrativePromise] = Field(default_factory=list, description="Commitments to future content")

class FollowUpSuggestion(BaseModel):
    """Proposes a deep technical follow-up post based on series analysis."""
    title: str = Field(..., description="Compelling technical title for the follow-up post")
    rationale: str = Field(..., description="Why this topic is architecturally and logically the next step")
    transition_hook: str = Field(..., description="Suggested opening hook or transition sentences")

class HandoffBrief(BaseModel):
    """Synthesizes logic gaps and next steps for continuing a content series."""
    series_name: str
    last_post_title: str
    logical_gaps: List[str] = Field(default_factory=list, description="Unaddressed trade-offs or conceptual holes")
    follow_ups: List[FollowUpSuggestion] = Field(default_factory=list, description="Proposed deep follow-up articles")
