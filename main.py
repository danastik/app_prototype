import sys

import json
import os

import zipfile

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QPlainTextEdit,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ZIP Prototype")
        self.resize(500, 400)

        self.load_settings()

        self.label = QLabel("Paste the path to a ZIP file:")
        self.path_edit = QLineEdit()
        placeholder = r"C:\example\archive.zip" if not self.settings["last_path"] else self.settings["last_path"]
        self.path_edit.setPlaceholderText(placeholder)

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_zip)

        self.contents = QPlainTextEdit()
        self.contents.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.open_button)
        layout.addWidget(self.contents)

    def open_zip(self):
        path = self.path_edit.text().strip()

        if not path and self.settings["last_path"]:
            path = self.settings["last_path"]

        if not path:
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please enter a ZIP file path."
            )
            return

        try:
            with zipfile.ZipFile(path, "r") as archive:
                files = []
                for info in archive.infolist():
                    # print(repr(info.filename.encode("cp437")))
                    try:
                        name = info.filename.encode("cp437").decode("cp866")
                    except UnicodeError:
                        name = info.filename

                    files.append(name)

                self.contents.clear()

                if not files:
                    self.contents.appendPlainText("The archive is empty.")
                    return

                self.contents.appendPlainText("Archive contents:\n")

                for file in files:
                    self.contents.appendPlainText(file)

        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Error",
                "The specified file does not exist."
            )

        except zipfile.BadZipFile:
            QMessageBox.critical(
                self,
                "Error",
                "The selected file is not a valid ZIP archive."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                str(e)
            )

        self.settings["last_path"] = path
        self.save_settings()

    def load_settings(self):
        self.settings_file = "settings.json"

        default_settings = {
            "last_path": "",
            "theme": "light",
            "size_w": 500,
            "size_h": 400,
        }

        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)

        with open(self.settings_file, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())