import os
import pytest
from chronicle.src.utils.paths import PathResolver

def test_path_resolver_relative():
    # Setup
    root = "/Users/vj/workspace/blogging-assistant/my-blog-site-copy/content/posts"
    resolver = PathResolver(root)
    abs_path = os.path.join(root, "modular-by-design/post-1/index.md")
    
    # Act
    rel_path = resolver.to_relative(abs_path)
    
    # Assert
    assert rel_path == "modular-by-design/post-1/index.md"

def test_path_resolver_absolute():
    # Setup
    root = "/tmp/blog"
    resolver = PathResolver(root)
    rel_path = "series-a/chapter-1.md"
    
    # Act
    abs_path = resolver.to_absolute(rel_path)
    
    # Assert
    assert abs_path == "/tmp/blog/series-a/chapter-1.md"
