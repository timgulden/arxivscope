"""
Query Deduplicator - Centralized API Query Deduplication

This module provides a centralized way to track and deduplicate API queries
to prevent unnecessary duplicate calls that can cause performance issues
and confusing behavior.
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class QueryDeduplicator:
    """
    Centralized query deduplication system.
    
    Tracks the most recent API query and skips duplicates to prevent
    unnecessary API calls and improve performance.
    """
    
    def __init__(self):
        self.last_query_hash = None
        self.last_query_time = 0
        self.last_query_params = None
        self.duplicate_count = 0
        self.total_queries = 0
        
    def should_skip_query(self, query_params: Dict[str, Any], 
                         time_threshold: float = 1.0) -> Tuple[bool, str]:
        """
        Determine if a query should be skipped due to duplication.
        
        Args:
            query_params: Dictionary of query parameters
            time_threshold: Time in seconds within which duplicates are considered relevant
            
        Returns:
            Tuple of (should_skip, reason)
        """
        self.total_queries += 1
        
        # Create a hash of the query parameters
        query_hash = self._hash_query_params(query_params)
        
        # Debug: Log hash comparison (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Current hash: {query_hash}")
            logger.debug(f"Last hash: {self.last_query_hash}")
            logger.debug(f"Hashes match: {query_hash == self.last_query_hash}")
        
        # Check if this is the same query as the last one
        if query_hash == self.last_query_hash:
            time_since_last = time.time() - self.last_query_time
            
            # If it's within the time threshold, it's likely a duplicate
            if time_since_last < time_threshold:
                self.duplicate_count += 1
                reason = f"Duplicate query detected (last: {time_since_last:.2f}s ago, total duplicates: {self.duplicate_count})"
                logger.debug(f"Duplicate query: {reason}")
                return True, reason
            
            # If it's been a while, it might be intentional (user retrying)
            else:
                logger.debug(f"Same query after {time_since_last:.2f}s - likely intentional retry")
        
        # Update tracking
        self.last_query_hash = query_hash
        self.last_query_time = time.time()
        self.last_query_params = query_params.copy()
        
        logger.debug(f"New query accepted (total queries: {self.total_queries})")
        return False, "New query"
    
    def _hash_query_params(self, params: Dict[str, Any]) -> str:
        """
        Create a hash of query parameters for comparison.
        
        Args:
            params: Dictionary of query parameters
            
        Returns:
            Hash string for parameter comparison
        """
        # Create a normalized version of the params for consistent hashing
        normalized_params = {}
        
        # Sort keys for consistent ordering
        for key in sorted(params.keys()):
            value = params[key]
            
            # Handle different types consistently
            if isinstance(value, (list, tuple)):
                # Sort lists for consistent hashing
                normalized_params[key] = sorted(value) if all(isinstance(x, (str, int, float)) for x in value) else value
            elif isinstance(value, dict):
                # Recursively normalize nested dicts
                normalized_params[key] = self._hash_query_params(value)
            else:
                normalized_params[key] = value
        
        # CRITICAL: Create a comprehensive hash that combines ALL parameters
        # This ensures that ANY change creates a unique query
        hash_components = []
        
        # Add universe constraints hash
        if 'universe_constraints' in params and params['universe_constraints']:
            universe_hash = hashlib.md5(str(params['universe_constraints']).encode()).hexdigest()[:8]
            hash_components.append(f"universe:{universe_hash}")
            logger.debug(f"🔍 QUERY DEDUP: Adding universe constraint hash: {universe_hash}")
            print(f"🌍 QUERY DEDUP: Adding universe constraint hash: {universe_hash}")
        
        # CRITICAL: Bbox changes MUST create unique queries - add it directly to normalized_params
        # This ensures bbox changes are never treated as duplicates
        if 'bbox' in params and params['bbox']:
            # Parse bbox string to get individual coordinates for more precise hashing
            if isinstance(params['bbox'], str):
                try:
                    # Parse "x1,y1,x2,y2" format
                    coords = [float(x.strip()) for x in params['bbox'].split(',')]
                    if len(coords) == 4:
                        # Format with 6 decimal places for precision
                        bbox_str = f"{coords[0]:.6f},{coords[1]:.6f},{coords[2]:.6f},{coords[3]:.6f}"
                        # Store the parsed coordinates in normalized_params for consistent hashing
                        normalized_params['bbox_parsed'] = bbox_str
                    else:
                        bbox_str = str(params['bbox'])
                        normalized_params['bbox_parsed'] = bbox_str
                except (ValueError, AttributeError):
                    bbox_str = str(params['bbox'])
                    normalized_params['bbox_parsed'] = bbox_str
            else:
                bbox_str = str(params['bbox'])
                normalized_params['bbox_parsed'] = bbox_str
            
            # Also keep the original bbox for backward compatibility
            normalized_params['bbox'] = params['bbox']
            
            bbox_hash = hashlib.md5(bbox_str.encode()).hexdigest()[:8]
            hash_components.append(f"bbox:{bbox_hash}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 QUERY DEDUP: Adding bbox hash: {bbox_hash}")
                logger.debug(f"🔍 QUERY DEDUP DEBUG: Bbox '{params['bbox']}' -> parsed '{bbox_str}' -> hash '{bbox_hash}'")
        
        # Add other constraint hashes
        constraint_keys = ['sources', 'year_range', 'search_text', 'similarity_threshold']
        for key in constraint_keys:
            if key in params and params[key] is not None:
                constraint_hash = hashlib.md5(str(params[key]).encode()).hexdigest()[:8]
                hash_components.append(f"{key}:{constraint_hash}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"🔍 QUERY DEDUP: Adding {key} hash: {constraint_hash}")
        
        # CRITICAL: Add the combined hash components to ensure uniqueness
        if hash_components:
            combined_hash = hashlib.md5("|".join(hash_components).encode()).hexdigest()[:16]
            normalized_params['_combined_constraint_hash'] = combined_hash
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 QUERY DEDUP: Combined constraint hash: {combined_hash}")
        
        # Convert to JSON string and hash
        param_string = json.dumps(normalized_params, sort_keys=True, default=str)
        final_hash = hashlib.md5(param_string.encode()).hexdigest()
        
        # Debug: Log the final hash components (only if debug enabled)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 QUERY DEDUP DEBUG: Final hash components:")
            logger.debug(f"  - Hash components: {hash_components}")
            logger.debug(f"  - Normalized params keys: {list(normalized_params.keys())}")
            logger.debug(f"  - Final hash: {final_hash}")
        
        return final_hash
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        return {
            'total_queries': self.total_queries,
            'duplicate_count': self.duplicate_count,
            'duplicate_rate': (self.duplicate_count / self.total_queries * 100) if self.total_queries > 0 else 0,
            'last_query_time': self.last_query_time,
            'last_query_params': self.last_query_params
        }
    
    def reset_stats(self):
        """Reset deduplication statistics."""
        self.last_query_hash = None
        self.last_query_time = 0
        self.last_query_params = None
        self.duplicate_count = 0
        self.total_queries = 0
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("🔍 QUERY DEDUP: Statistics reset")

# Global instance for the entire application
query_deduplicator = QueryDeduplicator()

def should_skip_query(query_params: Dict[str, Any], time_threshold: float = 1.0) -> Tuple[bool, str]:
    """
    Convenience function to check if a query should be skipped.
    
    Args:
        query_params: Dictionary of query parameters
        time_threshold: Time in seconds within which duplicates are considered relevant
        
    Returns:
        Tuple of (should_skip, reason)
    """
    return query_deduplicator.should_skip_query(query_params, time_threshold)

def get_dedup_stats() -> Dict[str, Any]:
    """Get deduplication statistics."""
    return query_deduplicator.get_stats()

def reset_dedup_stats():
    """Reset deduplication statistics."""
    query_deduplicator.reset_stats()
