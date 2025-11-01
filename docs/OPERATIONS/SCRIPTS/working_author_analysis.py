#!/usr/bin/env python3
"""
Working author analysis script to analyze data availability patterns.
"""

import sys
sys.path.append('doctrove-api')

from db import create_connection_factory
import json
from collections import defaultdict

def analyze_author_patterns():
    """Analyze patterns of country/institution data availability across author positions."""
    
    print("🔍 Starting author data availability analysis...")
    
    try:
        connection_factory = create_connection_factory()
        print("✅ Connection factory created")
        
        with connection_factory() as conn:
            print("✅ Database connection established")
            
            with conn.cursor() as cur:
                print("✅ Cursor created")
                
                # Get sample of papers
                print("🔍 Fetching sample papers...")
                cur.execute("""
                    SELECT openalex_raw_data 
                    FROM openalex_metadata 
                    WHERE openalex_raw_data IS NOT NULL 
                      AND openalex_raw_data != '{}' 
                      AND openalex_raw_data LIKE '%authorships%'
                    ORDER BY RANDOM()
                    LIMIT 1000
                """)
                
                results = cur.fetchall()
                print(f"✅ Fetched {len(results)} papers")
                
                # Analysis counters
                total_papers = len(results)
                paper_stats = {
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
                
                # Author position breakdown
                author_positions = defaultdict(lambda: {
                    'total': 0,
                    'has_country': 0,
                    'has_institution': 0,
                    'has_both': 0,
                    'has_neither': 0
                })
                
                print("🔍 Processing papers...")
                
                for i, row in enumerate(results):
                    if i % 100 == 0:
                        print(f"   Processed {i}/{total_papers} papers...")
                    
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
                        for j, authorship in enumerate(authorships):
                            position = f"position_{j+1}"
                            has_country = len(authorship.get('countries', [])) > 0
                            has_institution = len(authorship.get('institutions', [])) > 0
                            has_both = has_country and has_institution
                            has_neither = not has_country and not has_institution
                            
                            author_positions[position]['total'] += 1
                            if has_country:
                                author_positions[position]['has_country'] += 1
                            if has_institution:
                                author_positions[position]['has_institution'] += 1
                            if has_both:
                                author_positions[position]['has_both'] += 1
                            if has_neither:
                                author_positions[position]['has_neither'] += 1
                                
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        continue
                
                print("✅ Analysis complete!")
                
                # Calculate percentages
                def calc_pct(count, total):
                    return (count / total * 100) if total > 0 else 0
                
                # Results
                print(f"\n📊 ANALYSIS RESULTS (Sample: {total_papers} papers)")
                print("=" * 60)
                
                print(f"\n📋 PAPER-LEVEL SUMMARY:")
                print(f"   Total papers analyzed: {total_papers}")
                print(f"   First author has country: {paper_stats['first_author_has_country']} ({calc_pct(paper_stats['first_author_has_country'], total_papers):.1f}%)")
                print(f"   First author has institution: {paper_stats['first_author_has_institution']} ({calc_pct(paper_stats['first_author_has_institution'], total_papers):.1f}%)")
                print(f"   First author has both: {paper_stats['first_author_has_both']} ({calc_pct(paper_stats['first_author_has_both'], total_papers):.1f}%)")
                print(f"   First author has neither: {paper_stats['first_author_has_neither']} ({calc_pct(paper_stats['first_author_has_neither'], total_papers):.1f}%)")
                
                print(f"\n   Any author has country: {paper_stats['any_author_has_country']} ({calc_pct(paper_stats['any_author_has_country'], total_papers):.1f}%)")
                print(f"   Any author has institution: {paper_stats['any_author_has_institution']} ({calc_pct(paper_stats['any_author_has_institution'], total_papers):.1f}%)")
                print(f"   Any author has both: {paper_stats['any_author_has_both']} ({calc_pct(paper_stats['any_author_has_both'], total_papers):.1f}%)")
                print(f"   No author has data: {paper_stats['no_author_has_data']} ({calc_pct(paper_stats['no_author_has_data'], total_papers):.1f}%)")
                
                print(f"\n🔑 KEY INSIGHT - First Author Missing But Others Have:")
                print(f"   Country data: {first_author_missing_but_others_have['country']} papers ({calc_pct(first_author_missing_but_others_have['country'], total_papers):.1f}%)")
                print(f"   Institution data: {first_author_missing_but_others_have['institution']} papers ({calc_pct(first_author_missing_but_others_have['institution'], total_papers):.1f}%)")
                print(f"   Both: {first_author_missing_but_others_have['both']} papers ({calc_pct(first_author_missing_but_others_have['both'], total_papers):.1f}%)")
                
                print(f"\n👥 AUTHOR POSITION BREAKDOWN:")
                for position in sorted(author_positions.keys()):
                    stats = author_positions[position]
                    if stats['total'] > 0:
                        print(f"   {position}:")
                        print(f"     - Total authors: {stats['total']}")
                        print(f"     - Has country: {stats['has_country']} ({calc_pct(stats['has_country'], stats['total']):.1f}%)")
                        print(f"     - Has institution: {stats['has_institution']} ({calc_pct(stats['has_institution'], stats['total']):.1f}%)")
                        print(f"     - Has both: {stats['has_both']} ({calc_pct(stats['has_both'], stats['total']):.1f}%)")
                        print(f"     - Has neither: {stats['has_neither']} ({calc_pct(stats['has_neither'], stats['total']):.1f}%)")
                
                # Recommendations
                print(f"\n💡 RECOMMENDATIONS:")
                
                first_author_country_coverage = calc_pct(paper_stats['first_author_has_country'], total_papers)
                first_author_institution_coverage = calc_pct(paper_stats['first_author_has_institution'], total_papers)
                
                if first_author_country_coverage < 80:
                    print(f"   ⚠️  First author country coverage is only {first_author_country_coverage:.1f}%")
                    print(f"   📈 Looking at other authors could increase coverage by {calc_pct(first_author_missing_but_others_have['country'], total_papers):.1f}%")
                    print(f"   🎯 RECOMMENDED: Extract country data from ANY author, not just first")
                else:
                    print(f"   ✅ First author country coverage is good: {first_author_country_coverage:.1f}%")
                    print(f"   🎯 RECOMMENDED: First author approach is sufficient")
                
                if first_author_institution_coverage < 80:
                    print(f"   ⚠️  First author institution coverage is only {first_author_institution_coverage:.1f}%")
                    print(f"   📈 Looking at other authors could increase coverage by {calc_pct(first_author_missing_but_others_have['institution'], total_papers):.1f}%")
                    print(f"   🎯 RECOMMENDED: Extract institution data from ANY author, not just first")
                else:
                    print(f"   ✅ First author institution coverage is good: {first_author_institution_coverage:.1f}%")
                    print(f"   🎯 RECOMMENDED: First author approach is sufficient")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_author_patterns()
