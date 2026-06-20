from enum import Enum
from pathlib import Path

from PIL import Image


class FileType(Enum):
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class FileDetector:

    @staticmethod
    def detect(path: Path) -> FileType:

        if FileDetector.is_pdf(path):
            return FileType.PDF

        if FileDetector.is_image(path):
            return FileType.IMAGE

        return FileType.UNKNOWN

    @staticmethod
    def is_pdf(path: Path) -> bool:

        try:
            with open(path, "rb") as f:
                return f.read(4) == b"%PDF"

        except Exception:
            return False

    @staticmethod
    def is_image(path: Path) -> bool:

        try:
            with Image.open(path) as img:
                img.verify()

            return True

        except Exception:
            return False