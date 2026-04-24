"""Prometheus-backed metrics with a safe fallback.

Attempt to use prometheus_client when available. If not installed, keep an
in-memory counter store so tests and local runs continue to work. This
module exposes inc/get/reset and functions to retrieve Prometheus output so
the HTTP route can serve the correct format.
"""
from collections import Counter
import threading
from typing import Optional

_lock = threading.Lock()
_inmem = Counter()

# Try to use prometheus_client but tolerate absence
try:
    from prometheus_client import Counter as PromCounter, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    PROM_AVAILABLE = True
    _registry = CollectorRegistry()
    _prom_counters = {}
except Exception:
    PROM_AVAILABLE = False
    _registry = None
    _prom_counters = {}


def inc(name: str, amount: int = 1) -> None:
    """Increment a named counter (both Prometheus and in-memory)."""
    with _lock:
        _inmem[name] += amount
        if PROM_AVAILABLE:
            if name not in _prom_counters:
                # create a Prometheus counter in our private registry
                _prom_counters[name] = PromCounter(name, f"counter {name}", registry=_registry)
            _prom_counters[name].inc(amount)


def get(name: str) -> int:
    """Return the in-memory counter value (int)."""
    with _lock:
        return int(_inmem.get(name, 0))


def reset() -> None:
    """Reset in-memory counters and recreate Prometheus registry if used."""
    global _registry, _prom_counters, _inmem
    with _lock:
        _inmem.clear()
        if PROM_AVAILABLE:
            _registry = CollectorRegistry()
            _prom_counters = {}


def prometheus_metrics_latest() -> Optional[bytes]:
    """Return Prometheus exposition bytes if prometheus_client is available."""
    if PROM_AVAILABLE and _registry is not None:
        return generate_latest(_registry)
    return None


def prometheus_content_type() -> str:
    if PROM_AVAILABLE:
        return CONTENT_TYPE_LATEST
    return "application/json"
