import logging
import os
from datetime import datetime
from pathlib import Path

BASE_LOG_FOLDER = Path(os.environ["LOCALAPPDATA"]) / "Yoji" / "logs"

APP_LOG_FOLDER = "app"
PET_DEBUG_LOG_FOLDER = "pet_debug"


class AppLogger:
    def __init__(self):
        self.log_folder = (BASE_LOG_FOLDER / APP_LOG_FOLDER)

        self.logger = logging.getLogger("app")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        self._setup()

    def _setup(self):
        self.log_folder.mkdir(parents=True, exist_ok=True)

        date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_folder / f"{date}.log"

        handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )

        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s][%(levelname)s]: %(message)s",
                datefmt="%H:%M:%S"
            )
        )

        self.logger.addHandler(handler)

    def debug(self, message, *args):
        self.logger.debug(message, *args)

    def info(self, message, *args):
        self.logger.info(message, *args)

    def warning(self, message, *args):
        self.logger.warning(message, *args)

    def error(self, message, *args):
        self.logger.error(message, *args)

    def exception(self, message, *args):
        self.logger.exception(message, *args)


class DebugLogger:
    def __init__(self):
        self.log_folder = (BASE_LOG_FOLDER / PET_DEBUG_LOG_FOLDER)

        self.logger = logging.getLogger("debug")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        self.enabled = False

        # self._setup()

    def _setup(self, name: str):
        self.log_folder.mkdir(parents=True, exist_ok=True)

        date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_folder / f"{name} {date}.log"

        handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s][%(levelname)s]: %(message)s",
                datefmt="%H:%M:%S"
            )
        )

        self.logger.addHandler(handler)

        # Disabled by default
        self.logger.disabled = True

    def start_logging(self, name: str):
        self._setup(name=name)
        self.enabled = True
        self.logger.disabled = False

    def stop_logging(self):
        self.enabled = False
        self.logger.disabled = True

    # def set_enabled(self, enabled: bool):
    #     self.enabled = enabled
    #     self.logger.disabled = not enabled

    def debug(self, message, *args):
        self.logger.debug(message, *args)

    def info(self, message, *args):
        self.logger.info(message, *args)

    def warning(self, message, *args):
        self.logger.warning(message, *args)

    def error(self, message, *args):
        self.logger.error(message, *args)

    def exception(self, message, *args):
        self.logger.exception(message, *args)


app_logger = AppLogger()
debug_logger = DebugLogger()