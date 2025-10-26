from pdfminer.six import extract_text as pdfminer_extract
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

def extract_pdf_text(path: str) -> str:
    """
    Extract text from PDF using pdfminer.six (primary) with pypdf fallback
    """
    try:
        text = pdfminer_extract(path)
        if text and text.strip():
            return text
    except Exception as e:
        logger.warning(f"pdfminer.six failed, trying pypdf: {e}")
    
    # Fallback to pypdf
    try:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() for page in reader.pages)
        return text if text else ""
    except Exception as e:
        logger.error(f"All PDF extraction methods failed: {e}")
        return ""