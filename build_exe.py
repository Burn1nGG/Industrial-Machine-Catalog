"""
Build script to compile Industrial Equipment Catalog into a standalone Windows .exe using PyInstaller.
"""
import os
import sys
import subprocess

def build():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_dir, 'main.py')
    
    # Path separators for PyInstaller --add-data (Windows uses ;)
    sep = ';' if sys.platform.startswith('win') else ':'

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=EquipmentCatalog",
        "--onefile",
        "--windowed",
        "--clean",
        f"--add-data={os.path.join(project_dir, 'config.json')}{sep}.",
        f"--add-data={os.path.join(project_dir, 'database')}{sep}database",
        main_script
    ]

    print("Building EquipmentCatalog.exe with PyInstaller...")
    print("Command:", " ".join(cmd))
    
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        exe_path = os.path.join(project_dir, "dist", "EquipmentCatalog.exe")
        print("\n" + "="*60)
        print(f"BUILD SUCCESSFUL!")
        print(f"Executable created at: {exe_path}")
        print("="*60 + "\n")
    else:
        print("\nBUILD FAILED! Check error log above.\n")

if __name__ == '__main__':
    build()
