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


_HEADING = re.compile(r"^[A-Z][A-Z ,&/-]{3,}$")  # e.g. "FINANCIAL IMPACT"
_FOOTER = re.compile(r"Page \d+ of \d+\s*$")


def staff_recommendations(page_texts):
    """The numbered recommendations from a staff report (the "RECOMMENDATIONS" section),
    as one line of text, so they can be compared with the committee and Council versions.
    Returns "" if the section can't be found. Only line breaks and page footers are removed."""
    lines = [ln.strip() for t in page_texts for ln in t.splitlines()]
    lines = [ln for ln in lines if ln and not _FOOTER.search(ln)]
    try:
        start = lines.index("RECOMMENDATIONS") + 1
    except ValueError:
        return ""
    body = []
    for ln in lines[start:]:
        if _HEADING.match(ln):
            break
        body.append(ln)
    text = re.sub(r"\s+", " ", " ".join(body)).strip()
    m = re.search(r"\brecommends? that:\s*", text)
    return text if m and re.search(r"\b1\.\s", text[m.end():m.end() + 4]) else ""
