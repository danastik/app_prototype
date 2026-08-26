import win32gui
import win32con
from PySide6.QtCore import QTimer

HOTKEY_ID = 1

class HotkeyManager:
    def __init__(self, pet):
        self.pet = pet

        try:
            success = win32gui.RegisterHotKey(
                0,
                HOTKEY_ID,
                win32con.MOD_CONTROL | win32con.MOD_SHIFT,
                win32con.VK_F9
            )

            print("registered:", success)
        except Exception as e:
            print("Failed to register Ctrl+Shift+F9")            
            print("Error: ", e)            

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_hotkey)
        self.timer.start(500)

    def check_hotkey(self):
        while True:
            msg = win32gui.PeekMessage(
                0,
                0,
                0,
                win32con.PM_REMOVE
            )

            if not msg:
                break

            # print("hotkey id", msg[1][1], win32con.WM_HOTKEY)

            if msg[1][1] == win32con.WM_HOTKEY:
                self.handle()

    def handle(self):
        print("HOTKEY FIRED")

    def cleanup(self):
        win32gui.UnregisterHotKey(None, HOTKEY_ID)
        self.timer.stop()