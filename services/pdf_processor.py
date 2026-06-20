# services/pdf_processor.py

from io import BytesIO

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas


class PdfProcessor:

    TARGET_WIDTH = 595

    @staticmethod
    def add_label(
        input_pdf,
        output_pdf,
        student_id: str,
        start_page: int,
        total_pages: int
    ):
        """
        全ページを横幅595ptに揃えたうえで
        右上に

        B123456 (1/3)

        のようなラベルを追加する
        """

        reader = PdfReader(str(input_pdf))
        writer = PdfWriter()

        for page_index, page in enumerate(reader.pages):
            label_page = start_page + page_index

            label_text = (
                f"{student_id} "
                f"({label_page}/{total_pages})"
            )

            original_width = float(page.mediabox.width)
            original_height = float(page.mediabox.height)

            scale = (
                PdfProcessor.TARGET_WIDTH
                / original_width
            )

            new_width = PdfProcessor.TARGET_WIDTH
            new_height = original_height * scale

            page.scale_by(scale)

            page.mediabox.lower_left = (0, 0)
            page.mediabox.upper_right = (
                new_width,
                new_height
            )

            packet = BytesIO()

            c = canvas.Canvas(
                packet,
                pagesize=(new_width, new_height)
            )

            box_width = 120
            box_height = 20
            margin = 10

            x = (
                new_width
                - box_width
                - margin
            )

            y = (
                new_height
                - box_height
                - margin
            )

            c.setFillColor(white)
            c.rect(
                x,
                y,
                box_width,
                box_height,
                fill=1,
                stroke=1
            )

            c.setFillColor(black)
            c.setFont(
                "Helvetica",
                10
            )

            c.drawString(
                x + 5,
                y + 6,
                label_text
            )

            c.save()

            packet.seek(0)

            overlay = PdfReader(packet)

            page.merge_page(
                overlay.pages[0]
            )

            writer.add_page(page)

        with open(output_pdf, "wb") as f:
            writer.write(f)