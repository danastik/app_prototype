import sys

import zipfile

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ZIP Prototype")
        self.resize(500, 120)

        self.label = QLabel("Paste the path to a ZIP file:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(r"C:\example\archive.zip")

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_zip)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.open_button)

    def open_zip(self):
        path = self.path_edit.text().strip()

        if not path:
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please enter a ZIP file path."
            )
            return

        try:
            with zipfile.ZipFile(path, "r") as archive:
                files = archive.namelist()

                png_files = [
                    file for file in files
                    if file.lower().endswith(".png")
                ]

                if not png_files:
                    QMessageBox.information(
                        self,
                        "Result",
                        "No PNG files were found in the archive."
                    )
                    return

                first_png = png_files[0]

                QMessageBox.information(
                    self,
                    "PNG Found",
                    f"First PNG:\n{first_png}"
                )

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
                "The file is not a valid ZIP archive."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())