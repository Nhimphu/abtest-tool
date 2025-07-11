import os
import sys
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.history_panel import HistoryPanel


def test_session_states_table_created(tmp_path):
    db = tmp_path / 'history.db'
    conn = sqlite3.connect(db)
    panel = HistoryPanel(conn=conn)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE name='session_states'")
    assert c.fetchone() is not None


def test_add_and_undo_redo(tmp_path):
    db = tmp_path / 'history.db'
    conn = sqlite3.connect(db)
    panel = HistoryPanel(conn=conn)
    loaded = {}
    class Sig:
        def __call__(self, *a, **k):
            pass
        def emit(self, p):
            loaded['payload'] = p
    panel.state_loaded = Sig()

    panel.add_state({'v': 1})
    panel.add_state({'v': 2})
    panel.undo_state()
    assert loaded['payload'] == {'v': 1}
    panel.redo_state()
    assert loaded['payload'] == {'v': 2}
