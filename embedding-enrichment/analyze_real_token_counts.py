#!/usr/bin/env python3
"""
Analyze real token counts from actual titles and abstracts in the database.
"""

import os
import sys
import psycopg2
import tiktoken
from datetime import datetime

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

# Import database connection from doctrove-api
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """Count tokens using tiktoken for the specified model."""
    try:
        # For text-embedding-3-small, use cl100k_base encoding
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error counting tokens: {e}")
        # Fallback: rough estimate (1 token ≈ 4 characters for English)
        return len(text) // 4

def analyze_real_token_counts():
    """Analyze token counts from actual database content."""
    try:
        with psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
            options='-c statement_timeout=30000'  # 30 second timeout
        ) as conn:
            with conn.cursor() as cur:
                # Get a sample of real titles and abstracts
                cur.execute("""
                    SELECT doctrove_title, doctrove_abstract 
                    FROM doctrove_papers 
                    WHERE doctrove_title IS NOT NULL 
                    AND doctrove_abstract IS NOT NULL 
                    AND doctrove_title != ''
                    AND doctrove_abstract != ''
                    LIMIT 100;
                """)
                
                results = cur.fetchall()
                
                if not results:
                    print("No data found")
                    return
                
                print(f"Analyzing {len(results)} real papers from database...")
                print("=" * 60)
                
                title_tokens = []
                abstract_tokens = []
                total_tokens = []
                
                for i, (title, abstract) in enumerate(results[:10], 1):  # Show first 10
                    title_token_count = count_tokens(title)
                    abstract_token_count = count_tokens(abstract)
                    total_token_count = title_token_count + abstract_token_count
                    
                    title_tokens.append(title_token_count)
                    abstract_tokens.append(abstract_token_count)
                    total_tokens.append(total_token_count)
                    
                    print(f"\nPaper {i}:")
                    print(f"  Title: '{title[:80]}{'...' if len(title) > 80 else ''}'")
                    print(f"  Title tokens: {title_token_count}")
                    print(f"  Abstract: '{abstract[:100]}{'...' if len(abstract) > 100 else ''}'")
                    print(f"  Abstract tokens: {abstract_token_count}")
                    print(f"  Total tokens: {total_token_count}")
                
                # Calculate statistics for all 100 papers
                for title, abstract in results:
                    title_token_count = count_tokens(title)
                    abstract_token_count = count_tokens(abstract)
                    total_token_count = title_token_count + abstract_token_count
                    
                    title_tokens.append(title_token_count)
                    abstract_tokens.append(abstract_token_count)
                    total_tokens.append(total_token_count)
                
                # Calculate statistics
                avg_title_tokens = sum(title_tokens) / len(title_tokens)
                avg_abstract_tokens = sum(abstract_tokens) / len(abstract_tokens)
                avg_total_tokens = sum(total_tokens) / len(total_tokens)
                
                min_title = min(title_tokens)
                max_title = max(title_tokens)
                min_abstract = min(abstract_tokens)
                max_abstract = max(abstract_tokens)
                min_total = min(total_tokens)
                max_total = max(total_tokens)
                
                print(f"\n" + "=" * 60)
                print(f"STATISTICS FOR {len(results)} REAL PAPERS")
                print("=" * 60)
                print(f"Title tokens:")
                print(f"  Average: {avg_title_tokens:.1f}")
                print(f"  Range: {min_title} - {max_title}")
                print(f"  Median: {sorted(title_tokens)[len(title_tokens)//2]:.1f}")
                
                print(f"\nAbstract tokens:")
                print(f"  Average: {avg_abstract_tokens:.1f}")
                print(f"  Range: {min_abstract} - {max_abstract}")
                print(f"  Median: {sorted(abstract_tokens)[len(abstract_tokens)//2]:.1f}")
                
                print(f"\nTotal tokens per paper:")
                print(f"  Average: {avg_total_tokens:.1f}")
                print(f"  Range: {min_total} - {max_total}")
                print(f"  Median: {sorted(total_tokens)[len(total_tokens)//2]:.1f}")
                
                return avg_title_tokens, avg_abstract_tokens, avg_total_tokens
                
    except Exception as e:
        print(f"Database error: {e}")
        return None

def calculate_real_costs(avg_total_tokens):
    """Calculate costs based on real token counts."""
    print(f"\n" + "=" * 60)
    print(f"COST CALCULATION BASED ON REAL DATA")
    print("=" * 60)
    
    # Azure OpenAI pricing for text-embedding-3-small (as of 2024)
    cost_per_1k_tokens = 0.00002
    
    # Cost per paper
    cost_per_paper = (avg_total_tokens / 1000) * cost_per_1k_tokens
    
    print(f"Cost per 1K tokens: ${cost_per_1k_tokens}")
    print(f"Average tokens per paper: {avg_total_tokens:.1f}")
    print(f"Cost per paper: ${cost_per_paper:.6f}")
    
    # Scale up
    scales = [1000, 10000, 100000, 1000000, 5000000, 10000000, 20000000]
    
    print(f"\nCOST AT SCALE:")
    for scale in scales:
        total_cost = scale * cost_per_paper
        print(f"{scale:,} papers: ${total_cost:.2f}")
    
    # Compare with previous estimate
    old_estimate = 68  # tokens from test cases
    old_cost_per_paper = (old_estimate / 1000) * cost_per_1k_tokens
    old_total_cost = 20000000 * old_cost_per_paper
    
    real_total_cost = 20000000 * cost_per_paper
    
    print(f"\nCOMPARISON:")
    print(f"Previous estimate (test cases): {old_estimate} tokens = ${old_total_cost:.2f}")
    print(f"Real estimate (database): {avg_total_tokens:.1f} tokens = ${real_total_cost:.2f}")
    print(f"Difference: ${abs(real_total_cost - old_total_cost):.2f}")
    print(f"Real cost is {real_total_cost/old_total_cost:.1f}x higher than estimated")

def main():
    """Main function."""
    print("🔍 Real Token Count Analysis")
    print("=" * 60)
    
    # Analyze real token counts
    result = analyze_real_token_counts()
    
    if result:
        title_tokens, abstract_tokens, total_tokens = result
        
        # Calculate costs
        calculate_real_costs(total_tokens)
        
        # Write report
        with open("real_token_analysis_report.txt", "w") as f:
            f.write(f"Real Token Analysis Report - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis based on 100 real papers from database\n")
            f.write(f"Average title tokens: {title_tokens:.1f}\n")
            f.write(f"Average abstract tokens: {abstract_tokens:.1f}\n")
            f.write(f"Average total tokens per paper: {total_tokens:.1f}\n")
            f.write(f"Cost per paper: ${(total_tokens / 1000) * 0.00002:.6f}\n")
            f.write(f"Cost for 20M papers: ${20000000 * (total_tokens / 1000) * 0.00002:.2f}\n")
    
    else:
        print("❌ Failed to analyze token counts")

if __name__ == "__main__":
    main()


