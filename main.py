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
    QPlainTextEdit,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ZIP Prototype")
        self.resize(500, 400)

        self.label = QLabel("Paste the path to a ZIP file:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(r"C:\example\archive.zip")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())