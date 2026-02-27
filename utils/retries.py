from __future__ import annotations


def is_transient_error(exc_text: str) -> bool:
    transient_markers = [
        "net::ERR_NETWORK_CHANGED",
        "net::ERR_TIMED_OUT",
        "NS_ERROR_NET_TIMEOUT",
        "Execution context was destroyed",
        "Target page, context or browser has been closed",
    ]
    normalized = (exc_text or "").lower()
    has_timeout = "timeout" in normalized and "exceeded" in normalized
    return has_timeout or any(marker.lower() in normalized for marker in transient_markers)
