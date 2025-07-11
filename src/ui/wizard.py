"""Simple wizard for quick A/B test setup."""

try:
    from PyQt6.QtWidgets import (
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
    QWizard = type("QWizard", (), {"__init__": lambda self, *a, **k: None,
                                   "setWindowTitle": lambda *a, **k: None,
                                   "addPage": lambda *a, **k: None,
                                   "setButtonText": lambda *a, **k: None})
    QWizardPage = type("QWizardPage", (), {"setTitle": lambda *a, **k: None})
    QVBoxLayout = QHBoxLayout = type(
        "Layout",
        (),
        {"addWidget": lambda *a, **k: None, "setContentsMargins": lambda *a, **k: None},
    )
    QLabel = QComboBox = QLineEdit = QCheckBox = type(
        "Widget",
        (),
        {
            "addItems": lambda *a, **k: None,
            "setPlaceholderText": lambda *a, **k: None,
            "setText": lambda *a, **k: None,
        },
    )


class QuickABTestWizard(QWizard):
    """Step-by-step wizard for configuring a quick A/B test."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quick AB Test")

        self.addPage(self._build_flags_page())
        self.addPage(self._build_metrics_page())
        self.addPage(self._build_options_page())

        finish_const = None
        if hasattr(QWizard, "WizardButton") and hasattr(QWizard.WizardButton, "FinishButton"):
            finish_const = QWizard.WizardButton.FinishButton
        else:
            finish_const = getattr(QWizard, "FinishButton", 3)
        try:
            self.setButtonText(finish_const, "Start")
        except Exception:
            pass

    def _build_flags_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Flags")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Feature Flag"))
        page.flag_combo = QComboBox()
        layout.addWidget(page.flag_combo)

        layout.addWidget(QLabel("Rollout %"))
        page.rollout_edit = QLineEdit()
        page.rollout_edit.setPlaceholderText("0-100")
        layout.addWidget(page.rollout_edit)

        return page

    def _build_metrics_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Metrics")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Primary metric"))
        page.primary_edit = QLineEdit()
        layout.addWidget(page.primary_edit)

        layout.addWidget(QLabel("Custom metrics"))
        page.custom_edit = QLineEdit()
        layout.addWidget(page.custom_edit)

        return page

    def _build_options_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Options")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        page.seq_check = QCheckBox("Sequential analysis")
        layout.addWidget(page.seq_check)

        page.cuped_check = QCheckBox("CUPED adjustment")
        layout.addWidget(page.cuped_check)

        page.srm_check = QCheckBox("SRM check")
        layout.addWidget(page.srm_check)

        return page

__all__ = ["QuickABTestWizard"]
