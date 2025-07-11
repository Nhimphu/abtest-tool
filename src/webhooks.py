import json
import urllib.request
import logging


def send_webhook(url: str, message: str) -> None:
    """Send a simple POST webhook with text message."""
    data = json.dumps({"text": message}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logging.error("Webhook call failed: %s", e)
