try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
except Exception:  # pragma: no cover - allow tests without PyQt installed
    QDialog = type("QDialog", (), {"exec": lambda self: 0})
    QVBoxLayout = QLabel = QLineEdit = QPushButton = type(
        "Widget",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "setPlaceholderText": lambda *a, **k: None,
            "text": lambda self: "",
        },
    )


class LoginDialog(QDialog):
    """Simple dialog to collect login credentials."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Login")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_edit)
        layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        if hasattr(self.password_edit, "setEchoMode"):
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)  # type: ignore
        layout.addWidget(self.password_edit)
        self.login_button = QPushButton("Login")
        if hasattr(self.login_button, "clicked"):
            self.login_button.clicked.connect(self.accept)  # type: ignore
        layout.addWidget(self.login_button)

    def credentials(self) -> tuple[str, str]:
        return self.username_edit.text(), self.password_edit.text()
