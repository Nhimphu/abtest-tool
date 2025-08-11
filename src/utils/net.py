from __future__ import annotations

from urllib.parse import urlparse
import urllib.request
from typing import Any


def _extract_url(req: Any) -> str:
    if isinstance(req, urllib.request.Request):
        return req.full_url
    return str(req)


def ensure_http_https(req: Any) -> str:
    url = _extract_url(req)
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError(f"Disallowed URL scheme or host: {url!r}")
    return url


def urlopen_checked(req: Any, timeout: float = 5):
    # Validate scheme before delegating
    ensure_http_https(req)
    return urllib.request.urlopen(req, timeout=timeout)  # nosec B310

