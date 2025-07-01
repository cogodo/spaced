import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import psutil

from .logger import get_logger
from .metrics import set_gauge

logger = get_logger("performance")


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class PerformanceAlert:
    """Performance alert when thresholds are exceeded"""

    metric: str
    value: float
    threshold: float
    timestamp: datetime
    message: str


class PerformanceTracker:
    """System for tracking application and system performance"""

    def __init__(
        self,
        monitoring_interval: float = 30.0,
        history_size: int = 100,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
    ):
        """
        Initialize performance tracker

        Args:
            monitoring_interval: Seconds between monitoring snapshots
            history_size: Number of snapshots to keep in memory
            cpu_threshold: CPU usage alert threshold (percentage)
            memory_threshold: Memory usage alert threshold (percentage)
        """
        self.monitoring_interval = monitoring_interval
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

        self.resource_history = deque(maxlen=history_size)
        self.alerts = deque(maxlen=50)

        self._monitoring = False
        self._monitor_thread = None
        self._initial_disk_io = None
        self._initial_network_io = None

        # Performance tracking
        self.request_times = deque(maxlen=1000)
        self.slow_requests = deque(maxlen=100)

    def start_monitoring(self):
        """Start background system monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info(
            "Performance monitoring started",
            interval=self.monitoring_interval,
            cpu_threshold=self.cpu_threshold,
            memory_threshold=self.memory_threshold,
        )

    def stop_monitoring(self):
        """Stop background system monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                snapshot = self._take_snapshot()
                self.resource_history.append(snapshot)

                # Update gauge metrics
                set_gauge("system_cpu_percent", snapshot.cpu_percent)
                set_gauge("system_memory_percent", snapshot.memory_percent)
                set_gauge("system_memory_used_mb", snapshot.memory_used_mb)

                # Check thresholds and generate alerts
                self._check_thresholds(snapshot)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(
                    f"Error in performance monitoring loop: {e}",
                    error_type=type(e).__name__,
                )
                time.sleep(self.monitoring_interval)

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current system resources"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if self._initial_disk_io is None:
                self._initial_disk_io = disk_io
                disk_read_mb = 0
                disk_write_mb = 0
            else:
                disk_read_mb = (
                    disk_io.read_bytes - self._initial_disk_io.read_bytes
                ) / (1024 * 1024)
                disk_write_mb = (
                    disk_io.write_bytes - self._initial_disk_io.write_bytes
                ) / (1024 * 1024)

            # Network I/O
            network_io = psutil.net_io_counters()
            if self._initial_network_io is None:
                self._initial_network_io = network_io
                network_sent_mb = 0
                network_recv_mb = 0
            else:
                network_sent_mb = (
                    network_io.bytes_sent - self._initial_network_io.bytes_sent
                ) / (1024 * 1024)
                network_recv_mb = (
                    network_io.bytes_recv - self._initial_network_io.bytes_recv
                ) / (1024 * 1024)

            return ResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
            )

        except Exception as e:
            logger.error(f"Error taking resource snapshot: {e}")
            # Return zero snapshot on error
            return ResourceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=0,
                memory_percent=0,
                memory_used_mb=0,
                disk_io_read_mb=0,
                disk_io_write_mb=0,
                network_sent_mb=0,
                network_recv_mb=0,
            )

    def _check_thresholds(self, snapshot: ResourceSnapshot):
        """Check if any performance thresholds are exceeded"""

        # CPU threshold
        if snapshot.cpu_percent > self.cpu_threshold:
            alert = PerformanceAlert(
                metric="cpu_usage",
                value=snapshot.cpu_percent,
                threshold=self.cpu_threshold,
                timestamp=snapshot.timestamp,
                message=(
                    f"High CPU usage: {snapshot.cpu_percent:.1f}% > "
                    f"{self.cpu_threshold}%"
                ),
            )
            self.alerts.append(alert)
            logger.warning(
                "Performance alert: High CPU usage",
                cpu_percent=snapshot.cpu_percent,
                threshold=self.cpu_threshold,
            )

        # Memory threshold
        if snapshot.memory_percent > self.memory_threshold:
            alert = PerformanceAlert(
                metric="memory_usage",
                value=snapshot.memory_percent,
                threshold=self.memory_threshold,
                timestamp=snapshot.timestamp,
                message=(
                    f"High memory usage: {snapshot.memory_percent:.1f}% > "
                    f"{self.memory_threshold}%"
                ),
            )
            self.alerts.append(alert)
            logger.warning(
                "Performance alert: High memory usage",
                memory_percent=snapshot.memory_percent,
                memory_used_mb=snapshot.memory_used_mb,
                threshold=self.memory_threshold,
            )

    def track_request(self, duration: float, endpoint: str, status_code: int):
        """Track API request performance"""
        self.request_times.append(duration)

        # Track slow requests (>2 seconds)
        if duration > 2.0:
            self.slow_requests.append(
                {
                    "endpoint": endpoint,
                    "duration": duration,
                    "status_code": status_code,
                    "timestamp": datetime.utcnow(),
                }
            )

            logger.warning(
                "Slow request detected",
                endpoint=endpoint,
                duration_seconds=duration,
                status_code=status_code,
            )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics"""
        if not self.resource_history:
            return {"error": "No performance data available"}

        latest = self.resource_history[-1]

        # Calculate averages over last 10 snapshots
        recent_snapshots = list(self.resource_history)[-10:]

        avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(
            recent_snapshots
        )

        # Request performance
        recent_requests = list(self.request_times)[-100:]
        avg_request_time = (
            sum(recent_requests) / len(recent_requests) if recent_requests else 0
        )
        slow_request_count = len([t for t in recent_requests if t > 2.0])

        return {
            "timestamp": latest.timestamp.isoformat() + "Z",
            "system": {
                "cpu_percent": round(latest.cpu_percent, 1),
                "memory_percent": round(latest.memory_percent, 1),
                "memory_used_mb": round(latest.memory_used_mb, 1),
                "avg_cpu_10min": round(avg_cpu, 1),
                "avg_memory_10min": round(avg_memory, 1),
            },
            "requests": {
                "avg_response_time_ms": round(avg_request_time * 1000, 2),
                "slow_request_count_recent": slow_request_count,
                "total_slow_requests": len(self.slow_requests),
            },
            "alerts": {
                "recent_count": len(
                    [
                        a
                        for a in self.alerts
                        if a.timestamp > datetime.utcnow() - timedelta(hours=1)
                    ]
                ),
                "total_count": len(self.alerts),
            },
        }

    def get_resource_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get resource usage history for the specified number of hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_history = [
            {
                "timestamp": snapshot.timestamp.isoformat() + "Z",
                "cpu_percent": snapshot.cpu_percent,
                "memory_percent": snapshot.memory_percent,
                "memory_used_mb": snapshot.memory_used_mb,
            }
            for snapshot in self.resource_history
            if snapshot.timestamp > cutoff_time
        ]

        return filtered_history

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance alerts from the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_alerts = [
            {
                "metric": alert.metric,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat() + "Z",
                "message": alert.message,
            }
            for alert in self.alerts
            if alert.timestamp > cutoff_time
        ]

        return filtered_alerts

    def get_slow_requests(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get slow requests from the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_requests = [
            {
                "endpoint": req["endpoint"],
                "duration_seconds": req["duration"],
                "status_code": req["status_code"],
                "timestamp": req["timestamp"].isoformat() + "Z",
            }
            for req in self.slow_requests
            if req["timestamp"] > cutoff_time
        ]

        return filtered_requests


# Global performance tracker instance
_performance_tracker = PerformanceTracker()


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance"""
    return _performance_tracker


def start_performance_monitoring():
    """Start performance monitoring (convenience function)"""
    _performance_tracker.start_monitoring()


def track_request_performance(duration: float, endpoint: str, status_code: int):
    """Track request performance (convenience function)"""
    _performance_tracker.track_request(duration, endpoint, status_code)
