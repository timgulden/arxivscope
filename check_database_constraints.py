#!/usr/bin/env python3
"""
Check for database constraints, triggers, or other issues that might be preventing the massive ingestion.
"""

import psycopg2

def check_database_constraints():
    """Check for database issues that might prevent ingestion."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            print("🔍 Checking database constraints and triggers...")
            print("=" * 60)
            
            # Check table structure
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'doctrove_papers'
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            print(f"📋 Table structure for doctrove_papers:")
            for col_name, data_type, nullable, default in columns:
                print(f"  {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'} {f'DEFAULT {default}' if default else ''}")
            print()
            
            # Check for triggers
            cur.execute("""
                SELECT trigger_name, event_manipulation, action_statement
                FROM information_schema.triggers 
                WHERE event_object_table = 'doctrove_papers'
            """)
            
            triggers = cur.fetchall()
            print(f"🔧 Triggers on doctrove_papers:")
            if triggers:
                for trigger_name, event, action in triggers:
                    print(f"  {trigger_name}: {event} -> {action[:100]}...")
            else:
                print("  No triggers found")
            print()
            
            # Check for constraints
            cur.execute("""
                SELECT constraint_name, constraint_type, is_deferrable, initially_deferred
                FROM information_schema.table_constraints 
                WHERE table_name = 'doctrove_papers'
            """)
            
            constraints = cur.fetchall()
            print(f"🔒 Constraints on doctrove_papers:")
            for constraint_name, constraint_type, deferrable, deferred in constraints:
                print(f"  {constraint_name}: {constraint_type} {'DEFERRABLE' if deferrable == 'YES' else 'NOT DEFERRABLE'} {'INITIALLY DEFERRED' if deferred == 'YES' else 'INITIALLY IMMEDIATE'}")
            print()
            
            # Check for foreign key constraints
            cur.execute("""
                SELECT 
                    tc.constraint_name, 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='doctrove_papers'
            """)
            
            foreign_keys = cur.fetchall()
            print(f"🔗 Foreign key constraints:")
            if foreign_keys:
                for constraint_name, table_name, column_name, foreign_table, foreign_column in foreign_keys:
                    print(f"  {constraint_name}: {table_name}.{column_name} -> {foreign_table}.{foreign_column}")
            else:
                print("  No foreign key constraints found")
            print()
            
            # Check for unique constraints
            cur.execute("""
                SELECT 
                    tc.constraint_name, 
                    kcu.column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'UNIQUE' 
                AND tc.table_name='doctrove_papers'
            """)
            
            unique_constraints = cur.fetchall()
            print(f"🔐 Unique constraints:")
            if unique_constraints:
                for constraint_name, column_name in unique_constraints:
                    print(f"  {constraint_name}: {column_name}")
            else:
                print("  No unique constraints found")
            print()
            
            # Check table size and growth
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE tablename = 'doctrove_papers'
                AND attname IN ('doctrove_paper_id', 'doctrove_title', 'created_at')
            """)
            
            stats = cur.fetchall()
            print(f"📊 Table statistics:")
            for schema, table, column, distinct, correlation in stats:
                print(f"  {column}: {distinct} distinct values, correlation: {correlation}")
            print()
            
            # Check for any recent errors in PostgreSQL logs (if accessible)
            print(f"🔍 Checking for potential issues...")
            
            # Test a simple insert to see if there are any immediate constraints
            try:
                cur.execute("""
                    INSERT INTO doctrove_papers (doctrove_paper_id, doctrove_title, doctrove_source, doctrove_source_id, created_at, updated_at)
                    VALUES (gen_random_uuid(), 'Test Paper', 'openalex', 'test-123', NOW(), NOW())
                    ON CONFLICT (doctrove_source, doctrove_source_id) DO NOTHING
                """)
                conn.commit()
                print("  ✅ Test insert succeeded - basic constraints are working")
                
                # Clean up test record
                cur.execute("DELETE FROM doctrove_papers WHERE doctrove_source_id = 'test-123'")
                conn.commit()
                print("  🧹 Test record cleaned up")
                
            except Exception as e:
                print(f"  ❌ Test insert failed: {e}")
                conn.rollback()
            
            # Check if there are any locks or long-running transactions
            cur.execute("""
                SELECT 
                    pid, 
                    usename, 
                    application_name,
                    state,
                    query_start,
                    state_change,
                    query
                FROM pg_stat_activity 
                WHERE state != 'idle'
                AND query NOT LIKE '%pg_stat_activity%'
            """)
            
            active_queries = cur.fetchall()
            print(f"\n🔄 Active database queries:")
            if active_queries:
                for pid, user, app, state, start, change, query in active_queries:
                    print(f"  PID {pid} ({user}): {state} - {query[:80]}...")
            else:
                print("  No active queries found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_constraints()
