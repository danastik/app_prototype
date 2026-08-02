import sys

import json
import os

import zipfile

from PySide6.QtCore import Qt

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QFileDialog,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Yoji")
        self.resize(500, 400)

        self.load_settings()

        self.label = QLabel("Open your yoji file:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.path_edit = QLineEdit()
        placeholder = "Paste file path here!" if not self.settings["last_path"] else self.settings["last_path"]
        self.path_edit.setPlaceholderText(placeholder)

        self.browse_button = QPushButton("Browse:")
        self.browse_button.clicked.connect(self.browse_file)

        self.row = QHBoxLayout()
        self.row.addWidget(self.path_edit)
        self.row.addWidget(self.browse_button)

        self.call_button = QPushButton("Call")
        self.call_button.clicked.connect(self.open_zip)

        self.contents = QPlainTextEdit()
        self.contents.setReadOnly(True)


        self.setStyleSheet("""
            QWidget {
                font-family: "Rubik";
                font-size: 10pt;
                margin: 2px;
            }

            QPushButton {
                padding: 6px;
                border: 1px solid #0078D7;
            }

            QLineEdit {
                padding: 4px;
            }
            """)

        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border-radius: 8px;
            }

            QPushButton:hover {
                background-color: #0078D7;
                color: white;
            }
            """)

        self.call_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                max-with: 200px;
                border-radius: 8px;
                border: 0px;
            }

            QPushButton:hover {
                background-color: #2893FF;
            }

            QPushButton:pressed {
                background-color: #005A9E;
            }
            """)


        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addLayout(self.row)
        layout.addWidget(self.call_button)
        layout.addWidget(self.contents)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open ZIP Archive",
            "",
            "ZIP Files (*.zip);;All Files (*)"
        )

        if file_name:
            self.path_edit.setText(file_name)

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
    app.setWindowIcon(QIcon("icon.ico"))

    window = MainWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())