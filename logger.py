import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logging(config: dict) -> None:
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    log_file = log_config.get('file', 'app.log')
    log_level = log_config.get('level', 'INFO')
    log_format = log_config.get('format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    max_size = log_config.get('max_size', 10)  # MB
    backup_count = log_config.get('backup_count', 5)

    # Create log directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=max_size * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )

class Logger:
    """Logger wrapper for easy usage"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def exception(self, message: str):
        self.logger.exception(message)