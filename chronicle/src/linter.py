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

    def lint_file(self, file_path: str, include_drafts: bool = True) -> List[LintIssue]:
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

        # 1. Frontmatter Parsing & Validation
        try:
            post = frontmatter.loads(raw_content)
            meta = post.metadata
            if not meta:
                issues.append(LintIssue("frontmatter", "Missing frontmatter", "ERROR", 1))
                return issues

            # If we don't want to include drafts and this is a draft, skip validation entirely
            if not include_drafts and meta.get("draft", False):
                return []
                
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

        return issues
