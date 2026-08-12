import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db_manager import DatabaseManager
from folder_router import FolderRouter


class SchemaCompatibilityTests(unittest.TestCase):
    def test_schema_compatibility_mapping(self):
        db = DatabaseManager()
        db.config['db']['host'] = 'localhost'
        db.config['db']['port'] = 5432
        db.config['db']['user'] = 'postgres'
        db.config['db']['password'] = 'superuser'
        db.config['db']['dbname'] = 'postgres'

        self.assertEqual(db.get_schema_mapping()['machines'], 'equipment.machines')
        self.assertEqual(db.get_schema_mapping()['workshops'], 'equipment.workshops')
        self.assertEqual(db.get_schema_mapping()['computer_specs'], 'equipment.computer_specs')

    def test_normalize_equipment_row_maps_computer_specs(self):
        db = DatabaseManager()
        row = {
            'id': 1,
            'inventory_number': 111,
            'machine_name': 'Станок',
            'controller': 'PLC',
            'folder_path': 'C:/archive',
            'screen': '24"',
            'processor': 'i7',
            'ram': '16 GB',
            'rom': '512 GB',
            'operating_system': 'Windows 11',
            'antivirus': 'Kaspersky',
        }

        normalized = db._normalize_equipment_row(row)
        self.assertEqual(normalized['name'], 'Станок')
        self.assertEqual(normalized['screen'], '24"')
        self.assertEqual(normalized['processor'], 'i7')
        self.assertEqual(normalized['ram'], '16 GB')
        self.assertEqual(normalized['rom'], '512 GB')
        self.assertEqual(normalized['operating_system'], 'Windows 11')
        self.assertEqual(normalized['antivirus'], 'Kaspersky')

    def test_folder_router_handles_numeric_inventory_and_normalizes_archives(self):
        router = FolderRouter({
            'network_drive_path': 'S:\\New Archive',
            'unc_path': '\\\\100.76.39.21\\Share_folder',
            'unc_path_alt': '\\\\192.168.1.68\\Share_folder',
            'fallback_local_path': '',
            'path_mode': 1,
        })

        full_path = router._build_full_folder_path('\\\\100.76.39.21\\Share_folder', 'New Archive\\Цех 02 (ЗСКА)\\1895_Станок')
        self.assertEqual(full_path, '\\\\100.76.39.21\\Share_folder\\New Archive\\Цех 02 (ЗСКА)\\1895_Станок')

        normalized = router._normalize_folder_path_value('New Archive\\Цех 02 (ЗСКА)\\1895_Станок')
        self.assertEqual(normalized, 'New Archive\\Цех 02 (ЗСКА)\\1895_Станок')

    def test_resolve_equipment_folder_uses_database_folder_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = os.path.join(tmpdir, 'archive')
            os.makedirs(os.path.join(base_path, 'New Archive', 'Цех 02 (ЗСКА)'))
            target_path = os.path.join(base_path, 'New Archive', 'Цех 02 (ЗСКА)', '1895_Электроэрозионный проволочно-вырезной станок GF AgieCharmilles ROBОFIL 240 SLP')
            os.makedirs(target_path)

            router = FolderRouter({
                'network_drive_path': base_path,
                'unc_path': '\\\\100.76.39.21\\Share_folder',
                'unc_path_alt': '\\\\192.168.1.68\\Share_folder',
                'fallback_local_path': '',
                'path_mode': 1,
            })

            equipment = {
                'inventory_number': 1895,
                'name': 'Станок',
                'sub_folder': 'New Archive\\Цех 02 (ЗСКА)\\1895_Электроэрозионный проволочно-вырезной станок GF AgieCharmilles ROBОFIL 240 SLP',
                'workshop_name': 'Цех 02 (ЗСКА)',
                'workshop_code': '02',
            }

            found, resolved_path, message = router.resolve_equipment_folder(equipment)
            self.assertTrue(found)
            self.assertEqual(resolved_path, target_path)
            self.assertIn('Папка найдена', message)


if __name__ == '__main__':
    unittest.main()
