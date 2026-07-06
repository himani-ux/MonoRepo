from __future__ import annotations

from io import BytesIO
import unittest

from PyPDF2 import PdfReader

from apps.certs.services.pdf_renderer import ReportLabPdfRenderer


class CertPdfRendererTests(unittest.TestCase):
    def test_reportlab_renderer_turns_sample_html_into_pdf(self) -> None:
        renderer = ReportLabPdfRenderer()

        result = renderer.render_html_to_pdf(
            """
            <html>
              <body>
                <h1>SQE S 633</h1>
                <p>Certs renderer smoke</p>
                <p>Vessel: YC FORTITUDE</p>
              </body>
            </html>
            """,
            title="SQE S 633 - Certificates and Surveys",
        )

        self.assertEqual(result.engine, "reportlab")
        self.assertEqual(result.content_type, "application/pdf")
        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertGreater(len(result.content), 800)

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("SQE S 633", text)
        self.assertIn("Certs renderer smoke", text)
        self.assertIn("YC FORTITUDE", text)

    def test_reportlab_renderer_reports_available_runtime(self) -> None:
        renderer = ReportLabPdfRenderer()

        self.assertTrue(renderer.is_available())
        self.assertIsNone(renderer.availability_error())

