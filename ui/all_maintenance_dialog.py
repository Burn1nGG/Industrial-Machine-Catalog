"""
All Maintenance and Fault History Dialog for Industrial Equipment Catalog.
Compact, high-density enterprise maintenance log browsing with instant search
by inventory number, machine name, workshop, and text keywords.
"""
import csv
import re
import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QTextEdit, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.detail_card_dialog import DetailCardDialog


MAINT_TABLE_COLUMNS = [
    {"title": "ID", "width": 48, "sortable": True},
    {"title": "Инв. №", "width": 80, "sortable": True},
    {"title": "Наименование станка", "width": 260, "sortable": True},
    {"title": "Цех", "width": 85, "sortable": True},
    {"title": "Начало", "width": 95, "sortable": True},
    {"title": "Окончание", "width": 95, "sortable": True},
    {"title": "Тип / Категория", "width": 160, "sortable": True},
    {"title": "Выполненные работы", "width": 300, "sortable": False},
    {"title": "Неисправность / Примечания", "width": 300, "sortable": False},
    {"title": "Действия", "width": 140, "sortable": False},
]

COMPACT_TABLE_STYLE = """
QTableWidget#MaintCompactTable {
    background-color: #0F172A;
    border: 1px solid #334155;
    gridline-color: #1E293B;
    border-radius: 4px;
    font-size: 11px;
}
QTableWidget#MaintCompactTable::item {
    padding: 2px 4px;
    border-bottom: 1px solid #1E293B;
    font-size: 11px;
}
QTableWidget#MaintCompactTable::item:selected {
    background-color: #1E293B;
    color: #38BDF8;
}
QTableWidget#MaintCompactTable QHeaderView::section {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 3px 6px;
    font-size: 11px;
    font-weight: 600;
    border: none;
    border-right: 1px solid #334155;
    border-bottom: 2px solid #334155;
}
"""


