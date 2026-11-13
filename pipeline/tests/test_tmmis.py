from datetime import date
from pathlib import Path

import pytest

from civic.tmmis import parse_item_page

FX = Path(__file__).parent / "fixtures"


def load(ref):
    return parse_item_page((FX / f"item_{ref}.html").read_text(encoding="utf-8"), ref)


@pytest.fixture(scope="module")
def te():
    return load("2026.TE32.46")


@pytest.fixture(scope="module")
def ex():
    return load("2026.EX31.2")


@pytest.fixture(scope="module")
def pb():
    return load("2027.PB1.6")


def test_te_basics(te):
    assert te.title == "Pedestrianizing Church Street Pilot"
    assert te.wards == [13] and not te.city_wide


def test_te_stages(te):
    assert [(s.kind, s.start_date, s.end_date, s.outcome) for s in te.stages] == [
        ("community_council", date(2026, 4, 30), date(2026, 4, 30), "Adopted without amendment"),
        ("city_council", date(2026, 5, 20), date(2026, 5, 21), "Adopted with amendments"),
    ]
    assert [s.order for s in te.stages] == [1, 2]
    assert te.stages[1].decision_text.startswith("City Council on May 20 and 21, 2026, adopted")


def test_te_origin_is_letter_not_staff_stage(te):
    # The item started from a councillor's letter: no staff-report stage is invented.
    assert te.origin["type"] == "Letter" and te.origin["date"] == date(2026, 4, 16)
    assert all(s.kind != "staff_report" for s in te.stages)


def test_te_counts_only(te):
    assert te.public_submissions > 0 and te.speakers > 0
    assert not hasattr(te, "speaker_names")


def test_ex_stages(ex):
    assert ex.city_wide and ex.wards == []
    assert [(s.kind, s.start_date, s.amended) for s in ex.stages] == [
        ("staff_report", date(2026, 5, 8), None),
        ("committee", date(2026, 5, 12), True),
        ("city_council", date(2026, 5, 20), True),
    ]
    assert ex.stages[1].body_name == "Executive Committee"
    assert ex.stages[1].decision_text.startswith("The Executive Committee recommends")
    assert ex.upcoming_meeting is None
    assert ex.participation["submit_comments_url"] is None


def test_pb_upcoming(pb):
    assert pb.wards == [4]
    assert [(s.kind, s.start_date, s.outcome) for s in pb.stages] == [
        ("staff_report", date(2026, 10, 28), ""),
        ("board", date(2026, 11, 16), "Scheduled"),
    ]
    assert pb.upcoming_meeting == {"date": date(2026, 11, 16), "body": "Toronto Preservation Board"}
    # A scheduled meeting has decided nothing yet.
    assert pb.stages[1].decision_text == ""
    assert pb.stages[0].decision_text.startswith("The Senior Manager, Heritage Planning")


def test_pb_participation(pb):
    assert pb.participation["submit_comments_url"] == \
        "https://secure.toronto.ca/council/#/public-participation/2027.PB1.6/comments"
    # No deadline is ever produced by the page reader.
    assert "deadline" not in pb.participation


def test_pdfs_listed(pb):
    assert any(d["url"].endswith("backgroundfile-290746.pdf") for d in pb.documents)
