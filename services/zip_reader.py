# services/zip_reader.py

import zipfile
import tempfile
from pathlib import Path


class ZipReader:
    def __init__(self, zip_path: Path):
        self.zip_path = Path(zip_path)
        self.temp_dir = None

    def extract(self) -> Path:
        """
        ZIPを一時ディレクトリへ展開する
        """
        self.temp_dir = tempfile.TemporaryDirectory()

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            zf.extractall(self.temp_dir.name)

        return Path(self.temp_dir.name)

    def get_all_files(self) -> list[Path]:
        """
        展開後の全ファイルを取得する
        """
        if self.temp_dir is None:
            raise RuntimeError("extract() を先に呼んでください")

        root = Path(self.temp_dir.name)

        return [
            p
            for p in root.rglob("*")
            if p.is_file()
        ]

    def cleanup(self):
        """
        一時ディレクトリ削除
        """
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None