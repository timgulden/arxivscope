#!/usr/bin/env python3
"""
Focused analysis of click performance to identify bottlenecks.
Simulates the exact click behavior and measures each step.
"""
import time
import requests
import pandas as pd
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_click_data():
    """Simulate click data that would come from the frontend."""
    return {
        "points": [
            {
                "curveNumber": 0,
                "pointNumber": 0,
                "pointIndex": 0,
                "x": 10.5,
                "y": 9.2,
                "customdata": [0]  # This is the DataFrame index
            }
        ]
    }

def measure_data_store_processing(data_store: list) -> Dict[str, float]:
    """Measure the time it takes to process data store for click."""
    metrics = {}
    
    # Measure DataFrame creation
    start_time = time.time()
    df = pd.DataFrame(data_store)
    end_time = time.time()
    metrics['dataframe_creation_ms'] = (end_time - start_time) * 1000
    
    # Measure data access
    start_time = time.time()
    if len(df) > 0:
        paper = df.iloc[0]  # Simulate accessing the clicked point
        title = paper.get('Title', 'No title')
        summary = paper.get('Summary', 'No summary')
        authors = paper.get('Authors', [])
        country = paper.get('Country of Publication', 'Unknown')
    end_time = time.time()
    metrics['data_access_ms'] = (end_time - start_time) * 1000
    
    # Measure string processing
    start_time = time.time()
    if len(df) > 0:
        paper = df.iloc[0]
        title = paper.get('Title', 'No title')
        if title and title != 'No title':
            title = title.replace('\n', ' ').strip()
            title = ' '.join(title.split())
        
        # Simulate date formatting
        date = paper.get('Submitted Date', None)
        if date:
            try:
                if isinstance(date, str) and ('GMT' in date or 'UTC' in date):
                    from datetime import datetime
                    parsed_date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
                    formatted_date = parsed_date.strftime('%Y-%m-%d')
            except:
                formatted_date = str(date)
        
        # Simulate authors formatting
        authors = paper.get('Authors', [])
        if authors and isinstance(authors, list):
            authors_text = ', '.join(authors)
        elif authors and isinstance(authors, str):
            try:
                import json
                authors_list = json.loads(authors)
                authors_text = ', '.join(authors_list) if isinstance(authors_list, list) else authors
            except:
                authors_text = authors
    end_time = time.time()
    metrics['string_processing_ms'] = (end_time - start_time) * 1000
    
    return metrics

def measure_html_generation(data_store: list) -> float:
    """Measure the time it takes to generate HTML for the click response."""
    df = pd.DataFrame(data_store)
    if len(df) == 0:
        return 0
    
    paper = df.iloc[0]
    
    start_time = time.time()
    
    # Simulate the HTML generation process
    title = paper.get('Title', 'No title')
    if title and title != 'No title':
        title = title.replace('\n', ' ').strip()
        title = ' '.join(title.split())
    
    summary = paper.get('Summary', 'No summary available')
    date = paper.get('Submitted Date', None)
    country = paper.get('Country of Publication', 'Unknown source')
    authors = paper.get('Authors', [])
    doi = paper.get('DOI', None)
    
    # Format date
    if date:
        try:
            if isinstance(date, str) and ('GMT' in date or 'UTC' in date):
                from datetime import datetime
                parsed_date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
                formatted_date = parsed_date.strftime('%Y-%m-%d')
            else:
                formatted_date = str(date)
        except:
            formatted_date = str(date)
    else:
        formatted_date = 'No date available'
    
    # Format authors
    if authors and isinstance(authors, list):
        authors_text = ', '.join(authors)
    elif authors and isinstance(authors, str):
        try:
            import json
            authors_list = json.loads(authors)
            authors_text = ', '.join(authors_list) if isinstance(authors_list, list) else authors
        except:
            authors_text = authors
    else:
        authors_text = 'No authors available'
    
    # Simulate HTML structure creation (without actual HTML generation)
    html_structure = {
        'title': title,
        'authors': authors_text,
        'date': formatted_date,
        'country': country,
        'summary': summary,
        'doi': doi
    }
    
    end_time = time.time()
    return (end_time - start_time) * 1000

def analyze_click_performance():
    """Analyze the complete click performance flow."""
    logger.info("Analyzing click performance...")
    
    # Step 1: Get data from API (simulate what frontend does)
    logger.info("Step 1: Fetching data from API...")
    start_time = time.time()
    # Test with 2D coordinates
    response = requests.get(f"{API_BASE_URL}/papers?fields=doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,country2,doi,doctrove_links&limit=5000")
    api_time = (time.time() - start_time) * 1000
    logger.info(f"API call time: {api_time:.2f}ms")
    
    if response.status_code != 200:
        logger.error("Failed to fetch data from API")
        return
    
    data = response.json()
    data_store = data.get('results', [])
    
    # Step 2: Measure data store processing
    logger.info("Step 2: Processing data store...")
    processing_metrics = measure_data_store_processing(data_store)
    for metric, value in processing_metrics.items():
        logger.info(f"  {metric}: {value:.2f}ms")
    
    # Step 3: Measure HTML generation
    logger.info("Step 3: Generating HTML...")
    html_time = measure_html_generation(data_store)
    logger.info(f"HTML generation time: {html_time:.2f}ms")
    
    # Step 4: Simulate click data processing
    logger.info("Step 4: Processing click data...")
    click_data = simulate_click_data()
    start_time = time.time()
    
    # Simulate the click callback logic
    if click_data and "points" in click_data and click_data["points"]:
        point = click_data["points"][0]
        if "customdata" in point and point["customdata"] is not None:
            point_index = int(point["customdata"][0])
            df = pd.DataFrame(data_store)
            if point_index < len(df):
                paper = df.iloc[point_index]
                # Process the paper data (this is what takes time)
                title = paper.get('Title') or paper.get('doctrove_title') or 'No title'
                summary = paper.get('Summary', 'No summary available')
                # ... more processing
    
    click_processing_time = (time.time() - start_time) * 1000
    logger.info(f"Click data processing time: {click_processing_time:.2f}ms")
    
    # Total time
    total_time = api_time + sum(processing_metrics.values()) + html_time + click_processing_time
    logger.info(f"Total estimated click response time: {total_time:.2f}ms")
    
    # Analysis
    logger.info("\nPerformance Analysis:")
    if total_time > 1000:
        logger.warning(f"Total time exceeds 1 second: {total_time:.2f}ms")
        if api_time > 500:
            logger.warning(f"API call is the main bottleneck: {api_time:.2f}ms")
        if html_time > 200:
            logger.warning(f"HTML generation is slow: {html_time:.2f}ms")
        if click_processing_time > 200:
            logger.warning(f"Click processing is slow: {click_processing_time:.2f}ms")
    else:
        logger.info("All operations are within acceptable time limits")
    
    # Data size analysis
    response_size_mb = len(str(data)) / (1024 * 1024)
    logger.info(f"Response size: {response_size_mb:.2f}MB")
    logger.info(f"Records in data store: {len(data_store)}")
    
    if response_size_mb > 10:
        logger.warning(f"Large response size may cause network delays: {response_size_mb:.2f}MB")

def main():
    """Run the click performance analysis."""
    try:
        analyze_click_performance()
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to services. Make sure they are running.")
    except Exception as e:
        logger.error(f"Error during analysis: {e}")

if __name__ == "__main__":
    main() 