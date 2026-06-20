from pathlib import Path
from datetime import datetime


class Logger:

    def __init__(self):
        self._messages: list[str] = []

    def info(self, message: str):
        self._add("INFO", message)

    def warning(self, message: str):
        self._add("WARNING", message)

    def error(self, message: str):
        self._add("ERROR", message)

    def _add(
        self,
        level: str,
        message: str
    ):
        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        self._messages.append(
            f"[{timestamp}] [{level}] {message}"
        )

    def get_messages(self) -> list[str]:
        return self._messages.copy()

    def save(
        self,
        output_path: Path
    ):
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path.write_text(
            "\n".join(self._messages),
            encoding="utf-8"
        )

    def clear(self):
        self._messages.clear()

    def has_errors(self) -> bool:
        return any(
            "[ERROR]" in message
            for message in self._messages
        )