import pytest
from unittest.mock import MagicMock, AsyncMock

from app.modules.documents.parsers import (
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
