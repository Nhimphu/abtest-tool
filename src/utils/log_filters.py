import logging
import re

class RedactPIIFilter(logging.Filter):
    """Redact common PII fields from log messages."""

    pattern = re.compile(r"(user_id|email)=([^\s,]+)")

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple regex
        message = record.getMessage()
        message = self.pattern.sub(lambda m: f"{m.group(1)}=***", message)
        record.msg = message
        record.args = ()
        return True
