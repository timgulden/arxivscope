#!/usr/bin/env python3
"""
Direct vector search performance test using a sample embedding
"""
import time
import psycopg2
import numpy as np

def test_vector_search_performance():
    """Test vector similarity search performance directly"""
    
    # Database connection
    conn_params = {
        'host': 'localhost',
        'port': 5434,
        'database': 'doctrove',
        'user': 'doctrove_admin',
        'password': 'doctrove_admin'
    }
    
    print("🔍 Direct Vector Search Performance Test")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # First, get a sample embedding to use for testing
        print("📊 Getting sample embedding for testing...")
        cursor.execute("""
            SELECT doctrove_embedding 
            FROM doctrove_papers 
            WHERE doctrove_embedding IS NOT NULL 
            LIMIT 1
        """)
        
        sample_embedding = cursor.fetchone()[0]
        print(f"✅ Got sample embedding with {len(sample_embedding)} dimensions")
        
        # Test different query sizes
        test_cases = [
            {"limit": 10, "name": "Small query (10 results)"},
            {"limit": 100, "name": "Medium query (100 results)"},
            {"limit": 1000, "name": "Large query (1000 results)"}
        ]
        
        for test_case in test_cases:
            limit = test_case["limit"]
            name = test_case["name"]
            
            print(f"\n🎯 {name}")
            
            # Test vector similarity search
            query = """
                SELECT doctrove_paper_id, doctrove_title,
                       (1 - (doctrove_embedding <=> %s)) as similarity_score
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL
                ORDER BY doctrove_embedding <=> %s
                LIMIT %s
            """
            
            start_time = time.time()
            cursor.execute(query, (sample_embedding, sample_embedding, limit))
            results = cursor.fetchall()
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            print(f"   ⏱️  Duration: {duration_ms:.2f}ms")
            print(f"   📊 Results: {len(results)} papers")
            
            if results:
                # Show top similarity scores
                print(f"   🎯 Top similarity scores:")
                for i, (paper_id, title, similarity) in enumerate(results[:3]):
                    title_short = title[:50] if title else "No title"
                    print(f"      {i+1}. {similarity:.3f} - {title_short}...")
            
            # Performance assessment
            if duration_ms < 100:
                print(f"   🚀 Performance: Excellent (<100ms)")
            elif duration_ms < 500:
                print(f"   ⚡ Performance: Good (<500ms)")
            elif duration_ms < 2000:
                print(f"   ⚠️  Performance: Acceptable (<2s)")
            else:
                print(f"   ❌ Performance: Poor (>2s)")
        
        # Test with different similarity thresholds
        print(f"\n🎯 Testing similarity threshold filtering...")
        
        threshold_tests = [
            {"threshold": 0.5, "name": "Low threshold (0.5)"},
            {"threshold": 0.7, "name": "Medium threshold (0.7)"},
            {"threshold": 0.9, "name": "High threshold (0.9)"}
        ]
        
        for test_case in threshold_tests:
            threshold = test_case["threshold"]
            name = test_case["name"]
            
            print(f"\n🎯 {name}")
            
            # Test with threshold filtering (this should be slower due to post-processing)
            query = """
                SELECT doctrove_paper_id, doctrove_title,
                       (1 - (doctrove_embedding <=> %s)) as similarity_score
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL
                ORDER BY doctrove_embedding <=> %s
                LIMIT 5000
            """
            
            start_time = time.time()
            cursor.execute(query, (sample_embedding, sample_embedding, 5000))
            all_results = cursor.fetchall()
            
            # Filter by threshold (simulating the API behavior)
            filtered_results = [r for r in all_results if r[2] >= threshold]
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            print(f"   ⏱️  Duration: {duration_ms:.2f}ms")
            print(f"   📊 Total results: {len(all_results)}")
            print(f"   📊 Filtered results: {len(filtered_results)}")
            print(f"   📊 Filter ratio: {len(filtered_results)/len(all_results)*100:.1f}%")
            
            if filtered_results:
                print(f"   🎯 Top filtered similarity scores:")
                for i, (paper_id, title, similarity) in enumerate(filtered_results[:3]):
                    title_short = title[:50] if title else "No title"
                    print(f"      {i+1}. {similarity:.3f} - {title_short}...")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"\n{'='*50}")
    print("🎯 Direct Vector Search Performance Test Complete")

if __name__ == "__main__":
    test_vector_search_performance()











