#!/usr/bin/env python3
import os
import subprocess
import re
from datetime import datetime, timedelta

from src.utils.my_logger import get_logger
from src.utils.tg import send_telegram

from dotenv import load_dotenv
load_dotenv()

LOGGER = get_logger('default')
tg_api_key = os.getenv("TG_API_KEY")
tg_chat_id = os.getenv("TG_CHAT_ID")


def is_less_than_10m(listing_date: str) -> bool:
    """
    Check if a job listing date is less than 10 minutes old

    Args:
        listing_date: ISO 8601 formatted date string (e.g., "2025-11-03T06:40:11Z")
        
    Returns:
        True if listing is less than 10 minutes old, False otherwise
    """
    try:
        listing_datetime = datetime.fromisoformat(listing_date.replace('Z', '+00:00'))
        time_diff = datetime.utcnow() - listing_datetime
        return time_diff <= timedelta(minutes=10)
    except Exception as e:
        LOGGER.error(f"Error parsing listing date '{listing_date}': {e}")
        return False


def extract_job_data_from_url(url: str = None) -> list[dict]:
    """
    Extract job data from a Seek search URL using lynx
    
    Args:
        url: Seek search URL with filters
        
    Returns:
        List of job dictionaries with extracted fields
    """
    try:
        LOGGER.info(f"Fetching search results from URL: {url}")
        # Use lynx to fetch the page HTML and dump it to stdout
        result = subprocess.run(
            ["lynx", "-source", "-nolist", url],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print(f"❌ Lynx failed with return code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return []
        
        html_content = result.stdout

        if not html_content:
            print(f"❌ No content received from lynx")
            return []
        
        # Extract job data from the JSON embedded in the HTML
        json_pattern = re.compile(r'window\.SEEK_REDUX_DATA\s*=\s*(\{.+?\});')
        json_match = json_pattern.search(html_content)
        
        if not json_match:
            print("⚠️  Could not find SEEK_REDUX_DATA in page")
            print(f"   HTML length: {len(html_content)} bytes")
            return []
        
        try:
            import json
            redux_data = json.loads(json_match.group(1))
 
            # Get detailed job data from results.results.jobs (array)
            jobs_array = redux_data.get('results', {}).get('results', {}).get('jobs', [])
                       
            # Create a mapping from job ID to job data
            jobs_map = {job['id']: job for job in jobs_array if 'id' in job}

            # Extract requested fields for each job
            extracted_jobs = []
            seen = set()
            
            for job_id in jobs_map.keys():
                # Skip duplicates
                if job_id in seen:
                    continue
                seen.add(job_id)
                
                job = jobs_map.get(job_id, {})
                if not job:
                    continue
                
                # Extract requested fields
                extracted_job = {
                    'id': job.get('id'),
                    'title': job.get('title'),
                    'teaser': job.get('teaser'),
                    'bulletPoints': job.get('bulletPoints', []),
                    'employer_id': job.get('employer', {}).get('id'),
                    'employer_name': job.get('employer', {}).get('name'),
                    'roleId': job.get('roleId'),
                    'listingDate': job.get('listingDate'),
                    'locations': [
                        {
                            'label': loc.get('label'),
                            'countryCode': loc.get('countryCode')
                        }
                        for loc in job.get('locations', [])
                    ],
                    'salaryLabel': job.get('salaryLabel'),
                    'workTypes': job.get('workTypes', []),
                    'workArrangements': [
                        {
                            'id': wa.get('id'),
                            'label_text': wa.get('label', {}).get('text')
                        }
                        for wa in job.get('workArrangements', {}).get('data', [])
                    ]
                }

                role_id_of_interest = re.compile(r'data.+engineer', flags=re.I)
                match = role_id_of_interest.search(job.get('roleId', ''))
                if match:
                    LOGGER.info(f"✅ Match found for job ID {job_id} with role ID {job.get('roleId', '')}")
                    extracted_jobs.append(extracted_job)

                    # Check if listing is less than 10 minutes old
                    listing_date = job.get('listingDate', '')
                    if listing_date and is_less_than_10m(listing_date):
                        LOGGER.info(f"🆕 Recent listing found for job ID {job_id} listed at {listing_date}")
                        msg = f"🆕 New job listing found: {job.get('title', 'N/A')} at {job.get('employer', {}).get('name', 'N/A')}\nLink: https://www.seek.com.au/job/{job_id}"
                        send_telegram(
                            tg_api_key,
                            msg,
                            tg_chat_id
                        )
            LOGGER.info(f"✅ Found {len(extracted_jobs)} unique jobs")
            return extracted_jobs
            
        except json.JSONDecodeError as e:
            LOGGER.error(f"❌ Failed to parse JSON data: {e}")
            return []
        
    except Exception as e:
        LOGGER.error(f"❌ Error fetching search results: {e}")
        return []
