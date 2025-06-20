import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response

from core.monitoring.logger import get_logger, RequestContext

logger = get_logger("request_logging")


class LoggingMiddleware:
    """Middleware for structured request/response logging"""
    
    def __init__(self, 
                 log_requests: bool = True,
                 log_responses: bool = True,
                 log_request_body: bool = False,
                 log_response_body: bool = False,
                 max_body_size: int = 1024):
        """
        Initialize logging middleware
        
        Args:
            log_requests: Whether to log incoming requests
            log_responses: Whether to log outgoing responses
            log_request_body: Whether to log request body (security risk)
            log_response_body: Whether to log response body (performance impact)
            max_body_size: Maximum body size to log in bytes
        """
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging"""
        
        # Extract request context
        request_id = getattr(request.state, 'request_id', 'unknown')
        user_id = getattr(request.state, 'user_id', '')
        
        # Use request context for all logs in this request
        with RequestContext(request_id, user_id):
            
            # Log incoming request
            if self.log_requests:
                await self._log_request(request)
            
            # Process request
            start_time = time.time()
            
            try:
                response = await call_next(request)
                
                # Log outgoing response
                if self.log_responses:
                    duration = time.time() - start_time
                    await self._log_response(request, response, duration, success=True)
                
                return response
                
            except Exception as e:
                # Log error response
                duration = time.time() - start_time
                if self.log_responses:
                    await self._log_error_response(request, e, duration)
                
                # Re-raise exception
                raise
    
    async def _log_request(self, request: Request):
        """Log incoming request details"""
        
        # Basic request info
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._filter_headers(dict(request.headers)),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", 0)
        }
        
        # Log request body if enabled and safe
        if self.log_request_body and self._should_log_body(request):
            try:
                # Read body (this consumes the stream, so we need to be careful)
                body = await request.body()
                if len(body) <= self.max_body_size:
                    # Try to parse as JSON, fallback to string
                    try:
                        request_info["body"] = json.loads(body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_info["body"] = body.decode('utf-8', errors='ignore')[:self.max_body_size]
                else:
                    request_info["body_truncated"] = f"Body too large ({len(body)} bytes)"
                    
            except Exception as e:
                request_info["body_error"] = f"Failed to read body: {e}"
        
        logger.info("Incoming request", **request_info)
    
    async def _log_response(self, request: Request, response: Response, duration: float, success: bool):
        """Log outgoing response details"""
        
        response_info = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_headers": self._filter_response_headers(dict(response.headers)),
            "success": success
        }
        
        # Log response body if enabled
        if self.log_response_body and hasattr(response, 'body'):
            try:
                # This is tricky with streaming responses
                # Only log for simple responses
                if hasattr(response, 'body') and response.body:
                    body_size = len(response.body)
                    if body_size <= self.max_body_size:
                        try:
                            response_info["response_body"] = json.loads(response.body.decode('utf-8'))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            response_info["response_body"] = response.body.decode('utf-8', errors='ignore')
                    else:
                        response_info["response_body_truncated"] = f"Body too large ({body_size} bytes)"
            except Exception as e:
                response_info["response_body_error"] = f"Failed to read response body: {e}"
        
        if success:
            logger.info("Request completed successfully", **response_info)
        else:
            logger.warning("Request completed with error", **response_info)
    
    async def _log_error_response(self, request: Request, exception: Exception, duration: float):
        """Log error response details"""
        
        error_info = {
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round(duration * 1000, 2),
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "success": False
        }
        
        # Add stack trace for non-HTTP exceptions
        if not hasattr(exception, 'status_code'):
            import traceback
            error_info["stack_trace"] = traceback.format_exc()
        
        logger.error("Request failed with exception", **error_info)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter sensitive headers from logging"""
        
        # Headers to exclude for security
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'proxy-authorization', 'x-csrf-token'
        }
        
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in sensitive_headers:
                filtered[key] = "***REDACTED***"
            elif key_lower.startswith('x-forwarded-'):
                # Keep forwarded headers for debugging
                filtered[key] = value
            elif key_lower in {'content-type', 'content-length', 'user-agent', 'accept', 'host'}:
                # Keep common safe headers
                filtered[key] = value
            else:
                # Redact unknown headers to be safe
                filtered[key] = "***FILTERED***"
        
        return filtered
    
    def _filter_response_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter response headers for logging"""
        
        # Response headers are generally safer to log
        safe_headers = {
            'content-type', 'content-length', 'cache-control', 'expires',
            'x-request-id', 'x-response-time', 'x-ratelimit-limit',
            'x-ratelimit-remaining', 'x-ratelimit-reset'
        }
        
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in safe_headers or key_lower.startswith('x-'):
                filtered[key] = value
        
        return filtered
    
    def _should_log_body(self, request: Request) -> bool:
        """Determine if request body should be logged"""
        
        # Skip body logging for certain content types
        content_type = request.headers.get("content-type", "").lower()
        
        # Skip binary content
        if any(ct in content_type for ct in [
            'multipart/form-data', 'application/octet-stream',
            'image/', 'video/', 'audio/', 'application/pdf'
        ]):
            return False
        
        # Skip large requests
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            return False
        
        return True


class SecurityLoggingMiddleware:
    """Middleware for security-focused logging"""
    
    def __init__(self):
        self.security_logger = get_logger("security")
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Log security-relevant events"""
        
        # Check for suspicious patterns
        await self._check_suspicious_requests(request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log authentication events
            if request.url.path.startswith('/auth'):
                await self._log_auth_event(request, response)
            
            return response
            
        except Exception as e:
            # Log security exceptions
            if hasattr(e, 'status_code') and e.status_code in [401, 403, 429]:
                await self._log_security_exception(request, e)
            raise
    
    async def _check_suspicious_requests(self, request: Request):
        """Check for suspicious request patterns"""
        
        # Check for SQL injection patterns
        query_string = str(request.url.query)
        if any(pattern in query_string.lower() for pattern in [
            'union select', 'drop table', '1=1', 'or 1=1'
        ]):
            self.security_logger.warning("Suspicious SQL injection pattern detected",
                                       path=request.url.path,
                                       query=query_string,
                                       client_ip=self._get_client_ip(request))
        
        # Check for XSS patterns
        if any(pattern in query_string.lower() for pattern in [
            '<script>', 'javascript:', 'onerror=', 'onload='
        ]):
            self.security_logger.warning("Suspicious XSS pattern detected",
                                       path=request.url.path,
                                       query=query_string,
                                       client_ip=self._get_client_ip(request))
        
        # Check for path traversal
        if any(pattern in request.url.path for pattern in ['../', '..\\', '%2e%2e']):
            self.security_logger.warning("Suspicious path traversal attempt",
                                       path=request.url.path,
                                       client_ip=self._get_client_ip(request))
    
    async def _log_auth_event(self, request: Request, response: Response):
        """Log authentication-related events"""
        
        event_type = "unknown"
        if 'login' in request.url.path:
            event_type = "login_attempt"
        elif 'logout' in request.url.path:
            event_type = "logout"
        elif 'register' in request.url.path:
            event_type = "registration_attempt"
        
        success = 200 <= response.status_code < 300
        
        self.security_logger.info(f"Authentication event: {event_type}",
                                event_type=event_type,
                                success=success,
                                status_code=response.status_code,
                                client_ip=self._get_client_ip(request),
                                user_agent=request.headers.get("user-agent", ""))
    
    async def _log_security_exception(self, request: Request, exception: Exception):
        """Log security-related exceptions"""
        
        self.security_logger.warning("Security exception occurred",
                                   path=request.url.path,
                                   status_code=getattr(exception, 'status_code', 500),
                                   error_type=type(exception).__name__,
                                   client_ip=self._get_client_ip(request),
                                   user_agent=request.headers.get("user-agent", ""))
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown" 