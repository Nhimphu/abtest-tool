import os
import sys
import types
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Stubs for optional dependencies
if 'numpy' not in sys.modules:
    sys.modules['numpy'] = types.ModuleType('numpy')

if 'scipy.stats' not in sys.modules:
    nd = statistics.NormalDist()
    class Norm:
        @staticmethod
        def ppf(p):
            return nd.inv_cdf(p)
        @staticmethod
        def cdf(x):
            return nd.cdf(x)
    stats_mod = types.ModuleType('scipy.stats')
    stats_mod.norm = Norm
    stats_mod.beta = types.SimpleNamespace(pdf=lambda *a, **k: None,
                                           cdf=lambda *a, **k: None)
    scipy_mod = types.ModuleType('scipy')
    scipy_mod.stats = stats_mod
    sys.modules['scipy'] = scipy_mod
    sys.modules['scipy.stats'] = stats_mod

if 'plotly.graph_objects' not in sys.modules:
    plotly_mod = types.ModuleType('plotly')
    go_mod = types.ModuleType('graph_objects')
    plotly_mod.graph_objects = go_mod
    sys.modules['plotly'] = plotly_mod
    sys.modules['plotly.graph_objects'] = go_mod

# Stub reportlab used in utils
if 'reportlab' not in sys.modules:
    rl_mod = types.ModuleType('reportlab')
    lib_mod = types.ModuleType('reportlab.lib')
    pagesizes_mod = types.ModuleType('reportlab.lib.pagesizes')
    pagesizes_mod.letter = (0, 0)
    pdfgen_mod = types.ModuleType('reportlab.pdfgen')
    pdfgen_mod.canvas = types.SimpleNamespace(Canvas=lambda *a, **k: None)
    pdfbase_mod = types.ModuleType('reportlab.pdfbase')
    pdfmetrics_mod = types.ModuleType('reportlab.pdfbase.pdfmetrics')
    pdfmetrics_mod.registerFont = lambda *a, **k: None
    ttfonts_mod = types.ModuleType('reportlab.pdfbase.ttfonts')
    ttfonts_mod.TTFont = type('TTFont', (), {})
    pdfbase_mod.pdfmetrics = pdfmetrics_mod
    pdfbase_mod.ttfonts = ttfonts_mod
    rl_mod.lib = lib_mod
    rl_mod.pdfgen = pdfgen_mod
    rl_mod.pdfbase = pdfbase_mod
    sys.modules['reportlab'] = rl_mod
    sys.modules['reportlab.lib'] = lib_mod
    sys.modules['reportlab.lib.pagesizes'] = pagesizes_mod
    sys.modules['reportlab.pdfgen'] = pdfgen_mod
    sys.modules['reportlab.pdfbase'] = pdfbase_mod
    sys.modules['reportlab.pdfbase.pdfmetrics'] = pdfmetrics_mod
    sys.modules['reportlab.pdfbase.ttfonts'] = ttfonts_mod

# Additional stubs needed for ui_mainwindow
if 'pandas' not in sys.modules:
    sys.modules['pandas'] = types.ModuleType('pandas')

pyqt6_mod = sys.modules.get('PyQt6') or types.ModuleType('PyQt6')
widgets_mod = sys.modules.get('PyQt6.QtWidgets') or types.ModuleType('PyQt6.QtWidgets')
gui_mod = sys.modules.get('PyQt6.QtGui') or types.ModuleType('PyQt6.QtGui')
core_mod = sys.modules.get('PyQt6.QtCore') or types.ModuleType('PyQt6.QtCore')

widget_names = [
    'QApplication','QMainWindow','QWidget','QVBoxLayout','QHBoxLayout',
    'QGridLayout','QLabel','QLineEdit','QPushButton','QSlider',
    'QDoubleSpinBox','QTabWidget','QTableWidget','QTableWidgetItem',
    'QTextBrowser','QWizard','QWizardPage'
]
for name in widget_names:
    if not hasattr(widgets_mod, name):
        setattr(widgets_mod, name, type(name, (), {}))

class QFileDialog:
    @staticmethod
    def getSaveFileName(*args, **kwargs):
        return ('', '')
    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return ('', '')
widgets_mod.QFileDialog = QFileDialog

class QMessageBox:
    @staticmethod
    def information(*args, **kwargs):
        pass
    @staticmethod
    def critical(*args, **kwargs):
        pass
widgets_mod.QMessageBox = QMessageBox

pyqt6_mod.QtWidgets = widgets_mod

for name in ['QPalette','QColor','QIntValidator','QDoubleValidator','QAction']:
    if not hasattr(gui_mod, name):
        setattr(gui_mod, name, type(name, (), {}))
pyqt6_mod.QtGui = gui_mod

