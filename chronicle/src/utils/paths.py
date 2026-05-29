import os
from pathlib import Path

class PathResolver:
    """Handles resolution between absolute and project-relative paths."""
    
    def __init__(self, content_root: str):
        self.content_root = os.path.abspath(content_root)

    def to_relative(self, abs_path: str) -> str:
        """Converts an absolute path to one relative to the content root."""
        return os.path.relpath(abs_path, self.content_root)

    def to_absolute(self, rel_path: str) -> str:
        """Converts a relative path back to an absolute system path."""
        return os.path.abspath(os.path.join(self.content_root, rel_path))
