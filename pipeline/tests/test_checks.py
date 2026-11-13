from civic.checks import match_quote, check_no_dates, check_decision_words, check_loaded_words, reading_grade
from civic.pdf import Passage

SRC = "City Council direct the Executive Director to report back to the June 24, 25, 26, 2026 meeting of City Council."


def P(text):
    return Passage(1, text, text)


# --- quote matching (C1-C3) ---
def test_quote_exact_and_wrong():
    p = P("Council approved the proposal after careful review.")
    assert match_quote("Council approved the proposal", [p]).passed
    assert not match_quote("Completely unrelated wording", [p]).passed


def test_quote_loose_normalization_returns_original_span():
    original = "the City’s pilot – a sea-\nsonal closure of Church Street"
    m = match_quote("the City's pilot - a seasonal closure of Church Street", [P("Intro. " + original + " end.")])
    assert m.passed
    assert m.source_span == original  # shown as in the source, never the AI's copy


def test_quote_picks_right_passage():
    m = match_quote("report back by June 2027", [P("Unrelated text here."), P("direct the City Manager to report back by June 2027 with")])
    assert m.passed and m.passage_index == 1


# --- dates and deadlines (C6, revised rule) ---
def test_date_not_in_source_is_flagged():
    assert check_no_dates("Comments are accepted until November 20.", SRC)


def test_date_in_source_is_allowed():
    assert not check_no_dates("Staff will report back in June 24, 2026 meeting.", SRC)


def test_time_without_source_flagged():
    assert check_no_dates("Please attend at 9:30 AM")


def test_deadline_words_always_flagged_even_if_in_source():
    flags = check_no_dates("The deadline is June 24.", "deadline June 24")
    assert [f["type"] for f in flags] == ["deadline_word"]


def test_vote_tally_is_not_a_date():
    assert not check_no_dates("Council voted 16-8 for the change and 23-1 for the main item.")


def test_plain_sentence_passes():
    assert not check_no_dates("Council added money to the budget")


# --- decision words vs stage (C7) ---
def test_decision_words():
    assert check_decision_words("Council approved the closure", "staff_report")
    assert check_decision_words("City Council approved the closure", "committee")
    assert not check_decision_words("The committee recommends the closure", "committee")
    assert not check_decision_words("Council approved the closure", "city_council")


# --- neutral language (C8) ---
def test_loaded_words():
    assert check_loaded_words("the controversial closure")[0]["detail"].lower() == "controversial"
    assert not check_loaded_words("The street will close to cars on weekends.")
    assert not check_loaded_words("Justice and adjustments")  # whole words only


# --- reading level (C9) ---
def test_reading_grade_orders_texts():
    easy = reading_grade("The street is closed to cars. People can walk there. It is a test.")
    hard = reading_grade("The municipal administration recommends comprehensive implementation of "
                         "pedestrianization infrastructure notwithstanding jurisdictional considerations.")
    assert isinstance(easy, float) and easy < 8 < hard


# --- quotes with "..." (pieces must all match, in order, in one passage) ---
LONG = ("City Council authorize an amendment to Blanket Contract Number 4300000099, competitively awarded "
        "under nRFP Doc5443909641, issued to CLEAResult Canada Inc. for additional supply, delivery and "
        "installation of portable air conditioners by $1,041,667 net of all applicable taxes and charges.")


def test_ellipsis_quote_shows_full_span():
    m = match_quote("authorize an amendment to Blanket Contract Number 4300000099, competitively awarded ... "
                    "for additional supply, delivery and installation of portable air conditioners", [P(LONG)])
    assert m.passed
    assert "nRFP Doc5443909641" in m.source_span  # the skipped words are shown to residents


def test_ellipsis_pieces_out_of_order_fail():
    assert not match_quote("for additional supply, delivery and installation of portable ... "
                           "authorize an amendment to Blanket Contract Number", [P(LONG)]).passed


def test_ellipsis_with_invented_piece_fails():
    assert not match_quote("authorize an amendment to Blanket Contract Number 4300000099 ... "
                           "and cancel every other heat program in the city", [P(LONG)]).passed


def test_ellipsis_tiny_piece_fails():
    assert not match_quote("authorize an amendment to Blanket Contract ... taxes", [P(LONG)]).passed
