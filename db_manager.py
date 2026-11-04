"""
Database Manager module for Industrial Equipment Catalog.
Handles PostgreSQL connection, query execution, and the new equipment.* schema.
"""
import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from auth_manager import AuthManager


def safe_str_err(e):
    try:
        return str(e)
    except Exception:
        try:
            return getattr(e, 'pgerror', str(e)).encode('latin1', errors='ignore').decode('cp1251', errors='ignore')
        except Exception:
            return f"Database exception ({type(e).__name__})"


def get_config_path(filename='config.json'):
    """
    Returns the persistent path to config.json.
    - If running inside a PyInstaller bundle (sys.frozen is True):
      1. Uses config.json in the executable directory (portable mode) if it exists or if directory is writable.
      2. If exe directory is read-only (e.g. Program Files), uses %APPDATA%\\EquipmentCatalog\\config.json.
    - If running from source (development):
      Uses config.json in the project root directory.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidate = os.path.join(exe_dir, filename)
        # Check if we can write to exe_dir
        can_write = False
        try:
            if os.path.exists(candidate):
                with open(candidate, 'a'):
                    pass
                can_write = True
            else:
                test_file = os.path.join(exe_dir, f".test_{os.getpid()}.tmp")
                with open(test_file, 'w') as f:
                    f.write('')
                os.remove(test_file)
                can_write = True
        except (OSError, IOError, PermissionError):
            can_write = False

        if can_write:
            return candidate

        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
        appdata_dir = os.path.join(appdata, 'EquipmentCatalog')
        os.makedirs(appdata_dir, exist_ok=True)
        return os.path.join(appdata_dir, filename)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


class DatabaseManager:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = get_config_path()
        self.config_file = config_file
        self.config = self.load_config()
        self.use_demo_mode = False
        self.connection_failed_before = False
        self.auth_manager = AuthManager(self)

    def load_config(self):
        # 1. If self.config_file exists, load it
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config from {self.config_file}: {e}")

        # 2. If running frozen and self.config_file does not exist yet,
        # read the bundled template from sys._MEIPASS
        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', '')
            bundled = os.path.join(meipass, 'config.json')
            if os.path.exists(bundled):
                try:
                    with open(bundled, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    try:
                        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                        with open(self.config_file, 'w', encoding='utf-8') as f:
                            json.dump(cfg, f, indent=2, ensure_ascii=False)
                    except Exception:
                        pass
                    return cfg
                except Exception:
                    pass

        # 3. Default configuration
        return {
            "db": {
                "host": "localhost",
                "port": 5432,
                "dbname": "postgres",
                "user": "postgres",
                "password": "superuser"
            },
            "storage": {
                "network_drive_path": "S:\\New Archive",
                "unc_path": "\\\\Synology_DS423\\Share_folder",
                "unc_path_alt": "\\\\100.76.39.21\\Share_folder",
                "unc_path_ip": "\\\\192.168.1.68\\Share_folder",
                "fallback_local_path": "",
                "path_mode": 1
            }
        }

    def save_config(self, new_config):
        self.config = new_config
        self.connection_failed_before = False
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_connection(self):
        db_cfg = self.config.get("db", {})
        return psycopg2.connect(
            host=db_cfg.get('host', 'localhost'),
            port=db_cfg.get('port', 5432),
            dbname=db_cfg.get('dbname', 'postgres'),
            user=db_cfg.get('user', 'postgres'),
            password=db_cfg.get('password', 'superuser'),
            connect_timeout=2
        )

    def get_schema_mapping(self):
        return {
            "machines": "equipment.machines",
            "workshops": "equipment.workshops",
            "computer_specs": "equipment.computer_specs",
            "machine_maintenance": "equipment.machine_maintenance"
        }

    def test_connection(self, db_cfg=None):
        if db_cfg is None:
            db_cfg = self.config.get("db", {})
        try:
            conn = psycopg2.connect(
                host=db_cfg.get('host', 'localhost'),
                port=db_cfg.get('port', 5432),
                dbname=db_cfg.get('dbname', 'postgres'),
                user=db_cfg.get('user', 'postgres'),
                password=db_cfg.get('password', 'superuser'),
                connect_timeout=2
            )
            conn.close()
            self.use_demo_mode = False
            self.connection_failed_before = False
            return True, "Успешное подключение к PostgreSQL!"
        except Exception as e:
            self.use_demo_mode = False
            self.connection_failed_before = False
            return False, f"Ошибка подключения к БД: {safe_str_err(e)}"

    def _normalize_equipment_row(self, row):
        if row is None:
            return {}
        item = dict(row)
        item['inventory_number'] = item.get('inventory_number')
        item['name'] = item.get('name') or item.get('machine_name') or ''
        item['machine_name'] = item.get('machine_name') or item.get('name') or ''
        item['model'] = item.get('model') or item.get('controller') or ''
        item['workshop_name'] = item.get('workshop_name') or ''
        item['workshop_code'] = item.get('workshop_code') or ''
        item['sub_folder'] = item.get('sub_folder') or item.get('folder_path') or ''
        item['folder_path'] = item.get('folder_path') or item.get('sub_folder') or ''
        item['status'] = item.get('status') or 'В работе'
        item['year_built'] = item.get('year_built') or item.get('commissioning_year')
        item['commissioning_year'] = item.get('commissioning_year') or item.get('year_built')
        item['cnc_controller'] = item.get('cnc_controller') or item.get('controller') or ''
        item['controller'] = item.get('controller') or item.get('cnc_controller') or ''
        item['ip_address'] = item.get('ip_address') or ''
        item['mac_address'] = item.get('mac_address') or ''
        item['screen'] = item.get('screen') or ''
        item['processor'] = item.get('processor') or ''
        item['ram'] = item.get('ram') or ''
        item['rom'] = item.get('rom') or ''
        item['operating_system'] = item.get('operating_system') or ''
        item['antivirus'] = item.get('antivirus') or ''
        item['software_info'] = item.get('software_info') or ''
        item['tech_specs'] = item.get('tech_specs') or ''
        item['notes'] = item.get('notes') or ''
        return item

    def get_workshops(self):
        """Возвращает список всех цехов из схемы equipment.workshops."""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, name, description FROM equipment.workshops ORDER BY id ASC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            self.use_demo_mode = False
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"DB Error get_workshops: {safe_str_err(e)}")
            self.use_demo_mode = False
            self.connection_failed_before = False
            return []

    def search_equipment(self, workshop_id=None, machine_number="", machine_name=""):
        """Поиск оборудования с использованием представления equipment.v_machines_full и GIN-индексов."""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    id,
                    inventory_number,
                    machine_name AS name,
                    machine_name,
                    workshop_id,
                    workshop_name,
                    workshop_description,
                    folder_path AS sub_folder,
                    folder_path,
                    controller,
                    status,
                    commissioning_year AS year_built,
                    commissioning_year,
                    ip_address,
                    mac_address,
                    screen,
                    processor,
                    ram,
                    rom,
                    operating_system,
                    antivirus,
                    created_at
                FROM equipment.v_machines_full
                WHERE 1=1
            """
            params = []

            if workshop_id is not None and str(workshop_id).strip() != "" and str(workshop_id) != "0":
                query += " AND workshop_id = %s"
                params.append(int(workshop_id))

            if machine_number and machine_number.strip():
                pattern = f"%{machine_number.strip()}%"
                query += " AND (inventory_number::text ILIKE %s OR machine_name ILIKE %s)"
                params.extend([pattern, pattern])

            if machine_name and machine_name.strip():
                pattern = f"%{machine_name.strip()}%"
                query += " AND (machine_name ILIKE %s OR controller ILIKE %s)"
                params.extend([pattern, pattern])

            query += " ORDER BY id ASC;"

            try:
                cur.execute(query, params)
                rows = cur.fetchall()
            except Exception:
                # Резервный запрос в случае, если VIEW еще не создан в БД
                conn.rollback()
                fallback_query = """
                    SELECT
                        m.id,
                        m.inventory_number,
                        m.machine_name AS name,
                        m.machine_name,
                        m.workshop_id,
                        w.name AS workshop_name,
                        w.description AS workshop_description,
                        m.folder_path AS sub_folder,
                        m.folder_path,
                        m.controller,
                        m.status,
                        m.commissioning_year AS year_built,
                        m.commissioning_year,
                        cs.ip_address,
                        cs.mac_address,
                        cs.screen,
                        cs.processor,
                        cs.ram,
                        cs.rom,
                        cs.operating_system,
                        cs.antivirus,
                        m.created_at
                    FROM equipment.machines m
                    LEFT JOIN equipment.workshops w ON w.id = m.workshop_id
                    LEFT JOIN equipment.computer_specs cs ON cs.machine_id = m.id
                    WHERE 1=1
                """
                fb_params = []
                if workshop_id is not None and str(workshop_id).strip() != "" and str(workshop_id) != "0":
                    fallback_query += " AND m.workshop_id = %s"
                    fb_params.append(int(workshop_id))
                if machine_number and machine_number.strip():
                    pattern = f"%{machine_number.strip()}%"
                    fallback_query += " AND (m.inventory_number::text ILIKE %s OR m.machine_name ILIKE %s)"
                    fb_params.extend([pattern, pattern])
                if machine_name and machine_name.strip():
                    pattern = f"%{machine_name.strip()}%"
                    fallback_query += " AND (m.machine_name ILIKE %s OR m.controller ILIKE %s)"
                    fb_params.extend([pattern, pattern])
                fallback_query += " ORDER BY m.id ASC;"
                cur.execute(fallback_query, fb_params)
                rows = cur.fetchall()

            cur.close()
            conn.close()
            self.use_demo_mode = False
            return [self._normalize_equipment_row(dict(r)) for r in rows]
        except Exception as e:
            print(f"DB Error search_equipment: {safe_str_err(e)}")
            self.use_demo_mode = False
            self.connection_failed_before = False
            return []

    def get_equipment_docs(self, equipment_id):
        """Возвращает прикрепленные документы, если таблица доступна."""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT to_regclass('equipment.equipment_docs') AS tbl")
            res = cur.fetchone()
            if not res or not res.get('tbl'):
                cur.close()
                conn.close()
                return []
            cur.execute("SELECT id, title, doc_type, file_path_or_url FROM equipment.equipment_docs WHERE equipment_id = %s;", (int(equipment_id),))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_machine_maintenance(self, machine_id):
        """Возвращает историю обслуживания и неисправностей оборудования."""
        if not machine_id:
            return []
        try:
            m_id = int(machine_id)
        except (ValueError, TypeError):
            return []

        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT to_regclass('equipment.machine_maintenance') AS tbl")
            res = cur.fetchone()
            if not res or not res.get('tbl'):
                cur.close()
                conn.close()
                return []
            cur.execute(
                """
                SELECT
                    id,
                    machine_id,
                    work_type,
                    created_at,
                    start_date,
                    end_date,
                    work_performed,
                    notes
                FROM equipment.machine_maintenance
                WHERE machine_id = %s
                ORDER BY start_date DESC NULLS LAST, id DESC;
                """,
                (m_id,)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"DB Error get_machine_maintenance: {safe_str_err(e)}")
            return []

    def get_all_maintenance(self, inventory_number=None, machine_name=None, workshop_id=None, search_text=None):
        """Возвращает историю обслуживания и неисправностей всего оборудования с фильтрацией."""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT to_regclass('equipment.machine_maintenance') AS tbl")
            res = cur.fetchone()
            if not res or not res.get('tbl'):
                cur.close()
                conn.close()
                return []

            query = """
                SELECT
                    mm.id,
                    mm.machine_id,
                    mm.work_type,
                    mm.created_at,
                    mm.start_date,
                    mm.end_date,
                    mm.work_performed,
                    mm.notes,
                    m.inventory_number,
                    m.machine_name,
                    m.machine_name AS name,
                    m.workshop_id,
                    w.name AS workshop_name,
                    m.folder_path,
                    m.folder_path AS sub_folder,
                    m.controller,
                    m.status AS machine_status
                FROM equipment.machine_maintenance mm
                JOIN equipment.machines m ON m.id = mm.machine_id
                LEFT JOIN equipment.workshops w ON w.id = m.workshop_id
                WHERE 1=1
            """
            params = []

            if workshop_id is not None and str(workshop_id).strip() not in ("", "0"):
                query += " AND m.workshop_id = %s"
                params.append(int(workshop_id))

            if inventory_number and str(inventory_number).strip():
                pattern = f"%{str(inventory_number).strip()}%"
                query += " AND (m.inventory_number::text ILIKE %s OR m.machine_name ILIKE %s)"
                params.extend([pattern, pattern])

            if machine_name and machine_name.strip():
                pattern = f"%{machine_name.strip()}%"
                query += " AND (m.machine_name ILIKE %s OR m.controller ILIKE %s)"
                params.extend([pattern, pattern])

            if search_text and search_text.strip():
                pattern = f"%{search_text.strip()}%"
                query += " AND (mm.work_performed ILIKE %s OR mm.notes ILIKE %s OR mm.work_type ILIKE %s)"
                params.extend([pattern, pattern, pattern])

            query += " ORDER BY mm.start_date DESC NULLS LAST, mm.id DESC;"

            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"DB Error get_all_maintenance: {safe_str_err(e)}")
            return []

    def get_machine_by_id(self, machine_id):
        """Возвращает полную нормализованную карточку станка по его ID."""
        if not machine_id:
            return None
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            query = """
                SELECT
                    id, inventory_number, machine_name AS name, machine_name,
                    workshop_id, workshop_name, workshop_description,
                    folder_path AS sub_folder, folder_path, controller, status,
                    commissioning_year AS year_built, commissioning_year,
                    ip_address, mac_address, screen, processor, ram, rom,
                    operating_system, antivirus, created_at
                FROM equipment.v_machines_full
                WHERE id = %s
            """
            try:
                cur.execute(query, (int(machine_id),))
                row = cur.fetchone()
            except Exception:
                conn.rollback()
                fallback_query = """
                    SELECT
                        m.id, m.inventory_number, m.machine_name AS name, m.machine_name,
                        m.workshop_id, w.name AS workshop_name, w.description AS workshop_description,
                        m.folder_path AS sub_folder, m.folder_path, m.controller, m.status,
                        m.commissioning_year AS year_built, m.commissioning_year,
                        cs.ip_address, cs.mac_address, cs.screen, cs.processor, cs.ram, cs.rom,
                        cs.operating_system, cs.antivirus, m.created_at
                    FROM equipment.machines m
                    LEFT JOIN equipment.workshops w ON w.id = m.workshop_id
                    LEFT JOIN equipment.computer_specs cs ON cs.machine_id = m.id
                    WHERE m.id = %s
                """
                cur.execute(fallback_query, (int(machine_id),))
                row = cur.fetchone()

            cur.close()
            conn.close()
            return self._normalize_equipment_row(dict(row)) if row else None
        except Exception as e:
            print(f"DB Error get_machine_by_id: {safe_str_err(e)}")
            return None

    def save_machine_maintenance(self, maint_data):
        """Сохраняет или создает запись в equipment.machine_maintenance."""
        if not self.auth_manager.can_edit():
            return False, "Отказано в доступе: требуются права редактора или администратора.", None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            record_id = maint_data.get('id')
            machine_id = maint_data.get('machine_id')
            work_type = maint_data.get('work_type') or ''
            start_date = maint_data.get('start_date') or None
            end_date = maint_data.get('end_date') or None
            work_performed = maint_data.get('work_performed') or ''
            notes = maint_data.get('notes') or ''

            # If empty date string, convert to None
            if isinstance(start_date, str) and (not start_date.strip() or start_date.strip() == '—'):
                start_date = None
            if isinstance(end_date, str) and (not end_date.strip() or end_date.strip() == '—'):
                end_date = None

            if record_id:
                cur.execute(
                    """
                    UPDATE equipment.machine_maintenance SET
                        work_type = %s,
                        start_date = %s,
                        end_date = %s,
                        work_performed = %s,
                        notes = %s
                    WHERE id = %s
                    RETURNING id;
                    """,
                    (work_type, start_date, end_date, work_performed, notes, int(record_id))
                )
                saved_id = cur.fetchone()[0]
            else:
                if not machine_id:
                    cur.close()
                    conn.close()
                    return False, "Не указан станок (machine_id)", None

                cur.execute(
                    """
                    INSERT INTO equipment.machine_maintenance (
                        machine_id, work_type, start_date, end_date, work_performed, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (int(machine_id), work_type, start_date, end_date, work_performed, notes)
                )
                saved_id = cur.fetchone()[0]

            conn.commit()
            cur.close()
            conn.close()
            return True, "Запись обслуживания успешно сохранена в PostgreSQL!", saved_id
        except Exception as e:
            print(f"DB Error save_machine_maintenance: {safe_str_err(e)}")
            return False, f"Ошибка сохранения записи ТО: {safe_str_err(e)}", None

    def delete_machine_maintenance(self, record_id):
        """Удаляет запись из equipment.machine_maintenance."""
        if not self.auth_manager.can_delete():
            return False, "Отказано в доступе: требуются права на удаление записей."
        if not record_id:
            return False, "Не указан ID записи"
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM equipment.machine_maintenance WHERE id = %s;", (int(record_id),))
            conn.commit()
            cur.close()
            conn.close()
            return True, "Запись успешно удалена из PostgreSQL!"
        except Exception as e:
            print(f"DB Error delete_machine_maintenance: {safe_str_err(e)}")
            return False, f"Ошибка удаления записи ТО: {safe_str_err(e)}"

    def save_equipment(self, eq_data):
        """Сохраняет изменения в machines и computer_specs без блокировки интерфейса."""
        if not self.auth_manager.can_edit():
            return False, "Отказано в доступе: требуются права редактора или администратора."
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            machine_id = eq_data.get('id')

            inventory_value = None
            raw_inventory = eq_data.get('inventory_number')
            if raw_inventory not in (None, ''):
                try:
                    inventory_value = int(raw_inventory)
                except (ValueError, TypeError):
                    inventory_value = None

            machine_name = eq_data.get('name') or eq_data.get('machine_name') or ''
            folder_path = eq_data.get('sub_folder') or eq_data.get('folder_path') or ''
            controller = eq_data.get('cnc_controller') or eq_data.get('controller') or ''
            status = eq_data.get('status') or 'В работе'
            commissioning_year = eq_data.get('year_built') or eq_data.get('commissioning_year')
            workshop_id = eq_data.get('workshop_id')

            if machine_id:
                cur.execute(
                    """
                    UPDATE equipment.machines SET
                        workshop_id = %s,
                        inventory_number = %s,
                        machine_name = %s,
                        folder_path = %s,
                        controller = %s,
                        status = %s,
                        commissioning_year = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (workshop_id, inventory_value, machine_name, folder_path, controller, status, commissioning_year, machine_id)
                )
            else:
                cur.execute(
                    """
                    INSERT INTO equipment.machines (
                        workshop_id, inventory_number, machine_name, folder_path, controller, status, commissioning_year
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (workshop_id, inventory_value, machine_name, folder_path, controller, status, commissioning_year)
                )
                machine_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO equipment.computer_specs (
                    machine_id, mac_address, ip_address, screen, processor, ram, rom, operating_system, antivirus
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (machine_id) DO UPDATE SET
                    mac_address = EXCLUDED.mac_address,
                    ip_address = EXCLUDED.ip_address,
                    screen = EXCLUDED.screen,
                    processor = EXCLUDED.processor,
                    ram = EXCLUDED.ram,
                    rom = EXCLUDED.rom,
                    operating_system = EXCLUDED.operating_system,
                    antivirus = EXCLUDED.antivirus
                """,
                (
                    machine_id,
                    eq_data.get('mac_address') or '',
                    eq_data.get('ip_address') or '',
                    eq_data.get('screen') or '',
                    eq_data.get('processor') or '',
                    eq_data.get('ram') or '',
                    eq_data.get('rom') or '',
                    eq_data.get('operating_system') or '',
                    eq_data.get('antivirus') or ''
                )
            )

            conn.commit()
            cur.close()
            conn.close()
            return True, "Данные сохранены в PostgreSQL!"
        except Exception as e:
            print(f"DB Error save_equipment: {safe_str_err(e)}")
            self.use_demo_mode = False
            self.connection_failed_before = False
            return False, f"Не удалось сохранить данные в PostgreSQL: {safe_str_err(e)}"
