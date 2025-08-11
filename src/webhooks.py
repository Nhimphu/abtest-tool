import json
import urllib.request
import logging

from utils.net import urlopen_checked, ensure_http_https


def send_webhook(url: str, message: str) -> None:
    """Send a simple POST webhook with text message."""
    data = json.dumps({"text": message}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        ensure_http_https(req)
        urlopen_checked(req, timeout=5)
    except Exception as e:
        logging.error("Webhook call failed: %s", e)
