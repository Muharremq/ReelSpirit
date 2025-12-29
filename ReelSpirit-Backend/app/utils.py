import re
import logging
from config import settings

def setup_logger(name: str):
    """Professional logging configuration."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(settings.LOG_LEVEL)
        
    return logger

def extract_username(input_str: str) -> str:
    """Extracts the username from the URL or raw text."""
    if not input_str:
        return ""
    clean_str = input_str.replace("@", "").strip()
    match = re.search(r"instagram\.com/([a-zA-Z0-9._]+)", clean_str)
    if match:
        return match.group(1)
    return clean_str.split("/")[0].split("?")[0]