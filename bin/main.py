import sys
import json
import os
from pathlib import Path

import zipfile

from pet import Pet

from engine.particles.atlas_generator import AtlasGenerator
from engine.debug import Debug
from app.registrator import register_yoji_file_type

from PySide6.QtCore import Qt, QTimer

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

root = Path(__file__).resolve().parents[1]

app_path = Path(__file__).resolve()

icon_path = root / "resources" / "icons" / "icon.ico"
logo_path = root / "resources" / "icons" / "icon.png"
font_path = root / "resources" / "fonts"
settings_path = root / "settings.json"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        Debug.log("\n---APP LAUNCHED---")

        self.setWindowTitle("Yoji")
        self.resize(500, 400)

        if len(sys.argv) > 1:
            try:
                input_file_path = str(Path(sys.argv[1]))
                self.load_zip(input_file_path)
            except Exception as e:
                Debug.warning(f"Could not open a .yoji file.\n{e}")
                QMessageBox.warning(
                    self,
                    "Could not open a .yoji file",
                    f"{e}"
                )

        self.load_settings()


        # registering .yoji file format
        try:
            register_yoji_file_type(exe_path=app_path, icon_path=icon_path)
        except Exception as e:
            Debug.warning(f"Could not register .yoji file.\n{e}")

        # --- loading fonts ---
        try:
            QFontDatabase.addApplicationFont(str(font_path / "Rubik-Regular.ttf"))
            QFontDatabase.addApplicationFont(str(font_path / "Rubik-Italic.ttf"))
            QFontDatabase.addApplicationFont(str(font_path / "Rubik-Bold.ttf"))
            QFontDatabase.addApplicationFont(str(font_path / "Rubik-BoldItalic.ttf"))

            font = QFont("Rubik", 12)
            app.setFont(font)
        except Exception:
            Debug.error(f"Could not find font 'Rubik' in {font_path}")
            font = QFont("Arial", 12)
            app.setFont(font)

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
        self.info_icon.setPixmap(QPixmap(str(logo_path)))
        info_layout.addWidget(self.info_icon)

        info_layout.addSpacing(10)

        grid = QVBoxLayout()

        self.info_name = QLabel("Name")
        self.info_name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(self.info_name)

        self.info_author = QLabel("author")
        self.info_author.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(self.info_author)

        self.info_description = QLabel("description")
        self.info_description.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_description.setWordWrap(True)
        grid.addWidget(self.info_description)

        self.info_tags = QLabel("#yoji #pet #forever")
        self.info_tags.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(self.info_tags)

        grid.addStretch()

        self.info_widget.hide()

        self.call_button = QPushButton("Call")
        self.call_button.clicked.connect(self.call_pet)

        grid.addWidget(self.call_button, alignment=Qt.AlignmentFlag.AlignRight)

        info_layout.addLayout(grid)


        self.contents = QPlainTextEdit()
        self.contents.setReadOnly(True)


        # --- stylesheets ---

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

        self.info_widget.setStyleSheet("""
            QWidget {
                margin-left: 1px;
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

        # --- main layout  ---

        layout = QVBoxLayout(self)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.browse_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addStretch()

        self.pet_active = False
        self.files = []
        self.manifest = None
        self.call_in_progress = False

        if self.settings["last_path"]:
            try:
                self.load_zip(self.settings["last_path"])
            except Exception: pass

        Debug.log("---APP LOADED SUCCESSFULLY---\n")
        # self.hotkeys = HotkeyManager(self) # not doing anything for now, meh


    def load_zip(self, path):
        if not path:
            Debug.warning(f"Missing Path - archive file path was not valid")
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please enter a valid archive file path."
            )
            return
        
        self.archive = zipfile.ZipFile(path, "r")
        self.archive_path = path

        if not self.archive:
            Debug.warning(f"Could not open {path} as archive.")
            QMessageBox.warning(
                self,
                "Cannot open file",
                f"Cannot open {path} as archive."
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
            self.info_author.setText(f"v{self.manifest.get("version", 1)} by {self.manifest.get("author", "unknown")}")
            self.info_description.setText(str(self.manifest.get("description", "")))
            tag_list = self.manifest.get("tags", ["#untagged"])
            tags = " ".join(f"#{tag}" for tag in tag_list)
            self.info_tags.setText(tags)

            print("manifest opened successfully")

            thumbnail = self.manifest.get("thumbnail", "icon.png")

            try:
                with archive.open(thumbnail) as f:
                    image_data = f.read()
                    print("loading image")
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                self.info_icon.setPixmap(
                    pixmap.scaled(
                        self.info_icon.size(),
                        Qt.KeepAspectRatio, #type: ignore
                        Qt.SmoothTransformation #type: ignore
                    )
                )
            except Exception: 
                print("Thumbnail not found.")
                image_files = [
                    name for name in archive.namelist()
                    if name.lower().endswith((".png", ".webp"))
                ]
                suggested = image_files[0]
                text = f"Probably meant {suggested}" if suggested else ""
                Debug.warning(f"Missing thumbnail - You have specified thumbnail as {thumbnail}, but it is not present in archive.\n{text}")
                QMessageBox.warning(
                    self,
                    "Missing thumbnail",
                    f"You have specified thumbnail as {thumbnail},\nbut it is not present in archive.\n" +
                    text
                )

            self.info_widget.show()

        except Exception:
            self.manifest = None
            print("Manifest not found.")
            Debug.warning(f"Missing manifest - Selected archive is missing a yoji manifest.")
            QMessageBox.warning(
                self,
                "Missing manifest",
                "Selected archive is missing a yoji manifest."
            )
            return

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open your Yoji",
            "",
            "Yoji/ZIP Files (*.yoji *.zip);;All Files (*)"
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
            Debug.error(f"The specified file does not exist.")
            QMessageBox.critical(
                self,
                "Error",
                "The specified file does not exist."
            )

        except zipfile.BadZipFile:
            Debug.error(f"Selected file is not a valid ZIP archive.")
            QMessageBox.critical(
                self,
                "Error",
                "Selected file is not a valid ZIP archive."
            )

        except Exception as e:
            Debug.error(f"Unexpected Error:\n{e}")
            QMessageBox.critical(
                self,
                "Unexpected Error",
                str(e)
            )

    def load_settings(self):
        self.settings_file = settings_path
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

        self.resize(self.settings["size_w"], self.settings["size_h"])

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)
    
    def check_particle_atlas(self, PARTICLE_ASSETS) -> bool:
        atlas_generator = AtlasGenerator(PARTICLE_ASSETS, self.archive)

        if not atlas_generator.atlas_exists():
            reply = QMessageBox.question(
                self,
                "Atlas missing",
                "Atlas files are missing from generated/atlas. Would you like to generate them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # regenerate/rebuild here
                print("Regenerate atlas - yes")
                print("closing old archive")
                self.archive.close()
                print("regenerating archive")
                Debug.log("Regenerating atlas: start")
                atlas_generator.generate_atlas(self.archive_path)
                print("loading zip")
                Debug.log("--Loading ZIP archive")
                self.load_zip(self.archive_path)
                return True

            else: print("Regenerate atlas - no")
            return False
        
        print("Atlas found: success")
        Debug.log("Atlas found: success")
        return True

    def call_pet(self):
        print("windows id", window.winId())

        if self.call_in_progress: return

        if self.pet_active and self.pet is not None:
            print("recalling pet")
            Debug.log("---Recalling pet---\n")
            self.pet.close()
            self.pet.deleteLater()
            self.pet = None
            self.call_button.setEnabled(True)
            self.pet_active = False
            self.call_button.setText("Call")
            return

        self.call_in_progress = True
        self.call_button.setText("Calling...")
        self.call_button.setEnabled(False)
        QApplication.processEvents()
        print(f"--Trying to call {self.archive_path}")
        Debug.log(f"--Trying to call {self.archive_path}")
   
        try:
            PARTICLE_ASSETS = json.load(self.archive.open("data/particles/assets.json"))
            if not self.check_particle_atlas(PARTICLE_ASSETS):  return
        
            print("--Calling pet.py")
            Debug.log("--Calling pet.py")
            self.pet = Pet(self.archive, main_hwnd=int(window.winId()))
            self.pet.show()

        except Exception as e:
            Debug.error(f"Could not call yoji.\n{e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not call yoji.\n{e}"
            )
        finally:
            print("finally")
            QTimer.singleShot(500, self.finish_call)

    def finish_call(self):
        self.pet_active = True
        self.call_button.setText("Recall")
        self.call_button.setEnabled(True)
        self.call_in_progress = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())