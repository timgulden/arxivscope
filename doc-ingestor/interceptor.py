"""
Interceptor pattern implementation for doc-ingestor service.
Based on the interceptor101.md design principles.
"""

import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

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
    
    def __init__(self, interceptors: list[Interceptor]):
        self.interceptors = interceptors
    
    def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the interceptor stack with the given initial context.
        """
        context = initial_context.copy()
        entered_interceptors = []
        
        try:
            # Enter phase: call enter functions in order
            for interceptor in self.interceptors:
                if interceptor.enter:
                    context = interceptor.enter(context)
                entered_interceptors.append(interceptor)
            
            # Leave phase: call leave functions in reverse order
            for interceptor in reversed(entered_interceptors):
                if interceptor.leave:
                    context = interceptor.leave(context)
                    
        except Exception as e:
            # Error phase: put error in context and call error functions
            context['error'] = e
            logger.error(f"Error in interceptor stack: {e}")
            
            # Call error function of current interceptor
            for interceptor in reversed(entered_interceptors):
                if interceptor.error:
                    context = interceptor.error(context)
                    # If error is cleared, continue with leave phase
                    if 'error' not in context:
                        break
                else:
                    # If no error function, continue with leave phase
                    if interceptor.leave:
                        context = interceptor.leave(context)
        
        return context

# Common interceptor functions for doc-ingestor

def log_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log entry into a phase"""
    phase = ctx.get('phase', 'unknown')
    logger.debug(f"Entering phase: {phase}")
    return ctx

def log_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log exit from a phase"""
    phase = ctx.get('phase', 'unknown')
    logger.debug(f"Leaving phase: {phase}")
    return ctx

def log_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log errors and clear error from context"""
    error = ctx.get('error')
    if error:
        logger.error(f"Error in phase {ctx.get('phase', 'unknown')}: {error}")
        del ctx['error']
    return ctx

@contextmanager
def interceptor_context(phase: str):
    """Context manager for interceptor phases"""
    ctx = {'phase': phase}
    try:
        yield ctx
    except Exception as e:
        ctx['error'] = e
        raise 