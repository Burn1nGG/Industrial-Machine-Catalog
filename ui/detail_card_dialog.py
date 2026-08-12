"""
Detailed Machine Card Dialog for Industrial Equipment Catalog App.
Tabs wrapped in QScrollArea to prevent text clipping/cropping on any resolution.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QTabWidget, QWidget, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt

class DetailCardDialog(QDialog):
    def __init__(self, equipment_dict, db_manager, folder_router, parent=None):
        super().__init__(parent)
        self.eq_data = dict(equipment_dict)
        self.db_manager = db_manager
        self.folder_router = folder_router
        
        self.setWindowTitle(f"Подробная карточка оборудования — {self.eq_data.get('inventory_number', '')}")
        self.resize(920, 720)
        self.setMinimumSize(800, 600)
        self.init_ui()

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

        success, msg = self.db_manager.save_equipment(updated_data)
        if success:
            QMessageBox.information(
                self,
                "Сохранено",
                f"{msg}\n\nИзменения записаны в PostgreSQL и будут доступны при следующем открытии карточки."
            )
            self.eq_data.update(updated_data)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка сохранения", msg)
