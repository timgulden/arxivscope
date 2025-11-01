#!/usr/bin/env python3
"""
Comprehensive error handling for DocTrove API.
Provides standardized error responses, proper HTTP status codes, and detailed logging.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2 import OperationalError, ProgrammingError, DataError, IntegrityError

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels for logging and monitoring."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"

@dataclass
class APIError:
    """Standardized API error structure."""
    error_code: str
    message: str
    details: Optional[str] = None
    category: ErrorCategory = ErrorCategory.INTERNAL
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    http_status: int = 500
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'details': self.details,
                'category': self.category.value,
                'timestamp': self.timestamp,
                'request_id': self.request_id
            }
        }

class ErrorHandler:
    """Centralized error handling for the API."""
    
    # Standard error codes
    ERROR_CODES = {
        # Validation errors (400)
        'INVALID_PARAMETER': ('INVALID_PARAMETER', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'MISSING_PARAMETER': ('MISSING_PARAMETER', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'INVALID_FIELD': ('INVALID_FIELD', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'INVALID_SQL_FILTER': ('INVALID_SQL_FILTER', 400, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        'INVALID_BBOX': ('INVALID_BBOX', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'INVALID_LIMIT': ('INVALID_LIMIT', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'INVALID_OFFSET': ('INVALID_OFFSET', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        'INVALID_SORT_FIELD': ('INVALID_SORT_FIELD', 400, ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        
        # Not found errors (404)
        'PAPER_NOT_FOUND': ('PAPER_NOT_FOUND', 404, ErrorCategory.NOT_FOUND, ErrorSeverity.LOW),
        'RESOURCE_NOT_FOUND': ('RESOURCE_NOT_FOUND', 404, ErrorCategory.NOT_FOUND, ErrorSeverity.LOW),
        
        # Database errors (500)
        'DATABASE_CONNECTION_ERROR': ('DATABASE_CONNECTION_ERROR', 500, ErrorCategory.DATABASE, ErrorSeverity.HIGH),
        'DATABASE_QUERY_ERROR': ('DATABASE_QUERY_ERROR', 500, ErrorCategory.DATABASE, ErrorSeverity.HIGH),
        'DATABASE_INTEGRITY_ERROR': ('DATABASE_INTEGRITY_ERROR', 500, ErrorCategory.DATABASE, ErrorSeverity.HIGH),
        
        # External service errors (502)
        'EMBEDDING_SERVICE_ERROR': ('EMBEDDING_SERVICE_ERROR', 502, ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM),
        'LLM_SERVICE_ERROR': ('LLM_SERVICE_ERROR', 502, ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM),
        
        # Timeout errors (504)
        'REQUEST_TIMEOUT': ('REQUEST_TIMEOUT', 504, ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
        'DATABASE_TIMEOUT': ('DATABASE_TIMEOUT', 504, ErrorCategory.TIMEOUT, ErrorSeverity.HIGH),
        
        # Internal errors (500)
        'INTERNAL_ERROR': ('INTERNAL_ERROR', 500, ErrorCategory.INTERNAL, ErrorSeverity.HIGH),
        'UNEXPECTED_ERROR': ('UNEXPECTED_ERROR', 500, ErrorCategory.INTERNAL, ErrorSeverity.CRITICAL),
    }
    
    @classmethod
    def create_error(cls, error_code: str, message: str, details: str = None, 
                    request_id: str = None) -> APIError:
        """Create a standardized API error."""
        if error_code not in cls.ERROR_CODES:
            error_code = 'UNEXPECTED_ERROR'
        
        code, http_status, category, severity = cls.ERROR_CODES[error_code]
        
        return APIError(
            error_code=code,
            message=message,
            details=details,
            category=category,
            severity=severity,
            http_status=http_status,
            request_id=request_id
        )
    
    @classmethod
    def handle_database_error(cls, error: Exception, context: str = "", 
                            request_id: str = None) -> APIError:
        """Handle database-specific errors."""
        if isinstance(error, OperationalError):
            if "connection" in str(error).lower():
                return cls.create_error(
                    'DATABASE_CONNECTION_ERROR',
                    "Database connection failed",
                    f"Context: {context}. Error: {str(error)}",
                    request_id
                )
            elif "timeout" in str(error).lower():
                return cls.create_error(
                    'DATABASE_TIMEOUT',
                    "Database operation timed out",
                    f"Context: {context}. Error: {str(error)}",
                    request_id
                )
            else:
                return cls.create_error(
                    'DATABASE_QUERY_ERROR',
                    "Database operation failed",
                    f"Context: {context}. Error: {str(error)}",
                    request_id
                )
        elif isinstance(error, ProgrammingError):
            return cls.create_error(
                'DATABASE_QUERY_ERROR',
                "Invalid database query",
                f"Context: {context}. Error: {str(error)}",
                request_id
            )
        elif isinstance(error, DataError):
            return cls.create_error(
                'DATABASE_QUERY_ERROR',
                "Invalid data format for database operation",
                f"Context: {context}. Error: {str(error)}",
                request_id
            )
        elif isinstance(error, IntegrityError):
            return cls.create_error(
                'DATABASE_INTEGRITY_ERROR',
                "Database integrity constraint violated",
                f"Context: {context}. Error: {str(error)}",
                request_id
            )
        else:
            return cls.create_error(
                'DATABASE_QUERY_ERROR',
                "Database operation failed",
                f"Context: {context}. Error: {str(error)}",
                request_id
            )
    
    @classmethod
    def handle_validation_error(cls, field: str, value: Any, expected: str, 
                              request_id: str = None) -> APIError:
        """Handle validation errors."""
        return cls.create_error(
            'INVALID_PARAMETER',
            f"Invalid value for field '{field}'",
            f"Expected: {expected}, Got: {value}",
            request_id
        )
    
    @classmethod
    def handle_not_found_error(cls, resource_type: str, resource_id: str, 
                             request_id: str = None) -> APIError:
        """Handle not found errors."""
        return cls.create_error(
            'PAPER_NOT_FOUND' if resource_type == 'paper' else 'RESOURCE_NOT_FOUND',
            f"{resource_type.title()} not found",
            f"Resource ID: {resource_id}",
            request_id
        )
    
    @classmethod
    def handle_external_service_error(cls, service: str, error: Exception, 
                                    request_id: str = None) -> APIError:
        """Handle external service errors."""
        if "timeout" in str(error).lower():
            return cls.create_error(
                'REQUEST_TIMEOUT',
                f"{service} service timed out",
                f"Error: {str(error)}",
                request_id
            )
        else:
            error_code = f'{service.upper()}_SERVICE_ERROR'
            if error_code not in cls.ERROR_CODES:
                error_code = 'EXTERNAL_SERVICE_ERROR'
            
            return cls.create_error(
                error_code,
                f"{service} service error",
                f"Error: {str(error)}",
                request_id
            )
    
    @classmethod
    def log_error(cls, error: APIError, exception: Exception = None, 
                 context: Dict[str, Any] = None):
        """Log error with appropriate level and context."""
        log_message = f"API Error: {error.error_code} - {error.message}"
        if error.details:
            log_message += f" | Details: {error.details}"
        if context:
            log_message += f" | Context: {context}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=exception)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=exception)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, exc_info=exception)
        else:
            logger.info(log_message, exc_info=exception)

def create_error_response(error: APIError) -> Tuple[Dict[str, Any], int]:
    """Create Flask response tuple from API error."""
    return error.to_dict(), error.http_status

def handle_exception(exception: Exception, context: str = "", 
                    request_id: str = None) -> Tuple[Dict[str, Any], int]:
    """Handle any exception and return appropriate error response."""
    error_handler = ErrorHandler()
    
    # Handle specific exception types
    if isinstance(exception, (OperationalError, ProgrammingError, DataError, IntegrityError)):
        api_error = error_handler.handle_database_error(exception, context, request_id)
    elif isinstance(exception, ValueError):
        api_error = error_handler.create_error(
            'INVALID_PARAMETER',
            str(exception),
            context,
            request_id
        )
    elif isinstance(exception, KeyError):
        api_error = error_handler.create_error(
            'MISSING_PARAMETER',
            f"Missing required parameter: {exception}",
            context,
            request_id
        )
    elif isinstance(exception, TimeoutError):
        api_error = error_handler.create_error(
            'REQUEST_TIMEOUT',
            "Request timed out",
            context,
            request_id
        )
    else:
        api_error = error_handler.create_error(
            'UNEXPECTED_ERROR',
            "An unexpected error occurred",
            f"Context: {context}. Error: {str(exception)}",
            request_id
        )
    
    # Log the error
    error_handler.log_error(api_error, exception, {'context': context, 'request_id': request_id})
    
    return create_error_response(api_error) 