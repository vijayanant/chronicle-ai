import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file: str = "chronicle/data/chronicle.log"):
    """Sets up professional multi-destination logging."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    logger = logging.getLogger("chronicle")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # 1. Console Handler (Clean output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)

    # 2. File Handler (Detailed debug info)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def get_logger():
    return logging.getLogger("chronicle")
