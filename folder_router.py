"""
Folder Router module for Industrial Equipment Catalog.
Resolves equipment folders on network drive S:\\New Archive or UNC path \\\\100.76.39.21\\Share_folder\\New Archive
and opens Windows Explorer at the exact machine directory.
"""
import os
import subprocess
import platform

class FolderRouter:
    def __init__(self, storage_config=None):
        if storage_config is None:
            storage_config = {
                "network_drive_path": "S:\\New Archive",
                "unc_path": "\\\\100.76.39.21\\Share_folder",
                "unc_path_alt": "\\\\192.168.1.68\\Share_folder",
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
        if relative_path.startswith("\\") or relative_path.startswith("/"):
            return os.path.normpath(os.path.join(base_path, relative_path.lstrip('\\/')))
        return os.path.normpath(os.path.join(base_path, relative_path))

    def get_base_archive_path(self, force_recheck=False):
        """Проверяет доступность сетевого диска S: или UNC пути с кэшированием результатов."""
        if not force_recheck and self._cached_base_path is not None:
            return self._cached_base_path, self._cached_desc

        drive_path = self.config.get("network_drive_path", "S:\\New Archive")
        unc_path = self.config.get("unc_path", "\\\\100.76.39.21\\Share_folder")
        unc_path_alt = self.config.get("unc_path_alt", "\\\\192.168.1.68\\Share_folder")
        fallback_path = self.config.get("fallback_local_path", "")
        path_mode = int(self.config.get("path_mode", 1))

        preferred_unc = unc_path if path_mode == 1 else unc_path_alt

        # 1. Быстрая проверка диска S:
        try:
            if os.path.exists(drive_path):
                self._cached_base_path = drive_path
                self._cached_desc = "Сетевой диск S: (удалённое подключение)"
                return drive_path, "Сетевой диск S: (удалённое подключение)"
        except Exception:
            pass

        try:
            if preferred_unc and os.path.exists(preferred_unc):
                self._cached_base_path = preferred_unc
                self._cached_desc = f"UNC Сетевая папка {preferred_unc}"
                return preferred_unc, f"UNC Сетевая папка {preferred_unc}"
        except Exception:
            pass

        try:
            if unc_path and os.path.exists(unc_path):
                self._cached_base_path = unc_path
                self._cached_desc = f"UNC Сетевая папка {unc_path}"
                return unc_path, f"UNC Сетевая папка {unc_path}"
        except Exception:
            pass

        try:
            if unc_path_alt and os.path.exists(unc_path_alt):
                self._cached_base_path = unc_path_alt
                self._cached_desc = f"UNC Сетевая папка {unc_path_alt}"
                return unc_path_alt, f"UNC Сетевая папка {unc_path_alt}"
        except Exception:
            pass

        # 3. Проверка локального резервного пути
        try:
            if fallback_path and os.path.exists(fallback_path):
                self._cached_base_path = fallback_path
                self._cached_desc = "Локальный архив"
                return fallback_path, "Локальный архив"
        except Exception:
            pass

        # 4. Если ничего недоступно, возвращаем предпочтительный путь для сообщений
        self._cached_base_path = drive_path
        self._cached_desc = "Сетевой архив недоступен"
        return drive_path, "Сетевой архив недоступен"

    def resolve_equipment_folder(self, equipment_dict):
        """
        Ищет папку станка по структуре:
        BaseArchive / WorkshopFolder / [EquipmentFolder]
        """
        base_path, status_desc = self.get_base_archive_path()
        inv_num = self._normalize_folder_path_value(equipment_dict.get('inventory_number'))
        eq_name = self._normalize_folder_path_value(equipment_dict.get('name'))
        sub_folder = self._normalize_folder_path_value(
            equipment_dict.get('sub_folder'),
            equipment_dict.get('folder_path')
        )
        workshop_name = self._normalize_folder_path_value(equipment_dict.get('workshop_name'))
        workshop_code = self._normalize_folder_path_value(equipment_dict.get('workshop_code'))

        if not base_path or not os.path.exists(base_path):
            return False, base_path, f"Базовый каталог архива недоступен ({base_path})."

        base_path = os.path.normpath(base_path)

        if sub_folder:
            candidate_paths = []
            if os.path.isabs(sub_folder) or sub_folder.startswith('\\\\') or sub_folder.startswith('//'):
                candidate_paths.append(os.path.normpath(sub_folder))
            else:
                candidate_paths.append(self._build_full_folder_path(base_path, sub_folder))
                candidate_paths.append(sub_folder)

            for candidate in candidate_paths:
                try:
                    if candidate and os.path.exists(candidate):
                        return True, candidate, "Папка найдена по пути из базы"
                except Exception:
                    continue

        # Шаг 1: Ищем папку цеха на первом уровне
        workshop_dir = None
        try:
            for item in os.listdir(base_path):
                full_item = os.path.join(base_path, item)
                if os.path.isdir(full_item):
                    if (workshop_name and workshop_name.lower() in item.lower()) or \
                       (workshop_code and workshop_code.lower() in item.lower()) or \
                       (workshop_name and item.lower() in workshop_name.lower()):
                        workshop_dir = full_item
                        break
        except Exception as e:
            print(f"Error reading base archive directory: {e}")

        search_root = workshop_dir if workshop_dir else base_path

        if sub_folder:
            relative_candidate = os.path.normpath(os.path.join(search_root, sub_folder))
            try:
                if os.path.exists(relative_candidate):
                    return True, relative_candidate, "Папка найдена по пути из базы"
            except Exception:
                pass

        try:
            for root, dirs, files in os.walk(search_root, topdown=True):
                rel_depth = len(os.path.relpath(root, search_root).split(os.sep))
                if rel_depth > 2:
                    dirs.clear()
                    continue

                for d in dirs:
                    d_lower = d.lower()
                    if inv_num and inv_num.lower() in d_lower:
                        return True, os.path.join(root, d), "Папка найдена по инвентарному номеру"

                    if eq_name and eq_name.lower() in d_lower:
                        return True, os.path.join(root, d), "Папка найдена по названию станка"
        except Exception as e:
            print(f"Error walking directory {search_root}: {e}")

        if workshop_dir and os.path.exists(workshop_dir):
            return False, workshop_dir, f"Папка станка '{inv_num}' не найдена. Открыта общая папка цеха."

        default_folder_name = f"{inv_num}_{eq_name}".replace(' ', '_')
        expected_path = os.path.join(search_root, default_folder_name)
        return False, expected_path, f"Папка оборудования еще не создана по пути: {expected_path}"

    def open_folder_in_explorer(self, folder_path, create_if_missing=False):
        """Открывает указанную папку в Windows Explorer."""
        try:
            if not os.path.exists(folder_path):
                if create_if_missing:
                    os.makedirs(folder_path, exist_ok=True)
                else:
                    return False, f"Директория не существует:\n{folder_path}"

            if platform.system() == "Windows":
                os.startfile(os.path.normpath(folder_path))
                return True, f"Папка открыта в Explorer:\n{folder_path}"
            else:
                subprocess.Popen(['explorer', os.path.normpath(folder_path)])
                return True, f"Запущена команда открытия:\n{folder_path}"
        except Exception as e:
            return False, f"Не удалось открыть папку в Explorer:\n{e}"
