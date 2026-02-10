from __future__ import annotations


def is_transient_error(exc_text: str) -> bool:
    transient_markers = [
        "Timeout 30000ms exceeded",
        "net::ERR_NETWORK_CHANGED",
        "Execution context was destroyed",
        "Target page, context or browser has been closed",
    ]
    return any(marker in exc_text for marker in transient_markers)
