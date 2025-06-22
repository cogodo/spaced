from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.monitoring.metrics import get_metrics
from core.monitoring.performance import get_performance_tracker
from core.reliability.circuit_breaker import list_circuit_breakers, get_circuit_breaker
from middleware.rate_limiting import get_rate_limiter
from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from app.config import get_settings

logger = get_logger("monitoring_api")
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "learning_chatbot_api"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "learning_chatbot_api",
        "components": {}
    }
    
    # Check metrics system
    try:
        metrics = get_metrics()
        summary = metrics.get_summary()
        health_status["components"]["metrics"] = {
            "status": "healthy",
            "total_requests": summary.get("total_api_requests", 0)
        }
    except Exception as e:
        health_status["components"]["metrics"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check performance tracker
    try:
        perf_tracker = get_performance_tracker()
        perf_summary = perf_tracker.get_performance_summary()
        health_status["components"]["performance"] = {
            "status": "healthy" if "error" not in perf_summary else "degraded",
            "cpu_percent": perf_summary.get("system", {}).get("cpu_percent", 0),
            "memory_percent": perf_summary.get("system", {}).get("memory_percent", 0)
        }
    except Exception as e:
        health_status["components"]["performance"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check circuit breakers
    try:
        circuit_breakers = list_circuit_breakers()
        open_breakers = [
            name for name, stats in circuit_breakers.items()
            if stats["state"] == "open"
        ]
        
        health_status["components"]["circuit_breakers"] = {
            "status": "healthy" if not open_breakers else "degraded",
            "total_breakers": len(circuit_breakers),
            "open_breakers": len(open_breakers),
            "open_breaker_names": open_breakers
        }
        
        if open_breakers:
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["circuit_breakers"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check rate limiter
    try:
        rate_limiter = get_rate_limiter()
        rate_stats = rate_limiter.get_stats()
        health_status["components"]["rate_limiter"] = {
            "status": "healthy",
            "active_buckets": sum([
                rate_stats["active_ip_buckets"],
                rate_stats["active_user_buckets"],
                rate_stats["active_endpoint_buckets"]
            ])
        }
    except Exception as e:
        health_status["components"]["rate_limiter"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/metrics")
async def get_all_metrics():
    """Get all current metrics"""
    try:
        metrics = get_metrics()
        return metrics.get_all_metrics()
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {e}")


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary"""
    try:
        metrics = get_metrics()
        return metrics.get_summary()
    except Exception as e:
        logger.error("Failed to get metrics summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics summary: {e}")


@router.get("/performance")
async def get_performance_data():
    """Get current performance data"""
    try:
        perf_tracker = get_performance_tracker()
        return perf_tracker.get_performance_summary()
    except Exception as e:
        logger.error("Failed to get performance data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance data: {e}")


@router.get("/performance/history")
async def get_performance_history(
    hours: int = Query(1, ge=1, le=24, description="Hours of history to retrieve")
):
    """Get performance history"""
    try:
        perf_tracker = get_performance_tracker()
        return {
            "resource_history": perf_tracker.get_resource_history(hours),
            "alerts": perf_tracker.get_recent_alerts(hours),
            "slow_requests": perf_tracker.get_slow_requests(hours)
        }
    except Exception as e:
        logger.error("Failed to get performance history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance history: {e}")


@router.get("/circuit-breakers")
async def get_circuit_breakers():
    """Get all circuit breaker statuses"""
    try:
        return list_circuit_breakers()
    except Exception as e:
        logger.error("Failed to get circuit breakers", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve circuit breakers: {e}")


@router.get("/circuit-breakers/{breaker_name}")
async def get_circuit_breaker_details(breaker_name: str):
    """Get detailed information about a specific circuit breaker"""
    try:
        breaker = get_circuit_breaker(breaker_name)
        return breaker.get_stats()
    except Exception as e:
        logger.error("Failed to get circuit breaker details", breaker_name=breaker_name, error=str(e))
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{breaker_name}' not found")


@router.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(
    breaker_name: str,
    user = Depends(get_current_user)  # Require authentication for admin operations
):
    """Reset a circuit breaker to closed state"""
    try:
        breaker = get_circuit_breaker(breaker_name)
        breaker.reset()
        
        logger.info("Circuit breaker reset by admin",
                   breaker_name=breaker_name,
                   admin_user=user.get("uid", "unknown"))
        
        return {
            "message": f"Circuit breaker '{breaker_name}' has been reset",
            "breaker_name": breaker_name,
            "new_state": "closed"
        }
    except Exception as e:
        logger.error("Failed to reset circuit breaker", 
                    breaker_name=breaker_name, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {e}")


@router.post("/circuit-breakers/{breaker_name}/force-open")
async def force_open_circuit_breaker(
    breaker_name: str,
    user = Depends(get_current_user)  # Require authentication for admin operations
):
    """Force a circuit breaker to open state (for maintenance)"""
    try:
        breaker = get_circuit_breaker(breaker_name)
        breaker.force_open()
        
        logger.warning("Circuit breaker forced open by admin",
                      breaker_name=breaker_name,
                      admin_user=user.get("uid", "unknown"))
        
        return {
            "message": f"Circuit breaker '{breaker_name}' has been forced open",
            "breaker_name": breaker_name,
            "new_state": "open"
        }
    except Exception as e:
        logger.error("Failed to force open circuit breaker", 
                    breaker_name=breaker_name, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to force open circuit breaker: {e}")


@router.get("/rate-limiting")
async def get_rate_limiting_stats():
    """Get rate limiting statistics"""
    try:
        rate_limiter = get_rate_limiter()
        return rate_limiter.get_stats()
    except Exception as e:
        logger.error("Failed to get rate limiting stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rate limiting stats: {e}")


@router.get("/rate-limiting/buckets/{bucket_type}/{identifier}")
async def get_rate_limit_bucket(
    bucket_type: str,
    identifier: str
):
    """Get information about a specific rate limit bucket"""
    if bucket_type not in ["ip", "user", "endpoint"]:
        raise HTTPException(status_code=400, detail="bucket_type must be 'ip', 'user', or 'endpoint'")
    
    try:
        rate_limiter = get_rate_limiter()
        bucket_info = rate_limiter.get_bucket_info(bucket_type, identifier)
        
        if bucket_info is None:
            raise HTTPException(status_code=404, detail=f"Rate limit bucket not found: {bucket_type}:{identifier}")
        
        return {
            "bucket_type": bucket_type,
            "identifier": identifier,
            "info": bucket_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get rate limit bucket", 
                    bucket_type=bucket_type, 
                    identifier=identifier, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rate limit bucket: {e}")


@router.get("/system/info")
async def get_system_info():
    """Get system information"""
    import platform
    import sys
    import psutil
    from datetime import datetime
    
    settings = get_settings()
    
    try:
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_usage": {
                    path: {
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": round((usage.used / usage.total) * 100, 1)
                    }
                    for path, usage in [("/", psutil.disk_usage("/"))]
                }
            },
            "application": {
                "start_time": datetime.utcnow().isoformat() + "Z",  # Would be better to track actual start time
                "version": "1.0.0",  # Should come from config or package
                "environment": settings.environment
            }
        }
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system info: {e}")


@router.get("/logs/recent")
async def get_recent_logs(
    lines: int = Query(100, ge=1, le=1000, description="Number of recent log lines"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR)")
):
    """Get recent log entries (simplified - in production would query log aggregation system)"""
    # This is a placeholder - in production you'd query your log aggregation system
    # like ELK stack, Splunk, CloudWatch, etc.
    
    return {
        "message": "Log retrieval not implemented",
        "note": "In production, this would query your log aggregation system",
        "requested_lines": lines,
        "requested_level": level,
        "suggestion": "Use your log aggregation system (ELK, Splunk, CloudWatch, etc.) for log queries"
    }


@router.post("/monitoring/start")
async def start_monitoring():
    """Start performance monitoring"""
    try:
        from core.monitoring.performance import start_performance_monitoring
        start_performance_monitoring()
        
        logger.info("Performance monitoring started via API")
        
        return {
            "message": "Performance monitoring started",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {e}")


@router.get("/status")
async def get_status():
    """Get overall system status"""
    try:
        # Get all component statuses
        metrics = get_metrics()
        perf_tracker = get_performance_tracker()
        circuit_breakers = list_circuit_breakers()
        rate_limiter = get_rate_limiter()
        
        # Calculate overall status
        metrics_summary = metrics.get_summary()
        perf_summary = perf_tracker.get_performance_summary()
        
        open_breakers = [
            name for name, stats in circuit_breakers.items()
            if stats["state"] == "open"
        ]
        
        # Determine overall health
        status = "healthy"
        issues = []
        
        if open_breakers:
            status = "degraded"
            issues.append(f"{len(open_breakers)} circuit breakers open")
        
        if "error" in perf_summary:
            status = "degraded"
            issues.append("Performance monitoring unavailable")
        
        # Check error rate
        error_rate = metrics_summary.get("error_rate_percent", 0)
        if error_rate > 5:  # More than 5% error rate
            status = "degraded" if status == "healthy" else "unhealthy"
            issues.append(f"High error rate: {error_rate}%")
        
        # Check response time
        avg_response_time = metrics_summary.get("avg_response_time_ms", 0)
        if avg_response_time > 2000:  # Slower than 2 seconds
            status = "degraded" if status == "healthy" else "unhealthy"
            issues.append(f"Slow response time: {avg_response_time}ms")
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "issues": issues,
            "metrics": {
                "total_requests": metrics_summary.get("total_api_requests", 0),
                "error_rate_percent": error_rate,
                "avg_response_time_ms": avg_response_time,
                "active_sessions": metrics_summary.get("active_sessions", 0)
            },
            "components": {
                "circuit_breakers": {
                    "total": len(circuit_breakers),
                    "open": len(open_breakers)
                },
                "rate_limiter": {
                    "active_buckets": sum([
                        rate_limiter.get_stats()["active_ip_buckets"],
                        rate_limiter.get_stats()["active_user_buckets"],
                        rate_limiter.get_stats()["active_endpoint_buckets"]
                    ])
                }
            }
        }
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system status: {e}") 