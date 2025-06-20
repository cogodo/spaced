import time
from typing import Callable
from fastapi import Request, Response

from core.monitoring.logger import get_logger, generate_request_id
from core.monitoring.metrics import get_metrics, time_operation
from core.monitoring.performance import track_request_performance

logger = get_logger("performance_middleware")


class PerformanceMiddleware:
    """Middleware for tracking request performance and metrics"""
    
    def __init__(self):
        self.metrics = get_metrics()
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance tracking"""
        
        # Generate request ID for tracking
        request_id = generate_request_id()
        
        # Extract request information
        method = request.method
        path = str(request.url.path)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Start timing
        start_time = time.time()
        
        # Add request ID to state for other middleware/endpoints to use
        request.state.request_id = request_id
        
        # Log request start
        logger.log_api_request(
            method=method,
            path=path,
            user_id=getattr(request.state, 'user_id', ''),
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        # Track active requests
        self.metrics.gauge("active_requests").increment()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Get response info
            status_code = response.status_code
            
            # Log response
            logger.log_api_response(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                request_id=request_id
            )
            
            # Record metrics
            self._record_metrics(method, path, status_code, duration, True)
            
            # Track performance
            track_request_performance(duration, path, status_code)
            
            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log error
            logger.error(f"Request failed: {method} {path}",
                        method=method,
                        path=path,
                        duration_ms=duration_ms,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        request_id=request_id)
            
            # Record error metrics
            self._record_metrics(method, path, 500, duration, False)
            
            # Track performance for errors too
            track_request_performance(duration, path, 500)
            
            # Re-raise the exception
            raise
            
        finally:
            # Always decrement active requests
            self.metrics.gauge("active_requests").decrement()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def _record_metrics(self, method: str, path: str, status_code: int, duration: float, success: bool):
        """Record performance metrics"""
        
        # Increment request counters
        status_category = f"{status_code // 100}xx"
        self.metrics.increment_counter("api_requests_total", {"status": status_category})
        self.metrics.increment_counter("api_requests_total", {"method": method})
        self.metrics.increment_counter("api_requests_total", {"endpoint": path})
        
        # Record response time
        self.metrics.observe_histogram("api_request_duration_seconds", duration)
        self.metrics.observe_histogram("api_request_duration_seconds", duration, {"method": method})
        self.metrics.observe_histogram("api_request_duration_seconds", duration, {"endpoint": path})
        
        # Record endpoint-specific metrics
        endpoint_clean = self._clean_endpoint_path(path)
        self.metrics.observe_histogram("endpoint_response_time_seconds", duration, {"endpoint": endpoint_clean})
        
        # Record error metrics
        if not success:
            self.metrics.increment_counter("api_errors_total", {"endpoint": endpoint_clean})
            self.metrics.increment_counter("api_errors_total", {"status_code": str(status_code)})
    
    def _clean_endpoint_path(self, path: str) -> str:
        """Clean endpoint path for metrics (remove dynamic parts)"""
        # Replace UUIDs and numeric IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace other common dynamic parts
        path = re.sub(r'/[0-9a-zA-Z_-]{20,}', '/{token}', path)
        
        return path


class RequestSizeLimitMiddleware:
    """Middleware for limiting request size"""
    
    def __init__(self, max_size_mb: float = 10.0):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Check request size limits"""
        
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    logger.warning("Request size limit exceeded",
                                 content_length=size,
                                 max_size=self.max_size_bytes,
                                 path=str(request.url.path))
                    
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request too large",
                            "message": f"Request size {size} bytes exceeds limit of {self.max_size_bytes} bytes"
                        }
                    )
            except ValueError:
                pass  # Invalid content-length header, let it pass
        
        return await call_next(request) 