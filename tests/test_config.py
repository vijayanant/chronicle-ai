import pytest
import os
from unittest.mock import patch, mock_open
from chronicle.src.utils.config import AppConfig

def test_load_config_default_exists():
    mock_yaml = """
blog_root: "custom/path"
search_limit: 10
"""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_yaml)):
            config = AppConfig.from_yaml("chronicle/config.yaml")
            assert config.blog_root == "custom/path"
            assert config.search_limit == 10

def test_load_config_no_file():
    with patch("os.path.exists", return_value=False):
        config = AppConfig.from_yaml("missing.yaml")
        # Should return defaults from Pydantic model
        assert config.blog_root == ""
