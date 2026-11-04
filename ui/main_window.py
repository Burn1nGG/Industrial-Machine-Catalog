"""
Main Application Window for Industrial Equipment Catalog.
"""
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from db_manager import DatabaseManager
from folder_router import FolderRouter
from ui.db_settings_dialog import DBSettingsDialog
from ui.detail_card_dialog import DetailCardDialog
from ui.all_maintenance_dialog import AllMaintenanceDialog
from ui.login_dialog import LoginDialog
from ui.styles import STYLESHEET

TABLE_COLUMNS = [
    {"title": "Инв. №", "width": 80, "sortable": True},
    {"title": "Наименование станка", "width": 460, "sortable": True},
    {"title": "Цех", "width": 85, "sortable": True},
    {"title": "ЧПУ / Контроллер", "width": 150, "sortable": True},
    {"title": "IP-адрес", "width": 115, "sortable": True},
    {"title": "Статус", "width": 105, "sortable": True},
    {"title": "Действия", "width": 135, "sortable": False},
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Справочник промышленного оборудования — Поиск и Картотека станков")
        self.resize(1150, 720)
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Core Modules
        self.db_manager = DatabaseManager()
        self.folder_router = FolderRouter(self.db_manager.config.get("storage"))

        self.equipment_list = []
        self._active_sort_column = None
        self._active_sort_order = Qt.SortOrder.AscendingOrder
        
        # Apply Modern QSS Styling
        self.setStyleSheet(STYLESHEET)
        
        self.init_ui()
        self.load_workshops()
        self.on_search() # Начальный поиск при запуске

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ---------------- 1. COMPACT HEADER BAR ----------------
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(8)

        # App Logo & Title (compact single line)
        title_box = QHBoxLayout()
        title_box.setSpacing(6)
        title_lbl = QLabel("🏭 Справочник оборудования")
        title_lbl.setObjectName("AppTitle")
        title_box.addWidget(title_lbl)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Database connection status pill
        self.db_status_pill = QLabel("Подключение: PostgreSQL")
        self.db_status_pill.setObjectName("StatusPillWork")
        self.db_status_pill.setFixedHeight(26)
        header_layout.addWidget(self.db_status_pill)

        # Enterprise Maintenance Log Button
        self.btn_all_maint = QPushButton("🛠 История обслуживания")
        self.btn_all_maint.setObjectName("CardButton")
        self.btn_all_maint.setFixedHeight(28)
        self.btn_all_maint.setStyleSheet("font-size: 12px; padding: 4px 12px;")
        self.btn_all_maint.setToolTip("Открыть сводный журнал обслуживания и неисправностей всего оборудования")
        self.btn_all_maint.clicked.connect(self.open_all_maintenance_dialog)
        header_layout.addWidget(self.btn_all_maint)

        # DB Settings Button
        self.btn_settings = QPushButton("⚙ Настройки")
        self.btn_settings.setObjectName("SettingsButton")
        self.btn_settings.setFixedHeight(28)
        self.btn_settings.setStyleSheet("font-size: 12px; padding: 4px 12px;")
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        header_layout.addWidget(self.btn_settings)

        # Role & User Status Pill
        self.auth_status_pill = QLabel("👁 Только чтение")
        self.auth_status_pill.setObjectName("StatusPillViewer")
        self.auth_status_pill.setFixedHeight(26)
        header_layout.addWidget(self.auth_status_pill)

        # Login / Logout Button
        self.btn_auth = QPushButton("🔑 Войти")
        self.btn_auth.setObjectName("AuthButton")
        self.btn_auth.setFixedHeight(28)
        self.btn_auth.setStyleSheet("font-size: 12px; padding: 4px 12px;")
        self.btn_auth.setToolTip("Войти как редактор или администратор для изменения базы данных")
        self.btn_auth.clicked.connect(self.on_auth_clicked)
        header_layout.addWidget(self.btn_auth)

        # Connect user state change
        self.db_manager.auth_manager.user_changed.connect(self.on_user_changed)

        main_layout.addWidget(header_frame)

        # ---------------- 2. COMPACT SEARCH FILTERS ROW ----------------
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(6, 4, 6, 4)
        filter_layout.setSpacing(6)

        # Workshop Dropdown (Цех)
        ws_lbl = QLabel("Цех:")
        ws_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8;")
        self.ws_combo = QComboBox()
        self.ws_combo.addItem("— Все цеха —", 0)
        self.ws_combo.setFixedHeight(28)
        self.ws_combo.setMinimumWidth(110)
        filter_layout.addWidget(ws_lbl)
        filter_layout.addWidget(self.ws_combo, 2)

        # Machine Number / Inventory Number
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("Инв. / серийный номер...")
        self.num_input.setFixedHeight(28)
        self.num_input.setMinimumWidth(120)
        self.num_input.returnPressed.connect(self.on_search)
        filter_layout.addWidget(self.num_input, 2)

        # Machine Name / Model
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название / модель станка / ЧПУ...")
        self.name_input.setFixedHeight(28)
        self.name_input.setMinimumWidth(160)
        self.name_input.returnPressed.connect(self.on_search)
        filter_layout.addWidget(self.name_input, 3)

        # Action Buttons
        self.btn_search = QPushButton("🔍 Найти")
        self.btn_search.setObjectName("SearchButton")
        self.btn_search.setFixedHeight(28)
        self.btn_search.setStyleSheet("font-size: 12px; padding: 4px 14px;")
        self.btn_search.clicked.connect(self.on_search)
        filter_layout.addWidget(self.btn_search)

        self.btn_reset = QPushButton("🔄 Сброс")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.setFixedHeight(28)
        self.btn_reset.setStyleSheet("font-size: 12px; padding: 4px 12px;")
        self.btn_reset.clicked.connect(self.on_reset)
        filter_layout.addWidget(self.btn_reset)

        main_layout.addWidget(filter_frame)

        # ---------------- 3. HIGH-DENSITY RESULTS TABLE ----------------
        results_frame = QFrame()
        results_frame.setObjectName("ResultsFrame")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(6, 4, 6, 4)
        results_layout.setSpacing(4)

        # Summary Bar
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(4, 0, 4, 0)
        self.results_count_lbl = QLabel("Найдено оборудования: 0 шт.")
        self.results_count_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #F8FAFC;")
        
        summary_hint = QLabel("💡 Двойной клик открывает карточку станка")
        summary_hint.setStyleSheet("font-size: 11px; color: #94A3B8; font-style: italic;")

        summary_layout.addWidget(self.results_count_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(summary_hint)
        results_layout.addLayout(summary_layout)

        # Table Widget
        self.table = QTableWidget()
        self.table.setObjectName("EquipmentTable")
        self.table.setColumnCount(len(TABLE_COLUMNS))

        tbl_font = QFont()
        tbl_font.setPointSize(9)
        self.table.setFont(tbl_font)

        self._update_header_labels()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(50)
        header.setStretchLastSection(False)
        header.setHighlightSections(True)
        header.setDefaultSectionSize(100)

        for idx, col_info in enumerate(TABLE_COLUMNS):
            self.table.setColumnWidth(idx, col_info["width"])
            if not col_info["sortable"]:
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Fixed)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # High-density rows (26px) allows viewing 20-30 rows at once
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_table_double_clicked)
        header.sectionClicked.connect(self.on_header_clicked)
        header.setSortIndicatorShown(False)

        results_layout.addWidget(self.table)
        main_layout.addWidget(results_frame, 1)

        # ---------------- 4. STATUS BAR ----------------
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar("Готово к работе.")

    def load_workshops(self):
        """Загрузка списка цехов из базы данных в ComboBox."""
        self.ws_combo.blockSignals(True)
        self.ws_combo.clear()
        self.ws_combo.addItem("— Все цеха —", 0)
        workshops = self.db_manager.get_workshops()
        for ws in workshops:
            self.ws_combo.addItem(f"{ws['name']}", ws['id'])
        self.ws_combo.blockSignals(False)

        status_ok, status_msg = self.db_manager.test_connection()
        if status_ok:
            self.db_status_pill.setText("Режим: PostgreSQL Online")
            self.db_status_pill.setObjectName("StatusPillWork")
        else:
            self.db_status_pill.setText("Режим: PostgreSQL (нет соединения)")
            self.db_status_pill.setObjectName("StatusPillMaint")
        self.db_status_pill.style().unpolish(self.db_status_pill)
        self.db_status_pill.style().polish(self.db_status_pill)

    def on_search(self):
        ws_id = self.ws_combo.currentData()
        num_val = self.num_input.text().strip()
        name_val = self.name_input.text().strip()

        status_ok, status_msg = self.db_manager.test_connection()
        if not status_ok:
            self.equipment_list = []
            self.display_equipment([])
            self.update_status_bar(f"Нет соединения с PostgreSQL: {status_msg}")
            return

        self.equipment_list = self.db_manager.search_equipment(
            workshop_id=ws_id,
            machine_number=num_val,
            machine_name=name_val
        )

        self.display_equipment(self.equipment_list)
        
        # Обновление текста состояния
        search_desc = []
        if ws_id and ws_id != 0:
            search_desc.append(f"Цех: {self.ws_combo.currentText()}")
        if num_val:
            search_desc.append(f"№: '{num_val}'")
        if name_val:
            search_desc.append(f"Название: '{name_val}'")

        filt_str = ", ".join(search_desc) if search_desc else "Все записи"
        sort_desc = ""
        if self._active_sort_column is not None and self._active_sort_column < len(TABLE_COLUMNS):
            col_title = TABLE_COLUMNS[self._active_sort_column]["title"]
            order_name = "по возрастанию ▲" if self._active_sort_order == Qt.SortOrder.AscendingOrder else "по убыванию ▼"
            sort_desc = f" | Сортировка: {col_title} ({order_name})"

        self.update_status_bar(f"Поиск завершен [{filt_str}]. Найдено: {len(self.equipment_list)} шт.{sort_desc}")

    def _natural_sort_key(self, value):
        """Естественная сортировка для чисел, строк, IP-адресов и пустых значений."""
        if value is None:
            return (2, ())
        text = str(value).strip()
        if not text:
            return (2, ())
        chunks = []
        for part in re.split(r'(\d+)', text):
            if part.isdigit():
                chunks.append((0, int(part)))
            elif part:
                chunks.append((1, part.lower()))
        return (0, tuple(chunks))

    def _get_sort_value(self, eq, column):
        if column == 0:
            return self._natural_sort_key(eq.get('inventory_number'))
        if column == 1:
            return self._natural_sort_key(eq.get('name'))
        if column == 2:
            return self._natural_sort_key(eq.get('workshop_name') or eq.get('workshop_code'))
        if column == 3:
            return self._natural_sort_key(eq.get('controller') or eq.get('cnc_controller'))
        if column == 4:
            return self._natural_sort_key(eq.get('ip_address'))
        if column == 5:
            return self._natural_sort_key(eq.get('status'))
        return self._natural_sort_key("")

    def _sort_equipment_items(self, equipment_items, column):
        if column is None or column >= len(TABLE_COLUMNS) or not TABLE_COLUMNS[column]["sortable"]:
            return list(equipment_items)
        reverse = self._active_sort_order == Qt.SortOrder.DescendingOrder
        return sorted(equipment_items, key=lambda eq: self._get_sort_value(eq, column), reverse=reverse)

    def _update_header_labels(self):
        """Обновляет заголовки таблицы с визуальными индикаторами направления сортировки."""
        for idx, col_info in enumerate(TABLE_COLUMNS):
            base_title = col_info["title"]
            if col_info["sortable"]:
                if self._active_sort_column == idx:
                    arrow = " ▲" if self._active_sort_order == Qt.SortOrder.AscendingOrder else " ▼"
                    header_text = f"{base_title}{arrow}"
                    tooltip = f"Столбец: «{base_title}» (активна сортировка {'по возрастанию ▲' if self._active_sort_order == Qt.SortOrder.AscendingOrder else 'по убыванию ▼'}).\nНажмите для смены направления."
                else:
                    header_text = base_title
                    tooltip = f"Нажмите для сортировки по столбцу «{base_title}»"
            else:
                header_text = base_title
                tooltip = base_title

            item = self.table.horizontalHeaderItem(idx)
            if not item:
                item = QTableWidgetItem(header_text)
                self.table.setHorizontalHeaderItem(idx, item)
            else:
                item.setText(header_text)
            item.setToolTip(tooltip)

    def display_equipment(self, equipment_items):
        items_to_display = self._sort_equipment_items(equipment_items, self._active_sort_column)
        self.table.setRowCount(0)

        sort_info = ""
        if self._active_sort_column is not None and self._active_sort_column < len(TABLE_COLUMNS):
            col_title = TABLE_COLUMNS[self._active_sort_column]["title"]
            arrow = "▲" if self._active_sort_order == Qt.SortOrder.AscendingOrder else "▼"
            sort_info = f"  •  Сортировка: «{col_title}» {arrow}"

        self.results_count_lbl.setText(f"Найдено оборудования: {len(equipment_items)} шт.{sort_info}")

        for row_idx, eq in enumerate(items_to_display):
            self.table.insertRow(row_idx)

            # Columns
            inv_item = QTableWidgetItem(str(eq.get('inventory_number', '')))
            inv_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            inv_item.setData(Qt.ItemDataRole.UserRole, eq)

            name_item = QTableWidgetItem(str(eq.get('name', '')))
            ws_item = QTableWidgetItem(str(eq.get('workshop_name', eq.get('workshop_code', '-'))))
            ws_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            cnc_item = QTableWidgetItem(str(eq.get('cnc_controller', '-')))
            ip_item = QTableWidgetItem(str(eq.get('ip_address', '-')))
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            status = eq.get('status', 'В работе')
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row_idx, 0, inv_item)
            self.table.setItem(row_idx, 1, name_item)
            self.table.setItem(row_idx, 2, ws_item)
            self.table.setItem(row_idx, 3, cnc_item)
            self.table.setItem(row_idx, 4, ip_item)
            self.table.setItem(row_idx, 5, status_item)

            # Action cell: 2 compact buttons (Folder, Card)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 1, 2, 1)
            action_layout.setSpacing(4)

            btn_folder = QPushButton("📁")
            btn_folder.setObjectName("FolderButton")
            btn_folder.setToolTip("Открыть папку станка в Windows Explorer")
            btn_folder.setFixedSize(26, 20)
            btn_folder.setStyleSheet("font-size: 11px; padding: 0px;")
            btn_folder.clicked.connect(lambda checked=False, eq_data=eq: self.open_equipment_folder(eq_data))

            btn_card = QPushButton("🛈 Карточка")
            btn_card.setObjectName("CardButton")
            btn_card.setToolTip("Просмотреть подробную техническую карточку станка")
            btn_card.setFixedHeight(20)
            btn_card.setStyleSheet("font-size: 11px; padding: 1px 6px;")
            btn_card.clicked.connect(lambda checked=False, eq_data=eq: self.open_equipment_card(eq_data))

            action_layout.addWidget(btn_folder)
            action_layout.addWidget(btn_card)

            self.table.setCellWidget(row_idx, 6, action_widget)

    def _update_header_sort_state(self):
        header = self.table.horizontalHeader()
        if self._active_sort_column is not None and self._active_sort_column < len(TABLE_COLUMNS) and TABLE_COLUMNS[self._active_sort_column]["sortable"]:
            header.setSortIndicatorShown(True)
            header.setSortIndicator(self._active_sort_column, self._active_sort_order)
        else:
            header.setSortIndicatorShown(False)
        self._update_header_labels()

    def on_header_clicked(self, column):
        if column >= len(TABLE_COLUMNS) or not TABLE_COLUMNS[column]["sortable"]:
            return

        if self._active_sort_column == column:
            if self._active_sort_order == Qt.SortOrder.AscendingOrder:
                self._active_sort_order = Qt.SortOrder.DescendingOrder
            else:
                self._active_sort_order = Qt.SortOrder.AscendingOrder
        else:
            self._active_sort_column = column
            self._active_sort_order = Qt.SortOrder.AscendingOrder

        self._update_header_sort_state()
        self.display_equipment(self.equipment_list)

    def on_reset(self):
        self.ws_combo.setCurrentIndex(0)
        self.num_input.clear()
        self.name_input.clear()
        self._active_sort_column = None
        self._active_sort_order = Qt.SortOrder.AscendingOrder
        self._update_header_sort_state()
        self.on_search()


    def on_table_double_clicked(self, row, column):
        item = self.table.item(row, 0)
        if item:
            eq_data = item.data(Qt.ItemDataRole.UserRole)
            if eq_data:
                self.open_equipment_card(eq_data)

    def open_equipment_folder(self, eq_data):
        found, path, msg = self.folder_router.resolve_equipment_folder(eq_data)
        if path:
            self.folder_router.open_folder_in_explorer(path)
            self.update_status_bar(f"Папка открыта в проводнике: {path}")

    def open_equipment_card(self, eq_data):
        dialog = DetailCardDialog(eq_data, self.db_manager, self.folder_router, self)
        dialog.setWindowState(Qt.WindowState.WindowMaximized)
        if dialog.exec() == DetailCardDialog.DialogCode.Accepted:
            # Обновить результаты таблицы в случае изменений
            self.on_search()

    def open_settings_dialog(self):
        dialog = DBSettingsDialog(self.db_manager, self.folder_router, self)
        if dialog.exec() == DBSettingsDialog.DialogCode.Accepted:
            self.load_workshops()
            self.on_search()

    def on_auth_clicked(self):
        if self.db_manager.auth_manager.is_authenticated():
            reply = QMessageBox.question(
                self,
                "Выход из системы",
                "Вы уверены, что хотите выйти из учётной записи и перейти в режим только для чтения?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.auth_manager.logout()
                self.update_status_bar("Выполнен выход. Включен режим только для чтения.")
        else:
            dlg = LoginDialog(self.db_manager.auth_manager, self)
            if dlg.exec() == LoginDialog.DialogCode.Accepted:
                self.update_status_bar(f"Авторизован: {self.db_manager.auth_manager.get_display_name()}")

    def on_user_changed(self, user):
        if user:
            self.auth_status_pill.setText(f"👤 {self.db_manager.auth_manager.get_display_name()}")
            self.auth_status_pill.setObjectName("StatusPillUser")
            self.btn_auth.setText("🚪 Выйти")
            self.btn_auth.setObjectName("LogoutButton")
            self.btn_auth.setToolTip("Выйти из учётной записи (перейти в режим только для чтения)")
        else:
            self.auth_status_pill.setText("👁 Только чтение")
            self.auth_status_pill.setObjectName("StatusPillViewer")
            self.btn_auth.setText("🔑 Войти")
            self.btn_auth.setObjectName("AuthButton")
            self.btn_auth.setToolTip("Войти как редактор или администратор для изменения базы данных")

        self.auth_status_pill.style().unpolish(self.auth_status_pill)
        self.auth_status_pill.style().polish(self.auth_status_pill)
        self.btn_auth.style().unpolish(self.btn_auth)
        self.btn_auth.style().polish(self.btn_auth)

    def open_all_maintenance_dialog(self):
        dialog = AllMaintenanceDialog(self.db_manager, self.folder_router, self)
        dialog.setWindowState(Qt.WindowState.WindowMaximized)
        dialog.exec()
        self.on_search()

    def update_status_bar(self, message):
        base_path, storage_desc = self.folder_router.get_base_archive_path()
        self.status_bar.showMessage(f"{message}  |  Сетевой архив: {storage_desc} ({base_path})")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_name_column_width()

    def showEvent(self, event):
        super().showEvent(event)
        self._adjust_name_column_width()

    def _adjust_name_column_width(self):
        """Оптимизирует ширину столбца 'Наименование станка', занимая свободное пространство экрана."""
        if not hasattr(self, 'table'):
            return
        total_width = self.table.viewport().width()
        if total_width <= 0:
            return
        other_widths = sum(
            self.table.columnWidth(i)
            for i in range(self.table.columnCount())
            if i != 1
        )
        remaining = total_width - other_widths
        if remaining > TABLE_COLUMNS[1]["width"]:
            self.table.setColumnWidth(1, remaining)

