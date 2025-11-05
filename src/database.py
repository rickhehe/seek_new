"""
Database operations for storing job data in PostgreSQL
Using DuckDB with PostgreSQL extension
"""

import json
import os
from datetime import datetime
import duckdb
from dotenv import load_dotenv

from src.utils.my_logger import get_logger
from src.utils.tg import send_telegram

load_dotenv()

LOGGER = get_logger('default')


def get_connection():
    """Get DuckDB connection to PostgreSQL database"""
    password = os.getenv('DB_PASSWORD')
    if not password:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    # Create in-memory DuckDB connection
    conn = duckdb.connect()

    conn.execute(f"""
        ATTACH 'dbname=s user=postgres host=localhost port=5432 password={password}' 
        AS pg (TYPE POSTGRES, SCHEMA 'career')
    """)
    
    return conn


def init_database(conn):
    """Initialize database schema in PostgreSQL"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pg.jobs (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            teaser TEXT,
            employer_id VARCHAR,
            employer_name VARCHAR,
            role_id VARCHAR,
            listing_date TIMESTAMP,
            
            -- Text fields extracted from complex data
            bullet_points TEXT,
            locations TEXT,
            country_codes TEXT,
            work_types TEXT,
            work_arrangements TEXT,
            
            salary_label VARCHAR
        )
    """)
    
    # Add country_codes column if it doesn't exist (for existing tables)
    try:
        conn.execute("""
            ALTER TABLE pg.jobs 
            ADD COLUMN IF NOT EXISTS country_codes TEXT
        """)
    except Exception as e:
        # Column might already exist or other error
        pass
    
    print("✅ Database initialized")


def _extract_bullet_points_text(bullet_points) -> str:
    """Extract bullet points as semicolon-separated text"""
    if not bullet_points:
        return ""
    if isinstance(bullet_points, list):
        return "; ".join(str(bp) for bp in bullet_points if bp)
    return str(bullet_points)


def _extract_locations_text(locations) -> str:
    """Extract location labels as semicolon-separated text"""
    if not locations:
        return ""
    labels = [loc.get('label', '') for loc in locations if isinstance(loc, dict)]
    return "; ".join(labels)


def _extract_country_codes_text(locations) -> str:
    """Extract country codes as semicolon-separated text"""
    if not locations:
        return ""
    codes = [loc.get('countryCode', '') for loc in locations if isinstance(loc, dict)]
    return "; ".join(codes)


def _extract_work_types_text(work_types) -> str:
    """Extract work types as semicolon-separated text"""
    if not work_types:
        return ""
    if isinstance(work_types, list):
        return "; ".join(work_types)
    return str(work_types)


def _extract_work_arrangements_text(work_arrangements) -> str:
    """Extract work arrangement labels as semicolon-separated text"""
    if not work_arrangements:
        return ""
    
    # Handle dict with 'data' key
    if isinstance(work_arrangements, dict):
        data = work_arrangements.get('data', [])
        labels = []
        for wa in data:
            if isinstance(wa, dict):
                # Try label.text first, then label_text
                label = wa.get('label', {}).get('text') or wa.get('label_text', '')
                if label:
                    labels.append(label)
        return "; ".join(labels)
    
    # Handle list directly
    if isinstance(work_arrangements, list):
        labels = []
        for wa in work_arrangements:
            if isinstance(wa, dict):
                # Try label_text first, then label.text
                label = wa.get('label_text') or wa.get('label', {}).get('text', '')
                if label:
                    labels.append(label)
        return "; ".join(labels)
    
    return ""


