"""
Seek Job Details Extractor Package

This package provides functionality to extract and process job details from Seek.com.au
"""

from .search import extract_job_data_from_url
from .database import (
    get_connection,
    init_database,
    upsert_jobs,
    get_active_jobs,
    get_statistics,
)

__all__ = [
    "extract_job_data_from_url",
    "get_connection",
    "init_database",
    "upsert_jobs",
    "get_active_jobs",
    "get_statistics",
]
