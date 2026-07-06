from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from apps.certs.services.ocr_pipeline import (
    AUTO_ACCEPT,
    GAP_FILL,
    MANUAL_ENTRY,
    OFFICE_CONTEXT,
    VESSEL_CONTEXT,
    OcrEngineOutput,
    OcrFieldCandidate,
    OcrThresholds,
    TesseractOcrEngine,
    _configure_tesseract_command,
    classify_confidence,
    process_cert_pdf,
)


class StaticOcrEngine:
    engine_name = "static-test"

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        return OcrEngineOutput(
            raw_text=(
                "Certificate Type: Cargo Ship Safety Construction Certificate\n"
                "Vessel Name: YC FORTITUDE\n"
                "IMO: 9876543\n"
                "Issue Date: 01-Jan-2026\n"
                "Expiry Date: 31-Dec-2026\n"
                "Certificate No: CSSC-001\n"
                "Issuing Authority: NK\n"
                "Place of Issue: Bangkok\n"
            ),
            mean_confidence=0.82,
            fields={
                "certificate_type": OcrFieldCandidate(
                    value="Cargo Ship Safety Construction Certificate",
                    confidence=0.91,
                ),
                "imo_number": OcrFieldCandidate(value="9876543", confidence=0.82),
                "certificate_number": OcrFieldCandidate(value="CSSC-001", confidence=0.58),
            },
        )


class CompactKrCertificateEngine:
    engine_name = "compact-kr-test"

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        return OcrEngineOutput(
            raw_text=(
                "Thiscertificateisvaliduntil11July2030\n"
                "CertificateNo.:GZU-CC-0170-25\n"
                "KOREANREGISTER\n"
                "CertificateofClassification\n"
                "Particularsofship\n"
                "NameofShip EASTAYUTTHAYA\n"
                "IMONo. 9584293\n"
                "Issuedat on Guangzhou 11August2025THISISTOCERTIFYTHAT\n"
            ),
            mean_confidence=0.95,
            fields={},
        )


class ScbaServiceCertificateEngine:
    engine_name = "scba-service-test"

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        return OcrEngineOutput(
            raw_text=(
                "BLUE TECH\n"
                "MARINE SERVICES LLC\n"
                "CERTIFICATE & CHECKLIST\n"
                "BREATHING APPARATUS\n"
                "Vessel EAST AYUTTHAYA | Certificate No CERT/BTMS/14/BA02\n"
                "IMO No 9584293 Date 15/01/2024\n"
                "Class KR Place of Service | JEBEL ALI,UAE\n"
                "This Certificate is valid for-One. Year from the date of issue.\n"
            ),
            mean_confidence=0.89,
            fields={},
        )


def pdf_raster_runtime_available() -> bool:
    return TesseractOcrEngine().is_available() and importlib.util.find_spec("pypdfium2") is not None


