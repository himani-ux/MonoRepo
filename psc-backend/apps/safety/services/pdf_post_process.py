from __future__ import annotations

from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


class PdfPostProcessor:
    confidentiality_label = "Confidential - Safety Investigation"

    def add_page_numbering_and_confidentiality(
        self,
        pdf_content: bytes,
        *,
        incident_number: str,
        generated_at: str,
    ) -> bytes:
        reader = PdfReader(BytesIO(pdf_content))
        writer = PdfWriter()
        total_pages = len(reader.pages)

        for page_number, page in enumerate(reader.pages, start=1):
            overlay = self._build_overlay(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height),
                incident_number=incident_number,
                generated_at=generated_at,
                page_number=page_number,
                total_pages=total_pages,
            )
            page.merge_page(PdfReader(BytesIO(overlay)).pages[0])
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        return output.getvalue()

    def _build_overlay(
        self,
        *,
        width: float,
        height: float,
        incident_number: str,
        generated_at: str,
        page_number: int,
        total_pages: int,
    ) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(width, height), invariant=1)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.setFillColor(HexColor("#B91C1C"))
        pdf.drawString(40, height - 18, self.confidentiality_label)

        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(HexColor("#475569"))
        pdf.drawString(40, 18, f"{incident_number} | Generated {generated_at}")
        pdf.drawRightString(width - 40, 18, f"Page {page_number} of {total_pages}")
        pdf.save()
        return buffer.getvalue()
