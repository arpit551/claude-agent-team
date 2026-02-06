"""Performance monitoring and optimization utilities."""

import functools
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TimingStats:
    """Statistics for timed operations."""

    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_time: float = 0.0

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0

    def record(self, elapsed: float) -> None:
        """Record a timing measurement."""
        self.call_count += 1
        self.total_time += elapsed
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.last_time = elapsed

    def __str__(self) -> str:
        """Format timing statistics."""
        return (
            f"{self.name}: {self.call_count} calls, "
            f"avg={self.avg_time:.3f}s, "
            f"min={self.min_time:.3f}s, "
            f"max={self.max_time:.3f}s"
        )


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        self._stats: dict[str, TimingStats] = {}
        self._enabled = True

    def enable(self) -> None:
        """Enable performance monitoring."""
        self._enabled = True

    def disable(self) -> None:
        """Disable performance monitoring."""
        self._enabled = False

    def time(self, name: str) -> Callable:
        """Decorator to time function execution.

        Args:
            name: Name for this timing metric

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self._enabled:
                    return func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.perf_counter() - start
                    self.record(name, elapsed)

            return wrapper

        return decorator

    def record(self, name: str, elapsed: float) -> None:
        """Record a timing measurement.

        Args:
            name: Operation name
            elapsed: Elapsed time in seconds
        """
        if not self._enabled:
            return

        if name not in self._stats:
            self._stats[name] = TimingStats(name)

        self._stats[name].record(elapsed)

        # Log slow operations
        if elapsed > 1.0:
            logger.warning(f"Slow operation: {name} took {elapsed:.2f}s")

    def get_stats(self, name: str) -> Optional[TimingStats]:
        """Get statistics for a named operation.

        Args:
            name: Operation name

        Returns:
            Timing statistics or None
        """
        return self._stats.get(name)

    def get_all_stats(self) -> dict[str, TimingStats]:
        """Get all timing statistics.

        Returns:
            Dictionary of operation name to statistics
        """
        return self._stats.copy()

    def print_stats(self) -> None:
        """Print all timing statistics."""
        if not self._stats:
            print("No timing data collected")
            return

        print("\n=== Performance Statistics ===")
        for stats in sorted(self._stats.values(), key=lambda s: s.total_time, reverse=True):
            print(stats)
        print()

    def reset(self) -> None:
        """Reset all statistics."""
        self._stats.clear()


# Global performance monitor
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor.

    Returns:
        Global PerformanceMonitor instance
    """
    return _monitor


def timed(name: str) -> Callable:
    """Decorator to time function execution using global monitor.

    Args:
        name: Name for this timing metric

    Returns:
        Decorator function

    Example:
        @timed("spawn_agent")
        def spawn_agent(self, role):
            ...
    """
    return _monitor.time(name)


class LRUCache:
    """Simple LRU cache for output caching."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: dict[Any, tuple[float, Any]] = {}  # key -> (timestamp, value)
        self._access_order: list[Any] = []

    def get(self, key: Any, max_age: Optional[float] = None) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key
            max_age: Maximum age in seconds (None for no expiration)

        Returns:
            Cached value or None
        """
        if key not in self._cache:
            return None

        timestamp, value = self._cache[key]

        # Check expiration
        if max_age is not None:
            age = time.time() - timestamp
            if age > max_age:
                self.remove(key)
                return None

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return value

    def put(self, key: Any, value: Any) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        self._cache[key] = (time.time(), value)

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def remove(self, key: Any) -> None:
        """Remove key from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_order:
            return

        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._access_order.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
        }


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Percentage of system memory

    def __str__(self) -> str:
        return f"RSS: {self.rss_mb:.1f}MB, VMS: {self.vms_mb:.1f}MB, {self.percent:.1f}%"


def get_memory_usage() -> Optional[MemoryStats]:
    """Get current process memory usage.

    Returns:
        Memory statistics or None if unavailable
    """
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        return MemoryStats(
            rss_mb=mem_info.rss / (1024 * 1024),
            vms_mb=mem_info.vms / (1024 * 1024),
            percent=process.memory_percent(),
        )
    except ImportError:
        logger.debug("psutil not available for memory profiling")
        return None
    except Exception as e:
        logger.debug(f"Could not get memory usage: {e}")
        return None


class Benchmark:
    """Context manager for benchmarking code blocks."""

    def __init__(self, name: str, log: bool = True):
        self.name = name
        self.log = log
        self.start_time: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "Benchmark":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        _monitor.record(self.name, self.elapsed)

        if self.log:
            if self.elapsed > 1.0:
                logger.info(f"{self.name} took {self.elapsed:.2f}s")
            else:
                logger.debug(f"{self.name} took {self.elapsed*1000:.1f}ms")


def benchmark(name: str) -> Benchmark:
    """Create a benchmark context manager.

    Args:
        name: Name for the benchmark

    Returns:
        Benchmark context manager

    Example:
        with benchmark("load_config"):
            config = load_config()
    """
    return Benchmark(name)
