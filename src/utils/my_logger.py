import logging
from pathlib import Path

def get_logger(name='default'):
    """Get a logger with the specified name"""
    logger = logging.getLogger(name)
    
    # Only add handler if it doesn't already exist (avoid duplicates)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = Path('log')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file handler with log/logger.log path
        file_handler = logging.FileHandler(log_dir / 'logger.log')
        file_handler.setFormatter(
            logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
            )
        )
        
        logger.addHandler(file_handler)
    
    return logger