import sys
import winreg
from pathlib import Path

def register_yoji_file_type(exe_path, icon_path):
    if sys.platform != "win32":
        return

    # exe_path = Path(sys.executable).resolve()
    # icon_path = exe_path.parent.parent / "resources" / "icons" / "icon.ico"

    file_extension = ".yoji"
    file_type = "YojiFile"

    # .yoji -> YojiFile
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{file_extension}") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, file_type)

    # YojiFile -> application details
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{file_type}") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Yoji File (.yoji)")

    # Icon
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        rf"Software\Classes\{file_type}\DefaultIcon"
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(icon_path))

    # Double-click -> launch application with the .yoji path
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        rf"Software\Classes\{file_type}\shell\open\command"
    ) as key:
        winreg.SetValueEx(
            key,
            "",
            0,
            winreg.REG_SZ,
            f'"{exe_path}" "%1"'
        )