# services/image_to_pdf.py

from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


class ImageToPdfConverter:

    @staticmethod
    def convert(
        image_path: Path,
        output_path: Path
    ) -> Path:
        """
        画像をPDFへ変換する

        Parameters
        ----------
        image_path : Path
            元画像

        output_path : Path
            出力PDF

        Returns
        -------
        Path
            出力PDFパス
        """

        image = Image.open(image_path)

        # PDF保存時はRGB必須
        if image.mode != "RGB":
            image = image.convert("RGB")

        image.save(
            output_path,
            "PDF",
            resolution=100.0
        )

        return output_path