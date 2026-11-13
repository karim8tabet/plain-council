import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from civic.report_log import parse_report_log
from civic.tmmis import parse_item_page
from civic.votes import parse_votes
from load_item import build_rows, participation_row, toronto_time

FX = Path(__file__).parent / "fixtures"


def fake_out(ref):
    item = parse_item_page((FX / f"item_{ref}.html").read_text(encoding="utf-8"), ref)
    d = json.loads(json.dumps({k: v for k, v in asdict(item).items() if k != "stages"}, default=str))
    return {"ref": ref, "source_fingerprint": "abc", "item": d,
            "stages": json.loads(json.dumps([asdict(s) for s in item.stages], default=str)),
            "passages": [], "claims": [], "report": {"reading_grade": 7.0}}


def test_toronto_time_dst():
    assert toronto_time(datetime(2026, 5, 21, 11, 31)).isoformat() == "2026-05-21T11:31:00-04:00"
    assert toronto_time(datetime(2026, 11, 16, 9, 30)).isoformat() == "2026-11-16T09:30:00-05:00"
    assert toronto_time(datetime(2026, 3, 8, 12)).utcoffset().total_seconds() == -4 * 3600  # 2nd Sun of March
    assert toronto_time(datetime(2026, 11, 1, 12)).utcoffset().total_seconds() == -5 * 3600  # 1st Sun of Nov


def test_participation_rules():
    pb = fake_out("2027.PB1.6")["item"]
    row = participation_row("2027.PB1.6", pb)
    assert row["status"] == "open" and row["method_url"].endswith("/2027.PB1.6/comments")
    assert row["method_source"] == "https://secure.toronto.ca/council/agenda-item.do?item=2027.PB1.6"
    assert "deadline_text" not in row  # never inferred
    assert participation_row("2026.EX31.2", fake_out("2026.EX31.2")["item"])["status"] == "decided"
    no_form = dict(pb, participation={"submit_comments_url": None})
    assert participation_row("2027.PB1.6", no_form)["status"] == "upcoming"


def test_build_rows_ex31_2():
    records = json.loads((FX / "voting_record_sample.json").read_text(encoding="utf8"))["2026.EX31.2"]
    reqs = parse_report_log((FX / "report_request_log_sample.xlsx").read_bytes(), "2026.EX31.2")
    rows = build_rows(fake_out("2026.EX31.2"), parse_votes(records, "2026.EX31.2"), reqs)
    assert rows["item"]["city_wide"] and rows["item"]["decision_body"] == "City Council"
    assert [s["kind"] for s in rows["stages"]] == ["staff_report", "committee", "city_council"]
    assert rows["stages"][2]["stage_date"] == "2026-05-21"
    assert [v["motion_kind"] for v in rows["votes"]] == ["amendment", "amendment", "amendment", "main_item"]
    assert rows["votes"][0]["voted_at"] == "2026-05-21T11:31:00-04:00"
    assert [r["report_back_timing"] for r in rows["report_requests"]] == ["2026-06-24", "June 2027"]
    assert rows["participation"]["status"] == "decided"


def test_build_rows_staff_text_from_report():
    from civic.pdf import extract_passages
    out = fake_out("2026.EX31.2")
    out["passages"] = [{"stage": "staff_report", "page": p.page, "text_original": p.text_original,
                        "doc_title": "Staff report", "doc_url": "x"}
                       for p in reversed(extract_passages((FX / "ex31_2_staff_report.pdf").read_bytes()))]
    staff = build_rows(out, [], [])["stages"][0]
    assert staff["kind"] == "staff_report"
    assert "recommend that: 1. City Council increase the 2026 Operating Budget" in staff["decision_text"]
    assert build_rows(fake_out("2026.EX31.2"), [], [])["stages"][0]["decision_text"] is None  # no report, no text
