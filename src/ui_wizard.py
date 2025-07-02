# ui_wizard.py

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QLabel, QLineEdit, QVBoxLayout, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt

class BaselinePage(QWizardPage):
    def __init__(self, texts, default_value: str):
        super().__init__()
        self.setTitle(texts['wizard_step1'])
        self.setSubTitle(texts['wizard_step1_hint'])
        self.input = QLineEdit()
        self.input.setText(default_value)
        self.input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.input.setToolTip(texts['wizard_step1_hint'])
        layout = QVBoxLayout()
        layout.addWidget(self.input)
        self.setLayout(layout)
        self.registerField("baseline*", self.input)

    def validatePage(self) -> bool:
        txt = self.input.text().replace(',', '.')
        try:
            v = float(txt)
            if 0 < v < 100:
                return True
        except ValueError:
            pass
        QMessageBox.warning(self, "Ошибка", "Введите число от 0 до 100")
        return False


class UpliftPage(QWizardPage):
    def __init__(self, texts, default_value: str):
        super().__init__()
        self.setTitle(texts['wizard_step2'])
        self.setSubTitle(texts['wizard_step2_hint'])
        self.input = QLineEdit()
        self.input.setText(default_value)
        self.input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.input.setToolTip(texts['wizard_step2_hint'])
        layout = QVBoxLayout()
        layout.addWidget(self.input)
        self.setLayout(layout)
        self.registerField("uplift*", self.input)

    def validatePage(self) -> bool:
        txt = self.input.text().replace(',', '.')
        try:
            v = float(txt)
            if 0 < v < 100:
                return True
        except ValueError:
            pass
        QMessageBox.warning(self, "Ошибка", "Введите эффект от 0 до 100%")
        return False


class UsersPage(QWizardPage):
    def __init__(self, texts, default_value: str):
        super().__init__()
        self.setTitle(texts['wizard_step3'])
        self.setSubTitle(texts['wizard_step3_hint'])
        self.input = QLineEdit()
        self.input.setText(default_value)
        self.input.setValidator(QIntValidator(1, 10**9))
        self.input.setToolTip(texts['wizard_step3_hint'])
        layout = QVBoxLayout()
        layout.addWidget(self.input)
        self.setLayout(layout)
        self.registerField("users*", self.input)

    def validatePage(self) -> bool:
        txt = self.input.text()
        if txt.isdigit() and int(txt) > 0:
            return True
        QMessageBox.warning(self, "Ошибка", "Введите количество пользователей (>0)")
        return False


class Wizard(QWizard):
    def __init__(self, parent=None, lang="RU"):
        super().__init__(parent)
        # Текущие значения из главного окна
        cr_def     = f"{parent.baseline_slider.value()/10:.1f}"
        uplift_def = f"{parent.uplift_slider.value()/10:.1f}"
        users_def  = parent.users_A_var.text()

        # Локализация
        self.i18n = {
            'RU': {
                'wizard_title':      "Помощник настройки теста",
                'wizard_step1':      "Шаг 1: Базовая конверсия (%)",
                'wizard_step1_hint': "Укажите текущую CR, например 4.0",
                'wizard_step2':      "Шаг 2: Uplift (%)",
                'wizard_step2_hint': "Желаемый uplift, например 12.0",
                'wizard_step3':      "Шаг 3: Количество пользователей",
                'wizard_step3_hint': "Всего пользователей, например 1200",
            },
            'EN': {
                'wizard_title':      "Test Setup Wizard",
                'wizard_step1':      "Step 1: Baseline CR (%)",
                'wizard_step1_hint': "Enter current CR, e.g. 4.0",
                'wizard_step2':      "Step 2: Uplift (%)",
                'wizard_step2_hint': "Desired uplift, e.g. 12.0",
                'wizard_step3':      "Step 3: Total users",
                'wizard_step3_hint': "Total users, e.g. 1200",
            }
        }
        texts = self.i18n[lang]

        # Заголовок
        self.setWindowTitle(texts['wizard_title'])
        # Наследуем палитру тёмной темы из родителя
        if parent:
            self.setPalette(parent.palette())
            self.setAutoFillBackground(True)

        # Создаём и добавляем страницы
        p1 = BaselinePage(texts, cr_def)
        p2 = UpliftPage(texts, uplift_def)
        p3 = UsersPage(texts, users_def)
        self.addPage(p1)
        self.addPage(p2)
        self.addPage(p3)

        # Кнопка «Готово» на последней странице
        self.setOption(QWizard.WizardOption.HaveFinishButtonOnEarlyPages, True)
        self.setOption(QWizard.WizardOption.NoCancelButton, False)

        # По клику «Готово» переносим значения в main window
        finish_btn = self.button(QWizard.WizardButton.FinishButton)
        finish_btn.clicked.connect(self.commit)

    def commit(self):
        cr     = float(self.field("baseline"))
        uplift = float(self.field("uplift"))
        users  = self.field("users")
        parent = self.parent()

        # Обновляем главный UI
        parent.baseline_slider.setValue(int(cr * 10))
        parent.uplift_slider.setValue(int(uplift * 10))
        parent.users_A_var.setText(users)
        parent.users_B_var.setText(users)
        parent.users_C_var.setText(users)
