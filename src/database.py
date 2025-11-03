"""
Database operations for storing job data in PostgreSQL
Using DuckDB with PostgreSQL extension
"""

import json
import os
from datetime import datetime
import duckdb
from dotenv import load_dotenv

load_dotenv()


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
            work_types TEXT,
            work_arrangements TEXT,
            
            salary_label VARCHAR
        )
    """)
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
    
    Returns:
        dict with statistics (new_jobs, updated_jobs, total_active)
    """
    if not jobs:
        return {"new_jobs": 0, "updated_jobs": 0, "total_active": 0}
    
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
                work_types_text,
                work_arr_text,
                job.get('salaryLabel'),
                job_id
            ])
            updated_jobs += 1
        else:
            # New job - insert it
            conn.execute("""
                INSERT INTO pg.jobs (
                    id, title, teaser, employer_id, employer_name, role_id,
                    listing_date, bullet_points, locations, work_types,
                    work_arrangements, salary_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                work_types_text,
                work_arr_text,
                job.get('salaryLabel')
            ])
            new_jobs += 1
    
    # Get total jobs
    total_active = conn.execute("SELECT COUNT(*) FROM pg.jobs").fetchone()[0]
    
    return {
        "new_jobs": new_jobs,
        "updated_jobs": updated_jobs,
        "total_active": total_active
    }


def get_active_jobs(conn) -> list[dict]:
    """Get all jobs"""
    result = conn.execute("""
        SELECT 
            id, title, employer_name, salary_label, 
            locations, work_types, work_arrangements
        FROM pg.jobs 
        ORDER BY listing_date DESC
    """).fetchall()
    
    jobs = []
    for row in result:
        jobs.append({
            'id': row[0],
            'title': row[1],
            'employer_name': row[2],
            'salary_label': row[3],
            'locations': row[4] if row[4] else "",
            'work_types': row[5] if row[5] else "",
            'work_arrangements': row[6] if row[6] else ""
        })
    
    return jobs


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

