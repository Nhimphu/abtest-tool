"""Simple wizard for quick A/B test setup."""

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QWizard,
        QWizardPage,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QComboBox,
        QLineEdit,
        QCheckBox,
    )
except Exception:  # pragma: no cover - allow tests without PyQt installed

    class _Widget:
        def __init__(self, *a, **k):
            self._text = ""
            self._checked = False

        def addItems(self, *a, **k):
            pass

        def setPlaceholderText(self, *a, **k):
            pass

        def setText(self, text=""):
            self._text = text

        def text(self):
            return self._text

        def currentText(self):
            return self._text

        def setChecked(self, val):
            self._checked = bool(val)

        def isChecked(self):
            return self._checked

    QWizard = type(
        "QWizard",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setWindowTitle": lambda *a, **k: None,
            "addPage": lambda *a, **k: None,
            "setButtonText": lambda *a, **k: None,
            "exec": lambda *a, **k: 1,
            "tr": lambda self, text: text,
        },
    )
    QWizardPage = type(
        "QWizardPage",
        (),
        {"setTitle": lambda *a, **k: None, "tr": lambda self, text: text},
    )
    QVBoxLayout = QHBoxLayout = type(
        "Layout",
        (),
        {"addWidget": lambda *a, **k: None, "setContentsMargins": lambda *a, **k: None},
    )
    QLabel = QComboBox = QLineEdit = QCheckBox = _Widget


class QuickABTestWizard(QWizard):
    """Step-by-step wizard for configuring a quick A/B test."""

    def __init__(self, parent=None) -> None:
        self.parent = parent
        super().__init__(parent)
        try:
            # Synchronize palette and stylesheet so background, text and
            # input fields follow the selected theme
            self.setPalette(QApplication.palette())
            self.setStyleSheet(QApplication.instance().styleSheet())
        except Exception:
            pass
        self.setWindowTitle(self.tr("Quick AB Test"))

        self.addPage(self._build_flags_page())
        self.addPage(self._build_metrics_page())
        self.addPage(self._build_options_page())

        finish_const = None
        if hasattr(QWizard, "WizardButton") and hasattr(
            QWizard.WizardButton, "FinishButton"
        ):
            finish_const = QWizard.WizardButton.FinishButton
        else:
            finish_const = getattr(QWizard, "FinishButton", 3)
        try:
            self.setButtonText(finish_const, self.tr("Start"))
        except Exception:
            pass

    def data(self) -> dict:
        """Return user selected options."""
        flags_page = self.page(0)
        metrics_page = self.page(1)
        options_page = self.page(2)

        return {
            "flag": getattr(
                getattr(flags_page, "flag_combo", None), "currentText", lambda: ""
            )(),
            "rollout": getattr(
                getattr(flags_page, "rollout_edit", None), "text", lambda: ""
            )(),
            "primary_metric": getattr(
                getattr(metrics_page, "primary_edit", None), "text", lambda: ""
            )(),
            "custom_metrics": getattr(
                getattr(metrics_page, "custom_edit", None), "text", lambda: ""
            )(),
            "sequential": getattr(
                getattr(options_page, "seq_check", None), "isChecked", lambda: False
            )(),
            "cuped": getattr(
                getattr(options_page, "cuped_check", None), "isChecked", lambda: False
            )(),
            "srm": getattr(
                getattr(options_page, "srm_check", None), "isChecked", lambda: False
            )(),
        }

    def _build_flags_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(self.tr("Flags"))
        QVBoxLayout(page)
        try:
            page.layout().setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass

        page.layout().addWidget(QLabel(self.tr("Feature Flag")))
        page.flag_combo = QComboBox()
        page.layout().addWidget(page.flag_combo)

        page.layout().addWidget(QLabel(self.tr("Rollout %")))
        page.rollout_edit = QLineEdit()
        page.rollout_edit.setPlaceholderText("0-100")
        page.layout().addWidget(page.rollout_edit)

        return page

    def _build_metrics_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(self.tr("Metrics"))
        QVBoxLayout(page)
        try:
            page.layout().setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass

        page.layout().addWidget(QLabel(self.tr("Primary metric")))
        page.primary_edit = QLineEdit()
        page.layout().addWidget(page.primary_edit)

        page.layout().addWidget(QLabel(self.tr("Custom metrics")))
        page.custom_edit = QLineEdit()
        page.layout().addWidget(page.custom_edit)

        return page

    def _build_options_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(self.tr("Options"))
        QVBoxLayout(page)
        try:
            page.layout().setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass

        page.seq_check = QCheckBox(self.tr("Sequential analysis"))
        page.layout().addWidget(page.seq_check)

        page.cuped_check = QCheckBox(self.tr("CUPED adjustment"))
        page.layout().addWidget(page.cuped_check)

        page.srm_check = QCheckBox(self.tr("SRM check"))
        page.layout().addWidget(page.srm_check)

        return page


__all__ = ["QuickABTestWizard"]
