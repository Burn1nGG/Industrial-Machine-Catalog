"""
Folder Router module for Industrial Equipment Catalog.
Optimized for instant network folder navigation and machine card loading.
Constructs direct UNC paths: \\\\Synology_DS423\\Share_folder\\ + DB folder_path
without blocking network scans or UI freezes.
"""
import os
import subprocess
import platform


class FolderRouter:
    def __init__(self, storage_config=None):
        if storage_config is None:
            storage_config = {
                "unc_path": "\\\\Synology_DS423\\Share_folder",
                "unc_path_alt": "\\\\100.76.39.21\\Share_folder",
                "unc_path_ip": "\\\\192.168.1.68\\Share_folder",
                "network_drive_path": "S:\\New Archive",
                "fallback_local_path": "",
                "path_mode": 1,
            }
        self.config = storage_config
        self._cached_base_path = None
        self._cached_desc = None

    def _normalize_folder_path_value(self, *values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, (int, float)):
                value = str(value)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value
        return ""

    def _build_full_folder_path(self, base_path, relative_path):
        base_path = self._normalize_folder_path_value(base_path)
        relative_path = self._normalize_folder_path_value(relative_path)
        if not base_path:
            return relative_path
        if not relative_path:
            return base_path

        # Если путь уже абсолютный или сетевой UNC
        if relative_path.startswith('\\\\') or relative_path.startswith('//') or os.path.isabs(relative_path):
            return os.path.normpath(relative_path)

        norm_base = os.path.normpath(base_path)
        norm_rel = os.path.normpath(relative_path).lstrip('\\/')

        # Устранение дублирования, если базовый путь оканчивается на ту же папку, с которой начинается относительный
        # Например: base = S:\New Archive, rel = New Archive\Цех 02\...
        base_parts = [p for p in norm_base.split(os.sep) if p]
        rel_parts = [p for p in norm_rel.split(os.sep) if p]
        if base_parts and rel_parts and base_parts[-1].lower() == rel_parts[0].lower():
            return os.path.normpath(os.path.join(norm_base, *rel_parts[1:]))

        return os.path.normpath(os.path.join(norm_base, norm_rel))

    def get_base_archive_path(self, force_recheck=False):
        r"""
        Возвращает базовый сетевой путь к хранилищу:
        1. Режим 1: локальная сеть (\\Synology_DS423\Share_folder)
        2. Режим 2: удалённый доступ / VPN (\\100.76.39.21\Share_folder или диск S:)
        Возвращает путь мгновенно без блокирующих сетевых проверок и зависаний.
        """
        if not force_recheck and self._cached_base_path is not None:
            return self._cached_base_path, self._cached_desc

        unc_path = self.config.get("unc_path", "\\\\Synology_DS423\\Share_folder")
        unc_path_alt = self.config.get("unc_path_alt", "\\\\100.76.39.21\\Share_folder")
        drive_path = self.config.get("network_drive_path", "S:\\New Archive")
        path_mode = int(self.config.get("path_mode", 1))

        if path_mode == 2:
            base = unc_path_alt or drive_path or unc_path
            desc = f"Удалённый архив ({base})"
        else:
            base = unc_path or unc_path_alt or drive_path
            desc = f"Synology DS423 ({base})"

        self._cached_base_path = os.path.normpath(base)
        self._cached_desc = desc
        return self._cached_base_path, self._cached_desc

    def resolve_equipment_folder(self, equipment_dict, check_exists=True):
        r"""
        Мгновенно формирует путь к папке станка без алгоритмического поиска и сканирования.
        Сетевой путь (\\Synology_DS423\Share_folder\) + folder_path из БД.
        """
        base_path, _ = self.get_base_archive_path()
        sub_folder = self._normalize_folder_path_value(
            equipment_dict.get('folder_path'),
            equipment_dict.get('sub_folder')
        )

        if sub_folder:
            full_path = self._build_full_folder_path(base_path, sub_folder)
            if check_exists:
                try:
                    if os.path.exists(full_path):
                        return True, full_path, "Папка найдена по пути из базы данных"
                except Exception:
                    pass
                return False, full_path, f"Папка оборудования еще не создана по пути: {full_path}"
            return True, full_path, "Папка найдена по пути из базы данных"

        # Если в БД путь не заполнен (редкий случай)
        inv_num = self._normalize_folder_path_value(equipment_dict.get('inventory_number'))
        eq_name = self._normalize_folder_path_value(equipment_dict.get('name'))
        ws_name = self._normalize_folder_path_value(equipment_dict.get('workshop_name'))
        default_folder_name = f"{inv_num}_{eq_name}".strip('_')
        expected_path = os.path.normpath(os.path.join(base_path, "New Archive", ws_name, default_folder_name))

        if check_exists:
            try:
                if os.path.exists(expected_path):
                    return True, expected_path, "Папка найдена"
            except Exception:
                pass
        return False, expected_path, f"Папка оборудования еще не создана по пути: {expected_path}"

    def open_folder_in_explorer(self, folder_path, create_if_missing=False):
        """
        Открывает указанную сетевую папку в Windows Explorer мгновенно и без зависаний GUI.
        Запускает explorer.exe асинхронно отдельным процессом.
        """
        if not folder_path:
            return False, "Путь к папке не указан."

        norm_path = os.path.normpath(folder_path)

        if create_if_missing:
            try:
                os.makedirs(norm_path, exist_ok=True)
            except Exception as e:
                return False, f"Не удалось создать директорию:\n{e}"

        try:
            if platform.system() == "Windows":
                # subprocess.Popen не блокирует выполнение программы и не ждёт ответа сети
                subprocess.Popen(['explorer.exe', norm_path])
                return True, f"Папка открыта в Explorer:\n{norm_path}"
            else:
                subprocess.Popen(['xdg-open', norm_path])
                return True, f"Папка открыта:\n{norm_path}"
        except Exception:
            try:
                os.startfile(norm_path)
                return True, f"Папка открыта:\n{norm_path}"
            except Exception as ex:
                return False, f"Не удалось открыть папку:\n{ex}"

    def resolve_equipment_photo(self, equipment_dict):
        """
        Ищет фотографию станка (main.jpg) в подпапке 'Фото' оборудования.
        Выполняется в фоновом потоке PhotoLoaderThread, не блокируя работу интерфейса.
        """
        base_path, _ = self.get_base_archive_path()
        sub_folder = self._normalize_folder_path_value(
            equipment_dict.get('folder_path'),
            equipment_dict.get('sub_folder')
        )
        if not sub_folder:
            return False, None, None, "Папка оборудования не определена"

        norm_folder = self._build_full_folder_path(base_path, sub_folder)
        default_photo_folder = os.path.join(norm_folder, "Фото")
        default_photo_path = os.path.join(default_photo_folder, "main.jpg")

        # 1. Быстрая прямая проверка: стандартный файл Фото/main.jpg
        try:
            if os.path.isfile(default_photo_path):
                return True, default_photo_path, default_photo_folder, "Фотография найдена"
        except Exception:
            pass

        # 2. Быстрая прямая проверка расширений без сканирования папок
        for ext in (".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
            candidate = os.path.join(default_photo_folder, f"main{ext}")
            try:
                if os.path.isfile(candidate):
                    return True, candidate, default_photo_folder, "Фотография найдена"
            except Exception:
                pass

        # 3. Проверка латинской подпапки 'photo'
        try:
            alt_photo_folder = os.path.join(norm_folder, "photo")
            for ext in (".jpg", ".jpeg", ".png", ".JPG"):
                candidate = os.path.join(alt_photo_folder, f"main{ext}")
                if os.path.isfile(candidate):
                    return True, candidate, alt_photo_folder, "Фотография найдена"
        except Exception:
            pass

        # 4. Проверка main.jpg в корне папки станка (если нет подпапки Фото)
        try:
            root_main = os.path.join(norm_folder, "main.jpg")
            if os.path.isfile(root_main):
                return True, root_main, norm_folder, "Фотография найдена"
        except Exception:
            pass

        return False, default_photo_path, default_photo_folder, "Файл main.jpg не найден"
