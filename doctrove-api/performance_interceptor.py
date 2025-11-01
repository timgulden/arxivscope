"""
Performance Interceptor for DocTrove API
Uses functional programming principles to add comprehensive debug tracing with timestamps.
"""

import time
import logging
import json
from typing import Dict, Any, Callable
from functools import wraps
from datetime import datetime

# Configure logging to file
logger = logging.getLogger('performance_tracer')
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler('/tmp/doctrove_performance.log')
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

def log_performance(phase: str) -> Callable:
    """
    Functional decorator that logs performance timing for a specific phase.
    
    Args:
        phase: Name of the phase being timed
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_datetime = datetime.now()
            
            logger.info(f"🚀 PHASE_START: {phase} at {start_datetime}")
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                logger.info(f"✅ PHASE_COMPLETE: {phase} took {duration_ms:.2f}ms")
                
                return result
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                logger.error(f"❌ PHASE_ERROR: {phase} failed after {duration_ms:.2f}ms with error: {e}")
                raise
                
        return wrapper
    return decorator

def trace_database_query(query: str, parameters: list, phase: str = "database_query") -> Callable:
    """
    Functional decorator specifically for database query tracing.
    
    Args:
        query: SQL query being executed
        parameters: Query parameters
        phase: Phase name for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_datetime = datetime.now()
            
            # Log query details
            logger.info(f"🔍 DB_QUERY_START: {phase}")
            logger.info(f"🔍 DB_QUERY_SQL: {query[:200]}...")
            logger.info(f"🔍 DB_QUERY_PARAMS: {len(parameters)} parameters")
            logger.info(f"🔍 DB_QUERY_TIME: {start_datetime}")
            

            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Log result details
                if hasattr(result, '__len__'):
                    result_count = len(result)
                else:
                    result_count = "unknown"
                
                logger.info(f"✅ DB_QUERY_COMPLETE: {phase} took {duration_ms:.2f}ms, returned {result_count} results")
                
                return result
            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                logger.error(f"❌ DB_QUERY_ERROR: {phase} failed after {duration_ms:.2f}ms with error: {e}")
                raise
                
        return wrapper
    return decorator

def trace_json_serialization(data: Any, phase: str = "json_serialization"):
    """
    Context manager for JSON serialization tracing.
    
    Args:
        data: Data being serialized
        phase: Phase name for logging
        
    Returns:
        Context manager
    """
    class JsonSerializationContext:
        def __init__(self, data: Any, phase: str):
            self.data = data
            self.phase = phase
            self.start_time = None
            self.start_datetime = None
            
        def __enter__(self):
            self.start_time = time.time()
            self.start_datetime = datetime.now()
            
            # Estimate data size
            if hasattr(self.data, '__len__'):
                data_size = len(self.data)
            else:
                data_size = "unknown"
            
            logger.info(f"📝 JSON_START: {self.phase}, data size: {data_size}")
            
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = time.time()
            duration_ms = (end_time - self.start_time) * 1000
            
            if exc_type is None:
                logger.info(f"✅ JSON_COMPLETE: {self.phase} took {duration_ms:.2f}ms")
            else:
                logger.error(f"❌ JSON_ERROR: {self.phase} failed after {duration_ms:.2f}ms with error: {exc_val}")
    
    return JsonSerializationContext(data, phase)

def performance_context(operation: str) -> Callable:
    """
    Context manager for performance tracing of entire operations.
    
    Args:
        operation: Name of the operation being traced
        
    Returns:
        Context manager
    """
    class PerformanceContext:
        def __init__(self, operation: str):
            self.operation = operation
            self.start_time = None
            self.start_datetime = None
            
        def __enter__(self):
            self.start_time = time.time()
            self.start_datetime = datetime.now()
            
            logger.info(f"🚀 OPERATION_START: {self.operation} at {self.start_datetime}")
            
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = time.time()
            duration_ms = (end_time - self.start_time) * 1000
            
            if exc_type is None:
                logger.info(f"✅ OPERATION_COMPLETE: {self.operation} took {duration_ms:.2f}ms")
            else:
                logger.error(f"❌ OPERATION_ERROR: {self.operation} failed after {duration_ms:.2f}ms with error: {exc_val}")
    
    return PerformanceContext(operation)

# Utility functions for manual timing
def log_timestamp(message: str, phase: str = "manual"):
    """Log a timestamp with a custom message."""
    timestamp = datetime.now()
    logger.info(f"⏰ TIMESTAMP: {phase} - {message} at {timestamp}")

def log_duration(start_time: float, phase: str = "manual"):
    """Log the duration since a start time."""
    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"⏱️ DURATION: {phase} took {duration_ms:.2f}ms")
    return duration_ms

def log_performance_metrics(operation: str, duration_ms: float, result_count: int = None, search_text: str = None):
    """
    Log performance metrics for monitoring and alerting.
    
    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        result_count: Number of results returned
        search_text: Search text if this was a semantic search
    """
    timestamp = datetime.now()
    
    # Performance thresholds for alerting
    if duration_ms > 10000:  # 10 seconds
        level = "ERROR"
        emoji = "❌"
    elif duration_ms > 5000:  # 5 seconds
        level = "WARNING"
        emoji = "⚠️"
    elif duration_ms > 2000:  # 2 seconds
        level = "INFO"
        emoji = "ℹ️"
    else:
        level = "SUCCESS"
        emoji = "✅"
    
    # Log with appropriate level
    message = f"{emoji} PERFORMANCE_METRICS: {operation} took {duration_ms:.2f}ms"
    if result_count is not None:
        message += f", returned {result_count} results"
    if search_text:
        message += f", search: '{search_text[:50]}...'"
    
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "INFO":
        logger.info(message)
    else:
        logger.info(message)
    
    # Also log to performance metrics file for analysis
    try:
        with open('/tmp/doctrove_performance_metrics.csv', 'a') as f:
            f.write(f"{timestamp},{operation},{duration_ms:.2f},{result_count or 0},{search_text or ''}\n")
    except Exception as e:
        logger.warning(f"Failed to write performance metrics: {e}")
