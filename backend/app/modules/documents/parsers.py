import io
import logging
import re
from typing import List, Optional
from pydantic import BaseModel
import fitz
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pptx import Presentation
from docx import Document
from openpyxl import load_workbook


logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {"pdf", "pptx", "docx", "xlsx"}


MAGIC_BYTES = {
    b"%PDF": "pdf",
    b"PK\x03\x04": "pptx",
}


class ParsedSection(BaseModel):
    title: str
    body: str
    position: int


class ParseResult(BaseModel):
    material_id: int
    sections: List[ParsedSection]


def validate_file_type(content: bytes, filename: str) -> Optional[str]:
    """Validate file type using magic number detection."""
    if not filename or "." not in filename:
        return None

    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None

    magic = content[:4]
    if ext == "pdf" and magic.startswith(b"%PDF"):
        return ext
    if ext in {"pptx", "docx", "xlsx"} and magic.startswith(b"PK\x03\x04"):
        return ext
    return None


def parse_pdf_content(content: bytes) -> List[ParsedSection]:
    sections = []
    try:
        # Method 1: Try PyMuPDF with detailed text extraction
        doc = fitz.open(stream=content, filetype="pdf")
        logger.info(f"PDF has {len(doc)} pages")
        
        text_content = ""
        for i, page in enumerate(doc):
            # Try different extraction methods
            text = page.get_text("text")  # Raw text
            
            if not text or not text.strip():
                # Try dict extraction which includes more details
                text_dict = page.get_text("dict")
                if "blocks" in text_dict:
                    texts = []
                    for block in text_dict.get("blocks", []):
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line.get("spans", []):
                                    texts.append(span.get("text", ""))
                    text = " ".join(texts)
            
            if text and text.strip():
                text_content += f"\n\n=== Page {i+1} ===\n\n{text}"
        
        doc.close()
        
        # Method 2: If still no text, try pdfminer with layout preservation
        if not text_content.strip():
            logger.info("Trying pdfminer with layout analysis...")
            from pdfminer.pdfpage import PDFPage
            from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
            
            output = io.StringIO()
            resource_manager = PDFResourceManager()
            converter = TextConverter(resource_manager, output, laparams=LAParams(line_overlap=0.3, char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=False))
            interpreter = PDFPageInterpreter(resource_manager, converter)
            
            pdf_pages = list(PDFPage.get_pages(io.BytesIO(content)))
            logger.info(f"pdfminer found {len(pdf_pages)} pages")
            
            for page_num, page in enumerate(pdf_pages):
                try:
                    interpreter.process_page(page)
                    page_text = output.getvalue()
                    if page_text.strip():
                        text_content += f"\n\n=== Page {page_num+1} ===\n\n{page_text}"
                except Exception as e:
                    logger.warning(f"pdfminer page {page_num+1} error: {e}")
            
            converter.close()
        
        # Method 3: Try XHTML extraction (better for complex layouts)
        if not text_content.strip():
            logger.info("Trying XHTML extraction...")
            try:
                output = io.StringIO()
                extract_text_to_fp(io.BytesIO(content), output, output_type="xhtml", laparams=LAParams())
                xhtml_text = output.getvalue()
                if xhtml_text and "<" in xhtml_text:
                    # Strip HTML tags
                    import re
                    text_content = re.sub(r'<[^>]+>', ' ', xhtml_text)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
            except Exception as e:
                logger.warning(f"XHTML extraction error: {e}")
        
        logger.info(f"Total text extracted: {len(text_content)} chars")
        
        # Method 4: If still no text, use OCR (PaddleOCR)
        if not text_content.strip() or len(text_content.strip()) < 100:
            logger.info("Using PaddleOCR for image-based extraction...")
            try:
                ocr_text = extract_text_with_ocr(content)
                if ocr_text and len(ocr_text.strip()) > 50:
                    text_content += f"\n\n=== OCR Content ===\n\n{ocr_text}"
                    logger.info(f"OCR extracted {len(ocr_text)} chars successfully")
                else:
                    logger.warning("OCR did not extract useful text")
            except Exception as e:
                logger.error(f"OCR error: {e}")
        
        # Parse text into sections (page by page)
        if text_content and text_content.strip():
            pages = text_content.split("=== Page")
            for page_text in pages[1:]:  # Skip first empty split
                lines = page_text.strip().split("\n")
                if not lines:
                    continue
                    
                # Find first non-empty line as title
                title = None
                body_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if title is None:
                        title = line[:200]
                    else:
                        body_lines.append(line)
                
                if title or body_lines:
                    sections.append(ParsedSection(
                        title=title or f"Page",
                        body="\n".join(body_lines),
                        position=len(sections)
                    ))
        
        logger.info(f"Total sections extracted: {len(sections)}")
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
    return sections


