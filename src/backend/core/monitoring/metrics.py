import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MetricPoint:
    """Single metric measurement"""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CounterMetric:
    """Counter metric that only increases"""

    name: str
    value: int = 0
    tags: Dict[str, str] = field(default_factory=dict)

    def increment(self, amount: int = 1):
        self.value += amount


@dataclass
class GaugeMetric:
    """Gauge metric that can go up or down"""

    name: str
    value: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float):
        self.value = value

    def increment(self, amount: float = 1.0):
        self.value += amount

    def decrement(self, amount: float = 1.0):
        self.value -= amount


@dataclass
class HistogramMetric:
    """Histogram metric for tracking distributions"""

    name: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    tags: Dict[str, str] = field(default_factory=dict)

    def observe(self, value: float):
        self.values.append(value)

    def percentile(self, p: float) -> float:
        """Calculate percentile (p should be between 0 and 1)"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(p * (len(sorted_values) - 1))
        return sorted_values[index]

    def average(self) -> float:
        """Calculate average value"""
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)

    def min(self) -> float:
        """Get minimum value"""
        return min(self.values) if self.values else 0.0

    def max(self) -> float:
        """Get maximum value"""
        return max(self.values) if self.values else 0.0


class MetricsCollector:
    """Centralized metrics collection system"""

    def __init__(self):
        self._counters: Dict[str, CounterMetric] = {}
        self._gauges: Dict[str, GaugeMetric] = {}
        self._histograms: Dict[str, HistogramMetric] = {}
        self._lock = threading.RLock()

        # Built-in application metrics
        self._init_builtin_metrics()

    def _init_builtin_metrics(self):
        """Initialize built-in application metrics"""

        # API Metrics
        self.counter("api_requests_total", {"status": "2xx"})
        self.counter("api_requests_total", {"status": "4xx"})
        self.counter("api_requests_total", {"status": "5xx"})

        # Session Metrics
        self.counter("sessions_started_total")
        self.counter("sessions_completed_total")
        self.counter("questions_answered_total")
        self.counter("questions_skipped_total")

        # Service Metrics
        self.counter("openai_requests_total")
        self.counter("firebase_requests_total")
        self.counter("redis_requests_total")

        # Performance Metrics
        self.histogram("api_request_duration_seconds")
        self.histogram("openai_request_duration_seconds")
        self.histogram("firebase_request_duration_seconds")
        self.histogram("question_generation_duration_seconds")
        self.histogram("response_scoring_duration_seconds")

        # System Metrics
        self.gauge("active_sessions")
        self.gauge("active_users")
        self.gauge("cache_hit_ratio")

    def counter(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> CounterMetric:
        """Get or create a counter metric"""
        tags = tags or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(tags.items()))}"

        with self._lock:
            if key not in self._counters:
                self._counters[key] = CounterMetric(name=name, tags=tags)
            return self._counters[key]

    def gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> GaugeMetric:
        """Get or create a gauge metric"""
        tags = tags or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(tags.items()))}"

        with self._lock:
            if key not in self._gauges:
                self._gauges[key] = GaugeMetric(name=name, tags=tags)
            return self._gauges[key]

    def histogram(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> HistogramMetric:
        """Get or create a histogram metric"""
        tags = tags or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(tags.items()))}"

        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = HistogramMetric(name=name, tags=tags)
            return self._histograms[key]

    def increment_counter(
        self, name: str, tags: Optional[Dict[str, str]] = None, amount: int = 1
    ):
        """Increment a counter metric"""
        self.counter(name, tags).increment(amount)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        self.gauge(name, tags).set(value)

    def observe_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Add an observation to a histogram metric"""
        self.histogram(name, tags).observe(value)

    def time_histogram(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager to time an operation and record in histogram"""
        return TimerContext(self, name, tags)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        with self._lock:
            result = {
                "counters": {},
                "gauges": {},
                "histograms": {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            # Counters
            for key, counter in self._counters.items():
                result["counters"][key] = {
                    "name": counter.name,
                    "value": counter.value,
                    "tags": counter.tags,
                }

            # Gauges
            for key, gauge in self._gauges.items():
                result["gauges"][key] = {
                    "name": gauge.name,
                    "value": gauge.value,
                    "tags": gauge.tags,
                }

            # Histograms
            for key, histogram in self._histograms.items():
                result["histograms"][key] = {
                    "name": histogram.name,
                    "count": len(histogram.values),
                    "average": histogram.average(),
                    "min": histogram.min(),
                    "max": histogram.max(),
                    "p50": histogram.percentile(0.5),
                    "p95": histogram.percentile(0.95),
                    "p99": histogram.percentile(0.99),
                    "tags": histogram.tags,
                }

            return result

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics"""
        with self._lock:
            # API request metrics
            total_requests = sum(
                counter.value
                for key, counter in self._counters.items()
                if counter.name == "api_requests_total"
            )

            # Error rate calculation
            error_requests = sum(
                counter.value
                for key, counter in self._counters.items()
                if counter.name == "api_requests_total"
                and counter.tags.get("status", "").startswith(("4", "5"))
            )

            error_rate = (
                (error_requests / total_requests * 100) if total_requests > 0 else 0
            )

            # Performance metrics
            api_duration_hist = None
            for key, histogram in self._histograms.items():
                if histogram.name == "api_request_duration_seconds":
                    api_duration_hist = histogram
                    break

            return {
                "total_api_requests": total_requests,
                "error_rate_percent": round(error_rate, 2),
                "avg_response_time_ms": round(api_duration_hist.average() * 1000, 2)
                if api_duration_hist and api_duration_hist.values
                else 0,
                "p95_response_time_ms": round(
                    api_duration_hist.percentile(0.95) * 1000, 2
                )
                if api_duration_hist and api_duration_hist.values
                else 0,
                "active_sessions": self._gauges.get(
                    "active_sessions", GaugeMetric("active_sessions")
                ).value,
                "total_sessions_started": self._counters.get(
                    "sessions_started_total", CounterMetric("sessions_started_total")
                ).value,
                "total_questions_answered": self._counters.get(
                    "questions_answered_total",
                    CounterMetric("questions_answered_total"),
                ).value,
            }


class TimerContext:
    """Context manager for timing operations"""

    def __init__(
        self,
        metrics: MetricsCollector,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.metrics = metrics
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.observe_histogram(self.name, duration, self.tags)


# Global metrics instance
_global_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return _global_metrics


# Convenience functions for common operations
def increment_counter(
    name: str, tags: Optional[Dict[str, str]] = None, amount: int = 1
):
    """Increment a counter metric"""
    _global_metrics.increment_counter(name, tags, amount)


def set_gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Set a gauge metric value"""
    _global_metrics.set_gauge(name, value, tags)


def observe_histogram(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Add an observation to a histogram metric"""
    _global_metrics.observe_histogram(name, value, tags)


def time_operation(name: str, tags: Optional[Dict[str, str]] = None):
    """Context manager to time an operation"""
    return _global_metrics.time_histogram(name, tags)
