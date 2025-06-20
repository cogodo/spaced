import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
import uuid

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
            
        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False)


class LearningChatbotLogger:
    """Custom logger for the learning chatbot with context awareness"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional extra context"""
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra context"""
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional extra context"""
        self._log(logging.ERROR, message, kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra context"""
        self._log(logging.DEBUG, message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional extra context"""
        self._log(logging.CRITICAL, message, kwargs)
    
    def _log(self, level: int, message: str, extra: Dict[str, Any]):
        """Internal logging method with extra context"""
        if extra:
            # Create a LogRecord with extra data
            record = self.logger.makeRecord(
                self.logger.name, level, "", 0, message, (), None, 
                func="", extra=extra
            )
            self.logger.handle(record)
        else:
            self.logger.log(level, message)
    
    # Context managers for request tracking
    def with_request_context(self, request_id: str, user_id: str = ""):
        """Context manager to set request context"""
        return RequestContext(request_id, user_id)
    
    # Specific logging methods for common scenarios
    def log_api_request(self, method: str, path: str, user_id: str = "", **kwargs):
        """Log API request with standardized format"""
        self.info(f"API Request: {method} {path}", 
                 api_method=method, api_path=path, user_id=user_id, **kwargs)
    
    def log_api_response(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log API response with standardized format"""
        self.info(f"API Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
                 api_method=method, api_path=path, status_code=status_code, 
                 duration_ms=duration_ms, **kwargs)
    
    def log_service_call(self, service: str, operation: str, duration_ms: float, success: bool, **kwargs):
        """Log external service calls"""
        level = logging.INFO if success else logging.WARNING
        status = "SUCCESS" if success else "FAILURE"
        self._log(level, f"Service Call: {service}.{operation} - {status} ({duration_ms:.2f}ms)",
                 {"service": service, "operation": operation, "duration_ms": duration_ms, 
                  "success": success, **kwargs})
    
    def log_user_action(self, action: str, user_id: str, **kwargs):
        """Log user actions for analytics"""
        self.info(f"User Action: {action}", 
                 action=action, user_id=user_id, **kwargs)
    
    def log_system_event(self, event: str, component: str, **kwargs):
        """Log system events"""
        self.info(f"System Event: {event} in {component}",
                 event=event, component=component, **kwargs)


class RequestContext:
    """Context manager for request-scoped logging"""
    
    def __init__(self, request_id: str, user_id: str = ""):
        self.request_id = request_id
        self.user_id = user_id
        self.request_token = None
        self.user_token = None
    
    def __enter__(self):
        self.request_token = request_id_var.set(self.request_id)
        if self.user_id:
            self.user_token = user_id_var.set(self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        request_id_var.reset(self.request_token)
        if self.user_token:
            user_id_var.reset(self.user_token)


def setup_logging(log_level: str = "INFO", use_json: bool = True) -> None:
    """Setup application logging configuration"""
    
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # Setup our application logger
    app_logger = logging.getLogger("learning_chatbot")
    app_logger.setLevel(level)


def get_logger(name: str) -> LearningChatbotLogger:
    """Get a configured logger instance"""
    return LearningChatbotLogger(f"learning_chatbot.{name}")


# Utility function to generate request IDs
def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())[:8] 