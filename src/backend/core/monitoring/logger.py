import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs without format string issues
    """

    def __init__(self):
        # Initialize with percent style to avoid brace interpretation
        super().__init__(style="%", validate=False)

    def format(self, record: logging.LogRecord) -> str:
        # Build message manually to avoid ANY format string interpretation
        # This completely bypasses getMessage() and any format string processing

        # Get raw message without any formatting
        raw_msg = str(record.msg) if hasattr(record, "msg") else ""

        # If there are args, format them using percent style ONLY
        if hasattr(record, "args") and record.args:
            try:
                # Escape any curly braces in arguments to prevent format string issues
                safe_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        # Escape curly braces in string arguments
                        safe_arg = str(arg).replace("{", "{{").replace("}", "}}")
                        safe_args.append(safe_arg)
                    else:
                        safe_args.append(arg)
                # Only use percent formatting, which won't interpret {}
                message = raw_msg % tuple(safe_args)
            except (TypeError, ValueError, KeyError):
                # If percent formatting fails, concatenate safely
                message = f"{raw_msg} (args: {record.args})"
        else:
            message = raw_msg

        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": message,  # Already safe from format string issues
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
        if hasattr(record, "__dict__"):
            # Add any extra fields from the record
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ]:
                    log_entry[key] = value

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add stack info if present
        if hasattr(record, "stack_info") and record.stack_info:
            log_entry["stack_info"] = record.stack_info

        return json.dumps(log_entry, ensure_ascii=False)


class LearningChatbotLogger:
    """Custom logger for the learning chatbot with context awareness"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, *args, **kwargs):
        """Log info message with optional format arguments and extra context"""
        self._log(logging.INFO, message, args, kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message with optional format arguments and extra context"""
        self._log(logging.WARNING, message, args, kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message with optional format arguments and extra context"""
        self._log(logging.ERROR, message, args, kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message with optional format arguments and extra context"""
        self._log(logging.DEBUG, message, args, kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message with optional format arguments and extra context"""
        self._log(logging.CRITICAL, message, args, kwargs)

    def _log(self, level: int, message: str, args: tuple, extra: Dict[str, Any]):
        """Internal logging method with format arguments and extra context"""
        # Separate exc_info from other extra fields because it's a special
        # argument in the logging framework.
        exc_info = extra.pop("exc_info", None)

        # The logger will automatically handle the exception information
        # when exc_info is True or an exception tuple.
        self.logger.log(level, message, *args, exc_info=exc_info, extra=extra)

    # Context managers for request tracking
    def with_request_context(self, request_id: str, user_id: str = ""):
        """Context manager to set request context"""
        return RequestContext(request_id, user_id)

    # Specific logging methods for common scenarios
    def log_api_request(self, method: str, path: str, user_id: str = "", **kwargs):
        """Log API request with standardized format"""
        self.info(
            "API Request: %s %s",
            method,
            path,
            api_method=method,
            api_path=path,
            user_id=user_id,
            **kwargs,
        )

    def log_api_response(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log API response with standardized format"""
        self.info(
            "API Response: %s %s - %s (%.2fms)",
            method,
            path,
            status_code,
            duration_ms,
            api_method=method,
            api_path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_service_call(self, service: str, operation: str, duration_ms: float, success: bool, **kwargs):
        """Log external service calls"""
        level = logging.INFO if success else logging.WARNING
        status = "SUCCESS" if success else "FAILURE"
        message = "Service Call: %s.%s - %s (%.2fms)"
        extra = {
            "service": service,
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            **kwargs,
        }
        self._log(level, message, (service, operation, status, duration_ms), extra)

    def log_user_action(self, action: str, user_id: str, **kwargs):
        """Log user actions for analytics"""
        self.info("User Action: %s", action, action=action, user_id=user_id, **kwargs)

    def log_system_event(self, event: str, component: str, **kwargs):
        """Log system events"""
        self.info(
            "System Event: %s in %s",
            event,
            component,
            event=event,
            component=component,
            **kwargs,
        )


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
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
