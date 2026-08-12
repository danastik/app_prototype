from datetime import datetime
from pathlib import Path

class Debug:
    base = Path(__file__).resolve().parents[1]
    LOG_FOLDER = base / "logs"

    @staticmethod
    def log(message):
        Debug.LOG_FOLDER.mkdir(exist_ok=True)

        date = datetime.now().strftime("%Y-%m-%d")
        log_file = Debug.LOG_FOLDER / f"{date}.txt"

        timestamp = datetime.now().strftime("%H:%M:%S")

        with open(log_file, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {message}\n")

    @staticmethod
    def error(message):
        Debug.log(f"ERROR: {message}")

    @staticmethod
    def warning(message):
        Debug.log(f"WARNING: {message}")