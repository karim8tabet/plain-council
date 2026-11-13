from pathlib import Path

from civic.draft import (SourcePassage, chunk, draft_claims, run_report, stage_passages, verify_claims)
from civic.tmmis import parse_item_page

FX = Path(__file__).parent / "fixtures"
EX = parse_item_page((FX / "item_2026.EX31.2.html").read_text(encoding="utf-8"), "2026.EX31.2")
PASSAGES = stage_passages(EX)


def fake(sentences, verdicts=None):
    calls = []

    def llm(messages, schema):
        calls.append(messages)
        if "sentences" in schema["properties"]:
            # Answer each chunk only with sentences for the stage that chunk contains.
            user = messages[-1]["content"]
            return {"sentences": [s for s in sentences if f"stage: {s['stage']};" in user]}
        return {"results": verdicts or []}
    llm.calls = calls
    return llm


def council_quote(n=60):
    p = next(p for p in PASSAGES if p.stage == "city_council")
    return p.text_normalized[:n]


def test_stage_passages_tag_stages():
    assert [p.stage for p in PASSAGES] == ["committee", "city_council"]


def test_chunk_never_mixes_stages_and_respects_limit():
    ps = [SourcePassage("staff_report", "d", "u", 1, "a" * 5000),
          SourcePassage("staff_report", "d", "u", 2, "b" * 5000),
          SourcePassage("city_council", "d", "u", None, "c" * 100)]
    assert chunk(ps, limit=8000) == [[0], [1], [2]]


def test_good_sentence_kept_with_source_span():
    q = council_quote()
    claims = draft_claims(EX, PASSAGES, fake([{"section": "what", "stage": "city_council",
                                               "text": "City Council decided to add money to the program.", "quote": q}]))
    c = claims[0]
    assert c.status == "unreviewed" and c.quote_display and c.match_score >= 95
    assert c.stage_date == "2026-05-21"


def test_invented_quote_rejected_by_code():
    claims = draft_claims(EX, PASSAGES, fake([{"section": "what", "stage": "city_council",
                                               "text": "City Council banned air conditioners.", "quote": "City Council bans all air conditioners in Toronto immediately"}]))
    assert claims[0].status == "rejected"
    assert claims[0].flags[0]["type"] == "quote_not_found"


def test_quote_from_wrong_stage_rejected():
    committee_quote = next(p for p in PASSAGES if p.stage == "committee").text_normalized[:60]
    claims = draft_claims(EX, PASSAGES, fake([{"section": "what", "stage": "city_council",
                                               "text": "City Council decided this.", "quote": committee_quote}]))
    # The committee's words are not proof of what Council decided.
    assert claims[0].status == "rejected"


def test_code_flags_and_checker_flags():
    q = council_quote()
    llm = fake([{"section": "what", "stage": "city_council", "text": "City Council finally made a massive change. Comments are due by Friday.", "quote": q},
                {"section": "conditions", "stage": "city_council", "text": "City Council decided to add money.", "quote": q[:50]}],
               verdicts=[{"id": 1, "verdict": "missing_condition", "reason": "drops the one-time limit"}])
    claims = draft_claims(EX, PASSAGES, llm)
    verify_claims(claims, llm)
    types0 = {f["type"] for f in claims[0].flags}
    assert {"loaded_word", "deadline_word"} <= types0
    assert claims[1].flags == [{"type": "missing_condition", "detail": "drops the one-time limit"}]


def test_public_letters_never_sent():
    llm = fake([])
    draft_claims(EX, PASSAGES, llm)
    sent = " ".join(m["content"] for msgs in llm.calls for m in msgs)
    assert "Communications" not in sent and "/comm/" not in sent


def test_run_report_counts():
    q = council_quote()
    claims = draft_claims(EX, PASSAGES, fake([
        {"section": "what", "stage": "city_council", "text": "City Council decided to add money to the program.", "quote": q},
        {"section": "what", "stage": "city_council", "text": "Invented.", "quote": "not in the source at all, nothing like it"}]))
    r = run_report(claims)
    assert (r["drafted"], r["rejected_by_code"], r["clean"]) == (2, 1, 1)
