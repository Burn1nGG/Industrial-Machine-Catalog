import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import DatabaseManager, get_config_path


class ConfigPersistenceTests(unittest.TestCase):
    def test_get_config_path_default(self):
        path = get_config_path()
        self.assertTrue(path.endswith('config.json'))

    def test_config_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = os.path.join(tmp_dir, 'config.json')
            db = DatabaseManager(config_file=cfg_file)

            custom_data = {
                "db": {
                    "host": "192.168.1.200",
                    "port": 5432,
                    "dbname": "enterprise_db",
                    "user": "operator",
                    "password": "secret"
                },
                "storage": {
                    "unc_path": "\\\\synology\\share",
                    "path_mode": 2
                }
            }

            saved = db.save_config(custom_data)
            self.assertTrue(saved)
            self.assertTrue(os.path.exists(cfg_file))

            # New instance reading same config
            db2 = DatabaseManager(config_file=cfg_file)
            self.assertEqual(db2.config["db"]["host"], "192.168.1.200")
            self.assertEqual(db2.config["db"]["dbname"], "enterprise_db")
            self.assertEqual(db2.config["storage"]["path_mode"], 2)


if __name__ == '__main__':
    unittest.main()

