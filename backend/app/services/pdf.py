# ...existing code...
import logging
from typing import List

logger = logging.getLogger(__name__)

# Prefer PyMuPDF (fitz). Fallback to pypdf if unavailable.
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
    logger.debug("PyMuPDF (fitz) not available")

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
    logger.debug("pypdf not available")


def extract_pdf_text(path: str) -> str:
    """
    Extract text from PDF using PyMuPDF (fast, reliable).
    Falls back to pypdf if PyMuPDF is not installed or fails.
    Returns a single string with page texts separated by blank lines.
    """
    # 1) PyMuPDF extraction
    if fitz:
        try:
            doc = fitz.open(path)
            pages: List[str] = []
            for page in doc:
                try:
                    txt = page.get_text("text") or ""
                except Exception:
                    txt = ""
                if txt.strip():
                    pages.append(txt)
            if pages:
                return "\n\n".join(pages)
        except Exception as e:
            logger.warning("PyMuPDF extraction failed for %s: %s", path, e)

    # 2) Fallback to pypdf
    if PdfReader:
        try:
            reader = PdfReader(path)
            pages: List[str] = []
            for p in reader.pages:
                try:
                    t = p.extract_text() or ""
                except Exception:
                    t = ""
                pages.append(t)
            joined = "\n\n".join(pages).strip()
            if joined:
                return joined
        except Exception as e:
            logger.warning("pypdf extraction failed for %s: %s", path, e)

    logger.error("No PDF extraction backend succeeded for %s", path)
    return ""
# ...existing code...