#!/usr/bin/env python3
"""
Seek Job Search and Extractor
Main entry point for the application
"""

import os
from dotenv import load_dotenv

from src import (
    extract_job_data_from_url,
    get_connection,
    init_database,
    upsert_jobs,
    get_statistics,
)
from src.get_url import construct_seek_url

load_dotenv()
loi_for_tg = os.getenv("TG_LOCATIONS", "").lower().split(",")

def process(search_url: str):
    """Main application logic"""

    jobs = extract_job_data_from_url(search_url)
    
    conn = get_connection()
    init_database(conn)
    
    stats = upsert_jobs(conn, jobs)
    
    # Get overall statistics
    db_stats = get_statistics(conn)
    
    conn.close()
    
def main():
    """Main application logic"""
    # Generate all search URLs from environment variables
    for search_url in construct_seek_url():
        process(search_url)

if __name__ == "__main__":
    main()

