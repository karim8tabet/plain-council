from dataclasses import dataclass
from io import BytesIO
import re
import pdfplumber
from .text import normalize

@dataclass
class Passage:
    page: int
    text_original: str
    text_normalized: str

def extract_passages(pdf_bytes):
    result = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for para in re.split(r"\n\s*\n", text):
                norm = normalize(para)
                if len(norm) >= 40: result.append(Passage(page_no, para, norm))
    return result
