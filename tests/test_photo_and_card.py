"""
Tests for equipment photo resolution and DetailCardDialog layout.
"""
import unittest
import os
import tempfile
import shutil
from PySide6.QtWidgets import QApplication
from folder_router import FolderRouter
from ui.detail_card_dialog import DetailCardDialog, ImageViewerDialog


class MockDbManager:
    def __init__(self):
        self.config = {"storage": {}, "db": {}}

    def get_workshops(self):
        return [
            {"id": 1, "name": "Цех 01", "description": ""},
            {"id": 2, "name": "Цех 02 (ЗСКА)", "description": ""}
        ]

    def get_equipment_docs(self, eq_id):
        return []

    def get_machine_maintenance(self, machine_id):
        return []

    def save_equipment(self, data):
        return True, "Успешно"

    def save_machine_maintenance(self, data):
        return True, "Успешно", 1

    def delete_machine_maintenance(self, maint_id):
        return True, "Удалено"


class TestPhotoAndDetailCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db = MockDbManager()
        self.router = FolderRouter({
            "unc_path": self.temp_dir,
            "network_drive_path": self.temp_dir,
            "fallback_local_path": self.temp_dir,
            "path_mode": 1
        })

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_photo_not_found(self):
        eq = {
            "inventory_number": "9999",
            "name": "Тестовый станок",
            "workshop_name": "Цех 01",
            "sub_folder": "Цех 01/9999_Тестовый станок"
        }
        found, photo_path, folder, msg = self.router.resolve_equipment_photo(eq)
        self.assertFalse(found)
        self.assertIn("main.jpg", photo_path)

    def test_photo_found_when_main_jpg_exists(self):
        # Create machine folder and Фото/main.jpg
        machine_folder = os.path.join(self.temp_dir, "Цех 01", "1234_Фрезерный станок")
        photo_dir = os.path.join(machine_folder, "Фото")
        os.makedirs(photo_dir, exist_ok=True)
        main_jpg = os.path.join(photo_dir, "main.jpg")
        with open(main_jpg, "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0" + b"\x00" * 20)  # fake jpeg header

        eq = {
            "inventory_number": "1234",
            "name": "Фрезерный станок",
            "workshop_name": "Цех 01",
            "sub_folder": "Цех 01/1234_Фрезерный станок"
        }
        found, photo_path, actual_folder, msg = self.router.resolve_equipment_photo(eq)
        self.assertTrue(found)
        self.assertEqual(os.path.normpath(photo_path), os.path.normpath(main_jpg))
        self.assertEqual(os.path.normpath(actual_folder), os.path.normpath(photo_dir))

    def test_detail_card_dialog_layout(self):
        eq = {
            "id": 10,
            "inventory_number": "1895",
            "name": "Электроэрозионный станок",
            "workshop_id": 2,
            "workshop_name": "Цех 02 (ЗСКА)",
            "controller": "Fanuc 18i",
            "status": "В работе",
            "sub_folder": "Цех 02/1895_Электроэрозионный станок"
        }
        dlg = DetailCardDialog(eq, self.db, self.router)
        # Check that tabs are present
        self.assertEqual(dlg.tabs.count(), 4)
        # Tab 1 must contain photo widgets
        self.assertTrue(hasattr(dlg, 'photo_stack'))
        self.assertTrue(hasattr(dlg, 'photo_img_lbl'))
        self.assertTrue(hasattr(dlg, 'page_placeholder'))
        # Top banner in tab 1
        self.assertEqual(dlg.tab1_name_lbl.text(), "Электроэрозионный станок")
        self.assertEqual(dlg.tab1_status_lbl.text(), "В работе")
        # Ensure status change updates badge
        dlg.status_combo.setCurrentText("На обслуживании")
        self.assertEqual(dlg.tab1_status_lbl.text(), "На обслуживании")
        # Ensure viewer dialog can be instantiated
        viewer = ImageViewerDialog("test.jpg", "Станок", "1895", self.router, dlg)
        self.assertIsNotNone(viewer)

    def test_direct_synology_path_construction(self):
        router = FolderRouter({
            "unc_path": "\\\\Synology_DS423\\Share_folder",
            "path_mode": 1
        })
        eq = {
            "inventory_number": "1895",
            "name": "Электроэрозионный проволочно-вырезной станок GF AgieCharmilles ROBОFIL 240 SLP",
            "folder_path": "New Archive\\Цех 02 (ЗСКА)\\1895_Электроэрозионный проволочно-вырезной станок GF AgieCharmilles ROBОFIL 240 SLP"
        }
        found, resolved, msg = router.resolve_equipment_folder(eq, check_exists=False)
        self.assertTrue(found)
        expected = "\\\\Synology_DS423\\Share_folder\\New Archive\\Цех 02 (ЗСКА)\\1895_Электроэрозионный проволочно-вырезной станок GF AgieCharmilles ROBОFIL 240 SLP"
        self.assertEqual(resolved, expected)


if __name__ == "__main__":
    unittest.main()
