"""
Interceptor pattern implementation for doctrove-api service.
Based on the interceptor101.md design principles.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from flask import request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Interceptor:
    """
    An interceptor is a data structure with 0-3 functions:
    - enter: called on the way into the stack
    - leave: called on the way out of the stack  
    - error: called if an error occurs
    """
    
    def __init__(self, 
                 enter: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                 leave: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                 error: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None):
        self.enter = enter
        self.leave = leave
        self.error = error

class InterceptorStack:
    """
    Manages a stack of interceptors and executes them in the proper order.
    """
    
    def __init__(self, interceptors: list):
        self.interceptors = interceptors
    
    def execute(self, context: dict) -> dict:
        """
        Execute the interceptor stack with the given initial context.
        """
        # Enter phase
        for interceptor in self.interceptors:
            if hasattr(interceptor, 'enter') and interceptor.enter:
                context = interceptor.enter(context)
                # If a response is set, stop processing further
                if 'response' in context:
                    return context
                if 'error' in context:
                    if hasattr(interceptor, 'error') and interceptor.error:
                        context = interceptor.error(context)
                        if 'response' in context:
                            return context
        # Leave phase
        for interceptor in reversed(self.interceptors):
            if hasattr(interceptor, 'leave') and interceptor.leave:
                context = interceptor.leave(context)
                if 'response' in context:
                    return context
        return context

# Common interceptor functions for API service

def log_request_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log incoming request details"""
    endpoint = ctx.get('endpoint', 'unknown')
    method = ctx.get('method', 'unknown')
    logger.info(f"API Request: {method} {endpoint}")
    return ctx

def log_request_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log request completion"""
    endpoint = ctx.get('endpoint', 'unknown')
    method = ctx.get('method', 'unknown')
    duration = ctx.get('duration', 0)
    logger.info(f"API Response: {method} {endpoint} - {duration:.3f}s")
    return ctx

def log_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log errors and clear error from context"""
    error = ctx.get('error')
    if error:
        endpoint = ctx.get('endpoint', 'unknown')
        logger.error(f"API Error in {endpoint}: {error}")
        del ctx['error']
    return ctx

def timing_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Start timing the request"""
    ctx['start_time'] = time.time()
    return ctx

def timing_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate request duration"""
    start_time = ctx.get('start_time')
    if start_time:
        ctx['duration'] = time.time() - start_time
    return ctx

def validate_input_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input parameters"""
    # This will be customized per endpoint
    return ctx

def setup_database_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Setup database connection using dependency injection"""
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    import psycopg2
    
    def create_db_connection():
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    
    ctx['connection_factory'] = create_db_connection
    return ctx

def cleanup_database_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up database connections"""
    # Connections are handled by context managers in the business logic
    return ctx

def error_response_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Convert errors to proper HTTP responses"""
    error = ctx.get('error')
    if error:
        ctx['response'] = jsonify({'error': str(error)}), 500
        del ctx['error']
    return ctx

@contextmanager
def interceptor_context(endpoint: str, method: str = 'GET'):
    """Context manager for API interceptor phases"""
    ctx = {'endpoint': endpoint, 'method': method}
    try:
        yield ctx
    except Exception as e:
        ctx['error'] = e
        raise 