class AllMaintenanceDialog(QDialog):
    def __init__(self, db_manager, folder_router, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.folder_router = folder_router

        self.setWindowTitle("Журнал обслуживания и неисправностей оборудования")
        self.resize(1320, 820)
        self.setMinimumSize(900, 520)

        self.all_records = []
        self.current_record = None
        self._active_sort_column = 4  # Default sort by "Начало" (start_date)
        self._active_sort_order = Qt.SortOrder.DescendingOrder

        self.init_ui()
        self.load_workshops()
        self.on_search()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ---------------- 1. COMPACT TOP TOOLBAR & FILTERS ----------------
        # Single-row compact filter toolbar: saves maximum vertical space
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_frame.setStyleSheet("padding: 4px 6px; margin: 0px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(6, 4, 6, 4)
        filter_layout.setSpacing(6)

        # Workshop combo
        ws_lbl = QLabel("Цех:")
        ws_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8;")
        self.ws_combo = QComboBox()
        self.ws_combo.addItem("— Все цеха —", 0)
        self.ws_combo.setFixedHeight(28)
        self.ws_combo.setMinimumWidth(110)
        filter_layout.addWidget(ws_lbl)
        filter_layout.addWidget(self.ws_combo, 2)

        # Inventory number input
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("Инв. № станка...")
        self.num_input.setFixedHeight(28)
        self.num_input.setMinimumWidth(100)
        self.num_input.returnPressed.connect(self.on_search)
        filter_layout.addWidget(self.num_input, 2)

        # Machine name / model input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название / модель станка...")
        self.name_input.setFixedHeight(28)
        self.name_input.setMinimumWidth(140)
        self.name_input.returnPressed.connect(self.on_search)
        filter_layout.addWidget(self.name_input, 3)

        # Keyword search in work & notes
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Поиск в работах и поломках...")
        self.text_input.setFixedHeight(28)
        self.text_input.setMinimumWidth(140)
        self.text_input.returnPressed.connect(self.on_search)
        filter_layout.addWidget(self.text_input, 3)

        # Search & Reset buttons
        self.btn_search = QPushButton("🔍 Найти")
        self.btn_search.setObjectName("SearchButton")
        self.btn_search.setFixedHeight(28)
        self.btn_search.setStyleSheet("font-size: 12px; padding: 4px 12px;")
        self.btn_search.clicked.connect(self.on_search)
        filter_layout.addWidget(self.btn_search)

        self.btn_reset = QPushButton("🔄 Сброс")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.setFixedHeight(28)
        self.btn_reset.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self.btn_reset.clicked.connect(self.on_reset)
        filter_layout.addWidget(self.btn_reset)

        # Action tools: Toggle details panel, Export CSV, Close
        self.btn_toggle_detail = QPushButton("📋 Детали")
        self.btn_toggle_detail.setObjectName("ResetButton")
        self.btn_toggle_detail.setFixedHeight(28)
        self.btn_toggle_detail.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self.btn_toggle_detail.setToolTip("Показать или скрыть нижнюю панель деталей записи")
        self.btn_toggle_detail.setCheckable(True)
        self.btn_toggle_detail.setChecked(True)
        self.btn_toggle_detail.clicked.connect(self.on_toggle_details)
        filter_layout.addWidget(self.btn_toggle_detail)

        self.btn_export_csv = QPushButton("📥 CSV")
        self.btn_export_csv.setObjectName("ResetButton")
        self.btn_export_csv.setFixedHeight(28)
        self.btn_export_csv.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self.btn_export_csv.setToolTip("Экспорт отфильтрованного журнала в CSV")
        self.btn_export_csv.clicked.connect(self.on_export_csv)
        filter_layout.addWidget(self.btn_export_csv)

        self.btn_close_top = QPushButton("✕ Закрыть")
        self.btn_close_top.setObjectName("ResetButton")
        self.btn_close_top.setFixedHeight(28)
        self.btn_close_top.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self.btn_close_top.clicked.connect(self.accept)
        filter_layout.addWidget(self.btn_close_top)

        main_layout.addWidget(filter_frame)

        # ---------------- 2. VERTICAL SPLITTER: TABLE + DETAIL ----------------
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)

        # --- Top part of splitter: Table container ---
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(4)

        # Compact summary bar
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(4, 0, 4, 0)
        self.count_lbl = QLabel("Записей ТО: 0 шт.")
        self.count_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #F8FAFC;")

        summary_hint = QLabel("💡 Двойной клик открывает карточку станка")
        summary_hint.setStyleSheet("font-size: 11px; color: #94A3B8; font-style: italic;")

        summary_layout.addWidget(self.count_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(summary_hint)
        table_layout.addLayout(summary_layout)

        # Table Widget: High-density, smaller font, compact rows
        self.table = QTableWidget()
        self.table.setObjectName("MaintCompactTable")
        self.table.setStyleSheet(COMPACT_TABLE_STYLE)
        self.table.setColumnCount(len(MAINT_TABLE_COLUMNS))

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

        for idx, col_info in enumerate(MAINT_TABLE_COLUMNS):
            self.table.setColumnWidth(idx, col_info["width"])
            if not col_info["sortable"]:
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Fixed)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Compact row height: 26px allows showing 20+ rows on a standard monitor
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_table_double_clicked)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        header.sectionClicked.connect(self.on_header_clicked)

        table_layout.addWidget(self.table)
        self.splitter.addWidget(table_container)

        # --- Bottom part of splitter: Compact Detail Edit Frame ---
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("MaintenanceDetailFrame")
        self.detail_frame.setStyleSheet("padding: 6px 10px; margin: 0px;")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(6, 4, 6, 4)
        detail_layout.setSpacing(4)

        detail_hdr = QHBoxLayout()
        detail_hdr.setSpacing(6)
        self.detail_title = QLabel("Подробная информация о записи")
        self.detail_title.setObjectName("MaintSectionTitle")
        self.detail_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #38BDF8;")

        self.btn_card_detail = QPushButton("🛈 Карточка станка")
        self.btn_card_detail.setObjectName("CardButton")
        self.btn_card_detail.setFixedHeight(24)
        self.btn_card_detail.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_card_detail.clicked.connect(self.on_open_current_card)

        self.btn_folder_detail = QPushButton("📁 Папка")
        self.btn_folder_detail.setObjectName("FolderButton")
        self.btn_folder_detail.setFixedHeight(24)
        self.btn_folder_detail.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_folder_detail.clicked.connect(self.on_open_current_folder)

        self.btn_save_record = QPushButton("💾 Сохранить")
        self.btn_save_record.setObjectName("SearchButton")
        self.btn_save_record.setFixedHeight(24)
        self.btn_save_record.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_save_record.clicked.connect(self.on_save_detail)

        self.btn_delete_record = QPushButton("🗑 Удалить")
        self.btn_delete_record.setObjectName("DeleteButton")
        self.btn_delete_record.setFixedHeight(24)
        self.btn_delete_record.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_delete_record.clicked.connect(self.on_delete_detail)

        detail_hdr.addWidget(self.detail_title)
        detail_hdr.addStretch()
        detail_hdr.addWidget(self.btn_card_detail)
        detail_hdr.addWidget(self.btn_folder_detail)
        detail_hdr.addWidget(self.btn_save_record)
        detail_hdr.addWidget(self.btn_delete_record)
        detail_layout.addLayout(detail_hdr)

        # Fields row: Type, Start, End in one compact row
        f_row = QHBoxLayout()
        f_row.setSpacing(8)

        type_lbl = QLabel("Тип:")
        type_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #CBD5E1;")
        self.detail_type_input = QLineEdit()
        self.detail_type_input.setFixedHeight(24)
        self.detail_type_input.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        f_row.addWidget(type_lbl)
        f_row.addWidget(self.detail_type_input, 2)

        start_lbl = QLabel("Начало:")
        start_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #CBD5E1;")
        self.detail_start_input = QLineEdit()
        self.detail_start_input.setFixedHeight(24)
        self.detail_start_input.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        f_row.addWidget(start_lbl)
        f_row.addWidget(self.detail_start_input, 1)

        end_lbl = QLabel("Конец:")
        end_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #CBD5E1;")
        self.detail_end_input = QLineEdit()
        self.detail_end_input.setFixedHeight(24)
        self.detail_end_input.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        f_row.addWidget(end_lbl)
        f_row.addWidget(self.detail_end_input, 1)

        detail_layout.addLayout(f_row)

        # Text fields: Notes & Work Performed
        texts_layout = QHBoxLayout()
        texts_layout.setSpacing(8)

        notes_box = QVBoxLayout()
        notes_box.setSpacing(1)
        notes_lbl = QLabel("⚠️ Неисправность / Задача:")
        notes_lbl.setStyleSheet("font-weight: 600; font-size: 10px; color: #FBBF24;")
        self.detail_notes_view = QTextEdit()
        self.detail_notes_view.setObjectName("MaintDetailText")
        self.detail_notes_view.setStyleSheet("font-size: 11px; padding: 4px;")
        self.detail_notes_view.setMinimumHeight(48)
        notes_box.addWidget(notes_lbl)
        notes_box.addWidget(self.detail_notes_view)

        work_box = QVBoxLayout()
        work_box.setSpacing(1)
        work_lbl = QLabel("⚙️ Выполненные работы / Результат:")
        work_lbl.setStyleSheet("font-weight: 600; font-size: 10px; color: #34D399;")
        self.detail_work_view = QTextEdit()
        self.detail_work_view.setObjectName("MaintDetailText")
        self.detail_work_view.setStyleSheet("font-size: 11px; padding: 4px;")
        self.detail_work_view.setMinimumHeight(48)
        work_box.addWidget(work_lbl)
        work_box.addWidget(self.detail_work_view)

        texts_layout.addLayout(notes_box, 1)
        texts_layout.addLayout(work_box, 1)
        detail_layout.addLayout(texts_layout)

        self.splitter.addWidget(self.detail_frame)

        # Give 80% space to the table and 20% to detail panel
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([620, 140])

        main_layout.addWidget(self.splitter, 1)

        self.apply_permissions()
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and hasattr(auth, 'user_changed'):
            auth.user_changed.connect(self.apply_permissions)

    def apply_permissions(self):
        """Ограничение редактирования и удаления для пользователей в режиме только для чтения."""
        auth = getattr(self.db_manager, 'auth_manager', None)
        can_edit = auth.can_edit() if auth else True
        can_delete = auth.can_delete() if auth else True

        self.detail_type_input.setReadOnly(not can_edit)
        self.detail_start_input.setReadOnly(not can_edit)
        self.detail_end_input.setReadOnly(not can_edit)
        self.detail_notes_view.setReadOnly(not can_edit)
        self.detail_work_view.setReadOnly(not can_edit)

        has_rec = self.current_record is not None
        self.btn_save_record.setEnabled(can_edit and has_rec)
        self.btn_delete_record.setEnabled(can_delete and has_rec)

    def on_toggle_details(self):
        """Переключает видимость нижней панели деталей."""
        is_visible = self.btn_toggle_detail.isChecked()
        self.detail_frame.setVisible(is_visible)
        if is_visible:
            self.splitter.setSizes([580, 140])

    # ---------------- DATA LOADING & SEARCH ----------------
    def load_workshops(self):
        """Загрузка списка цехов в фильтр."""
        self.ws_combo.blockSignals(True)
        self.ws_combo.clear()
        self.ws_combo.addItem("— Все цеха —", 0)
        workshops = self.db_manager.get_workshops()
        for ws in workshops:
            self.ws_combo.addItem(f"{ws['name']}", ws['id'])
        self.ws_combo.blockSignals(False)

    def on_search(self):
        ws_id = self.ws_combo.currentData()
        num_val = self.num_input.text().strip()
        name_val = self.name_input.text().strip()
        text_val = self.text_input.text().strip()

        self.all_records = self.db_manager.get_all_maintenance(
            inventory_number=num_val,
            machine_name=name_val,
            workshop_id=ws_id,
            search_text=text_val
        )

        self.display_records(self.all_records)

    def on_reset(self):
        self.ws_combo.setCurrentIndex(0)
        self.num_input.clear()
        self.name_input.clear()
        self.text_input.clear()
        self._active_sort_column = 4
        self._active_sort_order = Qt.SortOrder.DescendingOrder
        self._update_header_labels()
        self.on_search()

    # ---------------- SORTING & DISPLAY ----------------
    @staticmethod
    def _format_date(dt_val):
        if not dt_val:
            return "—"
        if isinstance(dt_val, str):
            cleaned = dt_val.split("T")[0].split(" ")[0].strip()
            return cleaned if cleaned else "—"
        try:
            return dt_val.strftime("%Y-%m-%d")
        except Exception:
            return str(dt_val).split(" ")[0]

    def _natural_sort_key(self, value):
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

    def _get_sort_value(self, rec, column):
        if column == 0:
            return self._natural_sort_key(rec.get('id'))
        if column == 1:
            return self._natural_sort_key(rec.get('inventory_number'))
        if column == 2:
            return self._natural_sort_key(rec.get('machine_name') or rec.get('name'))
        if column == 3:
            return self._natural_sort_key(rec.get('workshop_name'))
        if column == 4:
            return self._natural_sort_key(self._format_date(rec.get('start_date')))
        if column == 5:
            return self._natural_sort_key(self._format_date(rec.get('end_date')))
        if column == 6:
            return self._natural_sort_key(rec.get('work_type'))
        return self._natural_sort_key("")

    def _sort_records(self, records, column):
        if column is None or column >= len(MAINT_TABLE_COLUMNS) or not MAINT_TABLE_COLUMNS[column]["sortable"]:
            return list(records)
        reverse = self._active_sort_order == Qt.SortOrder.DescendingOrder
        return sorted(records, key=lambda r: self._get_sort_value(r, column), reverse=reverse)

    def _update_header_labels(self):
        for idx, col_info in enumerate(MAINT_TABLE_COLUMNS):
            base_title = col_info["title"]
            if col_info["sortable"]:
                if self._active_sort_column == idx:
                    arrow = " ▲" if self._active_sort_order == Qt.SortOrder.AscendingOrder else " ▼"
                    header_text = f"{base_title}{arrow}"
                else:
                    header_text = base_title
            else:
                header_text = base_title

            item = self.table.horizontalHeaderItem(idx)
            if not item:
                item = QTableWidgetItem(header_text)
                self.table.setHorizontalHeaderItem(idx, item)
            else:
                item.setText(header_text)

    def on_header_clicked(self, column):
        if column >= len(MAINT_TABLE_COLUMNS) or not MAINT_TABLE_COLUMNS[column]["sortable"]:
            return

        if self._active_sort_column == column:
            if self._active_sort_order == Qt.SortOrder.AscendingOrder:
                self._active_sort_order = Qt.SortOrder.DescendingOrder
            else:
                self._active_sort_order = Qt.SortOrder.AscendingOrder
        else:
            self._active_sort_column = column
            self._active_sort_order = Qt.SortOrder.AscendingOrder

        self._update_header_labels()
        self.display_records(self.all_records)

    def display_records(self, records):
        items_to_display = self._sort_records(records, self._active_sort_column)
        self.table.setRowCount(0)

        sort_info = ""
        if self._active_sort_column is not None and self._active_sort_column < len(MAINT_TABLE_COLUMNS):
            col_title = MAINT_TABLE_COLUMNS[self._active_sort_column]["title"]
            arrow = "▲" if self._active_sort_order == Qt.SortOrder.AscendingOrder else "▼"
            sort_info = f"  •  Сортировка: «{col_title}» {arrow}"

        self.count_lbl.setText(f"Записей ТО: {len(records)} шт.{sort_info}")

        for row_idx, rec in enumerate(items_to_display):
            self.table.insertRow(row_idx)

            rec_id = str(rec.get('id', ''))
            inv_num = str(rec.get('inventory_number', '')) if rec.get('inventory_number') is not None else '—'
            m_name = str(rec.get('machine_name') or rec.get('name') or '—')
            w_name = str(rec.get('workshop_name') or '—')
            s_date = self._format_date(rec.get('start_date'))
            e_date = self._format_date(rec.get('end_date'))
            w_type = str(rec.get('work_type') or '—')
            w_perf = str(rec.get('work_performed') or '').replace('\n', ' ')
            notes = str(rec.get('notes') or '').replace('\n', ' ')

            item_id = QTableWidgetItem(rec_id)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_id.setData(Qt.ItemDataRole.UserRole, rec)

            item_inv = QTableWidgetItem(inv_num)
            item_inv.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_name = QTableWidgetItem(m_name)
            item_ws = QTableWidgetItem(w_name)
            item_start = QTableWidgetItem(s_date)
            item_start.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_end = QTableWidgetItem(e_date)
            item_end.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_type = QTableWidgetItem(w_type)
            item_perf = QTableWidgetItem(w_perf)
            item_notes = QTableWidgetItem(notes)

            self.table.setItem(row_idx, 0, item_id)
            self.table.setItem(row_idx, 1, item_inv)
            self.table.setItem(row_idx, 2, item_name)
            self.table.setItem(row_idx, 3, item_ws)
            self.table.setItem(row_idx, 4, item_start)
            self.table.setItem(row_idx, 5, item_end)
            self.table.setItem(row_idx, 6, item_type)
            self.table.setItem(row_idx, 7, item_perf)
            self.table.setItem(row_idx, 8, item_notes)

            # Compact Action cell with 2 buttons: Card & Folder
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 1, 2, 1)
            action_layout.setSpacing(4)

            btn_folder = QPushButton("📁")
            btn_folder.setObjectName("FolderButton")
            btn_folder.setToolTip(f"Открыть папку станка «{m_name}» в Explorer")
            btn_folder.setFixedSize(26, 20)
            btn_folder.setStyleSheet("font-size: 11px; padding: 0px;")
            btn_folder.clicked.connect(lambda checked=False, r=rec: self.open_machine_folder(r))

            btn_card = QPushButton("🛈 Карточка")
            btn_card.setObjectName("CardButton")
            btn_card.setToolTip(f"Открыть карточку станка «{m_name}»")
            btn_card.setFixedHeight(20)
            btn_card.setStyleSheet("font-size: 11px; padding: 1px 6px;")
            btn_card.clicked.connect(lambda checked=False, r=rec: self.open_machine_card(r))

            action_layout.addWidget(btn_folder)
            action_layout.addWidget(btn_card)
            self.table.setCellWidget(row_idx, 9, action_widget)

        if len(items_to_display) > 0:
            self.table.selectRow(0)
        else:
            self.clear_detail_panel()

    # ---------------- SELECTION & DETAIL LOGIC ----------------
    def on_table_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_detail_panel()
            return

        row_idx = selected_rows[0].row()
        item = self.table.item(row_idx, 0)
        if not item:
            return

        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return

        self.current_record = rec
        rec_id = rec.get('id')
        m_name = rec.get('machine_name') or rec.get('name') or 'Станок'
        inv = rec.get('inventory_number') or '—'

        self.detail_title.setText(f"Запись ТО #{rec_id} — {m_name} (Инв. № {inv})")
        self.detail_type_input.setText(str(rec.get('work_type') or ''))
        self.detail_start_input.setText(self._format_date(rec.get('start_date')).replace('—', ''))
        self.detail_end_input.setText(self._format_date(rec.get('end_date')).replace('—', ''))
        self.detail_notes_view.setPlainText(str(rec.get('notes') or ''))
        self.detail_work_view.setPlainText(str(rec.get('work_performed') or ''))

        self.btn_card_detail.setEnabled(True)
        self.btn_folder_detail.setEnabled(True)
        auth = getattr(self.db_manager, 'auth_manager', None)
        can_edit = auth.can_edit() if auth else True
        can_delete = auth.can_delete() if auth else True
        self.btn_save_record.setEnabled(can_edit)
        self.btn_delete_record.setEnabled(can_delete)

    def clear_detail_panel(self):
        self.current_record = None
        self.detail_title.setText("Выберите запись в таблице для просмотра или редактирования")
        self.detail_type_input.clear()
        self.detail_start_input.clear()
        self.detail_end_input.clear()
        self.detail_notes_view.clear()
        self.detail_work_view.clear()
        self.btn_card_detail.setEnabled(False)
        self.btn_folder_detail.setEnabled(False)
        self.btn_save_record.setEnabled(False)
        self.btn_delete_record.setEnabled(False)

    def on_table_double_clicked(self, row, column):
        item = self.table.item(row, 0)
        if item:
            rec = item.data(Qt.ItemDataRole.UserRole)
            if rec:
                self.open_machine_card(rec)

    # ---------------- ACTIONS: CARD & FOLDER ----------------
    def open_machine_card(self, record):
        m_id = record.get('machine_id')
        if not m_id:
            QMessageBox.warning(self, "Ошибка", "ID станка не определен.")
            return

        machine_data = self.db_manager.get_machine_by_id(m_id)
        if not machine_data:
            # Fallback to search if view not available
            results = self.db_manager.search_equipment(machine_number=str(record.get('inventory_number', '')))
            if results:
                machine_data = results[0]

        if not machine_data:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные станка #{m_id}.")
            return

        dialog = DetailCardDialog(machine_data, self.db_manager, self.folder_router, self)
        dialog.setWindowState(Qt.WindowState.WindowMaximized)
        if dialog.exec() == DetailCardDialog.DialogCode.Accepted:
            # Refresh logs in case maintenance was edited/added in card
            self.on_search()

    def open_machine_folder(self, record):
        m_id = record.get('machine_id')
        machine_data = self.db_manager.get_machine_by_id(m_id) if m_id else None
        if not machine_data:
            machine_data = dict(record)

        found, path, msg = self.folder_router.resolve_equipment_folder(machine_data)
        if path:
            self.folder_router.open_folder_in_explorer(path)

    def on_open_current_card(self):
        if self.current_record:
            self.open_machine_card(self.current_record)

    def on_open_current_folder(self):
        if self.current_record:
            self.open_machine_folder(self.current_record)

    # ---------------- ACTIONS: SAVE & DELETE ----------------
    def on_save_detail(self):
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_edit():
            QMessageBox.warning(self, "Доступ ограничен", "Для сохранения записи ТО требуется войти с правами редактора.")
            return

        if not self.current_record:
            return

        w_type = self.detail_type_input.text().strip()
        s_date = self.detail_start_input.text().strip()
        e_date = self.detail_end_input.text().strip()
        notes = self.detail_notes_view.toPlainText().strip()
        work = self.detail_work_view.toPlainText().strip()

        maint_data = {
            'id': self.current_record.get('id'),
            'machine_id': self.current_record.get('machine_id'),
            'work_type': w_type,
            'start_date': s_date if s_date and s_date != '—' else None,
            'end_date': e_date if e_date and e_date != '—' else None,
            'notes': notes,
            'work_performed': work
        }

        success, msg, saved_id = self.db_manager.save_machine_maintenance(maint_data)
        if success:
            QMessageBox.information(self, "Успешно", "Запись ТО успешно сохранена в базе данных!")
            self.on_search()
        else:
            QMessageBox.critical(self, "Ошибка сохранения", msg)

    def on_delete_detail(self):
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_delete():
            QMessageBox.warning(self, "Доступ ограничен", "Для удаления записи ТО требуется войти с правами редактора или администратора.")
            return

        if not self.current_record:
            return

        rec_id = self.current_record.get('id')
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить запись ТО #{rec_id}?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db_manager.delete_machine_maintenance(rec_id)
            if success:
                QMessageBox.information(self, "Удалено", msg)
                self.on_search()
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    # ---------------- CSV EXPORT ----------------
    def on_export_csv(self):
        if not self.all_records:
            QMessageBox.information(self, "Экспорт", "Список записей пуст для экспорта.")
            return

        default_filename = f"maintenance_log_{datetime.date.today().strftime('%Y%m%d')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет истории обслуживания",
            default_filename,
            "CSV файлы (*.csv);;Все файлы (*.*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                # Header row
                writer.writerow([
                    "ID записи",
                    "Инвентарный номер",
                    "Наименование станка",
                    "Цех",
                    "Дата начала",
                    "Дата окончания",
                    "Тип работы / Категория",
                    "Выполненные работы",
                    "Неисправность / Примечания"
                ])

                for rec in self._sort_records(self.all_records, self._active_sort_column):
                    writer.writerow([
                        rec.get('id', ''),
                        rec.get('inventory_number', ''),
                        rec.get('machine_name') or rec.get('name') or '',
                        rec.get('workshop_name') or '',
                        self._format_date(rec.get('start_date')),
                        self._format_date(rec.get('end_date')),
                        rec.get('work_type', ''),
                        rec.get('work_performed', ''),
                        rec.get('notes', '')
                    ])

            QMessageBox.information(self, "Экспорт завершен", f"Данные успешно выгружены в файл:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось записать файл:\n{e}")
