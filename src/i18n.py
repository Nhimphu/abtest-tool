import json
import locale
import os


HERE = os.path.dirname(__file__)
TRANSLATIONS_PATH = os.path.join(HERE, "i18n.json")

with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
    i18n = json.load(f)


def detect_language() -> str:
    """Return 'RU' if OS locale starts with ru, else 'EN'."""
    loc = locale.getdefaultlocale()[0] or ""
    return "RU" if loc.lower().startswith("ru") else "EN"
