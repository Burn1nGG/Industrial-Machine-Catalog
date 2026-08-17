"""
Detailed Machine Card Dialog for Industrial Equipment Catalog App.
Tabs wrapped in QScrollArea to prevent text clipping/cropping on any resolution.
"""
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QTabWidget, QWidget, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QScrollArea, QTextEdit,
    QAbstractItemView
)
from PySide6.QtCore import Qt

class DetailCardDialog(QDialog):
    def __init__(self, equipment_dict, db_manager, folder_router, parent=None):
        super().__init__(parent)
        self.eq_data = dict(equipment_dict)
        self.db_manager = db_manager
        self.folder_router = folder_router
        
        self.setWindowTitle(f"Подробная карточка оборудования — {self.eq_data.get('inventory_number', '')}")
        self.resize(1100, 750)
        self.setMinimumSize(800, 600)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Header Frame
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 10, 14, 10)
        
        title_box = QVBoxLayout()
        name_lbl = QLabel(self.eq_data.get('name', 'Без названия'))
        name_lbl.setStyleSheet("font-size: 19px; font-weight: bold; color: #38BDF8;")
        name_lbl.setWordWrap(True)

        sub_lbl = QLabel(f"Инв. №: {self.eq_data.get('inventory_number', '-')}   |   Контроллер: {self.eq_data.get('controller', '-')}   |   Цех: {self.eq_data.get('workshop_name', '-')}")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94A3B8;")
        sub_lbl.setWordWrap(True)

        title_box.addWidget(name_lbl)
        title_box.addWidget(sub_lbl)
        
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Status badge
        status = self.eq_data.get('status', 'В работе')
        status_lbl = QLabel(status)
        if status == 'В работе':
            status_lbl.setObjectName("StatusPillWork")
        elif status == 'На обслуживании':
            status_lbl.setObjectName("StatusPillMaint")
        elif status == 'Резерв':
            status_lbl.setObjectName("StatusPillReserve")
        else:
            status_lbl.setObjectName("StatusPillDecomm")
        
        header_layout.addWidget(status_lbl)
        main_layout.addWidget(header_frame)

        # Tab Widget
        self.tabs = QTabWidget()

        # --- TAB 1: General & Tech Specs (with Scroll Area) ---
        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.tab1 = QWidget()
        tab1_layout = QFormLayout(self.tab1)
        tab1_layout.setContentsMargins(16, 16, 16, 16)
        tab1_layout.setSpacing(12)

        self.inv_input = QLineEdit(str(self.eq_data.get('inventory_number', '')))
        self.inv_input.setMinimumHeight(32)

        self.name_input = QLineEdit(str(self.eq_data.get('name', '')))
        self.name_input.setMinimumHeight(32)

        self.controller_input = QLineEdit(str(self.eq_data.get('controller', '')))
        self.controller_input.setMinimumHeight(32)

        self.year_input = QSpinBox()
        self.year_input.setMinimumHeight(32)
        self.year_input.setRange(1900, 2100)
        self.year_input.setValue(int(self.eq_data.get('year_built') or self.eq_data.get('commissioning_year') or 2020))

        self.workshop_combo = QComboBox()
        self.workshop_combo.setMinimumHeight(32)
        self.workshops_list = self.db_manager.get_workshops()
        curr_ws_id = self.eq_data.get('workshop_id')
        selected_idx = 0
        for idx, ws in enumerate(self.workshops_list):
            self.workshop_combo.addItem(ws['name'], ws['id'])
            if ws['id'] == curr_ws_id:
                selected_idx = idx
        self.workshop_combo.setCurrentIndex(selected_idx)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumHeight(32)
        self.status_combo.addItems(['В работе', 'На обслуживании', 'Резерв', 'Списан'])
        self.status_combo.setCurrentText(status)

        self.folder_path_input = QLineEdit(str(self.eq_data.get('folder_path', self.eq_data.get('sub_folder', ''))))
        self.folder_path_input.setMinimumHeight(32)

        tab1_layout.addRow("Инвентарный номер:", self.inv_input)
        tab1_layout.addRow("Название станка:", self.name_input)
        tab1_layout.addRow("Контроллер / ЧПУ:", self.controller_input)
        tab1_layout.addRow("Год ввода в эксплуатацию:", self.year_input)
        tab1_layout.addRow("Цех размещения:", self.workshop_combo)
        tab1_layout.addRow("Статус:", self.status_combo)
        tab1_layout.addRow("Путь к папке архива:", self.folder_path_input)

        self.tab1_scroll.setWidget(self.tab1)
        self.tabs.addTab(self.tab1_scroll, "⚙ Технические данные")

        # --- TAB 2: IT & Software (with Scroll Area) ---
        self.tab2_scroll = QScrollArea()
        self.tab2_scroll.setWidgetResizable(True)
        self.tab2_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.tab2 = QWidget()
        tab2_layout = QFormLayout(self.tab2)
        tab2_layout.setContentsMargins(16, 16, 16, 16)
        tab2_layout.setSpacing(14)

        self.ip_input = QLineEdit(str(self.eq_data.get('ip_address', '')))
        self.ip_input.setMinimumHeight(32)

        self.mac_input = QLineEdit(str(self.eq_data.get('mac_address', '')))
        self.mac_input.setMinimumHeight(32)

        self.screen_input = QLineEdit(str(self.eq_data.get('screen', '')))
        self.screen_input.setMinimumHeight(32)

        self.processor_input = QLineEdit(str(self.eq_data.get('processor', '')))
        self.processor_input.setMinimumHeight(32)

        self.ram_input = QLineEdit(str(self.eq_data.get('ram', '')))
        self.ram_input.setMinimumHeight(32)

        self.rom_input = QLineEdit(str(self.eq_data.get('rom', '')))
        self.rom_input.setMinimumHeight(32)

        self.os_input = QLineEdit(str(self.eq_data.get('operating_system', '')))
        self.os_input.setMinimumHeight(32)

        self.antivirus_input = QLineEdit(str(self.eq_data.get('antivirus', '')))
        self.antivirus_input.setMinimumHeight(32)

        tab2_layout.addRow("IP-адрес контроллера:", self.ip_input)
        tab2_layout.addRow("MAC-адрес сетевой карты:", self.mac_input)
        tab2_layout.addRow("Экран / монитор:", self.screen_input)
        tab2_layout.addRow("Процессор:", self.processor_input)
        tab2_layout.addRow("ОЗУ:", self.ram_input)
        tab2_layout.addRow("ПЗУ / SSD:", self.rom_input)
        tab2_layout.addRow("Операционная система:", self.os_input)
        tab2_layout.addRow("Антивирус:", self.antivirus_input)

        self.tab2_scroll.setWidget(self.tab2)
        self.tabs.addTab(self.tab2_scroll, "💻 Сеть и Софт")

        # --- TAB 3: Documentation & Storage ---
        self.tab3 = QWidget()
        tab3_layout = QVBoxLayout(self.tab3)
        tab3_layout.setContentsMargins(16, 16, 16, 16)
        tab3_layout.setSpacing(12)

        # Storage info card
        storage_card = QFrame()
        storage_card.setObjectName("CardContentFrame")
        sc_layout = QVBoxLayout(storage_card)
        sc_layout.setSpacing(10)
        
        self.folder_status_lbl = QLabel("Поиск расположения папки...")
        self.folder_status_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #CBD5E1;")
        self.folder_status_lbl.setWordWrap(True)
        
        self.sub_folder_input = QLineEdit(str(self.eq_data.get('sub_folder', '')))
        self.sub_folder_input.setMinimumHeight(32)
        self.sub_folder_input.setPlaceholderText("Например: INV-001042_Токарно-карусельный")
        
        sf_layout = QHBoxLayout()
        sf_lbl = QLabel("Папка оборудования:")
        sf_lbl.setStyleSheet("font-weight: bold;")
        sf_layout.addWidget(sf_lbl)
        sf_layout.addWidget(self.sub_folder_input)
        
        self.btn_open_explorer = QPushButton("📁 Открыть папку оборудования в Windows Explorer")
        self.btn_open_explorer.setObjectName("FolderButton")
        self.btn_open_explorer.setStyleSheet("font-size: 14px; padding: 10px;")
        self.btn_open_explorer.clicked.connect(self.on_open_folder)

        sc_layout.addWidget(self.folder_status_lbl)
        sc_layout.addLayout(sf_layout)
        sc_layout.addWidget(self.btn_open_explorer)

        tab3_layout.addWidget(storage_card)

        # Docs table
        docs_lbl = QLabel("Прикрепленная документация (из PostgreSQL):")
        docs_lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 6px; color: #F1F5F9;")
        tab3_layout.addWidget(docs_lbl)

        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(3)
        self.docs_table.setHorizontalHeaderLabels(["Название документа", "Тип", "Путь / Файл"])
        self.docs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tab3_layout.addWidget(self.docs_table)

        self.load_docs()
        self.tabs.addTab(self.tab3, "📁 Сетевой Архив и Файлы")

        # --- TAB 4: Maintenance & Fault History ---
        self.tab4 = QWidget()
        tab4_layout = QVBoxLayout(self.tab4)
        tab4_layout.setContentsMargins(14, 14, 14, 14)
        tab4_layout.setSpacing(10)

        # Tab 4 Header Bar
        maint_header = QHBoxLayout()
        maint_title = QLabel("🛠 Журнал технического обслуживания и неисправностей")
        maint_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #F1F5F9;")
        
        self.maint_count_lbl = QLabel("Записей: 0")
        self.maint_count_lbl.setObjectName("MaintCountBadge")

        self.btn_refresh_maint = QPushButton("🔄 Обновить")
        self.btn_refresh_maint.setObjectName("ResetButton")
        self.btn_refresh_maint.clicked.connect(self.load_maintenance)

        maint_header.addWidget(maint_title)
        maint_header.addSpacing(8)
        maint_header.addWidget(self.maint_count_lbl)
        maint_header.addStretch()
        maint_header.addWidget(self.btn_refresh_maint)
        tab4_layout.addLayout(maint_header)

        # Maintenance Table
        self.maint_table = QTableWidget()
        self.maint_table.setColumnCount(6)
        self.maint_table.setHorizontalHeaderLabels([
            "ID",
            "Начало работ",
            "Окончание работ",
            "Тип работы / Категория",
            "Выполненные работы",
            "Неисправность / Примечания"
        ])
        self.maint_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.maint_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.maint_table.setAlternatingRowColors(False)
        self.maint_table.verticalHeader().setVisible(False)
        
        # Interactive column widths configuration
        header = self.maint_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        self.maint_table.setColumnWidth(0, 55)
        self.maint_table.setColumnWidth(1, 115)
        self.maint_table.setColumnWidth(2, 115)
        self.maint_table.setColumnWidth(3, 220)
        self.maint_table.setColumnWidth(4, 380)
        self.maint_table.setColumnWidth(5, 380)
        self.maint_table.itemSelectionChanged.connect(self.on_maint_row_selected)

        tab4_layout.addWidget(self.maint_table, 3)

        # Detailed editing view frame for selected row / new record
        self.maint_detail_frame = QFrame()
        self.maint_detail_frame.setObjectName("MaintenanceDetailFrame")
        detail_layout = QVBoxLayout(self.maint_detail_frame)
        detail_layout.setContentsMargins(12, 10, 12, 10)
        detail_layout.setSpacing(8)

        # Detail frame toolbar / header
        maint_detail_hdr = QHBoxLayout()
        self.maint_detail_title = QLabel("Редактирование записи ТО")
        self.maint_detail_title.setObjectName("MaintSectionTitle")
        
        self.btn_new_maint = QPushButton("➕ Добавить новую запись")
        self.btn_new_maint.setObjectName("ResetButton")
        self.btn_new_maint.clicked.connect(self.on_new_maint)

        self.btn_save_maint = QPushButton("💾 Сохранить запись ТО")
        self.btn_save_maint.setObjectName("SearchButton")
        self.btn_save_maint.clicked.connect(self.on_save_maint)

        self.btn_delete_maint = QPushButton("🗑 Удалить запись")
        self.btn_delete_maint.setObjectName("DeleteButton")
        self.btn_delete_maint.clicked.connect(self.on_delete_maint)

        maint_detail_hdr.addWidget(self.maint_detail_title)
        maint_detail_hdr.addStretch()
        maint_detail_hdr.addWidget(self.btn_new_maint)
        maint_detail_hdr.addWidget(self.btn_save_maint)
        maint_detail_hdr.addWidget(self.btn_delete_maint)
        detail_layout.addLayout(maint_detail_hdr)

        # Fields row: Work Type, Start Date, End Date
        fields_row = QHBoxLayout()
        fields_row.setSpacing(12)

        type_box = QVBoxLayout()
        type_box.setSpacing(3)
        type_lbl = QLabel("Тип работы / Категория:")
        type_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.maint_type_input = QLineEdit()
        self.maint_type_input.setPlaceholderText("Например: Анализ ПО / Плановое ТО / Ремонт")
        self.maint_type_input.setMinimumHeight(30)
        type_box.addWidget(type_lbl)
        type_box.addWidget(self.maint_type_input)

        start_box = QVBoxLayout()
        start_box.setSpacing(3)
        start_lbl = QLabel("Начало работ (ГГГГ-ММ-ДД):")
        start_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.maint_start_input = QLineEdit()
        self.maint_start_input.setPlaceholderText("2026-08-17")
        self.maint_start_input.setMinimumHeight(30)
        start_box.addWidget(start_lbl)
        start_box.addWidget(self.maint_start_input)

        end_box = QVBoxLayout()
        end_box.setSpacing(3)
        end_lbl = QLabel("Окончание работ (ГГГГ-ММ-ДД):")
        end_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #CBD5E1;")
        self.maint_end_input = QLineEdit()
        self.maint_end_input.setPlaceholderText("2026-08-17")
        self.maint_end_input.setMinimumHeight(30)
        end_box.addWidget(end_lbl)
        end_box.addWidget(self.maint_end_input)

        fields_row.addLayout(type_box, 2)
        fields_row.addLayout(start_box, 1)
        fields_row.addLayout(end_box, 1)
        detail_layout.addLayout(fields_row)

        text_boxes_layout = QHBoxLayout()
        text_boxes_layout.setSpacing(10)

        # Left box: Notes / Issue description (Editable)
        notes_box = QVBoxLayout()
        notes_box.setSpacing(4)
        notes_lbl = QLabel("⚠️ Неисправность / Исходная задача (notes):")
        notes_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #FBBF24;")
        self.maint_notes_view = QTextEdit()
        self.maint_notes_view.setObjectName("MaintDetailText")
        self.maint_notes_view.setReadOnly(False)
        self.maint_notes_view.setPlaceholderText("Введите описание неисправности, ошибки, отсутствующих компонентов или исходную задачу...")
        self.maint_notes_view.setMinimumHeight(95)
        notes_box.addWidget(notes_lbl)
        notes_box.addWidget(self.maint_notes_view)

        # Right box: Work performed / Result (Editable)
        work_box = QVBoxLayout()
        work_box.setSpacing(4)
        work_lbl = QLabel("⚙️ Выполненные работы / Результат (work_performed):")
        work_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #34D399;")
        self.maint_work_view = QTextEdit()
        self.maint_work_view.setObjectName("MaintDetailText")
        self.maint_work_view.setReadOnly(False)
        self.maint_work_view.setPlaceholderText("Введите описание выполненных работ, замененных деталей, статус восстановления...")
        self.maint_work_view.setMinimumHeight(95)
        work_box.addWidget(work_lbl)
        work_box.addWidget(self.maint_work_view)

        text_boxes_layout.addLayout(notes_box, 1)
        text_boxes_layout.addLayout(work_box, 1)
        detail_layout.addLayout(text_boxes_layout)

        tab4_layout.addWidget(self.maint_detail_frame, 2)

        self.current_maint_id = None
        self.maintenance_records = []
        self.load_maintenance()
        self.tabs.addTab(self.tab4, "🛠 История обслуживания и неисправностей")

        main_layout.addWidget(self.tabs, 1)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_quick_folder = QPushButton("📁 Открыть папку в Explorer")
        self.btn_quick_folder.setObjectName("FolderButton")
        self.btn_quick_folder.clicked.connect(self.on_open_folder)

        self.btn_save = QPushButton("Сохранить изменения")
        self.btn_save.setObjectName("SearchButton")
        self.btn_save.clicked.connect(self.on_save)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setObjectName("ResetButton")
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_quick_folder)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_close)

        main_layout.addLayout(btn_layout)

        # Check folder path on start
        self.update_folder_status()

    def update_folder_status(self):
        found, path, msg = self.folder_router.resolve_equipment_folder(self.eq_data)
        if found:
            self.folder_status_lbl.setText(f"✔ Статус папки: {msg}\nПуть: {path}")
            self.folder_status_lbl.setStyleSheet("color: #34D399; font-weight: bold;")
        else:
            self.folder_status_lbl.setText(f"⚠️ Статус папки: {msg}")
            self.folder_status_lbl.setStyleSheet("color: #FBBF24; font-weight: bold;")

    def load_docs(self):
        eq_id = self.eq_data.get('id')
        if not eq_id:
            return
        docs = self.db_manager.get_equipment_docs(eq_id)
        self.docs_table.setRowCount(len(docs))
        for row_idx, doc in enumerate(docs):
            self.docs_table.setItem(row_idx, 0, QTableWidgetItem(doc.get('title', '')))
            self.docs_table.setItem(row_idx, 1, QTableWidgetItem(doc.get('doc_type', '')))
            self.docs_table.setItem(row_idx, 2, QTableWidgetItem(doc.get('file_path_or_url', '')))

    @staticmethod
    def _format_date(dt_val):
        if not dt_val:
            return "—"
        if isinstance(dt_val, str):
            # Extract date YYYY-MM-DD
            cleaned = dt_val.split("T")[0].split(" ")[0].strip()
            return cleaned if cleaned else "—"
        try:
            return dt_val.strftime("%Y-%m-%d")
        except Exception:
            return str(dt_val).split(" ")[0]

    _format_dt = _format_date

    def load_maintenance(self, target_id=None):
        machine_id = self.eq_data.get('id')
        if not machine_id:
            self.maint_table.setRowCount(0)
            self.maint_count_lbl.setText("Записей: 0")
            self.maint_detail_title.setText("Нет данных")
            self.maint_type_input.clear()
            self.maint_start_input.clear()
            self.maint_end_input.clear()
            self.maint_notes_view.clear()
            self.maint_work_view.clear()
            self.btn_delete_maint.setEnabled(False)
            return

        self.maintenance_records = self.db_manager.get_machine_maintenance(machine_id)
        count = len(self.maintenance_records)
        self.maint_count_lbl.setText(f"Записей: {count}")
        self.maint_table.setRowCount(count)

        selected_row_idx = 0 if count > 0 else -1

        for row_idx, rec in enumerate(self.maintenance_records):
            rec_id = str(rec.get('id') or '')
            if target_id and rec.get('id') == target_id:
                selected_row_idx = row_idx

            start_d = self._format_date(rec.get('start_date'))
            end_d = self._format_date(rec.get('end_date'))
            w_type = str(rec.get('work_type') or '—')
            w_perf = str(rec.get('work_performed') or '').replace('\n', ' ')
            notes = str(rec.get('notes') or '').replace('\n', ' ')

            item_id = QTableWidgetItem(rec_id)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_start = QTableWidgetItem(start_d)
            item_start.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_end = QTableWidgetItem(end_d)
            item_end.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_type = QTableWidgetItem(w_type)
            item_perf = QTableWidgetItem(w_perf)
            item_notes = QTableWidgetItem(notes)

            self.maint_table.setItem(row_idx, 0, item_id)
            self.maint_table.setItem(row_idx, 1, item_start)
            self.maint_table.setItem(row_idx, 2, item_end)
            self.maint_table.setItem(row_idx, 3, item_type)
            self.maint_table.setItem(row_idx, 4, item_perf)
            self.maint_table.setItem(row_idx, 5, item_notes)

        if selected_row_idx >= 0:
            self.maint_table.selectRow(selected_row_idx)
        else:
            self.current_maint_id = None
            self.maint_detail_title.setText("Записей об обслуживании и неисправностях не найдено")
            self.maint_type_input.clear()
            self.maint_start_input.clear()
            self.maint_end_input.clear()
            self.maint_notes_view.clear()
            self.maint_work_view.clear()
            self.btn_delete_maint.setEnabled(False)

    def on_maint_row_selected(self):
        selected_rows = self.maint_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self.maintenance_records):
            rec = self.maintenance_records[row_idx]
            self.current_maint_id = rec.get('id')
            w_type = rec.get('work_type', '')
            start_d = self._format_date(rec.get('start_date'))
            end_d = self._format_date(rec.get('end_date'))

            self.maint_detail_title.setText(f"Редактирование записи #{self.current_maint_id}")
            self.maint_type_input.setText(w_type if w_type != '—' else '')
            self.maint_start_input.setText(start_d if start_d != '—' else '')
            self.maint_end_input.setText(end_d if end_d != '—' else '')
            self.maint_notes_view.setPlainText(rec.get('notes') or '')
            self.maint_work_view.setPlainText(rec.get('work_performed') or '')
            self.btn_delete_maint.setEnabled(True)

    def on_new_maint(self):
        self.maint_table.clearSelection()
        self.current_maint_id = None
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        self.maint_type_input.clear()
        self.maint_start_input.setText(today_str)
        self.maint_end_input.setText(today_str)
        self.maint_notes_view.clear()
        self.maint_work_view.clear()
        self.maint_detail_title.setText("✨ Новая запись технического обслуживания")
        self.btn_delete_maint.setEnabled(False)
        self.maint_type_input.setFocus()

    def on_save_maint(self, show_msg=True):
        w_type = self.maint_type_input.text().strip()
        s_date = self.maint_start_input.text().strip()
        e_date = self.maint_end_input.text().strip()
        notes = self.maint_notes_view.toPlainText().strip()
        work = self.maint_work_view.toPlainText().strip()

        if not any([w_type, s_date, e_date, notes, work]):
            if show_msg:
                QMessageBox.warning(self, "Внимание", "Заполните данные для сохранения записи ТО.")
            return True, "Нет данных"

        maint_data = {
            'id': self.current_maint_id,
            'machine_id': self.eq_data.get('id'),
            'work_type': w_type,
            'start_date': s_date if s_date and s_date != '—' else None,
            'end_date': e_date if e_date and e_date != '—' else None,
            'notes': notes,
            'work_performed': work
        }

        success, msg, saved_id = self.db_manager.save_machine_maintenance(maint_data)
        if success:
            self.current_maint_id = saved_id
            self.load_maintenance(target_id=saved_id)
            if show_msg:
                QMessageBox.information(self, "Сохранено", msg)
            return True, msg
        else:
            if show_msg:
                QMessageBox.critical(self, "Ошибка сохранения", msg)
            return False, msg

    def on_delete_maint(self):
        if not self.current_maint_id:
            QMessageBox.warning(self, "Внимание", "Выберите запись для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить запись ТО #{self.current_maint_id} из базы данных?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db_manager.delete_machine_maintenance(self.current_maint_id)
            if success:
                QMessageBox.information(self, "Удалено", msg)
                self.load_maintenance()
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def on_open_folder(self):
        self.eq_data['sub_folder'] = self.sub_folder_input.text().strip()
        found, path, msg = self.folder_router.resolve_equipment_folder(self.eq_data)
        success, open_msg = self.folder_router.open_folder_in_explorer(path, create_if_missing=False)
        if not success:
            reply = QMessageBox.question(
                self,
                "Папка не найдена",
                f"{open_msg}\n\nЖелаете создать данную папку на диске?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                ok, c_msg = self.folder_router.open_folder_in_explorer(path, create_if_missing=True)
                if ok:
                    QMessageBox.information(self, "Успешно", f"Папка создана и открыта:\n{path}")
                else:
                    QMessageBox.critical(self, "Ошибка", c_msg)
        self.update_folder_status()

    def on_save(self):
        updated_data = {
            'id': self.eq_data.get('id'),
            'inventory_number': self.inv_input.text().strip(),
            'name': self.name_input.text().strip(),
            'machine_name': self.name_input.text().strip(),
            'workshop_id': self.workshop_combo.currentData(),
            'sub_folder': self.folder_path_input.text().strip(),
            'folder_path': self.folder_path_input.text().strip(),
            'controller': self.controller_input.text().strip(),
            'cnc_controller': self.controller_input.text().strip(),
            'year_built': self.year_input.value(),
            'commissioning_year': self.year_input.value(),
            'status': self.status_combo.currentText(),
            'ip_address': self.ip_input.text().strip(),
            'mac_address': self.mac_input.text().strip(),
            'screen': self.screen_input.text().strip(),
            'processor': self.processor_input.text().strip(),
            'ram': self.ram_input.text().strip(),
            'rom': self.rom_input.text().strip(),
            'operating_system': self.os_input.text().strip(),
            'antivirus': self.antivirus_input.text().strip(),
        }

        # Save machine general data
        success, msg = self.db_manager.save_equipment(updated_data)
        if not success:
            QMessageBox.critical(self, "Ошибка сохранения", msg)
            return

        # Also save active maintenance record if present
        if self.maint_type_input.text().strip() or self.maint_notes_view.toPlainText().strip() or self.maint_work_view.toPlainText().strip():
            self.on_save_maint(show_msg=False)

        QMessageBox.information(
            self,
            "Сохранено",
            f"{msg}\n\nВсе изменения оборудования и журнала обслуживания сохранены в PostgreSQL."
        )
        self.eq_data.update(updated_data)
        self.accept()
