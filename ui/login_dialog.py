"""
Login Dialog for Industrial Equipment Catalog App.
Allows users to authenticate for editor/admin permissions.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle("Авторизация пользователя")
        self.setFixedWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title_lbl = QLabel("Вход в систему")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        subtitle_lbl = QLabel("Для добавления, изменения или удаления данных")
        subtitle_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        layout.addLayout(title_box)

        # Form Box
        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 12px; }"
        )
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Например: admin или operator")
        self.username_input.setMinimumHeight(32)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(32)
        self.password_input.returnPressed.connect(self.on_login)

        form_layout.addRow("Логин:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        layout.addWidget(form_frame)

        # Status Error / Info Label
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("color: #F87171; font-size: 11px; padding: 2px;")
        layout.addWidget(self.status_lbl)

        # Hint Label
        hint_lbl = QLabel(
            "ℹ По умолчанию каталог доступен для поиска и просмотра без авторизации."
        )
        hint_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        hint_lbl.setWordWrap(True)
        layout.addWidget(hint_lbl)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_login = QPushButton("Войти")
        self.btn_login.setObjectName("SearchButton")
        self.btn_login.setMinimumHeight(32)
        self.btn_login.clicked.connect(self.on_login)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("ResetButton")
        self.btn_cancel.setMinimumHeight(32)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.btn_login.setEnabled(False)
        self.status_lbl.setText("Проверка...")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 11px;")

        success, msg = self.auth_manager.login(username, password)
        self.btn_login.setEnabled(True)

        if success:
            self.accept()
        else:
            self.status_lbl.setText(msg)
            self.status_lbl.setStyleSheet("color: #F87171; font-size: 11px;")
            self.password_input.selectAll()
            self.password_input.setFocus()

