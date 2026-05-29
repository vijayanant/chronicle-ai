from pathlib import Path
import re
from typing import List, Dict, Any, Tuple, Optional
import frontmatter
from markdown_it import MarkdownIt
import networkx as nx

from .utils.config import AppConfig
from .utils.paths import PathResolver
from .utils.logging import get_logger

logger = get_logger()

class BlogGraph:
    def __init__(self, config: AppConfig):
        self.config = config
        self.content_root = Path(config.content_root).resolve()
        self.resolver = PathResolver(str(self.content_root))
        self.md = MarkdownIt()
        self.graph = nx.DiGraph()
        
    def _extract_hrefs(self, content: str) -> List[str]:
        """Parses Markdown content and extracts both standard markdown hrefs and Hugo shortcode refs."""
        hrefs = []
        # Strip code blocks to avoid extracting links inside code snippets
        clean_content = re.compile(r'```.*?```', re.DOTALL).sub('', content)
        clean_content = re.compile(r'`[^`\n]+`').sub('', clean_content)

        # 1. Extract standard links using markdown-it-py
        try:
            tokens = self.md.parse(clean_content)
            def walk(t_list):
                for t in t_list:
                    if t.type == "link_open" and t.attrs:
                        href = t.attrs.get("href")
                        if href:
                            hrefs.append(href)
                    elif t.children:
                        walk(t.children)
            walk(tokens)
        except Exception as e:
            logger.error(f"Error parsing markdown AST: {e}")

        # 2. Extract Hugo ref/relref shortcodes using regex
        # This catches shortcodes like {{< ref "/posts/target" >}} which markdown-it-py skips
        # since brackets like < and > break CommonMark URL validation rules.
        shortcodes = re.findall(r'\{\{<\s*(?:ref|relref)\s+["\']([^"\']+)["\']\s*>\}\}', clean_content)
        # Also handle standard % delimiters
        shortcodes += re.findall(r'\{\{%\s*(?:ref|relref)\s+["\']([^"\']+)["\']\s*%\}\}', clean_content)
        
        hrefs.extend(shortcodes)
        return hrefs

    def _normalize_target(self, href: str, current_file: Path) -> Optional[str]:
        """
        Normalizes a link target (relative path or Hugo shortcode ref) to a relative path
        from the content root, matching it to an existing post file.
        Returns None if it is an external link or cannot be resolved.
        """
        # 1. Ignore external links
        if href.startswith(("http://", "https://", "mailto:", "ftp:")):
            return None
            
        # 2. Extract target from Hugo ref/relref shortcodes if present
        # Pattern matches: {{< ref "target" >}} or {{% relref 'target' %}}
        shortcode_match = re.search(r'(?:ref|relref)\s+["\']([^"\']+)["\']', href)
        if shortcode_match:
            target = shortcode_match.group(1)
        else:
            target = href

        # Clean anchor hashes or queries (e.g. /posts/slug#header -> /posts/slug)
        target = target.split("#")[0].split("?")[0].strip()
        if not target:
            return None

        # 3. Resolve to relative path from content root
        # Check if it is a relative file path (like ../other-post/index.md)
        if not target.startswith("/"):
            # It is relative to the current file's directory
            resolved_abs = (current_file.parent / target).resolve()
            if resolved_abs.exists() and resolved_abs.is_file():
                return self.resolver.to_relative(str(resolved_abs))
        
        # If it starts with "/" or was not found as a direct relative file:
        # Standardize search term by stripping common prefixes
        clean_target = target.lstrip("/")
        if clean_target.startswith("posts/"):
            clean_target = clean_target[len("posts/"):]
        if clean_target.startswith("content/"):
            clean_target = clean_target[len("content/"):]
            
        # Strip trailing slashes
        clean_target = clean_target.rstrip("/")

        # Search for a matching file under the content root
        for p in self.content_root.glob("**/*.md"):
            if p.name == "_index.md":
                continue
            rel_p = self.resolver.to_relative(str(p))
            
            # Normalize slashes for matching
            rel_p_norm = rel_p.replace("\\", "/")
            clean_target_norm = clean_target.replace("\\", "/")
            
            # Match if clean target matches the stem or is a subpath of the file's path
            if clean_target_norm in rel_p_norm:
                return rel_p
                
        return None

    def build_graph(self, include_drafts: bool = False) -> Tuple[nx.DiGraph, List[str]]:
        """
        Scans all files in the content root, parses their links, and constructs the DiGraph.
        Returns the networkx DiGraph and a list of skipped targets (broken internal links).
        """
        self.graph.clear()
        
        # 1. Find all files
        all_files = [p for p in self.content_root.glob("**/*.md") if p.name != "_index.md"]
        
        # 2. Filter files (ignoring drafts unless include_drafts=True)
        posts_to_process = []
        for p in all_files:
            try:
                post = frontmatter.load(p)
                is_draft = post.get("draft", False)
                if not include_drafts and is_draft:
                    continue
                posts_to_process.append((p, post))
            except:
                posts_to_process.append((p, None))

        # Add all valid posts as nodes first
        nodes_map = {}
        for p, post in posts_to_process:
            rel_p = self.resolver.to_relative(str(p))
            title = post.get("title", p.stem) if post else p.stem
            self.graph.add_node(rel_p, title=title)
            nodes_map[rel_p] = p

        # 3. Scan for links and add edges
        skipped_targets = []
        for rel_p, p in nodes_map.items():
            try:
                content = p.read_text(encoding="utf-8")
                # Strip frontmatter for link parsing
                post = frontmatter.loads(content)
                hrefs = self._extract_hrefs(post.content)
                
                for href in hrefs:
                    resolved = self._normalize_target(href, p)
                    if resolved:
                        if resolved in self.graph:
                            self.graph.add_edge(rel_p, resolved)
                        else:
                            skipped_targets.append(resolved)
            except Exception as e:
                logger.error(f"Error building graph for {rel_p}: {e}")

        return self.graph, skipped_targets

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates topological metrics of the constructed graph."""
        total_posts = self.graph.number_of_nodes()
        total_links = self.graph.number_of_edges()
        
        # Find orphans (nodes with in-degree = 0)
        orphans = [node for node in self.graph.nodes if self.graph.in_degree(node) == 0]
        orphans.sort()
        
        density = total_links / total_posts if total_posts > 0 else 0.0
        
        return {
            "total_posts": total_posts,
            "total_links": total_links,
            "density": round(density, 2),
            "orphans": orphans
        }
