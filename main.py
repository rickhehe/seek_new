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

load_dotenv()

def process(search_url: str):
    """Main application logic"""

    # Extract job data from search URL
    print("🔎 Searching for jobs...\n")
    jobs = extract_job_data_from_url(search_url)
    
    # if not jobs:
    #     print("❌ No jobs found. Exiting.")
    #     return
    
    print(f"\n📊 Found {len(jobs)} jobs\n")
    
    # Save to database
    print("💾 Saving to database...")
    conn = get_connection()
    init_database(conn)
    
    stats = upsert_jobs(conn, jobs)
    print(f"✅ Database updated:")
    print(f"   New jobs: {stats['new_jobs']}")
    print(f"   Updated jobs: {stats['updated_jobs']}")
    print(f"   Total jobs: {stats['total_active']}")
    
    # Get overall statistics
    db_stats = get_statistics(conn)
    print(f"\n📊 Database Statistics:")
    print(f"   Total jobs: {db_stats['total_jobs']}")
    
    conn.close()
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"{'JOB SUMMARY':^80}")
    print(f"{'='*80}\n")
    
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['title']}")
        print(f"   Company: {job.get('employer_name', 'N/A')}")
        print(f"   Location: {job['locations'][0]['label'] if job['locations'] else 'N/A'}")
        print(f"   Salary: {job.get('salaryLabel', 'Not specified')}")
        print(f"   Work Type: {', '.join(job.get('workTypes', ['N/A']))}")
        if job.get('workArrangements'):
            work_arr = job['workArrangements']
            if isinstance(work_arr, dict) and 'data' in work_arr:
                arrangements = ', '.join([wa['label']['text'] for wa in work_arr['data']])
                print(f"   Work Arrangement: {arrangements}")
            elif isinstance(work_arr, list) and work_arr:
                # Handle if it's already a list
                arrangements = ', '.join([wa.get('label', {}).get('text', '') for wa in work_arr if isinstance(wa, dict)])
                if arrangements:
                    print(f"   Work Arrangement: {arrangements}")
        print(f"   Job ID: {job['id']}")
        print()
    
    print(f"{'='*80}\n")

def main():
    """Main application logic"""
    # Get search URL from environment variable
    search_url_1 = os.getenv("SEARCH_URL_1")
    search_url_2 = os.getenv("SEARCH_URL_2")
    search_url_3 = os.getenv("SEARCH_URL_3")
    
    if search_url_1:
        process(search_url_1)
    if search_url_2:
        process(search_url_2)
    if search_url_3:
        process(search_url_3)

if __name__ == "__main__":
    main()

