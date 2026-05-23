from typing import List, Dict
from semantic_text_splitter import MarkdownSplitter

class Chunker:
    """
    Expert Markdown Chunker using the battle-tested semantic-text-splitter.
    Optimized for technical depth and structural integrity.
    """
    
    @staticmethod
    def chunk(content: str, window_size: int = 1200, overlap: int = 200) -> List[Dict[str, str]]:
        """
        Splits markdown into logically coherent chunks at semantic boundaries.
        Ensures code blocks and headers remain intact.
        """
        # Initialize the Rust-based splitter
        # We use a character-based limit to match our configuration, 
        # but the library handles the 'Semantic' part (paragraphs, sentences).
        splitter = MarkdownSplitter(capacity=window_size, overlap=overlap)
        
        # Perform the split
        raw_chunks = splitter.chunks(content)
        
        # Wrap in our internal format
        return [{"text": chunk.strip(), "type": "semantic_window"} for chunk in raw_chunks if chunk.strip()]
