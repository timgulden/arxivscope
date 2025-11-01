"""
Advanced SQL Query Analyzer for DocTrove API
Captures detailed query information including execution plans, timing, and index usage.
"""

import time
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from functools import wraps
import hashlib

# Configure logging
logger = logging.getLogger('query_analyzer')
logger.setLevel(logging.DEBUG)

# Create file handler for query analysis
file_handler = logging.FileHandler('/tmp/doctrove_query_analysis.log')
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

class QueryAnalyzer:
    """Advanced query analyzer that captures execution plans and performance metrics."""
    
    def __init__(self, connection_factory):
        self.connection_factory = connection_factory
        self.query_cache = {}
        
    def analyze_query(self, query: str, params: List[Any] = None, 
                     operation: str = "unknown", capture_plan: bool = True) -> Dict[str, Any]:
        """
        Execute a query and capture detailed analysis including execution plan.
        
        Args:
            query: SQL query to analyze
            params: Query parameters
            operation: Operation name for logging
            capture_plan: Whether to capture execution plan
            
        Returns:
            Dictionary with query analysis results
        """
        start_time = time.time()
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        
        # Log query start
        logger.info(f"🔍 QUERY_START: {operation} (hash: {query_hash})")
        logger.info(f"🔍 QUERY_SQL: {query[:200]}...")
        logger.info(f"🔍 QUERY_PARAMS: {len(params) if params else 0} parameters")
        
        analysis = {
            'query_hash': query_hash,
            'operation': operation,
            'query': query,
            'params': params,
            'start_time': datetime.now().isoformat(),
            'execution_plan': None,
            'index_usage': [],
            'performance_issues': [],
            'warnings': [],
            'result_count': 0,
            'execution_time_ms': 0,
            'error': None
        }
        
        try:
            with self.connection_factory() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Execute the query
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    # Capture execution plan if requested
                    if capture_plan:
                        try:
                            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                            cur.execute(explain_query, params)
                            plan_result = cur.fetchone()
                            if plan_result and 'EXPLAIN' in plan_result:
                                analysis['execution_plan'] = plan_result['EXPLAIN'][0]
                                self._analyze_execution_plan(analysis)
                        except Exception as e:
                            analysis['warnings'].append(f"Failed to capture execution plan: {e}")
                    
                    analysis['result_count'] = len(results)
                    analysis['results'] = [dict(row) for row in results]
                    
        except Exception as e:
            analysis['error'] = str(e)
            logger.error(f"❌ QUERY_ERROR: {operation} failed with error: {e}")
            
        end_time = time.time()
        analysis['execution_time_ms'] = (end_time - start_time) * 1000
        analysis['end_time'] = datetime.now().isoformat()
        
        # Log completion
        logger.info(f"✅ QUERY_COMPLETE: {operation} took {analysis['execution_time_ms']:.2f}ms, returned {analysis['result_count']} results")
        
        # Log performance issues
        if analysis['performance_issues']:
            logger.warning(f"⚠️ PERFORMANCE_ISSUES: {operation} has {len(analysis['performance_issues'])} issues")
            for issue in analysis['performance_issues']:
                logger.warning(f"⚠️ ISSUE: {issue}")
        
        # Save analysis to file for later review
        self._save_analysis(analysis)
        
        return analysis
    
    def _analyze_execution_plan(self, analysis: Dict[str, Any]):
        """Analyze execution plan for performance issues and index usage."""
        if not analysis['execution_plan']:
            return
            
        plan = analysis['execution_plan']
        
        # Check for index usage
        self._check_index_usage(plan, analysis)
        
        # Check for performance issues
        self._check_performance_issues(plan, analysis)
        
        # Check for sequential scans
        self._check_sequential_scans(plan, analysis)
        
        # Check for expensive operations
        self._check_expensive_operations(plan, analysis)
    
    def _check_index_usage(self, plan: Dict[str, Any], analysis: Dict[str, Any]):
        """Check if indexes are being used effectively."""
        def traverse_plan(node, path=""):
            node_type = node.get('Node Type', '')
            
            if 'Index' in node_type:
                index_name = node.get('Index Name', 'unknown')
                analysis['index_usage'].append({
                    'type': node_type,
                    'name': index_name,
                    'path': path,
                    'cost': node.get('Total Cost', 0),
                    'rows': node.get('Actual Rows', 0)
                })
                logger.info(f"📊 INDEX_USED: {index_name} ({node_type})")
            
            # Recursively check child nodes
            if 'Plans' in node:
                for i, child in enumerate(node['Plans']):
                    traverse_plan(child, f"{path}.{i}")
        
        traverse_plan(plan)
    
    def _check_performance_issues(self, plan: Dict[str, Any], analysis: Dict[str, Any]):
        """Check for common performance issues."""
        def traverse_plan(node, path=""):
            node_type = node.get('Node Type', '')
            actual_time = node.get('Actual Total Time', 0)
            cost = node.get('Total Cost', 0)
            
            # Check for expensive nodes
            if actual_time > 1000:  # More than 1 second
                analysis['performance_issues'].append(
                    f"Slow operation: {node_type} took {actual_time:.2f}ms at {path}"
                )
            
            # Check for high cost operations
            if cost > 10000:
                analysis['performance_issues'].append(
                    f"High cost operation: {node_type} cost {cost:.2f} at {path}"
                )
            
            # Recursively check child nodes
            if 'Plans' in node:
                for i, child in enumerate(node['Plans']):
                    traverse_plan(child, f"{path}.{i}")
        
        traverse_plan(plan)
    
    def _check_sequential_scans(self, plan: Dict[str, Any], analysis: Dict[str, Any]):
        """Check for sequential scans that might indicate missing indexes."""
        def traverse_plan(node, path=""):
            node_type = node.get('Node Type', '')
            
            if node_type == 'Seq Scan':
                relation_name = node.get('Relation Name', 'unknown')
                actual_rows = node.get('Actual Rows', 0)
                
                if actual_rows > 1000:  # Large sequential scan
                    analysis['performance_issues'].append(
                        f"Large sequential scan: {relation_name} scanned {actual_rows} rows at {path}"
                    )
                    logger.warning(f"⚠️ SEQ_SCAN: {relation_name} scanned {actual_rows} rows")
            
            # Recursively check child nodes
            if 'Plans' in node:
                for i, child in enumerate(node['Plans']):
                    traverse_plan(child, f"{path}.{i}")
        
        traverse_plan(plan)
    
    def _check_expensive_operations(self, plan: Dict[str, Any], analysis: Dict[str, Any]):
        """Check for expensive operations like sorts, joins, etc."""
        expensive_ops = ['Sort', 'Hash Join', 'Nested Loop', 'Merge Join']
        
        def traverse_plan(node, path=""):
            node_type = node.get('Node Type', '')
            
            if node_type in expensive_ops:
                actual_time = node.get('Actual Total Time', 0)
                if actual_time > 500:  # More than 500ms
                    analysis['performance_issues'].append(
                        f"Expensive {node_type}: took {actual_time:.2f}ms at {path}"
                    )
            
            # Recursively check child nodes
            if 'Plans' in node:
                for i, child in enumerate(node['Plans']):
                    traverse_plan(child, f"{path}.{i}")
        
        traverse_plan(plan)
    
    def _save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis to file for later review."""
        try:
            # Save detailed analysis to JSON file
            filename = f"/tmp/query_analysis_{analysis['query_hash']}_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            # Also append to CSV for quick analysis
            csv_line = f"{analysis['start_time']},{analysis['operation']},{analysis['query_hash']},{analysis['execution_time_ms']:.2f},{analysis['result_count']},{len(analysis['index_usage'])},{len(analysis['performance_issues'])}\n"
            
            with open('/tmp/query_analysis_summary.csv', 'a') as f:
                f.write(csv_line)
                
        except Exception as e:
            logger.warning(f"Failed to save analysis: {e}")

def analyze_database_query(query: str, params: List[Any] = None, 
                          operation: str = "unknown", connection_factory=None):
    """
    Decorator for analyzing database queries.
    
    Args:
        query: SQL query to analyze
        params: Query parameters
        operation: Operation name
        connection_factory: Database connection factory
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if connection_factory:
                analyzer = QueryAnalyzer(connection_factory)
                analysis = analyzer.analyze_query(query, params, operation)
                
                # Add analysis to function result if it's a dict
                result = func(*args, **kwargs)
                if isinstance(result, dict):
                    result['_query_analysis'] = analysis
                
                return result
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def log_vector_query_performance(query: str, params: List[Any], operation: str, 
                                result_count: int, execution_time_ms: float):
    """
    Log vector query performance with special attention to index usage.
    
    Args:
        query: SQL query executed
        params: Query parameters
        operation: Operation name
        result_count: Number of results returned
        execution_time_ms: Execution time in milliseconds
    """
    # Check if this is a vector similarity query
    is_vector_query = any(op in query.upper() for op in ['<=>', '<->', '<#>'])
    
    if is_vector_query:
        logger.info(f"🎯 VECTOR_QUERY: {operation}")
        logger.info(f"🎯 VECTOR_SQL: {query[:200]}...")
        logger.info(f"🎯 VECTOR_RESULTS: {result_count} results in {execution_time_ms:.2f}ms")
        
        # Check for potential issues
        if execution_time_ms > 1000:
            logger.warning(f"⚠️ SLOW_VECTOR_QUERY: {operation} took {execution_time_ms:.2f}ms")
        
        if 'LIMIT' not in query.upper():
            logger.warning(f"⚠️ NO_LIMIT: Vector query without LIMIT clause")
        
        if 'WHERE' not in query.upper() or 'IS NOT NULL' not in query.upper():
            logger.warning(f"⚠️ NO_NULL_FILTER: Vector query without NULL filter")
    
    # Log to performance metrics
    try:
        with open('/tmp/vector_query_performance.csv', 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{operation},{execution_time_ms:.2f},{result_count},{is_vector_query}\n")
    except Exception as e:
        logger.warning(f"Failed to log vector query performance: {e}")













