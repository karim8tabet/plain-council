from datetime import date
from pathlib import Path

from civic.report_log import excel_serial_to_date, parse_report_log

DATA = (Path(__file__).parent / "fixtures" / "report_request_log_sample.xlsx").read_bytes()


def test_serials():
    assert excel_serial_to_date(46163) == date(2026, 5, 21)
    assert excel_serial_to_date(46197) == date(2026, 6, 24)
    assert excel_serial_to_date("46163.0") == date(2026, 5, 21)


def test_ex31_2_chain():
    first, follow = parse_report_log(DATA, "2026.EX31.2")
    assert (first.item_ref, first.status, first.closed_by, first.is_follow_up) == \
        ("2026.EX31.2", "closed", "2026.CC42.12", False)
    assert first.meeting_date == date(2026, 5, 21)
    assert first.report_back_timing == date(2026, 6, 24)
    assert first.status_label.startswith("When staff determine")

    assert (follow.item_ref, follow.status, follow.is_follow_up) == ("2026.CC42.12", "ncf", True)
    assert follow.report_back_timing == "June 2027"
    assert follow.status_label.startswith("Outstanding report requests are not carried forward")


def test_unknown_item_empty():
    assert parse_report_log(DATA, "2026.ZZ1.1") == []
