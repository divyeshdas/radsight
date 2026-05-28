import io
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from core.config import get_ai_settings
import structlog

logger = structlog.get_logger(__name__)
settings = get_ai_settings()

_ocr_instance = None


def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang=settings.ocr_lang,
                use_gpu=settings.ocr_use_gpu,
                show_log=False,
            )
            logger.info("PaddleOCR initialized")
        except ImportError:
            logger.warning("PaddleOCR not available, using Tesseract fallback")
            _ocr_instance = "tesseract"
    return _ocr_instance


def _extract_with_paddle(image_bytes: bytes, file_ext: str) -> Tuple[str, float]:
    import cv2

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return "", 0.0

    ocr = get_ocr()
    if ocr == "tesseract":
        return _extract_with_tesseract(image_bytes)

    result = ocr.ocr(img, cls=True)
    if not result or not result[0]:
        return "", 0.0

    lines = []
    confidences = []
    for line in result[0]:
        if line and len(line) >= 2:
            text_info = line[1]
            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                lines.append(str(text_info[0]))
                confidences.append(float(text_info[1]))

    extracted_text = "\n".join(lines)
    avg_confidence = float(np.mean(confidences)) if confidences else 0.0

    return extracted_text, avg_confidence


def _extract_with_tesseract(image_bytes: bytes) -> Tuple[str, float]:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, config="--psm 6")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confs = [c for c in data["conf"] if c != -1]
        avg_conf = float(np.mean(confs)) / 100 if confs else 0.5
        return text.strip(), avg_conf
    except Exception as e:
        logger.error("Tesseract OCR failed", error=str(e))
        return "", 0.0


def _extract_from_pdf(pdf_bytes: bytes) -> Tuple[str, float]:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        if text_parts:
            return "\n\n".join(text_parts), 0.95

        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return "\n\n".join(pages), 0.90

    except Exception as e:
        logger.warning("PDF text extraction failed, attempting OCR", error=str(e))
        return "", 0.0


def extract_text(file_bytes: bytes, file_ext: str) -> Dict:
    t0 = time.perf_counter()
    ext = file_ext.lower().lstrip(".")
    extracted_text = ""
    confidence = 0.0
    method = "none"

    try:
        if ext == "pdf":
            extracted_text, confidence = _extract_from_pdf(file_bytes)
            method = "pdf_text"
            if not extracted_text.strip():
                extracted_text, confidence = _extract_with_paddle(file_bytes, ext)
                method = "ocr_pdf"

        elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
            extracted_text, confidence = _extract_with_paddle(file_bytes, ext)
            method = "ocr_image"

        elif ext == "txt":
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
            confidence = 1.0
            method = "direct_text"

    except Exception as e:
        logger.error("Text extraction failed", ext=ext, error=str(e))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "text": extracted_text.strip(),
        "confidence": round(confidence, 4),
        "method": method,
        "word_count": len(extracted_text.split()),
        "char_count": len(extracted_text),
        "inference_ms": round(elapsed_ms, 2),
        "success": bool(extracted_text.strip()),
    }
