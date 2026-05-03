import pytest
from unittest.mock import MagicMock, AsyncMock
import io
import fitz

from app.modules.documents.parsers import (
    OcrRuntimeUnavailable,
    PdfPasswordInvalid,
    PdfPasswordRequired,
    parse_pdf_content,
    parse_pptx_content,
    parse_docx_content,
    parse_xlsx_content,
    parse_material,
    validate_file_type,
)


def test_validate_file_type_pdf():
    content = b"%PDF-1.4"
    assert validate_file_type(content, "test.pdf") == "pdf"


def test_validate_file_type_allowed():
    assert validate_file_type(b"%PDF-1.4", "test.pdf") == "pdf"
    assert validate_file_type(b"PK\x03\x04 content", "test.pptx") == "pptx"
    assert validate_file_type(b"PK\x03\x04 content", "test.docx") == "docx"
    assert validate_file_type(b"PK\x03\x04 content", "test.xlsx") == "xlsx"


def test_validate_file_type_not_allowed():
    content = b"some content"
    assert validate_file_type(content, "test.exe") is None
    assert validate_file_type(content, "test.txt") is None
    assert validate_file_type(content, "test.pdf") is None
    assert validate_file_type(content, "test.pptx") is None


def test_parse_material_unknown_type():
    result = parse_material("exe", b"content")
    assert result is None


def test_parse_material_pdf():
    result = parse_material("pdf", b"%PDF-1.4 fake pdf content")
    assert isinstance(result, list)


def test_parse_material_pptx():
    result = parse_material("pptx", b"PK\x03\x04 fake pptx content")
    assert isinstance(result, list)


def test_parse_pdf_content_extracts_selectable_text():
    sections = parse_pdf_content(_build_pdf_bytes("ECG Rate Assessment\nCount large boxes."))

    assert len(sections) == 1
    assert sections[0].title == "ECG Rate Assessment"
    assert "Count large boxes." in sections[0].body


def test_parse_pdf_content_requires_password_for_encrypted_pdf():
    encrypted = _build_pdf_bytes("Protected ECG", password="secret")

    with pytest.raises(PdfPasswordRequired, match="PDF requires password"):
        parse_pdf_content(encrypted)


def test_parse_pdf_content_rejects_invalid_password():
    encrypted = _build_pdf_bytes("Protected ECG", password="secret")

    with pytest.raises(PdfPasswordInvalid, match="Invalid PDF password"):
        parse_pdf_content(encrypted, password="wrong")


def test_parse_pdf_content_accepts_valid_password():
    encrypted = _build_pdf_bytes("Protected ECG\nUse a 6-second strip.", password="secret")

    sections = parse_pdf_content(encrypted, password="secret")

    assert len(sections) == 1
    assert sections[0].title == "Protected ECG"
    assert "Use a 6-second strip." in sections[0].body


def test_parse_pdf_content_uses_ocr_when_text_is_insufficient(monkeypatch):
    calls = []

    def fake_ocr(page, page_number):
        calls.append(page_number)
        return "Scanned ECG\nIdentify rhythm from image text."

    monkeypatch.setattr("app.modules.documents.parsers.extract_page_text_with_ocr", fake_ocr)

    sections = parse_pdf_content(_build_blank_pdf_bytes())

    assert calls == [1]
    assert len(sections) == 1
    assert sections[0].title == "Scanned ECG"
    assert "Identify rhythm" in sections[0].body


def test_parse_pdf_content_reports_missing_ocr_runtime(monkeypatch):
    def fake_ocr(page, page_number):
        raise OcrRuntimeUnavailable("Tesseract OCR runtime is not available")

    monkeypatch.setattr("app.modules.documents.parsers.extract_page_text_with_ocr", fake_ocr)

    with pytest.raises(OcrRuntimeUnavailable, match="Tesseract OCR runtime"):
        parse_pdf_content(_build_blank_pdf_bytes())


def _build_pdf_bytes(text: str, password: str | None = None) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    output = io.BytesIO()
    save_kwargs = {}
    if password:
        save_kwargs = {
            "encryption": fitz.PDF_ENCRYPT_AES_256,
            "owner_pw": password,
            "user_pw": password,
        }
    doc.save(output, **save_kwargs)
    doc.close()
    return output.getvalue()


def _build_blank_pdf_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page()
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()
