import json
from pathlib import Path

import pytest

from civic.votes import parse_votes

RECORDS = json.loads((Path(__file__).parent / "fixtures" / "voting_record_sample.json").read_text(encoding="utf8"))


def summary(ref):
    return [(v.motion_kind, v.motion_type, v.votes_for, v.votes_against, v.result.split(",")[0])
            for v in parse_votes(RECORDS[ref], ref)]


def test_ex31_2_four_votes_excludes_other_items():
    assert summary("2026.EX31.2") == [
        ("amendment", "Amend Item", 8, 16, "Lost"),
        ("amendment", "Amend Item", 23, 1, "Carried"),
        ("amendment", "Amend Item (Additional)", 23, 1, "Carried"),
        ("main_item", "Adopt Item as Amended", 23, 1, "Carried"),
    ]


def test_te32_46_three_votes_including_typo_description():
    assert summary("2026.TE32.46") == [
        ("main_item", "Adopt Item", 6, 0, "Carried"),
        ("amendment", "Amend Item (Additional)", 16, 8, "Carried"),
        ("main_item", "Adopt Item as Amended", 20, 4, "Carried"),
    ]


@pytest.mark.parametrize("ref", ["2026.EX31.2", "2026.TE32.46"])
def test_member_counts_match_result(ref):
    for v in parse_votes(RECORDS[ref], ref):
        assert (v.yes_count, v.no_count) == (v.votes_for, v.votes_against)


def test_comma_ref_matches():
    rows = [dict(r, **{"Agenda Item #": "2026.TE32,46"}) for r in RECORDS["2026.TE32.46"]]
    assert len(parse_votes(rows, "2026.TE32.46")) == 3
