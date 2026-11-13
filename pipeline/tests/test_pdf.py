from pathlib import Path
from civic.pdf import extract_passages
FIXTURES = Path(__file__).parent / "fixtures"

def test_pdf_fixture():
    data = (Path(__file__).parent/'fixtures'/'ex31_2_staff_report.pdf').read_bytes()
    passages = extract_passages(data)
    assert passages and all(p.page >= 1 and len(p.text_normalized) >= 40 for p in passages)


def test_staff_recommendations_from_real_report():
    from civic.pdf import extract_passages, staff_recommendations
    pages = [p.text_original for p in extract_passages((FIXTURES / "ex31_2_staff_report.pdf").read_bytes())]
    recs = staff_recommendations(pages)
    assert recs.startswith("The Executive Director, Environment, Climate and Forestry")
    assert "recommend that: 1. City Council increase the 2026 Operating Budget" in recs
    assert "3. City Council direct the Executive Director" in recs
    assert recs.endswith("for any additional supply required.")
    assert "FINANCIAL IMPACT" not in recs and "Page 2 of 7" not in recs
    assert "the City\u2019s Hardship Fund" in recs


def test_staff_recommendations_missing_section():
    from civic.pdf import staff_recommendations
    assert staff_recommendations(["SUMMARY\nNo recommendations here."]) == ""
