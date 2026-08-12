"""
Main entry point for Industrial Equipment Catalog Windows Desktop App.
"""
import sys
import os

# Ensure current project directory is in python import path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    # Enable High DPI scaling for modern Windows displays
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("Industrial Equipment Catalog")
    app.setOrganizationName("Industrial Systems")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
