import os
from pathlib import Path

class PathResolver:
    """Handles resolution between absolute and project-relative paths."""
    
    def __init__(self, blog_root: str):
        self.blog_root = os.path.abspath(blog_root)

    def to_relative(self, abs_path: str) -> str:
        """Converts an absolute path to one relative to the blog root."""
        return os.path.relpath(abs_path, self.blog_root)

    def to_absolute(self, rel_path: str) -> str:
        """Converts a relative path back to an absolute system path."""
        return os.path.abspath(os.path.join(self.blog_root, rel_path))
