"""
Main Application Window for Industrial Equipment Catalog.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QSize

from db_manager import DatabaseManager
from folder_router import FolderRouter
from ui.db_settings_dialog import DBSettingsDialog
from ui.detail_card_dialog import DetailCardDialog
from ui.styles import STYLESHEET

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Справочник промышленного оборудования — Поиск и Картотека станков")
        self.resize(1150, 720)

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
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # ---------------- 1. HEADER BAR ----------------
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)

        # App Logo & Title
        title_box = QVBoxLayout()
        title_lbl = QLabel("🏭 Справочник Промышленного Оборудования")
        title_lbl.setObjectName("AppTitle")
        subtitle_lbl = QLabel("Быстрый поиск станков, просмотр карточек и открытие папок по сети (S: для удалённого доступа / \\Synology_DS423\\Share_folder для локальной сети)")
        subtitle_lbl.setObjectName("AppSubTitle")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Database connection status pill
        self.db_status_pill = QLabel("Подключение: PostgreSQL")
        self.db_status_pill.setObjectName("StatusPillWork")
        header_layout.addWidget(self.db_status_pill)

        # DB Settings Button
        self.btn_settings = QPushButton("⚙ Настройки БД и Диска")
        self.btn_settings.setObjectName("SettingsButton")
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        header_layout.addWidget(self.btn_settings)

        main_layout.addWidget(header_frame)

        # ---------------- 2. SEARCH FILTERS CARD ----------------
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_layout = QVBoxLayout(filter_frame)

        filter_title = QLabel("🔍 Фильтры поиска оборудования")
        filter_title.setObjectName("FilterTitle")
        filter_layout.addWidget(filter_title)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(14)

        # Input 1: Workshop Dropdown (Цех)
        ws_box = QVBoxLayout()
        ws_box.addWidget(QLabel("1. Выбрать цех:"))
        self.ws_combo = QComboBox()
        self.ws_combo.addItem("— Все цеха —", 0)
        ws_box.addWidget(self.ws_combo)
        inputs_layout.addLayout(ws_box, 2)

        # Input 2: Machine Number / Inventory Number (Номер станка)
        num_box = QVBoxLayout()
        num_box.addWidget(QLabel("2. Номер станка (Инвентарный / Серийный):"))
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("Например: INV-001042")
        self.num_input.returnPressed.connect(self.on_search)
        num_box.addWidget(self.num_input)
        inputs_layout.addLayout(num_box, 2)

        # Input 3: Machine Name / Model (Название/модель станка)
        name_box = QVBoxLayout()
        name_box.addWidget(QLabel("3. Название / Модель станка / ЧПУ:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: 1516Ф3 или DMG MORI")
        self.name_input.returnPressed.connect(self.on_search)
        name_box.addWidget(self.name_input)
        inputs_layout.addLayout(name_box, 3)

        # Action Buttons for Search
        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(0, 18, 0, 0)

        self.btn_search = QPushButton("🔍 Выполнить поиск")
        self.btn_search.setObjectName("SearchButton")
        self.btn_search.clicked.connect(self.on_search)

        self.btn_reset = QPushButton("🔄 Сбросить")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.clicked.connect(self.on_reset)

        btn_box.addWidget(self.btn_search)
        btn_box.addWidget(self.btn_reset)
        inputs_layout.addLayout(btn_box, 2)

        filter_layout.addLayout(inputs_layout)
        
        # Hint label requirement
        hint_lbl = QLabel("ℹ * Для поиска достаточно заполнить хотя бы одно из полей.")
        hint_lbl.setStyleSheet("color: #64748B; font-size: 11px; margin-top: 4px;")
        filter_layout.addWidget(hint_lbl)

        main_layout.addWidget(filter_frame)

        # ---------------- 3. RESULTS TABLE SECTION ----------------
        results_frame = QFrame()
        results_frame.setObjectName("ResultsFrame")
        results_layout = QVBoxLayout(results_frame)

        # Summary Bar
        summary_layout = QHBoxLayout()
        self.results_count_lbl = QLabel("Найдено оборудования: 0 шт.")
        self.results_count_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #F8FAFC;")
        
        summary_hint = QLabel("💡 Двойной клик по строке открывает карточку станка")
        summary_hint.setStyleSheet("font-size: 12px; color: #94A3B8; font-style: italic;")

        summary_layout.addWidget(self.results_count_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(summary_hint)
        results_layout.addLayout(summary_layout)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Инв. №",
            "Наименование станка",
            "Цех",
            "ЧПУ / Контроллер",
            "IP-адрес",
            "Статус",
            "Быстрые действия"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 230)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.cellDoubleClicked.connect(self.on_table_double_clicked)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.table.horizontalHeader().setSortIndicatorShown(False)

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
        self.update_status_bar(f"Поиск завершен [{filt_str}]. Найдено: {len(self.equipment_list)} шт.")

    def _normalize_sort_value(self, value):
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return (0, float(value))
        text = str(value).strip()
        if not text:
            return ""
        try:
            return (0, float(text))
        except ValueError:
            return (1, text.lower())

    def _get_sort_value(self, eq, column):
        if column == 0:
            return self._normalize_sort_value(eq.get('inventory_number'))
        if column == 1:
            return self._normalize_sort_value(eq.get('name'))
        if column == 2:
            return self._normalize_sort_value(eq.get('workshop_name') or eq.get('workshop_code'))
        if column == 3:
            return self._normalize_sort_value(eq.get('controller') or eq.get('cnc_controller'))
        if column == 4:
            return self._normalize_sort_value(eq.get('ip_address'))
        if column == 5:
            return self._normalize_sort_value(eq.get('status'))
        return self._normalize_sort_value("")

    def _sort_equipment_items(self, equipment_items, column):
        if column is None or column == 6:
            return list(equipment_items)
        reverse = self._active_sort_order == Qt.SortOrder.DescendingOrder
        return sorted(equipment_items, key=lambda eq: self._get_sort_value(eq, column), reverse=reverse)

    def display_equipment(self, equipment_items):
        items_to_display = self._sort_equipment_items(equipment_items, self._active_sort_column)
        self.table.setRowCount(0)
        self.results_count_lbl.setText(f"Найдено оборудования: {len(equipment_items)} шт.")

        for row_idx, eq in enumerate(items_to_display):
            self.table.insertRow(row_idx)

            # Columns
            inv_item = QTableWidgetItem(str(eq.get('inventory_number', '')))
            inv_item.setData(Qt.ItemDataRole.UserRole, eq)

            name_item = QTableWidgetItem(str(eq.get('name', '')))
            ws_item = QTableWidgetItem(str(eq.get('workshop_name', eq.get('workshop_code', '-'))))
            cnc_item = QTableWidgetItem(str(eq.get('cnc_controller', '-')))
            ip_item = QTableWidgetItem(str(eq.get('ip_address', '-')))

            status = eq.get('status', 'В работе')
            status_item = QTableWidgetItem(status)

            self.table.setItem(row_idx, 0, inv_item)
            self.table.setItem(row_idx, 1, name_item)
            self.table.setItem(row_idx, 2, ws_item)
            self.table.setItem(row_idx, 3, cnc_item)
            self.table.setItem(row_idx, 4, ip_item)
            self.table.setItem(row_idx, 5, status_item)

            # Action cell: 2 buttons (Folder, Card)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            btn_folder = QPushButton("📁 Папка")
            btn_folder.setObjectName("FolderButton")
            btn_folder.setToolTip("Открыть папку станка в Windows Explorer")
            btn_folder.clicked.connect(lambda checked=False, eq_data=eq: self.open_equipment_folder(eq_data))

            btn_card = QPushButton("🛈 Карточка")
            btn_card.setObjectName("CardButton")
            btn_card.setToolTip("Просмотреть подробную техническую карточку станка")
            btn_card.clicked.connect(lambda checked=False, eq_data=eq: self.open_equipment_card(eq_data))

            action_layout.addWidget(btn_folder)
            action_layout.addWidget(btn_card)

            self.table.setCellWidget(row_idx, 6, action_widget)

    def _update_header_sort_state(self):
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            if col == 6:
                continue
            if col == self._active_sort_column:
                header.setSectionHidden(col, False)
                header.setSortIndicatorShown(True)
                header.setSortIndicator(col, self._active_sort_order)
            else:
                header.setSortIndicatorShown(self._active_sort_column is not None)
                if self._active_sort_column is None:
                    header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

    def on_header_clicked(self, column):
        if column == 6:
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
        self.table.horizontalHeader().setSortIndicatorShown(False)
        self.on_search()

    def on_table_double_clicked(self, row, column):
        item = self.table.item(row, 0)
        if item:
            eq_data = item.data(Qt.ItemDataRole.UserRole)
            if eq_data:
                self.open_equipment_card(eq_data)

    def open_equipment_folder(self, eq_data):
        found, path, msg = self.folder_router.resolve_equipment_folder(eq_data)
        success, open_msg = self.folder_router.open_folder_in_explorer(path, create_if_missing=False)
        if success:
            self.update_status_bar(f"Папка открыта: {path}")
        else:
            reply = QMessageBox.question(
                self,
                "Папка станка не найдена",
                f"{open_msg}\n\nСоздать новую папку по адресу:\n{path}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                ok, c_msg = self.folder_router.open_folder_in_explorer(path, create_if_missing=True)
                if ok:
                    QMessageBox.information(self, "Создано", f"Папка создана:\n{path}")
                    self.update_status_bar(f"Папка создана и открыта: {path}")
                else:
                    QMessageBox.critical(self, "Ошибка", c_msg)

    def open_equipment_card(self, eq_data):
        dialog = DetailCardDialog(eq_data, self.db_manager, self.folder_router, self)
        if dialog.exec() == DetailCardDialog.DialogCode.Accepted:
            # Обновить результаты таблицы в случае изменений
            self.on_search()

    def open_settings_dialog(self):
        dialog = DBSettingsDialog(self.db_manager, self.folder_router, self)
        if dialog.exec() == DBSettingsDialog.DialogCode.Accepted:
            self.load_workshops()
            self.on_search()

    def update_status_bar(self, message):
        base_path, storage_desc = self.folder_router.get_base_archive_path()
        self.status_bar.showMessage(f"{message}  |  Сетевой архив: {storage_desc} ({base_path})")
