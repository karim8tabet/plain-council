from shapely.geometry import box

from build_fsa_wards import fsa_wards

# Two wards side by side: ward 1 is x 0-10, ward 2 is x 10-20.
WARDS = {1: box(0, 0, 10, 10), 2: box(10, 0, 20, 10)}


def test_area_inside_one_ward():
    assert fsa_wards({"M1A": box(1, 1, 4, 4)}, WARDS) == {"M1A": [1]}


def test_area_crossing_wards_largest_first():
    assert fsa_wards({"M1B": box(8, 0, 20, 10)}, WARDS) == {"M1B": [2, 1]}


def test_sliver_dropped():
    # Only 1% of this area is in ward 1: a boundary sliver, not a real overlap.
    assert fsa_wards({"M1C": box(9.9, 0, 19.9, 10)}, WARDS) == {"M1C": [2]}


def test_area_outside_toronto_skipped():
    assert fsa_wards({"M9Z": box(50, 50, 60, 60)}, WARDS) == {}


# --- the built lookup used by the website (golden checks on known places) ---
import json
from pathlib import Path

LOOKUP = json.loads((Path(__file__).resolve().parents[2] / "web" / "lib" / "fsa-wards.json").read_text(encoding="utf-8"))


def test_known_postal_areas():
    assert LOOKUP["M5V"] == [10]        # King West / CityPlace: Spadina-Fort York
    assert LOOKUP["M6R"] == [4]         # Roncesvalles: Parkdale-High Park
    assert LOOKUP["M6K"][0] == 4        # 1337 Queen St W area: mostly Ward 4
    assert LOOKUP["M5B"] == [13]        # Downtown Yonge: Toronto Centre
    assert LOOKUP["M9W"] == [1]         # Rexdale: Etobicoke North


def test_every_ward_reachable():
    assert {w for ws in LOOKUP.values() for w in ws} == set(range(1, 26))
