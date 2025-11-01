#!/usr/bin/env python3
"""
Health check module for the enrichment service.
Provides functions to verify the enrichment system is running and responsive.
"""

import sys
import os
import logging
import time
import psycopg2
from typing import Dict, Any, Optional
import json

# Add paths for imports
sys.path.append('../doctrove-api')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connectivity() -> Dict[str, Any]:
    """Check if we can connect to the database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def check_event_listener_process() -> Dict[str, Any]:
    """Check if the event listener process is running."""
    try:
        import subprocess
        result = subprocess.run(
            ['pgrep', '-f', 'event_listener.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return {
                "status": "healthy",
                "message": f"Event listener running (PIDs: {', '.join(pids)})",
                "pids": pids,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Event listener process not found",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Failed to check event listener process: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def check_database_triggers() -> Dict[str, Any]:
    """Check if the database triggers for enrichment are properly installed."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Check if triggers exist
            cur.execute("""
                SELECT trigger_name 
                FROM information_schema.triggers 
                WHERE trigger_name IN ('trigger_paper_added', 'trigger_embedding_ready', 'trigger_projection_ready')
                AND event_object_table = 'doctrove_papers'
            """)
            
            triggers = [row[0] for row in cur.fetchall()]
            expected_triggers = ['trigger_paper_added', 'trigger_embedding_ready', 'trigger_projection_ready']
            
            missing_triggers = set(expected_triggers) - set(triggers)
            
            if not missing_triggers:
                return {
                    "status": "healthy",
                    "message": "All enrichment triggers are installed",
                    "triggers": triggers,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Missing triggers: {list(missing_triggers)}",
                    "installed_triggers": triggers,
                    "missing_triggers": list(missing_triggers),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Failed to check database triggers: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def check_embedding_status() -> Dict[str, Any]:
    """Check the status of embeddings in the database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Get counts
            cur.execute("SELECT COUNT(*) FROM doctrove_papers")
            total_papers = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL")
            papers_with_embeddings = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding_2d IS NOT NULL")
            papers_with_2d_embeddings = cur.fetchone()[0]
            
            # Calculate percentages
            embedding_coverage = (papers_with_embeddings / total_papers * 100) if total_papers > 0 else 0
            embedding_2d_coverage = (papers_with_2d_embeddings / total_papers * 100) if total_papers > 0 else 0
            
            return {
                "status": "healthy",
                "total_papers": total_papers,
                "papers_with_embeddings": papers_with_embeddings,
                "papers_with_2d_embeddings": papers_with_2d_embeddings,
                "embedding_coverage_percent": round(embedding_coverage, 2),
                "embedding_2d_coverage_percent": round(embedding_2d_coverage, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def comprehensive_health_check() -> Dict[str, Any]:
    """Perform a comprehensive health check of the enrichment system."""
    logger.debug("Starting comprehensive enrichment health check...")
    
    checks = {
        "database_connectivity": check_database_connectivity(),
        "event_listener_process": check_event_listener_process(),
        "database_triggers": check_database_triggers(),
        "embedding_status": check_embedding_status()
    }
    
    # Determine overall status
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    overall_status = {
        "service": "enrichment",
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": checks
    }
    
    logger.debug(f"Health check completed. Overall status: {overall_status['status']}")
    return overall_status

def main():
    """Main entry point for health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrichment service health check')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--check', choices=['all', 'database', 'process', 'triggers', 'embeddings'],
                       default='all', help='Specific check to run (default: all)')
    
    args = parser.parse_args()
    
    if args.check == 'all':
        result = comprehensive_health_check()
    elif args.check == 'database':
        result = check_database_connectivity()
    elif args.check == 'process':
        result = check_event_listener_process()
    elif args.check == 'triggers':
        result = check_database_triggers()
    elif args.check == 'embeddings':
        result = check_embedding_status()
    else:
        print("Invalid check type")
        sys.exit(1)
    
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Text format
        print(f"Service: enrichment")
        print(f"Status: {result['status']}")
        print(f"Timestamp: {result['timestamp']}")
        if 'checks' in result:
            for check_name, check_result in result['checks'].items():
                print(f"\n{check_name}:")
                print(f"  Status: {check_result['status']}")
                print(f"  Message: {check_result['message']}")
        else:
            print(f"Message: {result['message']}")
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'healthy' else 1)

if __name__ == "__main__":
    main() 