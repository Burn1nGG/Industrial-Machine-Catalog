"""
Detailed Machine Card Dialog for Industrial Equipment Catalog App.
Tabs wrapped in QScrollArea to prevent text clipping/cropping on any resolution.
"""
import os
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QTabWidget, QWidget, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QScrollArea, QTextEdit,
    QAbstractItemView, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QCursor


class ImageViewerDialog(QDialog):
    """Полноразмерный просмотр фотографии станка с возможностью открытия в Windows Explorer."""
    def __init__(self, photo_path, machine_name="", inv_num="", folder_router=None, parent=None):
        super().__init__(parent)
        self.photo_path = photo_path
        self.machine_name = machine_name
        self.inv_num = inv_num
        self.folder_router = folder_router
        
        self.setWindowTitle(f"Фото станка: {self.inv_num} — {self.machine_name}")
        self.resize(1000, 750)
        self.setMinimumSize(600, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header toolbar
        hdr_frame = QFrame()
        hdr_frame.setObjectName("HeaderFrame")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(10, 8, 10, 8)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        title_lbl = QLabel(f"📷 {self.machine_name} (Инв. № {self.inv_num})")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        path_lbl = QLabel(self.photo_path or "Путь не указан")
        path_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
        path_lbl.setWordWrap(True)
        info_box.addWidget(title_lbl)
        info_box.addWidget(path_lbl)
        hdr_layout.addLayout(info_box, 1)

        self.btn_system_open = QPushButton("🖼 Открыть в Windows")
        self.btn_system_open.setObjectName("ResetButton")
        self.btn_system_open.clicked.connect(self.on_system_open)

        self.btn_folder = QPushButton("📁 Открыть папку «Фото»")
        self.btn_folder.setObjectName("FolderButton")
        self.btn_folder.clicked.connect(self.on_open_folder)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setObjectName("ResetButton")
        self.btn_close.clicked.connect(self.accept)

        hdr_layout.addWidget(self.btn_system_open)
        hdr_layout.addWidget(self.btn_folder)
        hdr_layout.addWidget(self.btn_close)
        layout.addWidget(hdr_frame)

        # Scroll area for large image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #070B14; border-radius: 6px;")

        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("background-color: #070B14;")

        if self.photo_path and os.path.isfile(self.photo_path):
            pixmap = QPixmap(self.photo_path)
            if not pixmap.isNull():
                self.img_lbl.setPixmap(pixmap)
            else:
                self.img_lbl.setText("Не удалось загрузить изображение")
                self.img_lbl.setStyleSheet("color: #EF4444; font-size: 15px; font-weight: bold;")
        else:
            self.img_lbl.setText("Файл фотографии не найден")
            self.img_lbl.setStyleSheet("color: #EF4444; font-size: 15px; font-weight: bold;")

        self.scroll_area.setWidget(self.img_lbl)
        layout.addWidget(self.scroll_area, 1)

    def on_system_open(self):
        if self.photo_path and os.path.isfile(self.photo_path):
            try:
                os.startfile(os.path.normpath(self.photo_path))
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def on_open_folder(self):
        if self.photo_path:
            folder = os.path.dirname(self.photo_path)
            if self.folder_router:
                self.folder_router.open_folder_in_explorer(folder, create_if_missing=False)
            elif os.path.exists(folder):
                try:
                    os.startfile(os.path.normpath(folder))
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку:\n{e}")


class PhotoLoaderThread(QThread):
    """Асинхронная загрузка фотографии станка для мгновенного отклика интерфейса."""
    loaded = Signal(bool, str, str, object)  # found, photo_path, message, QImage or None

    def __init__(self, folder_router, eq_data):
        super().__init__()
        self.folder_router = folder_router
        self.eq_data = dict(eq_data)

    def run(self):
        try:
            found, photo_path, photo_folder, msg = self.folder_router.resolve_equipment_photo(self.eq_data)
            if found and photo_path and os.path.isfile(photo_path):
                img = QImage()
                if img.load(photo_path):
                    self.loaded.emit(True, photo_path, msg, img)
                    return
                else:
                    self.loaded.emit(False, photo_path, "Не удалось декодировать файл изображения", None)
                    return
            self.loaded.emit(False, photo_path or "", msg, None)
        except Exception as e:
            self.loaded.emit(False, "", str(e), None)


class DetailCardDialog(QDialog):
    def __init__(self, equipment_dict, db_manager, folder_router, parent=None):
        super().__init__(parent)
        self.eq_data = dict(equipment_dict)
        self.db_manager = db_manager
        self.folder_router = folder_router
        
        self.current_photo_path = None
        self.current_photo_folder = None
        self.current_qimage = None
        self.current_pixmap = None
        self._photo_thread = None

        inv_num = self.eq_data.get('inventory_number', '')
        eq_name = self.eq_data.get('name', 'Без названия')
        self.setWindowTitle(f"Карточка станка: {inv_num} — {eq_name}")
        self.resize(1150, 780)
        self.setMinimumSize(850, 620)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        self.init_ui()
        self.start_photo_load()

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Tab Widget (placed directly at the top so other tabs have maximum vertical space)
        self.tabs = QTabWidget()

        # =========================================================================
        # --- TAB 1: General & Tech Specs + Machine Photo (with Scroll Area) ---
        # =========================================================================
        self.tab1_scroll = QScrollArea()
        self.tab1_scroll.setWidgetResizable(True)
        self.tab1_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.tab1 = QWidget()
        tab1_layout = QVBoxLayout(self.tab1)
        tab1_layout.setContentsMargins(14, 14, 14, 14)
        tab1_layout.setSpacing(12)

        # 1. Top Header Banner inside Tab 1
        tab1_header_card = QFrame()
        tab1_header_card.setObjectName("HeaderFrame")
        tab1_header_layout = QHBoxLayout(tab1_header_card)
        tab1_header_layout.setContentsMargins(14, 10, 14, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.tab1_name_lbl = QLabel(self.eq_data.get('name', 'Без названия'))
        self.tab1_name_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #38BDF8;")
        self.tab1_name_lbl.setWordWrap(True)

        inv_val = self.eq_data.get('inventory_number', '-')
        ctrl_val = self.eq_data.get('controller', '-')
        ws_val = self.eq_data.get('workshop_name', '-')
        self.tab1_sub_lbl = QLabel(f"Инв. №: {inv_val}   |   ЧПУ / Контроллер: {ctrl_val}   |   Цех: {ws_val}")
        self.tab1_sub_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        self.tab1_sub_lbl.setWordWrap(True)

        title_box.addWidget(self.tab1_name_lbl)
        title_box.addWidget(self.tab1_sub_lbl)
        tab1_header_layout.addLayout(title_box, 1)

        # Status badge pill
        initial_status = self.eq_data.get('status', 'В работе')
        self.tab1_status_lbl = QLabel(initial_status)
        self._apply_status_style(self.tab1_status_lbl, initial_status)
        tab1_header_layout.addWidget(self.tab1_status_lbl, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        tab1_layout.addWidget(tab1_header_card)

        # 2. Main Two-Column Row: Left = Photo Card, Right = Tech Specs Form
        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        # --- LEFT: Machine Photo Card ---
        self.photo_card = QFrame()
        self.photo_card.setObjectName("PhotoCardFrame")
        self.photo_card.setMinimumWidth(380)
        self.photo_card.setMaximumWidth(450)
        photo_card_layout = QVBoxLayout(self.photo_card)
        photo_card_layout.setContentsMargins(12, 12, 12, 12)
        photo_card_layout.setSpacing(10)

        # Photo card header
        photo_hdr = QHBoxLayout()
        photo_title = QLabel("📷 Внешний вид станка")
        photo_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #F1F5F9;")
        self.btn_refresh_photo = QPushButton("🔄")
        self.btn_refresh_photo.setObjectName("ResetButton")
        self.btn_refresh_photo.setToolTip("Перепроверить и обновить фотографию станка")
        self.btn_refresh_photo.setFixedSize(32, 30)
        self.btn_refresh_photo.clicked.connect(self.start_photo_load)

        photo_hdr.addWidget(photo_title)
        photo_hdr.addStretch()
        photo_hdr.addWidget(self.btn_refresh_photo)
        photo_card_layout.addLayout(photo_hdr)

        # Stacked display: Loading (0), Photo (1), Placeholder (2)
        self.photo_stack = QStackedWidget()
        self.photo_stack.setMinimumHeight(350)

        # Page 0: Loading
        self.page_loading = QFrame()
        self.page_loading.setObjectName("PhotoPlaceholderFrame")
        p0_layout = QVBoxLayout(self.page_loading)
        p0_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_load_icon = QLabel("⏳")
        lbl_load_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_load_icon.setStyleSheet("font-size: 36px;")
        lbl_load_text = QLabel("Поиск и загрузка фотографии...")
        lbl_load_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_load_text.setStyleSheet("font-size: 13px; color: #94A3B8; font-weight: 600;")
        p0_layout.addWidget(lbl_load_icon)
        p0_layout.addWidget(lbl_load_text)
        self.photo_stack.addWidget(self.page_loading)

        # Page 1: Loaded Photo
        self.page_photo = QWidget()
        p1_layout = QVBoxLayout(self.page_photo)
        p1_layout.setContentsMargins(0, 0, 0, 0)
        p1_layout.setSpacing(8)

        self.photo_img_lbl = QLabel()
        self.photo_img_lbl.setObjectName("PhotoImageLabel")
        self.photo_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_img_lbl.setMinimumHeight(280)
        self.photo_img_lbl.setMaximumHeight(350)
        self.photo_img_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.photo_img_lbl.setToolTip("Нажмите для полноразмерного просмотра")
        self.photo_img_lbl.mousePressEvent = self.on_photo_clicked
        p1_layout.addWidget(self.photo_img_lbl, 1)

        # Photo action buttons
        photo_btn_row = QHBoxLayout()
        photo_btn_row.setSpacing(8)
        self.btn_view_full = QPushButton("🔍 В полный размер")
        self.btn_view_full.setObjectName("PhotoActionButton")
        self.btn_view_full.clicked.connect(self.on_open_full_image)

        self.btn_open_photo_folder = QPushButton("📁 Папка «Фото»")
        self.btn_open_photo_folder.setObjectName("PhotoActionButton")
        self.btn_open_photo_folder.clicked.connect(self.on_open_photo_folder)

        photo_btn_row.addWidget(self.btn_view_full)
        photo_btn_row.addWidget(self.btn_open_photo_folder)
        p1_layout.addLayout(photo_btn_row)
        self.photo_stack.addWidget(self.page_photo)

        # Page 2: Placeholder ("Без фото")
        self.page_placeholder = QFrame()
        self.page_placeholder.setObjectName("PhotoPlaceholderFrame")
        p2_layout = QVBoxLayout(self.page_placeholder)
        p2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p2_layout.setSpacing(8)

        icon_lbl = QLabel("📷")
        icon_lbl.setObjectName("PhotoPlaceholderIcon")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_ph = QLabel("Фотография отсутствует")
        title_ph.setObjectName("PhotoPlaceholderTitle")
        title_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_ph = QLabel("В папке оборудования не найден файл main.jpg")
        desc_ph.setObjectName("PhotoPlaceholderDesc")
        desc_ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_ph.setWordWrap(True)

        self.expected_photo_path_lbl = QLabel()
        self.expected_photo_path_lbl.setObjectName("PhotoPathBox")
        self.expected_photo_path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expected_photo_path_lbl.setWordWrap(True)

        btn_ph_row = QVBoxLayout()
        btn_ph_row.setSpacing(6)
        self.btn_open_eq_folder_for_photo = QPushButton("📁 Открыть папку оборудования")
        self.btn_open_eq_folder_for_photo.setObjectName("FolderButton")
        self.btn_open_eq_folder_for_photo.clicked.connect(self.on_open_folder)

        self.btn_recheck_photo = QPushButton("🔄 Проверить наличие main.jpg")
        self.btn_recheck_photo.setObjectName("PhotoActionButton")
        self.btn_recheck_photo.clicked.connect(self.start_photo_load)

        btn_ph_row.addWidget(self.btn_open_eq_folder_for_photo)
        btn_ph_row.addWidget(self.btn_recheck_photo)

        p2_layout.addStretch()
        p2_layout.addWidget(icon_lbl)
        p2_layout.addWidget(title_ph)
        p2_layout.addWidget(desc_ph)
        p2_layout.addWidget(self.expected_photo_path_lbl)
        p2_layout.addSpacing(6)
        p2_layout.addLayout(btn_ph_row)
        p2_layout.addStretch()
        self.photo_stack.addWidget(self.page_placeholder)

        photo_card_layout.addWidget(self.photo_stack, 1)

        # Status text at the bottom of the photo card
        self.photo_status_lbl = QLabel()
        self.photo_status_lbl.setStyleSheet("font-size: 11px; color: #64748B;")
        self.photo_status_lbl.setWordWrap(True)
        photo_card_layout.addWidget(self.photo_status_lbl)

        content_row.addWidget(self.photo_card, 0)

        # --- RIGHT: Technical Specs Form Card ---
        specs_card = QFrame()
        specs_card.setObjectName("CardContentFrame")
        specs_card_layout = QVBoxLayout(specs_card)
        specs_card_layout.setContentsMargins(16, 14, 16, 14)
        specs_card_layout.setSpacing(12)

        specs_header = QLabel("⚙️ Технические характеристики и привязка к архиву")
        specs_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #F1F5F9;")
        specs_card_layout.addWidget(specs_header)

        tab1_form = QFormLayout()
        tab1_form.setContentsMargins(0, 4, 0, 4)
        tab1_form.setSpacing(12)

        self.inv_input = QLineEdit(str(self.eq_data.get('inventory_number', '')))
        self.inv_input.setMinimumHeight(32)
        self.inv_input.textChanged.connect(self._on_header_inputs_changed)

        self.name_input = QLineEdit(str(self.eq_data.get('name', '')))
        self.name_input.setMinimumHeight(32)
        self.name_input.textChanged.connect(self._on_header_inputs_changed)

        self.controller_input = QLineEdit(str(self.eq_data.get('controller', '')))
        self.controller_input.setMinimumHeight(32)
        self.controller_input.textChanged.connect(self._on_header_inputs_changed)

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
        self.workshop_combo.currentIndexChanged.connect(self._on_header_inputs_changed)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumHeight(32)
        self.status_combo.addItems(['В работе', 'На обслуживании', 'Резерв', 'Списан'])
        self.status_combo.setCurrentText(initial_status)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)

        self.folder_path_input = QLineEdit(str(self.eq_data.get('folder_path', self.eq_data.get('sub_folder', ''))))
        self.folder_path_input.setMinimumHeight(32)
        self.folder_path_input.setPlaceholderText("Относительный или прямой путь к папке станка в архиве")

        tab1_form.addRow("Инвентарный номер:", self.inv_input)
        tab1_form.addRow("Название станка:", self.name_input)
        tab1_form.addRow("Контроллер / ЧПУ:", self.controller_input)
        tab1_form.addRow("Год ввода в эксплуатацию:", self.year_input)
        tab1_form.addRow("Цех размещения:", self.workshop_combo)
        tab1_form.addRow("Статус оборудования:", self.status_combo)
        tab1_form.addRow("Путь к папке архива:", self.folder_path_input)

        specs_card_layout.addLayout(tab1_form)

        # Folder status and quick open
        self.folder_status_lbl = QLabel("Поиск расположения папки...")
        self.folder_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #CBD5E1;")
        self.folder_status_lbl.setWordWrap(True)
        specs_card_layout.addWidget(self.folder_status_lbl)

        btn_folder_action = QPushButton("📁 Открыть папку оборудования в Windows Explorer")
        btn_folder_action.setObjectName("FolderButton")
        btn_folder_action.setStyleSheet("font-size: 13px; padding: 9px;")
        btn_folder_action.clicked.connect(self.on_open_folder)
        specs_card_layout.addWidget(btn_folder_action)

        specs_card_layout.addStretch()
        content_row.addWidget(specs_card, 1)

        tab1_layout.addLayout(content_row)
        self.tab1_scroll.setWidget(self.tab1)
        self.tabs.addTab(self.tab1_scroll, "⚙ Технические данные")

        # =========================================================================
        # --- TAB 2: IT & Software (with Scroll Area) ---
        # =========================================================================
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

        # =========================================================================
        # --- TAB 3: Documentation & Storage ---
        # =========================================================================
        self.tab3 = QWidget()
        tab3_layout = QVBoxLayout(self.tab3)
        tab3_layout.setContentsMargins(16, 16, 16, 16)
        tab3_layout.setSpacing(12)

        storage_card = QFrame()
        storage_card.setObjectName("CardContentFrame")
        sc_layout = QVBoxLayout(storage_card)
        sc_layout.setSpacing(10)
        
        self.tab3_folder_status_lbl = QLabel("Поиск расположения папки...")
        self.tab3_folder_status_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #CBD5E1;")
        self.tab3_folder_status_lbl.setWordWrap(True)
        
        self.sub_folder_input = QLineEdit(str(self.eq_data.get('sub_folder', '')))
        self.sub_folder_input.setMinimumHeight(32)
        self.sub_folder_input.setPlaceholderText("Например: New Archive\\Цех 02 (ЗСКА)\\1895_...")
        
        sf_layout = QHBoxLayout()
        sf_lbl = QLabel("Папка оборудования:")
        sf_lbl.setStyleSheet("font-weight: bold;")
        sf_layout.addWidget(sf_lbl)
        sf_layout.addWidget(self.sub_folder_input)
        
        self.btn_open_explorer = QPushButton("📁 Открыть папку оборудования в Windows Explorer")
        self.btn_open_explorer.setObjectName("FolderButton")
        self.btn_open_explorer.setStyleSheet("font-size: 14px; padding: 10px;")
        self.btn_open_explorer.clicked.connect(self.on_open_folder)

        sc_layout.addWidget(self.tab3_folder_status_lbl)
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

        # =========================================================================
        # --- TAB 4: Maintenance & Fault History ---
        # =========================================================================
        self.tab4 = QWidget()
        tab4_layout = QVBoxLayout(self.tab4)
        tab4_layout.setContentsMargins(14, 14, 14, 14)
        tab4_layout.setSpacing(10)

        # Tab 4 Header Bar
        maint_header = QHBoxLayout()
        maint_title = QLabel("🛠 Журнал технического обслуживания и неисправностей")
        maint_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #F1F5F9;")
        
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
        m_hdr = self.maint_table.horizontalHeader()
        m_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        m_hdr.setStretchLastSection(True)
        
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
        self.maint_notes_view.setMinimumHeight(105)
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
        self.maint_work_view.setMinimumHeight(105)
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

        # Action Buttons Layout at bottom of dialog
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

        # Apply role-based access permissions
        self.apply_permissions()
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and hasattr(auth, 'user_changed'):
            auth.user_changed.connect(self.apply_permissions)

    def apply_permissions(self):
        """Ограничение редактирования и удаления для пользователей в режиме только для чтения."""
        auth = getattr(self.db_manager, 'auth_manager', None)
        can_edit = auth.can_edit() if auth else True
        can_delete = auth.can_delete() if auth else True

        # General and technical specs inputs
        for inp in (
            self.inv_input, self.name_input, self.folder_path_input,
            self.controller_input, self.ip_input, self.mac_input,
            self.screen_input, self.processor_input, self.ram_input,
            self.rom_input, self.os_input, self.antivirus_input
        ):
            inp.setReadOnly(not can_edit)

        self.workshop_combo.setEnabled(can_edit)
        self.year_input.setEnabled(can_edit)
        self.status_combo.setEnabled(can_edit)

        # Bottom save button
        self.btn_save.setEnabled(can_edit)
        if can_edit:
            self.btn_save.setToolTip("Сохранить изменения карточки станка в базе данных")
        else:
            self.btn_save.setToolTip("Требуется авторизация с правами редактора для сохранения")

        # Maintenance controls
        self.btn_new_maint.setEnabled(can_edit)
        self.btn_save_maint.setEnabled(can_edit)
        self.btn_delete_maint.setEnabled(can_delete and self.current_maint_id is not None)

        self.maint_type_input.setReadOnly(not can_edit)
        self.maint_start_input.setReadOnly(not can_edit)
        self.maint_end_input.setReadOnly(not can_edit)
        self.maint_notes_view.setReadOnly(not can_edit)
        self.maint_work_view.setReadOnly(not can_edit)

    # =========================================================================
    # --- PHOTO LOGIC & HELPERS ---
    # =========================================================================
    def start_photo_load(self):
        """Запускает поиск и загрузку фото в фоновом потоке без блокировки GUI."""
        self.photo_stack.setCurrentIndex(0)  # Show loading
        self.photo_status_lbl.setText("Поиск фотографии main.jpg...")

        # Синхронизируем актуальные значения из полей перед поиском
        current_eq = dict(self.eq_data)
        current_eq['sub_folder'] = self.folder_path_input.text().strip() if hasattr(self, 'folder_path_input') else current_eq.get('sub_folder', '')
        current_eq['folder_path'] = current_eq['sub_folder']
        current_eq['inventory_number'] = self.inv_input.text().strip() if hasattr(self, 'inv_input') else current_eq.get('inventory_number', '')
        current_eq['name'] = self.name_input.text().strip() if hasattr(self, 'name_input') else current_eq.get('name', '')

        self._photo_thread = PhotoLoaderThread(self.folder_router, current_eq)
        self._photo_thread.loaded.connect(self._on_photo_loaded)
        self._photo_thread.start()

    def _on_photo_loaded(self, found, photo_path, message, qimage):
        self.current_photo_path = photo_path
        self.current_photo_folder = os.path.dirname(photo_path) if photo_path else None
        self.current_qimage = qimage

        if found and qimage and not qimage.isNull():
            self.current_pixmap = QPixmap.fromImage(qimage)
            self._render_photo()
            self.photo_stack.setCurrentIndex(1)  # Loaded
            self.photo_status_lbl.setText(f"✔ Фото: {os.path.basename(photo_path)}")
            self.photo_status_lbl.setStyleSheet("font-size: 11px; color: #34D399;")
        else:
            self.current_pixmap = None
            self.expected_photo_path_lbl.setText(photo_path or "Путь к фото не сформирован")
            self.photo_stack.setCurrentIndex(2)  # Placeholder
            self.photo_status_lbl.setText(f"⚠️ {message}")
            self.photo_status_lbl.setStyleSheet("font-size: 11px; color: #FBBF24;")

    def _render_photo(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            lbl_w = max(self.photo_img_lbl.width(), 360)
            lbl_h = max(self.photo_img_lbl.height(), 280)
            scaled = self.current_pixmap.scaled(
                QSize(lbl_w, lbl_h),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.photo_img_lbl.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_pixmap and self.photo_stack.currentIndex() == 1:
            self._render_photo()

    def on_photo_clicked(self, event):
        self.on_open_full_image()

    def on_open_full_image(self):
        if not self.current_photo_path or not os.path.isfile(self.current_photo_path):
            QMessageBox.information(self, "Фотография отсутствует", "Файл фотографии не найден на сетевом накопителе.")
            return
        inv_str = self.inv_input.text().strip()
        name_str = self.name_input.text().strip()
        dlg = ImageViewerDialog(self.current_photo_path, name_str, inv_str, self.folder_router, self)
        dlg.exec()

    def on_open_photo_folder(self):
        if not self.current_photo_folder:
            self.on_open_folder()
            return
        self.folder_router.open_folder_in_explorer(self.current_photo_folder)

    def _on_header_inputs_changed(self):
        """Динамически обновляет заголовки в карточке при редактировании пользователем."""
        inv_txt = self.inv_input.text().strip() or '-'
        name_txt = self.name_input.text().strip() or 'Без названия'
        ctrl_txt = self.controller_input.text().strip() or '-'
        ws_txt = self.workshop_combo.currentText() or '-'

        self.tab1_name_lbl.setText(name_txt)
        self.tab1_sub_lbl.setText(f"Инв. №: {inv_txt}   |   ЧПУ / Контроллер: {ctrl_txt}   |   Цех: {ws_txt}")
        self.setWindowTitle(f"Карточка станка: {inv_txt} — {name_txt}")

    def _on_status_changed(self, new_status):
        self._apply_status_style(self.tab1_status_lbl, new_status)

    @staticmethod
    def _apply_status_style(label, status):
        label.setText(status)
        if status == 'В работе':
            label.setObjectName("StatusPillWork")
        elif status == 'На обслуживании':
            label.setObjectName("StatusPillMaint")
        elif status == 'Резерв':
            label.setObjectName("StatusPillReserve")
        else:
            label.setObjectName("StatusPillDecomm")
        # Force stylesheet refresh on dynamic change
        label.style().unpolish(label)
        label.style().polish(label)

    # =========================================================================
    # --- STORAGE & FOLDER STATUS ---
    # =========================================================================
    def update_folder_status(self):
        temp_data = dict(self.eq_data)
        if hasattr(self, 'folder_path_input') and self.folder_path_input.text().strip():
            temp_data['sub_folder'] = self.folder_path_input.text().strip()
            temp_data['folder_path'] = self.folder_path_input.text().strip()

        found, path, msg = self.folder_router.resolve_equipment_folder(temp_data)
        text = f"📁 Сетевой путь: {path}"
        style = "color: #38BDF8; font-weight: bold;"

        self.folder_status_lbl.setText(text)
        self.folder_status_lbl.setStyleSheet(style)
        if hasattr(self, 'tab3_folder_status_lbl'):
            self.tab3_folder_status_lbl.setText(text)
            self.tab3_folder_status_lbl.setStyleSheet(style)

    def on_open_folder(self):
        target_path = self.folder_path_input.text().strip() if hasattr(self, 'folder_path_input') else ''
        if not target_path and hasattr(self, 'sub_folder_input'):
            target_path = self.sub_folder_input.text().strip()

        self.eq_data['sub_folder'] = target_path
        self.eq_data['folder_path'] = target_path
        found, path, msg = self.folder_router.resolve_equipment_folder(self.eq_data)
        if path:
            self.folder_router.open_folder_in_explorer(path)

    # =========================================================================
    # --- DOCUMENTATION LOGIC ---
    # =========================================================================
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

    # =========================================================================
    # --- MAINTENANCE JOURNAL LOGIC ---
    # =========================================================================
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
            auth = getattr(self.db_manager, 'auth_manager', None)
            can_delete = auth.can_delete() if auth else True
            self.btn_delete_maint.setEnabled(can_delete)

    def on_new_maint(self):
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_edit():
            QMessageBox.warning(self, "Доступ ограничен", "Для создания записи ТО требуется войти с правами редактора.")
            return
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
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_edit():
            if show_msg:
                QMessageBox.warning(self, "Доступ ограничен", "Для сохранения записи ТО требуется войти с правами редактора.")
            return False, "Отказано в доступе"

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
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_delete():
            QMessageBox.warning(self, "Доступ ограничен", "Для удаления записи ТО требуется войти с правами редактора или администратора.")
            return

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

    # =========================================================================
    # --- SAVE ENTIRE EQUIPMENT ---
    # =========================================================================
    def on_save(self):
        auth = getattr(self.db_manager, 'auth_manager', None)
        if auth and not auth.can_edit():
            QMessageBox.warning(self, "Доступ ограничен", "Для сохранения изменений станка требуется войти с правами редактора или администратора.")
            return

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
