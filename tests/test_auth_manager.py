import unittest
from db_manager import DatabaseManager
from auth_manager import AuthManager, hash_password


class AuthManagerTests(unittest.TestCase):
    def test_default_viewer_role(self):
        db = DatabaseManager()
        auth = db.auth_manager

        self.assertFalse(auth.is_authenticated())
        self.assertEqual(auth.role, AuthManager.ROLE_VIEWER)
        self.assertFalse(auth.can_edit())
        self.assertFalse(auth.can_delete())
        self.assertFalse(auth.is_admin())
        self.assertIn("Только чтение", auth.get_display_name())

    def test_hash_password_consistency(self):
        # Known SHA-256 for 'admin': 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
        expected = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
        self.assertEqual(hash_password("admin"), expected)

    def test_editor_permissions(self):
        db = DatabaseManager()
        auth = db.auth_manager

        auth.current_user = {
            'id': 10,
            'username': 'technician',
            'full_name': 'Инженер Иванов',
            'role': AuthManager.ROLE_EDITOR
        }

        self.assertTrue(auth.is_authenticated())
        self.assertTrue(auth.can_edit())
        self.assertTrue(auth.can_delete())
        self.assertFalse(auth.is_admin())
        self.assertIn("Редактор", auth.get_display_name())

    def test_admin_permissions(self):
        db = DatabaseManager()
        auth = db.auth_manager

        auth.current_user = {
            'id': 1,
            'username': 'admin',
            'full_name': 'Главный администратор',
            'role': AuthManager.ROLE_ADMIN
        }

        self.assertTrue(auth.is_authenticated())
        self.assertTrue(auth.can_edit())
        self.assertTrue(auth.can_delete())
        self.assertTrue(auth.is_admin())
        self.assertIn("Администратор", auth.get_display_name())

    def test_logout(self):
        db = DatabaseManager()
        auth = db.auth_manager

        auth.current_user = {'id': 1, 'username': 'admin', 'role': 'admin'}
        self.assertTrue(auth.is_authenticated())

        auth.logout()
        self.assertFalse(auth.is_authenticated())
        self.assertEqual(auth.role, AuthManager.ROLE_VIEWER)
        self.assertFalse(auth.can_edit())

    def test_db_operations_permission_denied_for_viewer(self):
        db = DatabaseManager()
        db.auth_manager.logout()  # Viewer mode

        ok, msg = db.save_equipment({'id': 1, 'name': 'New Machine'})
        self.assertFalse(ok)
        self.assertIn("Отказано в доступе", msg)

        ok, msg, saved_id = db.save_machine_maintenance({'machine_id': 1, 'work_type': 'Test'})
        self.assertFalse(ok)
        self.assertIsNone(saved_id)
        self.assertIn("Отказано в доступе", msg)

        ok, msg = db.delete_machine_maintenance(1)
        self.assertFalse(ok)
        self.assertIn("Отказано в доступе", msg)


if __name__ == '__main__':
    unittest.main()

