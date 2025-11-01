"""
Performance monitoring utilities for DocScope frontend.
Helps identify bottlenecks and measure response times.
"""
import time
import logging
import functools
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring utility for tracking execution times."""
    
    def __init__(self):
        self.metrics = {}
        self.current_trace = {}
    
    @contextmanager
    def trace(self, operation_name: str):
        """Context manager for tracing operation execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            self.record_metric(operation_name, duration)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Performance: {operation_name} took {duration:.2f}ms")
    
    def record_metric(self, operation_name: str, duration_ms: float):
        """Record a performance metric."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(duration_ms)
    
    def get_average_time(self, operation_name: str) -> Optional[float]:
        """Get average execution time for an operation."""
        if operation_name in self.metrics and self.metrics[operation_name]:
            return sum(self.metrics[operation_name]) / len(self.metrics[operation_name])
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'total_ms': sum(times)
                }
        return summary
    
    def clear_metrics(self):
        """Clear all recorded metrics."""
        self.metrics.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with performance_monitor.trace(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def analyze_click_performance(clickData: Dict[str, Any], data_store: list) -> Dict[str, Any]:
    """
    Analyze performance of click data processing.
    
    Args:
        clickData: The click data from the graph
        data_store: The current data store
        
    Returns:
        Dictionary with performance analysis
    """
    analysis = {
        'data_store_size': len(data_store) if data_store else 0,
        'click_data_complexity': len(str(clickData)) if clickData else 0,
        'has_customdata': bool(clickData and clickData.get('points') and 
                              clickData['points'][0].get('customdata')),
        'performance_metrics': performance_monitor.get_summary()
    }
    
    # Analyze data store characteristics
    if data_store:
        df = pd.DataFrame(data_store)
        analysis.update({
            'dataframe_columns': list(df.columns),
            'dataframe_shape': df.shape,
            'has_country_column': 'Country of Publication' in df.columns,
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
        })
    
    return analysis

def log_performance_issue(operation: str, duration_ms: float, threshold_ms: float = 1000):
    """Log performance issues that exceed threshold."""
    if duration_ms > threshold_ms:
        logger.warning(f"Performance issue detected: {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)")
        return True
    return False

def get_performance_recommendations(analysis: Dict[str, Any]) -> list:
    """Get performance improvement recommendations based on analysis."""
    recommendations = []
    
    # Check data store size
    if analysis.get('data_store_size', 0) > 10000:
        recommendations.append("Consider reducing data store size or implementing pagination")
    
    # Check memory usage
    memory_mb = analysis.get('memory_usage_mb', 0)
    if memory_mb > 100:
        recommendations.append(f"High memory usage ({memory_mb:.1f}MB) - consider data optimization")
    
    # Check for missing columns
    if not analysis.get('has_country_column', False):
        recommendations.append("Missing 'Country of Publication' column - check API response")
    
    # Check performance metrics
    metrics = analysis.get('performance_metrics', {})
    for operation, stats in metrics.items():
        if stats.get('avg_ms', 0) > 500:
            recommendations.append(f"Slow operation: {operation} (avg: {stats['avg_ms']:.1f}ms)")
    
    return recommendations 