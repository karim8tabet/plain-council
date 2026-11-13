from pathlib import Path
from civic.pdf import extract_passages

def test_pdf_fixture():
    data = (Path(__file__).parent/'fixtures'/'ex31_2_staff_report.pdf').read_bytes()
    passages = extract_passages(data)
    assert passages and all(p.page >= 1 and len(p.text_normalized) >= 40 for p in passages)
