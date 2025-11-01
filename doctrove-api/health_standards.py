#!/usr/bin/env python3
"""
Standardized health check utilities for DocScope/DocTrove services.
Defines consistent response formats and health check patterns.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Standard health status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Standard service types."""
    API = "api"
    FRONTEND = "frontend"
    ENRICHMENT = "enrichment"
    DATABASE = "database"

@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None

@dataclass
class ServiceHealth:
    """Complete service health status."""
    service: str
    service_type: ServiceType
    status: HealthStatus
    timestamp: str
    version: Optional[str] = None
    uptime_seconds: Optional[float] = None
    checks: Optional[List[HealthCheck]] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthCheckManager:
    """Manages health checks for services."""
    
    def __init__(self, service_name: str, service_type: ServiceType, version: str = "1.0.0"):
        self.service_name = service_name
        self.service_type = service_type
        self.version = version
        self.start_time = time.time()
        self.checks = []
    
    def add_check(self, name: str, status: HealthStatus, message: str, 
                  details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None) -> None:
        """Add a health check result."""
        check = HealthCheck(
            name=name,
            status=status,
            message=message,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            details=details,
            duration_ms=duration_ms
        )
        self.checks.append(check)
    
    def get_overall_status(self) -> HealthStatus:
        """Determine overall status based on individual checks."""
        if not self.checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.checks]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to standardized dictionary format."""
        return {
            "service": self.service_name,
            "service_type": self.service_type.value,
            "status": self.get_overall_status().value,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": self.version,
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "checks": [{
                "name": check.name,
                "status": check.status.value,
                "message": check.message,
                "timestamp": check.timestamp,
                "details": check.details,
                "duration_ms": check.duration_ms
            } for check in self.checks] if self.checks else None,
            "metadata": {
                "total_checks": len(self.checks),
                "healthy_checks": len([c for c in self.checks if c.status == HealthStatus.HEALTHY]),
                "unhealthy_checks": len([c for c in self.checks if c.status == HealthStatus.UNHEALTHY]),
                "degraded_checks": len([c for c in self.checks if c.status == HealthStatus.DEGRADED])
            }
        }

def create_api_health_response() -> Dict[str, Any]:
    """Create standardized API health response."""
    manager = HealthCheckManager("doctrove-api", ServiceType.API, "2.0.0")
    
    # Add basic API health checks
    manager.add_check(
        name="api_server",
        status=HealthStatus.HEALTHY,
        message="API server is running and responding",
        details={"port": 5001, "host": "0.0.0.0"}
    )
    
    return manager.to_dict()

def create_enrichment_health_response() -> Dict[str, Any]:
    """Create standardized enrichment health response."""
    manager = HealthCheckManager("enrichment", ServiceType.ENRICHMENT, "1.0.0")
    
    try:
        # Import enrichment health check
        import sys
        import os
        sys.path.append('../embedding-enrichment')
        from health_check import comprehensive_health_check
        
        # Run the enrichment health check
        result = comprehensive_health_check()
        
        # Convert to standardized format
        if result['status'] == 'healthy':
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        # Add individual checks
        for check_name, check_result in result.get('checks', {}).items():
            check_status = HealthStatus.HEALTHY if check_result['status'] == 'healthy' else HealthStatus.UNHEALTHY
            manager.add_check(
                name=check_name,
                status=check_status,
                message=check_result['message'],
                details=check_result
            )
        
        return manager.to_dict()
        
    except Exception as e:
        logger.error(f"Error creating enrichment health response: {e}")
        manager.add_check(
            name="enrichment_health_check",
            status=HealthStatus.UNHEALTHY,
            message=f"Failed to check enrichment health: {str(e)}"
        )
        return manager.to_dict()

def create_frontend_health_response() -> Dict[str, Any]:
    """Create standardized frontend health response."""
    import os
    
    manager = HealthCheckManager("docscope", ServiceType.FRONTEND, "1.0.0")
    
    # Get frontend port from environment
    frontend_port = os.getenv('DOCSCOPE_PORT', 'NOT_SET')
    if frontend_port == 'NOT_SET':
        manager.add_check(
            name="frontend_configuration",
            status=HealthStatus.UNHEALTHY,
            message="DOCSCOPE_PORT environment variable is not set",
            details={"error": "Missing required configuration"}
        )
        return manager.to_dict()
    
    # Add basic frontend health checks
    manager.add_check(
        name="frontend_server",
        status=HealthStatus.HEALTHY,
        message="Frontend server is running and responding",
        details={"port": frontend_port, "host": "0.0.0.0"}
    )
    
    # Add API connectivity check
    try:
        import requests
        # Get API URL from environment
        api_url = os.getenv('DOCTROVE_API_URL', 'NOT_SET')
        if api_url == 'NOT_SET':
            manager.add_check(
                name="api_connectivity",
                status=HealthStatus.UNHEALTHY,
                message="DOCTROVE_API_URL environment variable is not set",
                details={"error": "Missing required configuration"}
            )
            return manager.to_dict()
        
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            manager.add_check(
                name="api_connectivity",
                status=HealthStatus.HEALTHY,
                message="Successfully connected to API server",
                details={"api_url": api_url, "response_time_ms": response.elapsed.total_seconds() * 1000}
            )
        else:
            manager.add_check(
                name="api_connectivity",
                status=HealthStatus.DEGRADED,
                message=f"API server responded with status {response.status_code}",
                details={"api_url": api_url, "status_code": response.status_code}
            )
    except Exception as e:
        manager.add_check(
            name="api_connectivity",
            status=HealthStatus.UNHEALTHY,
            message=f"Failed to connect to API server: {str(e)}",
            details={"api_url": api_url if 'api_url' in locals() else 'NOT_SET', "error": str(e)}
        )
    
    return manager.to_dict()

def validate_health_response(response: Dict[str, Any]) -> bool:
    """Validate that a health response follows the standard format."""
    required_fields = ["service", "service_type", "status", "timestamp"]
    
    for field in required_fields:
        if field not in response:
            logger.error(f"Missing required field in health response: {field}")
            return False
    
    # Validate status
    valid_statuses = [status.value for status in HealthStatus]
    if response["status"] not in valid_statuses:
        logger.error(f"Invalid status in health response: {response['status']}")
        return False
    
    # Validate service type
    valid_service_types = [service_type.value for service_type in ServiceType]
    if response["service_type"] not in valid_service_types:
        logger.error(f"Invalid service type in health response: {response['service_type']}")
        return False
    
    return True

def get_health_summary() -> Dict[str, Any]:
    """Get a summary of all service health statuses."""
    services = {
        "api": create_api_health_response(),
        "enrichment": create_enrichment_health_response(),
        "frontend": create_frontend_health_response()
    }
    
    # Determine overall system status
    all_statuses = [service["status"] for service in services.values()]
    
    if "unhealthy" in all_statuses:
        overall_status = "unhealthy"
    elif "degraded" in all_statuses:
        overall_status = "degraded"
    elif all(status == "healthy" for status in all_statuses):
        overall_status = "healthy"
    else:
        overall_status = "unknown"
    
    return {
        "system": "docscope-doctrove",
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "services": services,
        "summary": {
            "total_services": len(services),
            "healthy_services": len([s for s in services.values() if s["status"] == "healthy"]),
            "unhealthy_services": len([s for s in services.values() if s["status"] == "unhealthy"]),
            "degraded_services": len([s for s in services.values() if s["status"] == "degraded"])
        }
    } 