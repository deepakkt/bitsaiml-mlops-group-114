"""Prometheus metrics helpers."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "heart_api_requests_total",
    "Total number of requests",
    ["endpoint", "method", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "heart_api_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint", "method"],
)

ERROR_COUNT = Counter(
    "heart_api_errors_total",
    "Total number of errors",
    ["endpoint", "method"],
)

# Endpoints like /metrics can be noisy or recursive; opt-out if needed.
EXCLUDED_PATH_PREFIXES = {"/metrics"}


def record_request(endpoint: str, method: str, status_code: int, elapsed_seconds: float) -> None:
    """Record request count and latency."""
    REQUEST_COUNT.labels(endpoint=endpoint, method=method, http_status=status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(elapsed_seconds)


def record_error(endpoint: str, method: str) -> None:
    """Record an error."""
    ERROR_COUNT.labels(endpoint=endpoint, method=method).inc()


def prometheus_response():
    """Return metrics body and content type."""
    return generate_latest(), CONTENT_TYPE_LATEST


def should_track_path(path: str) -> bool:
    """Return True if the given path should be tracked."""
    return not any(path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)
