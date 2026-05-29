import pytest
from chronicle.src.linter import ProseLinter, LintIssue
from chronicle.src.utils.config import AppConfig

def test_linter_checks_nonexistent_file(tmp_path):
    config = AppConfig(content_root=str(tmp_path))
    linter = ProseLinter(config)
    issues = linter.lint_file(str(tmp_path / "nonexistent.md"))
    assert len(issues) == 1
    assert issues[0].category == "system"

def test_linter_invalid_frontmatter(tmp_path):
    config = AppConfig(content_root=str(tmp_path))
    linter = ProseLinter(config)
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("---bad frontmatter---")
    issues = linter.lint_file(str(bad_file))
    assert len(issues) > 0
    assert any(i.category == "frontmatter" for i in issues)

def test_linter_missing_title(tmp_path):
    config = AppConfig(content_root=str(tmp_path))
    linter = ProseLinter(config)
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("---\ndraft: false\n---\nSome content.")
    issues = linter.lint_file(str(bad_file))
    assert len(issues) == 1
    assert issues[0].category == "frontmatter"
    assert "title" in issues[0].message

def test_linter_configurable_frontmatter(tmp_path):
    config = AppConfig(
        content_root=str(tmp_path),
        required_frontmatter_fields=["title", "custom_field"],
        frontmatter_field_types={"custom_field": "int", "seo_title": "str"}
    )
    linter = ProseLinter(config)
    
    # 1. Test missing required custom field
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("---\ntitle: A\n---\n")
    issues = linter.lint_file(str(bad_file))
    assert len(issues) == 1
    assert "Missing required frontmatter field: 'custom_field'" in issues[0].message
    
    # 2. Test bad field type
    bad_type_file = tmp_path / "bad_type.md"
    bad_type_file.write_text("---\ntitle: A\ncustom_field: \"should be int\"\n---\n")
    issues = linter.lint_file(str(bad_type_file))
    assert len(issues) == 1
    assert "Field 'custom_field' must be of type 'int'" in issues[0].message

    # 3. Test correct custom field configuration
    good_file = tmp_path / "good.md"
    good_file.write_text("---\ntitle: A\ncustom_field: 42\nseo_title: \"Optimized Title\"\n---\n")
    issues = linter.lint_file(str(good_file))
    assert len(issues) == 0

def test_linter_validates_drafts(tmp_path):
    config = AppConfig(
        content_root=str(tmp_path),
        required_frontmatter_fields=["title", "custom_field"],
        frontmatter_field_types={"custom_field": "int"}
    )
    linter = ProseLinter(config)
    
    # A draft post missing 'custom_field' should fail because drafts are also validated
    draft_file = tmp_path / "draft.md"
    draft_file.write_text("---\ntitle: A\ndraft: true\n---\n")
    issues = linter.lint_file(str(draft_file))
    assert len(issues) == 1
    assert "Missing required frontmatter field: 'custom_field'" in issues[0].message

def test_linter_skips_drafts(tmp_path):
    config = AppConfig(
        content_root=str(tmp_path),
        required_frontmatter_fields=["title", "custom_field"],
        frontmatter_field_types={"custom_field": "int"}
    )
    linter = ProseLinter(config)
    
    draft_file = tmp_path / "draft.md"
    draft_file.write_text("---\ntitle: A\ndraft: true\n---\n")
    
    # With include_drafts=False, the draft file is skipped and returns no issues
    issues = linter.lint_file(str(draft_file), include_drafts=False)
    assert len(issues) == 0