def upsert_jobs(conn, jobs: list[dict]) -> dict:
    """
    Insert or update jobs in the database
    Sends Telegram notification for new jobs only
    
    Returns:
        dict with statistics (new_jobs, updated_jobs, total_active)
    """
    if not jobs:
        return {"new_jobs": 0, "updated_jobs": 0, "total_active": 0}
    
    # Get Telegram credentials
    tg_api_key = os.getenv("TG_API_KEY")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    
    new_jobs = 0
    updated_jobs = 0
    
    for job in jobs:
        job_id = int(job['id'])
        
        # Check if job exists
        result = conn.execute(
            "SELECT id FROM pg.jobs WHERE id = ?",
            [job_id]
        ).fetchone()
        
        # Extract text values
        bullet_points_text = _extract_bullet_points_text(job.get('bulletPoints', []))
        locations_text = _extract_locations_text(job.get('locations', []))
        country_codes_text = _extract_country_codes_text(job.get('locations', []))
        work_types_text = _extract_work_types_text(job.get('workTypes', []))
        work_arr_text = _extract_work_arrangements_text(job.get('workArrangements'))
        
        if result:
            # Job exists - update it
            conn.execute("""
                UPDATE pg.jobs SET
                    title = ?,
                    teaser = ?,
                    employer_id = ?,
                    employer_name = ?,
                    role_id = ?,
                    listing_date = ?,
                    bullet_points = ?,
                    locations = ?,
                    country_codes = ?,
                    work_types = ?,
                    work_arrangements = ?,
                    salary_label = ?
                WHERE id = ?
            """, [
                job['title'],
                job.get('teaser'),
                job.get('employer_id'),
                job.get('employer_name'),
                job.get('roleId'),
                job.get('listingDate'),
                bullet_points_text,
                locations_text,
                country_codes_text,
                work_types_text,
                work_arr_text,
                job.get('salaryLabel'),
                job_id
            ])
            updated_jobs += 1
        else:
            # New job - insert it and send notification
            conn.execute("""
                INSERT INTO pg.jobs (
                    id, title, teaser, employer_id, employer_name, role_id,
                    listing_date, bullet_points, locations, country_codes, work_types,
                    work_arrangements, salary_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                job_id,
                job['title'],
                job.get('teaser'),
                job.get('employer_id'),
                job.get('employer_name'),
                job.get('roleId'),
                job.get('listingDate'),
                bullet_points_text,
                locations_text,
                country_codes_text,
                work_types_text,
                work_arr_text,
                job.get('salaryLabel')
            ])
            new_jobs += 1
            
            # Send Telegram notification for new job
            if tg_api_key and tg_chat_id:
                try:
                    msg = (
                        f"Title: {job.get('title', 'N/A')}\n"
                        f"Company: {job.get('employer_name', 'N/A')}\n"
                        f"Location: {locations_text or 'N/A'}\n"
                        f"Salary: {job.get('salaryLabel', 'Not specified')}\n"
                        f"Link: https://www.seek.com.au/job/{job_id}"
                    )
                    send_telegram(tg_api_key, msg, tg_chat_id)
                    LOGGER.info(f"📱 Telegram notification sent for job ID {job_id}")
                except Exception as e:
                    LOGGER.error(f"Failed to send Telegram notification for job {job_id}: {e}")
    
    # Get total jobs
    total_active = conn.execute("SELECT COUNT(*) FROM pg.jobs").fetchone()[0]
    
    return {
        "new_jobs": new_jobs,
        "updated_jobs": updated_jobs,
        "total_active": total_active
    }


def get_statistics(conn) -> dict:
    """Get database statistics"""
    stats = {}
    
    # Total jobs
    stats['total_jobs'] = conn.execute("SELECT COUNT(*) FROM pg.jobs").fetchone()[0]
    
    # Date range
    date_range = conn.execute("SELECT MIN(listing_date), MAX(listing_date) FROM pg.jobs").fetchone()
    stats['earliest_job_date'] = date_range[0]
    stats['latest_job_date'] = date_range[1]
    
    return stats


if __name__ == "__main__":
    # Test database operations
    conn = get_connection()
    init_database(conn)
    stats = get_statistics(conn)
    print(f"\n📊 Database Statistics:")
    print(f"   Total jobs: {stats['total_jobs']}")
    conn.close()

