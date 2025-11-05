#!/usr/bin/env python3
import os
import subprocess
import re

from src.utils.my_logger import get_logger

from dotenv import load_dotenv
load_dotenv()

LOGGER = get_logger('default')


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
            
            LOGGER.info(f"✅ Found {len(extracted_jobs)} unique jobs")
            return extracted_jobs
            
        except json.JSONDecodeError as e:
            LOGGER.error(f"❌ Failed to parse JSON data: {e}")
            return []
        
    except Exception as e:
        LOGGER.error(f"❌ Error fetching search results: {e}")
        return []