class CertOcrPipelineTests(unittest.TestCase):
    def test_confidence_bands_use_office_and_vessel_thresholds(self) -> None:
        self.assertEqual(classify_confidence(0.80, OFFICE_CONTEXT), AUTO_ACCEPT)
        self.assertEqual(classify_confidence(0.79, OFFICE_CONTEXT), GAP_FILL)
        self.assertEqual(classify_confidence(0.59, OFFICE_CONTEXT), MANUAL_ENTRY)

        self.assertEqual(classify_confidence(0.85, VESSEL_CONTEXT), AUTO_ACCEPT)
        self.assertEqual(classify_confidence(0.84, VESSEL_CONTEXT), GAP_FILL)
        self.assertEqual(classify_confidence(0.59, VESSEL_CONTEXT), MANUAL_ENTRY)

    def test_confidence_bands_accept_tuned_thresholds(self) -> None:
        thresholds = OcrThresholds(
            office_auto_accept=0.90,
            vessel_auto_accept=0.92,
            manual_floor=0.65,
        )

        self.assertEqual(classify_confidence(0.90, OFFICE_CONTEXT, thresholds=thresholds), AUTO_ACCEPT)
        self.assertEqual(classify_confidence(0.89, OFFICE_CONTEXT, thresholds=thresholds), GAP_FILL)
        self.assertEqual(classify_confidence(0.65, OFFICE_CONTEXT, thresholds=thresholds), GAP_FILL)
        self.assertEqual(classify_confidence(0.64, OFFICE_CONTEXT, thresholds=thresholds), MANUAL_ENTRY)

        self.assertEqual(classify_confidence(0.92, VESSEL_CONTEXT, thresholds=thresholds), AUTO_ACCEPT)
        self.assertEqual(classify_confidence(0.91, VESSEL_CONTEXT, thresholds=thresholds), GAP_FILL)

    @patch("apps.certs.services.ocr_pipeline.load_configured_ocr_thresholds")
    def test_process_cert_pdf_uses_tuned_settings_thresholds(self, load_configured_ocr_thresholds) -> None:
        load_configured_ocr_thresholds.return_value = OcrThresholds(
            office_auto_accept=0.90,
            vessel_auto_accept=0.92,
            manual_floor=0.65,
        )

        payload = process_cert_pdf("sample.pdf", context=OFFICE_CONTEXT, engine=StaticOcrEngine())

        load_configured_ocr_thresholds.assert_called_once()
        self.assertEqual(payload["thresholds"]["auto_accept"], 0.90)
        self.assertEqual(payload["thresholds"]["manual_floor"], 0.65)
        self.assertEqual(payload["fields"]["certificate_type"]["mode"], AUTO_ACCEPT)
        self.assertEqual(payload["fields"]["imo_number"]["mode"], GAP_FILL)
        self.assertEqual(payload["fields"]["imo_number"]["threshold"], 0.90)
        self.assertEqual(payload["fields"]["imo_number"]["manual_floor"], 0.65)
        self.assertEqual(payload["fields"]["certificate_number"]["mode"], MANUAL_ENTRY)

    def test_mock_engine_payload_carries_per_field_modes(self) -> None:
        payload = process_cert_pdf("sample.pdf", context=OFFICE_CONTEXT, engine=StaticOcrEngine())

        self.assertEqual(payload["schema_version"], "certs-ocr-v1")
        self.assertEqual(payload["engine"], "static-test")
        self.assertEqual(payload["status"], "processed")
        self.assertEqual(payload["context"], OFFICE_CONTEXT)
        self.assertEqual(payload["thresholds"]["auto_accept"], 0.8)
        self.assertEqual(payload["thresholds"]["manual_floor"], 0.6)
        self.assertEqual(payload["fields"]["certificate_type"]["mode"], AUTO_ACCEPT)
        self.assertEqual(payload["fields"]["imo_number"]["mode"], AUTO_ACCEPT)
        self.assertEqual(payload["fields"]["certificate_number"]["mode"], MANUAL_ENTRY)
        self.assertIsNone(payload["fields"]["certificate_number"]["value"])
        self.assertEqual(payload["fields"]["certificate_number"]["raw_value"], "CSSC-001")
        self.assertEqual(payload["fields"]["certificate_number"]["threshold"], 0.8)
        self.assertEqual(payload["fields"]["issuing_authority"]["value"], "NK")
        self.assertFalse(payload["unprocessable"])

    def test_vessel_context_uses_stricter_threshold_metadata(self) -> None:
        payload = process_cert_pdf("sample.pdf", context=VESSEL_CONTEXT, engine=StaticOcrEngine())

        self.assertEqual(payload["context"], VESSEL_CONTEXT)
        self.assertEqual(payload["thresholds"]["auto_accept"], 0.85)
        self.assertEqual(payload["fields"]["imo_number"]["mode"], GAP_FILL)
        self.assertEqual(payload["fields"]["imo_number"]["threshold"], 0.85)
        self.assertEqual(payload["fields"]["imo_number"]["manual_floor"], 0.6)

    def test_blank_engine_output_is_manual_entry_payload(self) -> None:
        class BlankEngine:
            engine_name = "blank-test"

            def extract(self, source_path: str | Path) -> OcrEngineOutput:
                return OcrEngineOutput(raw_text="", mean_confidence=0.0, fields={})

        payload = process_cert_pdf("blank.pdf", context=VESSEL_CONTEXT, engine=BlankEngine())

        self.assertEqual(payload["status"], "manual_entry_required")
        self.assertTrue(payload["unprocessable"])
        self.assertEqual(payload["fields"]["imo_number"]["mode"], MANUAL_ENTRY)

    def test_tesseract_adapter_reports_missing_runtime_without_import_side_effects(self) -> None:
        engine = TesseractOcrEngine()

        if not engine.is_available():
            self.assertIn("Tesseract OCR", engine.availability_error())

    def test_tesseract_command_can_be_configured_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "tesseract.exe"
            executable.write_text("", encoding="utf-8")
            fake_pytesseract = SimpleNamespace(pytesseract=SimpleNamespace(tesseract_cmd="tesseract"))

            with patch.dict("os.environ", {"TESSERACT_CMD": str(executable)}, clear=False), patch("shutil.which", return_value=None):
                _configure_tesseract_command(fake_pytesseract)

        self.assertEqual(fake_pytesseract.pytesseract.tesseract_cmd, str(executable))

    def test_searchable_pdf_text_layer_is_processed_without_rasterization(self) -> None:
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "cert.pdf"
            page = canvas.Canvas(str(pdf_path))
            page.drawString(72, 760, "Certificate Type: Safety Certificate")
            page.drawString(72, 736, "Vessel Name: YC FORTITUDE")
            page.drawString(72, 712, "IMO: 9876543")
            page.drawString(72, 688, "Issue Date: 01-Jan-2026")
            page.drawString(72, 664, "Expiry Date: 31-Dec-2026")
            page.drawString(72, 640, "Certificate No: TEST-001")
            page.drawString(72, 616, "Issuing Authority: NK")
            page.drawString(72, 592, "Place of Issue: Bangkok")
            page.save()

            payload = process_cert_pdf(pdf_path, context=OFFICE_CONTEXT)

        self.assertEqual(payload["status"], "processed")
        self.assertEqual(payload["fields"]["imo_number"]["value"], "9876543")
        self.assertEqual(payload["fields"]["imo_number"]["mode"], AUTO_ACCEPT)
        self.assertIn("Safety Certificate", payload["raw_text"])

    def test_compact_kr_certificate_text_is_parsed(self) -> None:
        payload = process_cert_pdf("sample.pdf", context=OFFICE_CONTEXT, engine=CompactKrCertificateEngine())

        self.assertEqual(payload["status"], "processed")
        self.assertEqual(payload["fields"]["certificate_type"]["value"], "Certificate of Classification")
        self.assertEqual(payload["fields"]["issuing_authority"]["value"], "Korean Register")
        self.assertEqual(payload["fields"]["vessel_name"]["value"], "EAST AYUTTHAYA")
        self.assertEqual(payload["fields"]["imo_number"]["value"], "9584293")
        self.assertEqual(payload["fields"]["issue_date"]["value"], "11 August 2025")
        self.assertEqual(payload["fields"]["expiry_date"]["value"], "11 July 2030")
        self.assertEqual(payload["fields"]["certificate_number"]["value"], "GZU-CC-0170-25")

    def test_scba_service_certificate_text_is_parsed(self) -> None:
        payload = process_cert_pdf("sample.pdf", context=VESSEL_CONTEXT, engine=ScbaServiceCertificateEngine())

        self.assertEqual(payload["status"], "processed")
        self.assertEqual(payload["fields"]["certificate_type"]["value"], "Breathing Apparatus")
        self.assertEqual(payload["fields"]["issuing_authority"]["value"], "BLUE TECH MARINE SERVICES LLC")
        self.assertEqual(payload["fields"]["vessel_name"]["value"], "EAST AYUTTHAYA")
        self.assertEqual(payload["fields"]["imo_number"]["value"], "9584293")
        self.assertEqual(payload["fields"]["certificate_number"]["value"], "CERT/BTMS/14/BA02")
        self.assertEqual(payload["fields"]["issue_date"]["value"], "15 January 2024")
        self.assertEqual(payload["fields"]["expiry_date"]["value"], "15 January 2025")
        self.assertEqual(payload["fields"]["place_of_issue"]["value"], "JEBEL ALI,UAE")
        self.assertEqual(payload["fields"]["certificate_number"]["mode"], AUTO_ACCEPT)

    @unittest.skipUnless(pdf_raster_runtime_available(), "Tesseract OCR and pypdfium2 are required for PDF raster OCR")
    def test_image_only_pdf_is_rasterized_for_tesseract(self) -> None:
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_path = temp_path / "scan.png"
            pdf_path = temp_path / "scan.pdf"
            image = Image.new("RGB", (1100, 420), "white")
            draw = ImageDraw.Draw(image)
            draw.text((50, 50), "Certificate Type: Safety Certificate", fill="black")
            draw.text((50, 110), "Vessel Name: EAST AYUTTHAYA", fill="black")
            draw.text((50, 170), "IMO: 9584293", fill="black")
            draw.text((50, 230), "Certificate No: TEST-001", fill="black")
            image.save(image_path)
            page = canvas.Canvas(str(pdf_path), pagesize=(1100, 420))
            page.drawImage(ImageReader(str(image_path)), 0, 0, width=1100, height=420)
            page.save()

            payload = process_cert_pdf(pdf_path, context=OFFICE_CONTEXT)

        self.assertEqual(payload["status"], "processed")
        self.assertFalse(payload["unprocessable"])
        self.assertEqual(payload["fields"]["imo_number"]["value"], "9584293")
        self.assertEqual(payload["fields"]["certificate_number"]["value"], "TEST-001")

    @unittest.skipUnless(TesseractOcrEngine().is_available(), "Tesseract OCR runtime is not installed")
    def test_tesseract_adapter_can_extract_real_image_text_when_runtime_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "cert.png"
            image = Image.new("RGB", (900, 260), "white")
            draw = ImageDraw.Draw(image)
            draw.text((30, 30), "Certificate Type: Safety Certificate", fill="black")
            draw.text((30, 80), "IMO: 9876543", fill="black")
            draw.text((30, 130), "Certificate No: TEST-001", fill="black")
            image.save(image_path)

            output = TesseractOcrEngine().extract(image_path)

        self.assertIn("9876543", output.raw_text)
        self.assertGreater(output.mean_confidence, 0.0)
