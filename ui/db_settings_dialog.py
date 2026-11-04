"""
Database & System Settings Dialog for Industrial Equipment Catalog App.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt
from database.init_db import init_database

class DBSettingsDialog(QDialog):
    def __init__(self, db_manager, folder_router, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.folder_router = folder_router
        self.setWindowTitle("Настройки подключения к базе данных и архиву")
        self.setMinimumWidth(540)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Параметры подключения")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8; margin-bottom: 8px;")
        layout.addWidget(title_label)

        # Group 1: PostgreSQL Settings
        db_group = QGroupBox("База данных PostgreSQL")
        db_group.setStyleSheet("QGroupBox { font-weight: bold; color: #F1F5F9; border: 1px solid #334155; margin-top: 6px; padding-top: 12px; }")
        db_layout = QFormLayout(db_group)

        curr_db = self.db_manager.config.get("db", {})
        
        self.host_input = QLineEdit(curr_db.get("host", "localhost"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(int(curr_db.get("port", 5432)))
        self.dbname_input = QLineEdit(curr_db.get("dbname", "postgres"))
        self.user_input = QLineEdit(curr_db.get("user", "postgres"))
        self.pass_input = QLineEdit(curr_db.get("password", "superuser"))
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        db_layout.addRow("Сервер (Host):", self.host_input)
        db_layout.addRow("Порт (Port):", self.port_input)
        db_layout.addRow("Имя БД (Database):", self.dbname_input)
        db_layout.addRow("Пользователь (User):", self.user_input)
        db_layout.addRow("Пароль (Password):", self.pass_input)

        layout.addWidget(db_group)

        # Group 2: Storage Settings
        storage_group = QGroupBox("Сетевой архив оборудования")
        storage_group.setStyleSheet("QGroupBox { font-weight: bold; color: #F1F5F9; border: 1px solid #334155; margin-top: 6px; padding-top: 12px; }")
        storage_layout = QFormLayout(storage_group)

        curr_storage = self.db_manager.config.get("storage", {})
        self.unc_input = QLineEdit(curr_storage.get("unc_path", "\\\\Synology_DS423\\Share_folder"))
        self.unc_alt_input = QLineEdit(curr_storage.get("unc_path_alt", "\\\\100.76.39.21\\Share_folder"))
        self.drive_input = QLineEdit(curr_storage.get("network_drive_path", "S:\\New Archive"))
        self.fallback_input = QLineEdit(curr_storage.get("fallback_local_path", ""))
        self.fallback_input.setPlaceholderText("Опционально: C:\\Equipment_Archive_Backup")
        self.path_mode_combo = QComboBox()
        self.path_mode_combo.addItem("Synology_DS423 (Локальная сеть)", 1)
        self.path_mode_combo.addItem("Удалённый архив 100.76.39.21 (VPN / Диск S:)", 2)
        mode_idx = 0 if int(curr_storage.get("path_mode", 1)) == 1 else 1
        self.path_mode_combo.setCurrentIndex(mode_idx)

        storage_layout.addRow("Сетевое имя (Synology_DS423):", self.unc_input)
        storage_layout.addRow("Удалённый UNC (100.76.39.21):", self.unc_alt_input)
        storage_layout.addRow("Сетевой диск (S:):", self.drive_input)
        storage_layout.addRow("Режим подключения:", self.path_mode_combo)
        storage_layout.addRow("Резервная локальная папка:", self.fallback_input)

        layout.addWidget(storage_group)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(self.status_label)

        # Config file path label
        self.config_path_label = QLabel(f"Файл настроек: {self.db_manager.config_file}")
        self.config_path_label.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 2px;")
        self.config_path_label.setWordWrap(True)
        layout.addWidget(self.config_path_label)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()

        self.btn_test = QPushButton("Проверить связь с БД")
        self.btn_test.setObjectName("SettingsButton")
        self.btn_test.clicked.connect(self.on_test_connection)

        self.btn_init = QPushButton("Инициализировать БД")
        self.btn_init.setObjectName("SettingsButton")
        self.btn_init.clicked.connect(self.on_init_database)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setObjectName("SearchButton")
        self.btn_save.clicked.connect(self.on_save)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("ResetButton")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_init)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def get_form_config(self):
        return {
            "db": {
                "host": self.host_input.text().strip(),
                "port": self.port_input.value(),
                "dbname": self.dbname_input.text().strip(),
                "user": self.user_input.text().strip(),
                "password": self.pass_input.text()
            },
            "storage": {
                "network_drive_path": self.drive_input.text().strip(),
                "unc_path": self.unc_input.text().strip(),
                "unc_path_alt": self.unc_alt_input.text().strip(),
                "fallback_local_path": self.fallback_input.text().strip(),
                "path_mode": int(self.path_mode_combo.currentData() or 1)
            }
        }

    def on_test_connection(self):
        cfg = self.get_form_config()
        success, msg = self.db_manager.test_connection(cfg["db"])
        if success:
            self.status_label.setText(f"✔ {msg}")
            self.status_label.setStyleSheet("color: #34D399;")
        else:
            self.status_label.setText(f"✖ {msg}")
            self.status_label.setStyleSheet("color: #FCA5A5;")

    def on_init_database(self):
        cfg = self.get_form_config()
        reply = QMessageBox.question(
            self,
            "Инициализация базы данных",
            "Вы уверены, что хотите выполнить SQL-скрипт инициализации таблиц и тестовых данных?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = init_database(cfg["db"])
            if success:
                QMessageBox.information(self, "Успех", msg)
                self.status_label.setText("✔ Таблицы и тестовые данные в PostgreSQL успешно созданы!")
                self.status_label.setStyleSheet("color: #34D399;")
            else:
                QMessageBox.critical(self, "Ошибка", msg)
                self.status_label.setText(f"✖ {msg}")
                self.status_label.setStyleSheet("color: #FCA5A5;")

    def on_save(self):
        cfg = self.get_form_config()
        if self.db_manager.save_config(cfg):
            self.folder_router.config = cfg["storage"]
            self.folder_router._cached_base_path = None
            self.folder_router._cached_desc = None
            QMessageBox.information(
                self,
                "Сохранено",
                f"Настройки успешно сохранены в:\n{self.db_manager.config_file}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить файл конфигурации:\n{self.db_manager.config_file}"
            )
