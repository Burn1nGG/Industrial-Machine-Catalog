"""
Authentication & Authorization Manager for Industrial Equipment Catalog App.
Handles user authentication against PostgreSQL equipment.users and role-based permissions.
"""
import hashlib
from PySide6.QtCore import QObject, Signal


def hash_password(password: str) -> str:
    """Calculates SHA-256 hash of password, compatible with PostgreSQL encode(sha256(...), 'hex')."""
    return hashlib.sha256(password.strip().encode('utf-8')).hexdigest()


class AuthManager(QObject):
    user_changed = Signal(object)  # Emits current_user dict or None

    ROLE_VIEWER = 'viewer'
    ROLE_EDITOR = 'editor'
    ROLE_ADMIN = 'admin'

    ROLE_LABELS = {
        'viewer': 'Просмотр',
        'editor': 'Редактор',
        'admin': 'Администратор'
    }

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = None  # None indicates unauthenticated guest / viewer

    @property
    def role(self) -> str:
        if self.current_user:
            return self.current_user.get('role', self.ROLE_VIEWER)
        return self.ROLE_VIEWER

    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def can_edit(self) -> bool:
        """Права на добавление и изменение данных."""
        return self.role in (self.ROLE_EDITOR, self.ROLE_ADMIN)

    def can_delete(self) -> bool:
        """Права на удаление данных."""
        return self.role in (self.ROLE_EDITOR, self.ROLE_ADMIN)

    def is_admin(self) -> bool:
        """Права администратора."""
        return self.role == self.ROLE_ADMIN

    def get_display_name(self) -> str:
        if not self.current_user:
            return "Только чтение"
        name = self.current_user.get('full_name') or self.current_user.get('username') or 'Пользователь'
        role_label = self.ROLE_LABELS.get(self.role, self.role)
        return f"{name} ({role_label})"

    def login(self, username, password):
        username = (username or "").strip()
        password = password or ""
        if not username or not password:
            return False, "Пожалуйста, введите имя пользователя и пароль."

        pwd_hash = hash_password(password)

        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, username, full_name, role
                FROM equipment.users
                WHERE LOWER(username) = LOWER(%s) AND password_hash = %s;
                """,
                (username, pwd_hash)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                self.current_user = {
                    'id': row[0],
                    'username': row[1],
                    'full_name': row[2] or row[1],
                    'role': row[3] or self.ROLE_VIEWER
                }
                self.user_changed.emit(self.current_user)
                return True, f"Успешный вход: {self.get_display_name()}"
            else:
                return False, "Неверное имя пользователя или пароль."

        except Exception as e:
            err_msg = str(e)
            if "equipment.users" in err_msg or "does not exist" in err_msg or "relation" in err_msg:
                return False, (
                    "Таблица 'equipment.users' ещё не создана в PostgreSQL.\n"
                    "Выполните SQL-скрипт создания пользователей в базе данных."
                )
            return False, f"Ошибка подключения к БД при авторизации:\n{err_msg}"

    def logout(self):
        self.current_user = None
        self.user_changed.emit(None)