if not hasattr(core_mod, 'Qt'):
    core_mod.Qt = type('Qt', (), {})
if not hasattr(core_mod, 'QDateTime'):
    core_mod.QDateTime = type('QDateTime', (), {})
pyqt6_mod.QtCore = core_mod

sys.modules['PyQt6'] = pyqt6_mod
sys.modules['PyQt6.QtWidgets'] = widgets_mod
sys.modules['PyQt6.QtGui'] = gui_mod
sys.modules['PyQt6.QtCore'] = core_mod

from ui_mainwindow import ABTestWindow, QFileDialog, utils


def test_export_pdf_invokes_util(monkeypatch):
    recorded = {}
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: ('out.pdf', ''))
    monkeypatch.setattr(utils, 'export_pdf', lambda html, path: recorded.setdefault('args', (html, path)))

    dummy = types.SimpleNamespace(results_text=types.SimpleNamespace(toPlainText=lambda: 'text'))
    ABTestWindow.export_pdf(dummy)

    assert recorded.get('args') == ('text', 'out.pdf')


def test_export_excel_invokes_util(monkeypatch):
    recorded = {}
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: ('out.xlsx', ''))
    monkeypatch.setattr(utils, 'export_excel', lambda sec, path: recorded.setdefault('args', (sec, path)))

    dummy = types.SimpleNamespace(results_text=types.SimpleNamespace(toPlainText=lambda: 'line1\nline2'))
    ABTestWindow.export_excel(dummy)

    assert recorded.get('args') == ({'Results': ['line1', 'line2']}, 'out.xlsx')


def test_export_csv_invokes_util(monkeypatch):
    recorded = {}
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: ('out.csv', ''))
    monkeypatch.setattr(utils, 'export_csv', lambda sec, path: recorded.setdefault('args', (sec, path)))

    dummy = types.SimpleNamespace(results_text=types.SimpleNamespace(toPlainText=lambda: 'line1\nline2'))
    ABTestWindow.export_csv(dummy)

    assert recorded.get('args') == ({'Results': ['line1', 'line2']}, 'out.csv')


def test_save_session_invokes_util(monkeypatch):
    recorded = {}
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: ('sess.json', ''))
    monkeypatch.setattr(utils, 'save_session_data', lambda data, path: recorded.setdefault('args', (data, path)))

    dummy = types.SimpleNamespace(
        baseline_slider=types.SimpleNamespace(value=lambda: 10),
        uplift_slider=types.SimpleNamespace(value=lambda: 5),
        alpha_slider=types.SimpleNamespace(value=lambda: 5),
        power_slider=types.SimpleNamespace(value=lambda: 90),
        users_A_var=types.SimpleNamespace(text=lambda: '10'),
        conv_A_var=types.SimpleNamespace(text=lambda: '1'),
        users_B_var=types.SimpleNamespace(text=lambda: '12'),
        conv_B_var=types.SimpleNamespace(text=lambda: '2'),
        users_C_var=types.SimpleNamespace(text=lambda: '0'),
        conv_C_var=types.SimpleNamespace(text=lambda: '0'),
        i18n={'RU':{'save_session':'s','load_session':'l'},'EN':{'save_session':'s','load_session':'l'}},
        lang='EN'
    )
    ABTestWindow.save_session(dummy)

    assert recorded.get('args')[1] == 'sess.json'


def test_load_session_invokes_util(monkeypatch):
    data = {
        'baseline': 10,
        'uplift': 5,
        'alpha': 5,
        'power': 90,
        'users_a': '10',
    }
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: ('sess.json', ''))
    monkeypatch.setattr(utils, 'load_session_data', lambda p: data)

    dummy = types.SimpleNamespace(
        baseline_slider=types.SimpleNamespace(setValue=lambda v: recorded.setdefault('baseline', v)),
        uplift_slider=types.SimpleNamespace(setValue=lambda v: None),
        alpha_slider=types.SimpleNamespace(setValue=lambda v: None),
        power_slider=types.SimpleNamespace(setValue=lambda v: None),
        users_A_var=types.SimpleNamespace(setText=lambda v: None),
        conv_A_var=types.SimpleNamespace(setText=lambda v: None),
        users_B_var=types.SimpleNamespace(setText=lambda v: None),
        conv_B_var=types.SimpleNamespace(setText=lambda v: None),
        users_C_var=types.SimpleNamespace(setText=lambda v: None),
        conv_C_var=types.SimpleNamespace(setText=lambda v: None),
        update_ui_text=lambda: None,
        i18n={'RU':{'save_session':'s','load_session':'l'},'EN':{'save_session':'s','load_session':'l'}},
        lang='EN'
    )
    recorded = {}
    ABTestWindow.load_session(dummy)
    assert recorded.get('baseline') == 10
