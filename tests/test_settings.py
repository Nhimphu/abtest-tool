import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# PyQt stubs are provided in ui.settings when import fails
import ui.settings as settings
from ui.settings import SettingsWidget


def test_test_webhook_emits(monkeypatch):
    recorded = {}

    class Resp:
        status = 200

        def read(self):
            return b'ok'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_open(req, timeout=5):
        recorded['url'] = req.full_url
        recorded['data'] = req.data
        return Resp()

    monkeypatch.setattr(settings.urllib.request, 'urlopen', fake_open)

    w = SettingsWidget()
    w.webhook_edit.text = lambda: 'http://example.com'

    class Capturer:
        def __init__(self):
            self.msg = None

        def __call__(self, *a, **k):
            pass

        def emit(self, m):
            self.msg = m

    capt = Capturer()
    w.log_message = capt

    w._on_test_webhook()

    assert recorded['url'] == 'http://example.com'
    assert b'test' in recorded['data']
    assert capt.msg.startswith('Webhook response 200')
