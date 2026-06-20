# services/pdf_merger.py

from pathlib import Path

from pypdf import PdfReader, PdfWriter


class PdfMerger:

    @staticmethod
    def merge(
        pdf_files: list[Path],
        output_path: Path
    ) -> Path:
        """
        PDFを順番に結合する

        Parameters
        ----------
        pdf_files
            結合対象PDF一覧

        output_path
            出力先

        Returns
        -------
        Path
            出力PDF
        """

        writer = PdfWriter()

        for pdf_file in pdf_files:
            reader = PdfReader(str(pdf_file))

            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path