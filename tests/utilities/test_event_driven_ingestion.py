#!/usr/bin/env python3
"""
Test script to manually insert papers and test the event-driven enrichment system.
"""

import sys
import os
import uuid
from datetime import date
import psycopg2

# Add paths for imports
sys.path.append('doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def create_test_papers():
    """Create a few test papers to trigger the event-driven enrichment system."""
    
    # Database connection parameters
    connection_params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
    
    # Test papers data
    test_papers = [
        {
            'doctrove_paper_id': str(uuid.uuid4()),
            'doctrove_source': 'test',
            'doctrove_source_id': 'test-001',
            'doctrove_title': 'Machine Learning Applications in Healthcare',
            'doctrove_abstract': 'This paper explores the use of machine learning techniques in healthcare applications, including diagnosis, treatment planning, and patient monitoring.',
            'doctrove_authors': ['Dr. Smith', 'Dr. Johnson'],
            'doctrove_primary_date': date(2024, 1, 15),
            'doctrove_title_embedding': None,  # Will trigger embedding generation
            'doctrove_abstract_embedding': None,  # Will trigger embedding generation
            'embedding_model_version': None,
            'doctrove_embedding_2d': None,
            'doctrove_embedding_2d': None,
            'created_at': None,
            'updated_at': None
        },
        {
            'doctrove_paper_id': str(uuid.uuid4()),
            'doctrove_source': 'test',
            'doctrove_source_id': 'test-002',
            'doctrove_title': 'Natural Language Processing for Scientific Literature',
            'doctrove_abstract': 'A comprehensive study of NLP techniques applied to scientific literature analysis, including text mining, summarization, and knowledge extraction.',
            'doctrove_authors': ['Prof. Brown', 'Dr. Davis'],
            'doctrove_primary_date': date(2024, 2, 20),
            'doctrove_title_embedding': None,
            'doctrove_abstract_embedding': None,
            'embedding_model_version': None,
            'doctrove_embedding_2d': None,
            'doctrove_embedding_2d': None,
            'created_at': None,
            'updated_at': None
        },
        {
            'doctrove_paper_id': str(uuid.uuid4()),
            'doctrove_source': 'test',
            'doctrove_source_id': 'test-003',
            'doctrove_title': 'Computer Vision in Autonomous Vehicles',
            'doctrove_abstract': 'This research examines computer vision algorithms for autonomous vehicle navigation, including object detection, lane recognition, and obstacle avoidance.',
            'doctrove_authors': ['Dr. Wilson', 'Prof. Taylor'],
            'doctrove_primary_date': date(2024, 3, 10),
            'doctrove_title_embedding': None,
            'doctrove_abstract_embedding': None,
            'embedding_model_version': None,
            'doctrove_embedding_2d': None,
            'doctrove_embedding_2d': None,
            'created_at': None,
            'updated_at': None
        }
    ]
    
    try:
        # Connect to database
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                
                # Insert test papers
                for paper in test_papers:
                    cur.execute("""
                        INSERT INTO doctrove_papers (
                            doctrove_paper_id, doctrove_source, doctrove_source_id,
                            doctrove_title, doctrove_abstract, doctrove_authors,
                            doctrove_primary_date, doctrove_title_embedding,
                            doctrove_abstract_embedding, embedding_model_version,
                            doctrove_embedding_2d,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        paper['doctrove_paper_id'], paper['doctrove_source'],
                        paper['doctrove_source_id'], paper['doctrove_title'],
                        paper['doctrove_abstract'], paper['doctrove_authors'],
                        paper['doctrove_primary_date'], paper['doctrove_title_embedding'],
                        paper['doctrove_abstract_embedding'], paper['embedding_model_version'],
                        paper['doctrove_embedding_2d'],
                        paper['created_at'], paper['updated_at']
                    ))
                    
                    print(f"Inserted paper: {paper['doctrove_title']} (ID: {paper['doctrove_paper_id']})")
                
                conn.commit()
                print(f"\nSuccessfully inserted {len(test_papers)} test papers")
                print("These should trigger the event-driven enrichment system!")
                
    except Exception as e:
        print(f"Error inserting test papers: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing Event-Driven Enrichment System")
    print("=" * 50)
    
    success = create_test_papers()
    
    if success:
        print("\n✅ Test papers inserted successfully!")
        print("The event listener should now trigger embedding generation for these papers.")
        print("Check the event listener logs to see the enrichment process in action.")
    else:
        print("\n❌ Failed to insert test papers")
        sys.exit(1) 