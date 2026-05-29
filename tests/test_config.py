import pytest
import os
from unittest.mock import patch, mock_open, MagicMock
from chronicle.src.utils.config import AppConfig

def test_load_config_default_exists():
    mock_yaml = """
content_root: "custom/path"
search_limit: 10
"""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_yaml)):
            config = AppConfig.from_yaml("chronicle/config.yaml")
            assert config.content_root == "custom/path"
            assert config.search_limit == 10

def test_load_config_no_file():
    with patch("os.path.exists", return_value=False):
        config = AppConfig.from_yaml("missing.yaml")
        # Should return defaults from Pydantic model
        assert config.content_root == ""

def test_historian_library_path_propagation(tmp_path):
    from chronicle.src.guardians.orchestrator import Council
    from chronicle.src.indexer import LibrarianIndexer
    from chronicle.src.utils.config import AppConfig

    custom_library_path = str(tmp_path / "custom_catalog.json")
    config = AppConfig(library_path=custom_library_path)
    indexer = MagicMock(spec=LibrarianIndexer)

    with patch("chronicle.src.guardians.systems_historian.ReferenceLibrary") as mock_ref_lib:
        council = Council(indexer, config)
        # Verify ReferenceLibrary is initialized with the config path
        mock_ref_lib.assert_called_once_with(catalog_path=custom_library_path)

def test_init_workspace_copies_playbooks(tmp_path):
    from chronicle.main import init_workspace
    from pathlib import Path
    
    # We will mock the package directory to have one playbooks file
    dummy_file = Path("/pkg/data/guardians/peer.md")
    
    with patch("os.getcwd", return_value=str(tmp_path)), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=[dummy_file]), \
         patch("shutil.copy") as mock_copy:
        
        init_workspace()
        mock_copy.assert_called_once_with(dummy_file, tmp_path / ".chronicle" / "data" / "guardians")
