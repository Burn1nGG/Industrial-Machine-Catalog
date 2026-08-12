"""
QSS Stylesheet and Design System for Industrial Equipment Catalog App.
Theme: Modern Industrial Dark & Accent Blue with vibrant status indicators.
"""

STYLESHEET = """
/* --- GLOBAL APP STYLES --- */
QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 13px;
}

/* --- HEADER BAR --- */
#HeaderFrame {
    background-color: #1E293B;
    border-bottom: 1px solid #334155;
    padding: 12px;
}

#AppTitle {
    font-size: 20px;
    font-weight: bold;
    color: #38BDF8;
}

#AppSubTitle {
    font-size: 12px;
    color: #94A3B8;
}

/* --- CARDS & FRAMES --- */
#FilterFrame, #ResultsFrame, #CardContentFrame {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 14px;
}

#FilterTitle {
    font-size: 15px;
    font-weight: 600;
    color: #F1F5F9;
}

/* --- FORM CONTROLS --- */
QLabel {
    color: #CBD5E1;
    font-weight: 500;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #0F172A;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 8px 12px;
    color: #F8FAFC;
    selection-background-color: #0284C7;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #38BDF8;
    background-color: #161F33;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #475569;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #475569;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
    color: #F8FAFC;
    padding: 4px;
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton#SearchButton {
    background-color: #0284C7;
    font-size: 14px;
    padding: 9px 20px;
}

QPushButton#SearchButton:hover {
    background-color: #0369A1;
}

QPushButton#ResetButton {
    background-color: #334155;
    color: #CBD5E1;
}

QPushButton#ResetButton:hover {
    background-color: #475569;
    color: #FFFFFF;
}

QPushButton#FolderButton {
    background-color: #059669;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton#FolderButton:hover {
    background-color: #047857;
}

QPushButton#CardButton {
    background-color: #7C3AED;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton#CardButton:hover {
    background-color: #6D28D9;
}

QPushButton#SettingsButton {
    background-color: #475569;
    color: #F8FAFC;
}

QPushButton#SettingsButton:hover {
    background-color: #64748B;
}

/* --- TABLE WIDGET --- */
QTableWidget {
    background-color: #0F172A;
    border: 1px solid #334155;
    gridline-color: #1E293B;
    border-radius: 6px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #1E293B;
}

QTableWidget::item:selected {
    background-color: #1E293B;
    color: #38BDF8;
}

QHeaderView::section {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #334155;
}

/* --- TAB WIDGET --- */
QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #1E293B;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 10px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #38BDF8;
    border-bottom: 2px solid #38BDF8;
}

QTabBar::tab:hover:!selected {
    background-color: #161F33;
    color: #CBD5E1;
}

/* --- STATUS PILLS / BADGES --- */
QLabel#StatusPillWork {
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: bold;
}

QLabel#StatusPillMaint {
    background-color: #78350F;
    color: #FBBF24;
    border: 1px solid #D97706;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: bold;
}

QLabel#StatusPillReserve {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #64748B;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: bold;
}

QLabel#StatusPillDecomm {
    background-color: #7F1D1D;
    color: #FCA5A5;
    border: 1px solid #DC2626;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: bold;
}

/* --- STATUS BAR --- */
QStatusBar {
    background-color: #090D16;
    color: #94A3B8;
    border-top: 1px solid #1E293B;
}
"""
