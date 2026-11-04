"""
Unit tests for enterprise-wide maintenance log feature and AllMaintenanceDialog.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication
from db_manager import DatabaseManager
from folder_router import FolderRouter

# Ensure QApplication exists for Qt widget tests
app = QApplication.instance()
if not app:
    app = QApplication([])


class AllMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.router = FolderRouter({
            'network_drive_path': 'S:\\New Archive',
            'unc_path': '\\\\Synology_DS423\\Share_folder',
            'fallback_local_path': ''
        })

    def test_get_all_maintenance_sql_generation(self):
        """Проверяет корректное формирование SQL и параметров в get_all_maintenance."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock to_regclass checking
        mock_cursor.fetchone.return_value = {'tbl': 'equipment.machine_maintenance'}
        mock_cursor.fetchall.return_value = [
            {
                'id': 10,
                'machine_id': 1,
                'inventory_number': 1895,
                'machine_name': 'Станок 1895',
                'workshop_name': 'Цех 02',
                'work_type': 'Плановое ТО',
                'start_date': '2026-08-17',
                'end_date': '2026-08-17',
                'work_performed': 'Замена фильтров',
                'notes': 'Плановая замена'
            }
        ]

        with patch.object(self.db, 'get_connection', return_value=mock_conn):
            # Test filter by inventory_number and machine_name
            results = self.db.get_all_maintenance(
                inventory_number="1895",
                machine_name="ROBОFIL",
                workshop_id=2,
                search_text="фильтр"
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['inventory_number'], 1895)
            self.assertEqual(results[0]['work_type'], 'Плановое ТО')

            # Verify cursor execution received query with filters
            executed_query, executed_params = mock_cursor.execute.call_args_list[1][0]
            self.assertIn("equipment.machine_maintenance", executed_query)
            self.assertIn("inventory_number", executed_query)
            self.assertIn("machine_name", executed_query)
            self.assertIn("workshop_id", executed_query)
            self.assertIn("work_performed ILIKE", executed_query)
            self.assertIn(2, executed_params)
            self.assertIn("%1895%", executed_params)
            self.assertIn("%ROBОFIL%", executed_params)
            self.assertIn("%фильтр%", executed_params)

    def test_get_machine_by_id(self):
        """Проверяет получение карточки станка по его ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            'id': 5,
            'inventory_number': 1042,
            'machine_name': 'DMG MORI CTX 310',
            'controller': 'Heidenhain',
            'workshop_id': 1,
            'workshop_name': 'Цех 01',
            'folder_path': 'New Archive/Цех 01/1042_DMG'
        }

        with patch.object(self.db, 'get_connection', return_value=mock_conn):
            machine = self.db.get_machine_by_id(5)
            self.assertIsNotNone(machine)
            self.assertEqual(machine['id'], 5)
            self.assertEqual(machine['inventory_number'], 1042)
            self.assertEqual(machine['name'], 'DMG MORI CTX 310')
            self.assertEqual(machine['sub_folder'], 'New Archive/Цех 01/1042_DMG')

    def test_all_maintenance_dialog_ui_and_search(self):
        """Проверяет интерфейс диалога AllMaintenanceDialog и фильтрацию."""
        from ui.all_maintenance_dialog import AllMaintenanceDialog

        sample_records = [
            {
                'id': 1,
                'machine_id': 101,
                'inventory_number': 1895,
                'machine_name': 'Станок 1895 ROBОFIL',
                'workshop_name': 'Цех 02 (ЗСКА)',
                'work_type': 'Ремонт',
                'start_date': '2026-05-10',
                'end_date': '2026-05-11',
                'work_performed': 'Ремонт привода осей',
                'notes': 'Ошибка энкодера E-402'
            },
            {
                'id': 2,
                'machine_id': 102,
                'inventory_number': 2040,
                'machine_name': 'Фрезерный станок 65А80',
                'workshop_name': 'Цех 01',
                'work_type': 'Плановое ТО',
                'start_date': '2026-06-01',
                'end_date': '2026-06-02',
                'work_performed': 'Замена масла в шпинделе',
                'notes': 'Регламент'
            }
        ]

        with patch.object(self.db, 'get_workshops', return_value=[{'id': 1, 'name': 'Цех 01'}, {'id': 2, 'name': 'Цех 02 (ЗСКА)'}]), \
             patch.object(self.db, 'get_all_maintenance', return_value=sample_records):
            dialog = AllMaintenanceDialog(self.db, self.router)

            # Check that table populated
            self.assertEqual(dialog.table.rowCount(), 2)

            # Check search fields exist
            self.assertTrue(hasattr(dialog, 'num_input'))
            self.assertTrue(hasattr(dialog, 'name_input'))
            self.assertTrue(hasattr(dialog, 'ws_combo'))
            self.assertTrue(hasattr(dialog, 'text_input'))
            self.assertTrue(hasattr(dialog, 'btn_export_csv'))

            # Check first row selection updates details (sorted descending by start_date: 2026-06-01 is row 0)
            dialog.table.selectRow(0)
            self.assertIsNotNone(dialog.current_record)
            self.assertIn("2040", dialog.detail_title.text())
            self.assertEqual(dialog.detail_type_input.text(), 'Плановое ТО')

            # Row 1 is 2026-05-10 (inventory 1895)
            dialog.table.selectRow(1)
            self.assertIn("1895", dialog.detail_title.text())
            self.assertEqual(dialog.detail_type_input.text(), 'Ремонт')

            # Test reset
            dialog.num_input.setText("1895")
            dialog.on_reset()
            self.assertEqual(dialog.num_input.text(), "")

    def test_main_window_has_maintenance_button(self):
        """Проверяет наличие кнопки истории обслуживания на главном окне."""
        from ui.main_window import MainWindow

        with patch.object(self.db, 'test_connection', return_value=(True, "OK")), \
             patch.object(self.db, 'get_workshops', return_value=[]), \
             patch.object(self.db, 'search_equipment', return_value=[]):
            win = MainWindow()
            self.assertTrue(hasattr(win, 'btn_all_maint'))
            self.assertEqual(win.btn_all_maint.text(), "🛠 История обслуживания")
            self.assertTrue(hasattr(win, 'open_all_maintenance_dialog'))


if __name__ == '__main__':
    unittest.main()
