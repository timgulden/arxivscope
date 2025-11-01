#!/usr/bin/env python3
"""
Analyze author data availability patterns in OpenAlex metadata.
This will help us understand if first author is sufficient or if we need to look at other authors.
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any
from collections import defaultdict, Counter

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('.')

from db import create_connection_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_author_data_availability(connection_factory, sample_size: int = 10000):
    """Analyze patterns of country/institution data availability across author positions."""
    
    logger.info(f"🔍 Analyzing author data availability for {sample_size} papers...")
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Get sample of papers with authorships
            cur.execute("""
                SELECT openalex_raw_data 
                FROM openalex_metadata 
                WHERE openalex_raw_data IS NOT NULL 
                  AND openalex_raw_data != '{}' 
                  AND openalex_raw_data LIKE '%authorships%'
                ORDER BY RANDOM()
                LIMIT %s
            """, (sample_size,))
            
            results = cur.fetchall()
    
    # Analysis counters
    total_papers = len(results)
    author_position_stats = defaultdict(lambda: {
        'total': 0,
        'has_country': 0,
        'has_institution': 0,
        'has_both': 0,
        'has_neither': 0
    })
    
    # Paper-level analysis
    paper_stats = {
        'total': total_papers,
        'first_author_has_country': 0,
        'first_author_has_institution': 0,
        'first_author_has_both': 0,
        'first_author_has_neither': 0,
        'any_author_has_country': 0,
        'any_author_has_institution': 0,
        'any_author_has_both': 0,
        'no_author_has_data': 0
    }
    
    # Track when first author lacks data but others have it
    first_author_missing_but_others_have = {
        'country': 0,
        'institution': 0,
        'both': 0
    }
    
    for row in results:
        try:
            data = json.loads(row[0])
            authorships = data.get('authorships', [])
            
            if not authorships:
                continue
            
            # Track first author data
            first_author = authorships[0]
            first_has_country = len(first_author.get('countries', [])) > 0
            first_has_institution = len(first_author.get('institutions', [])) > 0
            first_has_both = first_has_country and first_has_institution
            first_has_neither = not first_has_country and not first_has_institution
            
            # Update paper stats
            if first_has_country:
                paper_stats['first_author_has_country'] += 1
            if first_has_institution:
                paper_stats['first_author_has_institution'] += 1
            if first_has_both:
                paper_stats['first_author_has_both'] += 1
            if first_has_neither:
                paper_stats['first_author_has_neither'] += 1
            
            # Check if any author has data
            any_has_country = any(len(auth.get('countries', [])) > 0 for auth in authorships)
            any_has_institution = any(len(auth.get('institutions', [])) > 0 for auth in authorships)
            any_has_both = any(len(auth.get('countries', [])) > 0 and len(auth.get('institutions', [])) > 0 for auth in authorships)
            
            if any_has_country:
                paper_stats['any_author_has_country'] += 1
            if any_has_institution:
                paper_stats['any_author_has_institution'] += 1
            if any_has_both:
                paper_stats['any_author_has_both'] += 1
            
            if not any_has_country and not any_has_institution:
                paper_stats['no_author_has_data'] += 1
            
            # Track when first author is missing data but others have it
            if not first_has_country and any_has_country:
                first_author_missing_but_others_have['country'] += 1
            if not first_has_institution and any_has_institution:
                first_author_missing_but_others_have['institution'] += 1
            if not first_has_both and any_has_both:
                first_author_missing_but_others_have['both'] += 1
            
            # Analyze each author position
            for i, authorship in enumerate(authorships):
                position = f"position_{i+1}"
                has_country = len(authorship.get('countries', [])) > 0
                has_institution = len(authorship.get('institutions', [])) > 0
                has_both = has_country and has_institution
                has_neither = not has_country and not has_institution
                
                author_position_stats[position]['total'] += 1
                if has_country:
                    author_position_stats[position]['has_country'] += 1
                if has_institution:
                    author_position_stats[position]['has_institution'] += 1
                if has_both:
                    author_position_stats[position]['has_both'] += 1
                if has_neither:
                    author_position_stats[position]['has_neither'] += 1
                    
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Error processing paper: {e}")
            continue
    
    # Calculate percentages
    def calculate_percentage(count, total):
        return (count / total * 100) if total > 0 else 0
    
    logger.info(f"\n📊 ANALYSIS RESULTS (Sample: {total_papers} papers)")
    logger.info("=" * 60)
    
    # Paper-level summary
    logger.info(f"\n📋 PAPER-LEVEL SUMMARY:")
    logger.info(f"   Total papers analyzed: {total_papers}")
    logger.info(f"   First author has country: {paper_stats['first_author_has_country']} ({calculate_percentage(paper_stats['first_author_has_country'], total_papers):.1f}%)")
    logger.info(f"   First author has institution: {paper_stats['first_author_has_institution']} ({calculate_percentage(paper_stats['first_author_has_institution'], total_papers):.1f}%)")
    logger.info(f"   First author has both: {paper_stats['first_author_has_both']} ({calculate_percentage(paper_stats['first_author_has_both'], total_papers):.1f}%)")
    logger.info(f"   First author has neither: {paper_stats['first_author_has_neither']} ({calculate_percentage(paper_stats['first_author_has_neither'], total_papers):.1f}%)")
    
    logger.info(f"\n   Any author has country: {paper_stats['any_author_has_country']} ({calculate_percentage(paper_stats['any_author_has_country'], total_papers):.1f}%)")
    logger.info(f"   Any author has institution: {paper_stats['any_author_has_institution']} ({calculate_percentage(paper_stats['any_author_has_institution'], total_papers):.1f}%)")
    logger.info(f"   Any author has both: {paper_stats['any_author_has_both']} ({calculate_percentage(paper_stats['any_author_has_both'], total_papers):.1f}%)")
    logger.info(f"   No author has data: {paper_stats['no_author_has_data']} ({calculate_percentage(paper_stats['no_author_has_data'], total_papers):.1f}%)")
    
    # Key insight: when first author is missing data but others have it
    logger.info(f"\n🔑 KEY INSIGHT - First Author Missing But Others Have:")
    logger.info(f"   Country data: {first_author_missing_but_others_have['country']} papers ({calculate_percentage(first_author_missing_but_others_have['country'], total_papers):.1f}%)")
    logger.info(f"   Institution data: {first_author_missing_but_others_have['institution']} papers ({calculate_percentage(first_author_missing_but_others_have['institution'], total_papers):.1f}%)")
    logger.info(f"   Both: {first_author_missing_but_others_have['both']} papers ({calculate_percentage(first_author_missing_but_others_have['both'], total_papers):.1f}%)")
    
    # Author position breakdown
    logger.info(f"\n👥 AUTHOR POSITION BREAKDOWN:")
    for position in sorted(author_position_stats.keys()):
        stats = author_position_stats[position]
        if stats['total'] > 0:
            logger.info(f"   {position}:")
            logger.info(f"     - Total authors: {stats['total']}")
            logger.info(f"     - Has country: {stats['has_country']} ({calculate_percentage(stats['has_country'], stats['total']):.1f}%)")
            logger.info(f"     - Has institution: {stats['has_institution']} ({calculate_percentage(stats['has_institution'], stats['total']):.1f}%)")
            logger.info(f"     - Has both: {stats['has_both']} ({calculate_percentage(stats['has_both'], stats['total']):.1f}%)")
            logger.info(f"     - Has neither: {stats['has_neither']} ({calculate_percentage(stats['has_neither'], stats['total']):.1f}%)")
    
    # Recommendations
    logger.info(f"\n💡 RECOMMENDATIONS:")
    
    first_author_country_coverage = calculate_percentage(paper_stats['first_author_has_country'], total_papers)
    first_author_institution_coverage = calculate_percentage(paper_stats['first_author_has_institution'], total_papers)
    
    if first_author_country_coverage < 80:
        logger.info(f"   ⚠️  First author country coverage is only {first_author_country_coverage:.1f}%")
        logger.info(f"   📈 Looking at other authors could increase coverage by {calculate_percentage(first_author_missing_but_others_have['country'], total_papers):.1f}%")
        logger.info(f"   🎯 RECOMMENDED: Extract country data from ANY author, not just first")
    else:
        logger.info(f"   ✅ First author country coverage is good: {first_author_country_coverage:.1f}%")
        logger.info(f"   🎯 RECOMMENDED: First author approach is sufficient")
    
    if first_author_institution_coverage < 80:
        logger.info(f"   ⚠️  First author institution coverage is only {first_author_institution_coverage:.1f}%")
        logger.info(f"   📈 Looking at other authors could increase coverage by {calculate_percentage(first_author_missing_but_others_have['institution'], total_papers):.1f}%")
        logger.info(f"   🎯 RECOMMENDED: Extract institution data from ANY author, not just first")
    else:
        logger.info(f"   ✅ First author institution coverage is good: {first_author_institution_coverage:.1f}%")
        logger.info(f"   🎯 RECOMMENDED: First author approach is sufficient")
    
    return {
        'paper_stats': paper_stats,
        'author_position_stats': dict(author_position_stats),
        'first_author_missing_but_others_have': first_author_missing_but_others_have
    }

def main():
    """Main function to run the analysis."""
    logger.info("🚀 Starting author data availability analysis...")
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Run analysis with 10K sample
    results = analyze_author_data_availability(connection_factory, sample_size=10000)
    
    logger.info("\n🎉 Analysis complete!")
    logger.info("💡 Use these insights to decide whether first author is sufficient or if you need to look at all authors")

if __name__ == "__main__":
    main()


