import sys

import json
import os

import zipfile

from PySide6.QtCore import Qt

from PySide6.QtGui import QIcon, QPixmap, QFontDatabase, QFont

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
    QGridLayout,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Yoji")
        self.resize(500, 400)

        self.load_settings()

        # --- loading fonts ---

        QFontDatabase.addApplicationFont("fonts/Rubik-Regular.ttf")
        QFontDatabase.addApplicationFont("fonts/Rubik-Italic.ttf")
        QFontDatabase.addApplicationFont("fonts/Rubik-Bold.ttf")
        QFontDatabase.addApplicationFont("fonts/Rubik-BoldItalic.ttf")

        self.font_regular = QFont("Rubik", 10)

        self.font_bold = QFont("Rubik", 10)
        self.font_bold.setBold(True)

        self.font_italic = QFont("Rubik", 10)
        self.font_italic.setItalic(True)

        self.font_bold_italic = QFont("Rubik", 10)
        self.font_bold_italic.setBold(True)
        self.font_bold_italic.setItalic(True)

        # --- widgets ---

        self.label = QLabel("Open your yoji file:")

        self.path_edit = QLineEdit()
        placeholder = "Paste file path here!" if not self.settings["last_path"] else self.settings["last_path"]
        self.path_edit.setPlaceholderText(placeholder)

        self.browse_button = QPushButton("Browse:")
        self.browse_button.clicked.connect(self.browse_file)

        self.browse_widget = QWidget()
        self.browse_layout = QHBoxLayout(self.browse_widget)
        self.browse_layout.addWidget(self.path_edit)
        self.browse_layout.addWidget(self.browse_button)

        # info box
        self.info_widget = QWidget()
        info_layout = QHBoxLayout(self.info_widget)

        self.info_icon = QLabel()
        self.info_icon.setPixmap(QPixmap("icon.png"))
        info_layout.addWidget(self.info_icon)

        info_layout.addSpacing(10)

        grid = QVBoxLayout()

        self.info_name = QLabel("Name")
        grid.addWidget(self.info_name)

        self.info_author = QLabel("author")
        grid.addWidget(self.info_author)

        self.info_description = QLabel("description description description description description description description description descriptiondescription description description")
        self.info_description.setWordWrap(True)
        grid.addWidget(self.info_description)

        self.info_tags = QLabel("nice cool round")
        grid.addWidget(self.info_tags)

        grid.addStretch()

        self.info_widget.hide()

        self.call_button = QPushButton("Call")
        self.call_button.clicked.connect(self.open_zip)

        grid.addWidget(self.call_button, alignment=Qt.AlignmentFlag.AlignRight)

        info_layout.addLayout(grid)


        self.contents = QPlainTextEdit()
        self.contents.setReadOnly(True)

        self.setStyleSheet("""
            QWidget {
                font-family: "Rubik";
                font-size: 10pt;
                margin: 0px;
            }

            QPushButton {
                padding: 6px;
                border: 1px solid #0078D7;
            }

            QLineEdit {
                padding: 4px;
            }
            """)

        self.info_icon.setStyleSheet("""
            QLabel {
                max-width: 230px;
                max-height: 230px;
            }
            """)
        
        self.info_name.setStyleSheet("""
            QLabel {
                font-family: "Rubik";
                font-weight: bold;
                font-size: 20px;
            }
            """)

        self.info_author.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #595959;
                margin-top: 0px;
            }
            """)
        
        self.info_description.setStyleSheet("""
            QLabel {
                margin-top: 10px;
            }
            """)
        
        self.info_tags.setStyleSheet("""
            QLabel {
                font-size: 12px;
                margin-top: 10px;
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
                font-family: "Rubik";
                font-weight: bold;
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                border: 0px;
                width: 80px;
                max-width: 150px;
            }

            QPushButton:hover {
                background-color: #2893FF;
            }

            QPushButton:pressed {
                background-color: #005A9E;
            }
            """)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.browse_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addStretch()
        # layout.addWidget(self.call_button)
        # layout.addWidget(self.contents)

        self.files = []
        self.manifest = None

        if self.settings["last_path"]:
            try:
                self.load_zip(self.settings["last_path"])
            except Exception: pass


    def load_zip(self, path):
        if not path:
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please enter a ZIP file path."
            )
            return
        
        self.archive = zipfile.ZipFile(path, "r")

        if not self.archive:
            QMessageBox.warning(
                self,
                "Cannot open ZIP",
                "Cannot open ZIP file as archive."
            )
            return

        self.read_manifest()

        self.settings["last_path"] = path
        self.save_settings()

    def read_manifest(self):
        archive = self.archive
        try:
            with archive.open("manifest.json") as f:
                self.manifest = json.load(f)


            print(self.manifest)
            self.info_name.setText(str(self.manifest.get("name", "Unnamed")))
            self.info_author.setText(f"by {self.manifest.get("author", "unknown")}")
            self.info_description.setText(str(self.manifest.get("description", "")))
            tag_list = self.manifest.get("tags", ["#untagged"])
            tags = " ".join(f"#{tag}" for tag in tag_list)
            self.info_tags.setText(tags)

            thumbnail = self.manifest.get("thumbnail", "icon.png")
            with archive.open(thumbnail) as f:
                image_data = f.read()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.info_icon.setPixmap(
                pixmap.scaled(
                    self.info_icon.size(),
                    Qt.KeepAspectRatio, #type: ignore
                    Qt.SmoothTransformation #type: ignore
                )
            )

            self.info_widget.show()

        except Exception:
            self.manifest = None
            print("Manifest not found.")
            QMessageBox.warning(
                self,
                "Missing manifest",
                "Selected ZIP archive is missing a yoji manifest."
            )
            return

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open ZIP Archive",
            "",
            "ZIP Files (*.zip);;All Files (*)"
        )

        if file_name:
            self.path_edit.setText(file_name)
            print("File selected")
            self.load_zip(file_name)


    def open_zip(self):
        archive = self.archive

        try:
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
                self.files.append(file)

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