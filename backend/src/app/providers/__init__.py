"""Providers package for pluggable backends.

This package exposes provider namespaces (e.g., db) used by the
application so modules can import from ``app.providers`` instead of concrete
implementations.
"""

__all__ = ["db"]