def extract_text_with_ocr(pdf_content: bytes) -> Optional[str]:
    """Extract text from PDF using OCR (for scanned/image PDFs)."""
    try:
        from paddleocr import PaddleOCR
        
        logger.info("Initializing PaddleOCR...")
        # Initialize OCR with English support
        ocr = PaddleOCR(lang='en')
        logger.info("PaddleOCR initialized successfully")
        
        # Convert PDF pages to images and run OCR
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        logger.info(f"PDF has {len(doc)} pages for OCR")
        all_text = []
        
        for i, page in enumerate(doc):
            logger.info(f"Processing page {i+1}/{len(doc)} for OCR")
            # Render page as image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            logger.info(f"Page {i+1} rendered as PNG, size: {len(img_data)} bytes")
            
            # Run OCR on image
            result = ocr.ocr(img_data)
            logger.info(f"Page {i+1} OCR result: {result is not None}")
            
            if result and len(result) > 0 and result[0]:
                page_text = []
                for line_idx, line in enumerate(result[0]):
                    if line and len(line) >= 2:
                        # Handle different result formats
                        if isinstance(line[-1], (list, tuple)):
                            text = line[-1][0]
                        else:
                            text = str(line[-1])
                        if isinstance(text, str):
                            page_text.append(text)
                
                if page_text:
                    text_content = "\n".join(page_text)
                    all_text.append(f"--- Page {i+1} ---\n{text_content}")
                    logger.info(f"OCR page {i+1}: extracted {len(text_content)} chars")
        
        doc.close()
        
        if all_text:
            return "\n\n".join(all_text)
        else:
            logger.warning("OCR found no text in any page")
            return None
        
    except Exception as e:
        import traceback
        logger.error(f"OCR extraction failed: {e}")
        logger.error(f"OCR traceback: {traceback.format_exc()}")
        return None


def parse_pptx_content(content: bytes) -> List[ParsedSection]:
    sections = []
    try:
        with io.BytesIO(content) as f:
            prs = Presentation(f)
            for i, slide in enumerate(prs.slides):
                texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        texts.append(shape.text)
                if texts:
                    title = texts[0][:200] if texts else f"Slide {i + 1}"
                    body = "\n".join(texts[1:]) if len(texts) > 1 else ""
                    sections.append(ParsedSection(
                        title=title,
                        body=body,
                        position=i
                    ))
    except Exception as e:
        logger.error(f"PPTX parsing error: {e}")
    return sections


def parse_docx_content(content: bytes) -> List[ParsedSection]:
    sections = []
    try:
        with io.BytesIO(content) as f:
            doc = Document(f)
            current_title = ""
            current_body = []
            position = 0
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                if para.style.name.startswith("Heading"):
                    if current_title or current_body:
                        sections.append(ParsedSection(
                            title=current_title or f"Section {position + 1}",
                            body="\n".join(current_body),
                            position=position
                        ))
                        position += 1
                        current_body = []
                    current_title = text[:200]
                else:
                    current_body.append(text)
            if current_title or current_body:
                sections.append(ParsedSection(
                    title=current_title or f"Section {position + 1}",
                    body="\n".join(current_body),
                    position=position
                ))
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
    return sections


def parse_xlsx_content(content: bytes) -> List[ParsedSection]:
    sections = []
    try:
        with io.BytesIO(content) as f:
            wb = load_workbook(f, read_only=True)
            for sheet_idx, sheet in enumerate(wb.sheetnames):
                ws = wb[sheet]
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    continue
                headers = rows[0] if rows else ()
                data_rows = rows[1:] if len(rows) > 1 else []
                table_data = []
                for row in data_rows:
                    if any(cell is not None for cell in row):
                        try:
                            table_data.append(dict(zip(headers, row)))
                        except Exception:
                            pass
                if table_data:
                    body_lines = [f"Sheet: {sheet}"]
                    for row in table_data[:20]:
                        row_str = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                        body_lines.append(row_str)
                    sections.append(ParsedSection(
                        title=sheet[:200],
                        body="\n".join(body_lines),
                        position=sheet_idx
                    ))
    except Exception as e:
        logger.error(f"XLSX parsing error: {e}")
    return sections


def parse_material(file_type: str, content: bytes) -> Optional[List[ParsedSection]]:
    """Parse material content into sections.
    
    Args:
        file_type: File extension (e.g., 'pdf', 'pptx')
        content: Raw file content in bytes
        
    Returns:
        List of ParsedSection objects, or None if file type not allowed
    """
    handlers = {
        "pdf": parse_pdf_content,
        "pptx": parse_pptx_content,
        "docx": parse_docx_content,
        "xlsx": parse_xlsx_content,
    }
    handler = handlers.get(file_type.lower())
    if handler:
        return handler(content)
    return None
