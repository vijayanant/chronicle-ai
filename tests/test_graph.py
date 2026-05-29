import pytest
from pathlib import Path
from chronicle.src.graph import BlogGraph
from chronicle.src.utils.config import AppConfig

def test_extract_hrefs():
    config = AppConfig(content_root=".")
    analyzer = BlogGraph(config)
    
    content = (
        "# Hello World\n"
        "This is a [markdown link](/posts/first-post).\n"
        "And this is a Hugo ref link: [Akshara logic]({{< ref \"/posts/building-akshara/the-rebirth-invariant\" >}}).\n"
        "Here is an external link: [Google](https://google.com).\n"
        "```markdown\n"
        "[Ignored link in code block](/ignored)\n"
        "```\n"
    )
    
    hrefs = analyzer._extract_hrefs(content)
    assert "/posts/first-post" in hrefs
    assert "/posts/building-akshara/the-rebirth-invariant" in hrefs
    assert "https://google.com" in hrefs
    # Verify that links inside code blocks are ignored by the MarkdownIt parser
    assert "/ignored" not in hrefs

def test_normalize_target(tmp_path):
    # Set up dummy folder layout
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    post_a_dir = content_dir / "post-a"
    post_a_dir.mkdir()
    post_a_file = post_a_dir / "index.md"
    post_a_file.touch()
    
    post_b_dir = content_dir / "post-b"
    post_b_dir.mkdir()
    post_b_file = post_b_dir / "index.md"
    post_b_file.touch()
    
    config = AppConfig(content_root=str(content_dir))
    analyzer = BlogGraph(config)
    
    # 1. Test external url -> None
    assert analyzer._normalize_target("https://google.com", post_a_file) is None
    
    # 2. Test relative path matching
    assert analyzer._normalize_target("../post-b/index.md", post_a_file) == "post-b/index.md"
    
    # 3. Test Hugo ref translation
    assert analyzer._normalize_target('{{< ref "/posts/post-b" >}}', post_a_file) == "post-b/index.md"

def test_graph_and_metrics(tmp_path):
    config = AppConfig(content_root=str(tmp_path))
    
    # Create three posts:
    # post-a: links to post-b and has draft: true
    # post-b: links to post-c and draft: false
    # post-c: has draft: false (no outgoing links)
    
    post_a = tmp_path / "post-a.md"
    post_a.write_text("---\ntitle: Post A\ndraft: true\n---\n[Link to B](post-b.md)")
    
    post_b = tmp_path / "post-b.md"
    post_b.write_text("---\ntitle: Post B\ndraft: false\n---\n[Link to C](post-c.md)")
    
    post_c = tmp_path / "post-c.md"
    post_c.write_text("---\ntitle: Post C\ndraft: false\n---\nNothing here.")
    
    # 1. Test build_graph with include_drafts=False (default)
    # Graph should only contain post-b and post-c.
    # post-b should link to post-c.
    # post-b should be an orphan (0 incoming links) since post-a is skipped.
    analyzer = BlogGraph(config)
    g, skipped = analyzer.build_graph(include_drafts=False)
    
    assert "post-a.md" not in g
    assert "post-b.md" in g
    assert "post-c.md" in g
    assert g.has_edge("post-b.md", "post-c.md")
    
    metrics = analyzer.get_metrics()
    assert metrics["total_posts"] == 2
    assert metrics["total_links"] == 1
    assert metrics["orphans"] == ["post-b.md"]
    
    # 2. Test build_graph with include_drafts=True
    # Graph should contain post-a, post-b, and post-c.
    # post-a should link to post-b, which links to post-c.
    # post-a should be the only orphan.
    analyzer_all = BlogGraph(config)
    g_all, skipped_all = analyzer_all.build_graph(include_drafts=True)
    
    assert "post-a.md" in g_all
    assert g_all.has_edge("post-a.md", "post-b.md")
    assert g_all.has_edge("post-b.md", "post-c.md")
    
    metrics_all = analyzer_all.get_metrics()
    assert metrics_all["total_posts"] == 3
    assert metrics_all["total_links"] == 2
    assert metrics_all["orphans"] == ["post-a.md"]
