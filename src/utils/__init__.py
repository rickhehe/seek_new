"""
Utility modules for the Seek job scraper
"""
from .my_logger import get_logger
from .tg import send_telegram

__all__ = ['get_logger', 'send_telegram']