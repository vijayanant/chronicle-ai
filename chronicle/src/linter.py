import re
import os
import frontmatter
from pathlib import Path
from typing import List, Dict, Any

class LintIssue:
    def __init__(self, category: str, message: str, severity: str = "ERROR", line: int = None):
        self.category = category
        self.message = message
        self.severity = severity
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "line": self.line
        }

class ProseLinter:
    def __init__(self, config_or_root: Any):
        from .utils.config import AppConfig
        if isinstance(config_or_root, AppConfig):
            self.config = config_or_root
        else:
            self.config = AppConfig(content_root=str(config_or_root))
        self.content_root = Path(self.config.content_root)

    def lint_file(self, file_path: str) -> List[LintIssue]:
        issues = []
        abs_path = Path(file_path).resolve()
        if not abs_path.exists():
            return [LintIssue("system", f"File does not exist: {file_path}", "ERROR")]

        # Read content
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except Exception as e:
            return [LintIssue("system", f"Failed to read file: {e}", "ERROR")]

        # 1. Frontmatter Validation
        try:
            post = frontmatter.loads(raw_content)
            meta = post.metadata
            if not meta:
                issues.append(LintIssue("frontmatter", "Missing frontmatter", "ERROR", 1))
            else:
                # Validate required fields
                for field in self.config.required_frontmatter_fields:
                    if field not in meta or meta[field] is None or meta[field] == "":
                        issues.append(LintIssue("frontmatter", f"Missing required frontmatter field: '{field}'", "ERROR", 1))
                
                # Validate field types
                for field, expected_type in self.config.frontmatter_field_types.items():
                    if field in meta and meta[field] is not None:
                        val = meta[field]
                        is_valid = True
                        if expected_type in ("bool", "boolean"):
                            is_valid = isinstance(val, bool)
                        elif expected_type in ("int", "integer"):
                            is_valid = isinstance(val, int) and not isinstance(val, bool)
                        elif expected_type in ("str", "string"):
                            is_valid = isinstance(val, str)
                        elif expected_type in ("list", "array"):
                            is_valid = isinstance(val, list)
                        elif expected_type == "date":
                            from datetime import datetime, date as dt_date
                            if not isinstance(val, (datetime, dt_date)):
                                try:
                                    datetime.fromisoformat(str(val))
                                except:
                                    is_valid = False
                        if not is_valid:
                            issues.append(LintIssue("frontmatter", f"Field '{field}' must be of type '{expected_type}'", "ERROR", 1))
        except Exception as e:
            issues.append(LintIssue("frontmatter", f"Failed to parse frontmatter: {e}", "ERROR", 1))
            return issues # Cannot lint content if frontmatter parsing fails

        # Split content into lines to calculate line numbers for inline issues
        lines = raw_content.splitlines()

        # 2. Markdown Link & Image Validation
        # Regex for standard markdown link: [text](link)
        link_pattern = re.compile(r'\[([^\]]*?)\]\(([^)]+?)\)')
        # Regex for standard image link: ![alt](image)
        image_pattern = re.compile(r'\!\[([^\]]*?)\]\(([^)]+?)\)')
        # Regex for Hugo ref links: {{< ref "target" >}} or {{% ref "target" %}}
        hugo_ref_pattern = re.compile(r'\{\{\s*[<%]\s*ref\s+"([^"]+?)"\s*[>%]\s*\}\}')
        # Regex for Hugo figures: {{< figure src="target" ... >}}
        hugo_fig_pattern = re.compile(r'\{\{\s*[<%]\s*figure\s+src="([^"]+?)"')

        for line_idx, line_content in enumerate(lines, 1):
            # A. Check standard links
            for match in link_pattern.finditer(line_content):
                label, target = match.groups()
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                
                # Check local relative file existence
                target_path = abs_path.parent / target.split('#')[0]
                if not target_path.exists():
                    issues.append(LintIssue(
                        "link", 
                        f"Local markdown link target does not exist: {target}", 
                        "ERROR", 
                        line_idx
                    ))

            # B. Check standard images
            for match in image_pattern.finditer(line_content):
                alt, target = match.groups()
                if target.startswith(("http://", "https://")):
                    continue
                target_path = abs_path.parent / target
                if not target_path.exists():
                    issues.append(LintIssue(
                        "image", 
                        f"Local image file does not exist: {target}", 
                        "ERROR", 
                        line_idx
                    ))

            # C. Check Hugo ref links
            for match in hugo_ref_pattern.finditer(line_content):
                target = match.group(1).lstrip('/')
                # Find matching target in content directory
                found = False
                # Try relative to content_root directly
                direct_path = self.content_root / target
                if direct_path.is_dir() and (direct_path / "index.md").exists():
                    found = True
                elif direct_path.exists():
                    found = True
                else:
                    slug = Path(target).name
                    for match_path in self.content_root.glob(f"**/{slug}*"):
                        if match_path.is_file():
                            found = True
                            break
                if not found:
                    issues.append(LintIssue(
                        "hugo-ref", 
                        f"Hugo ref link target not found: {target}", 
                        "WARNING", 
                        line_idx
                    ))

            # D. Check Hugo figure image links
            for match in hugo_fig_pattern.finditer(line_content):
                target = match.group(1)
                if target.startswith(("http://", "https://")):
                    continue
                target_path = abs_path.parent / target
                if not target_path.exists():
                    issues.append(LintIssue(
                        "image", 
                        f"Hugo figure src file does not exist: {target}", 
                        "ERROR", 
                        line_idx
                    ))

        return issues
