GOAL: The pipeline can read Toronto council records (item pages, staff report PDFs, Voting Record, Report Request Log) into plain Python data, and can check AI-drafted sentences (quote match, no dates, decision words, loaded words, reading level), all proven by passing pytest tests against real saved fixtures.

CONTEXT:
- Files to create: `pipeline/civic/__init__.py`, `pipeline/civic/text.py`, `pipeline/civic/tmmis.py`, `pipeline/civic/pdf.py`, `pipeline/civic/votes.py`, `pipeline/civic/report_log.py`, `pipeline/civic/checks.py`, `pipeline/civic/fingerprint.py`, `pipeline/pytest.ini`, and tests under `pipeline/tests/test_*.py`.
- Fixtures (real data, saved Nov 13, 2026; read-only):
  - `pipeline/tests/fixtures/item_2026.TE32.46.html`, `item_2026.EX31.2.html`, `item_2027.PB1.6.html`: item pages from `https://secure.toronto.ca/council/agenda-item.do?item=<ref>`
  - `pipeline/tests/fixtures/ex31_2_staff_report.pdf`
  - `pipeline/tests/fixtures/voting_record_sample.json`: `{ref: [records]}` from the CKAN datastore. Fields: `Committee`, `Date/Time`, `Agenda Item #`, `Motion Type`, `Vote` (Yes/No/Absent per member), `Result`, `Vote Description`, plus member names.
  - `pipeline/tests/fixtures/report_request_log_sample.xlsx`: sheets "Main Data" and "Glossary". Columns include `Status`, `Meeting \r\nDate` (Excel serial), `Item Number`, `Agenda title`, `Directive`, `Report Back Timing` (Excel serial OR text like "June 2027"), `Assigned to`, `Closed \r\nby`. Header names contain `\r\n`, so normalize headers by collapsing whitespace.
- Item page structure:
  - one accordion card per stage, newest first. The card button text is like "City Council consideration on May 20 and 21, 2026" or "Executive Committee consideration on May 12, 2026".
  - inside each card: `<h3 class="heading">` holds the title, and `<h4>` sections such as "City Council Decision", "Committee Recommendations", "Community Council Recommendations", "Recommendations", "Origin", "Summary", "Background Information…", "Communications…", "Speakers", "Motions…".
  - a "Tracking Status" section near the top.
  - ward line like "Ward: 13 - Toronto Centre", or "Wards: All".
  - an upcoming item may have a "Submit Comments" button.
  - Open the fixtures to confirm the exact markup.
- Key decisions:
  - Python 3.14, run from the `.venv` at the repo root. BeautifulSoup with the built-in `"html.parser"` (no lxml).
  - Use dataclasses for return types. Pure functions take HTML/bytes/records; separate small `fetch_*` functions do network I/O with httpx (timeout 60s, User-Agent `plain-council/0.1`). **Tests never touch the network.**
  - Stage kinds (strings, matching the DB enum): `staff_report`, `committee`, `community_council`, `board`, `city_council`.
  - **Never store or return member-of-public names** from Communications/Speakers. Counts only. (Councillor names in vote records are fine but are not needed in output: return counts.)
  - The displayed quote must be the ORIGINAL source text span, never the AI's text.

CONSTRAINTS:
- Do NOT change: `supabase/`, `web/`, `README.md`, `PLAN.md`, `TESTS.md`, `RESUME.md`, the fixtures.
- Do NOT add dependencies beyond what's installed: httpx, beautifulsoup4, pdfplumber, rapidfuzz, textstat, openpyxl, pytest (stdlib is fine).

STEPS:
1. `pipeline/pytest.ini` with `pythonpath = .` and `testpaths = tests`.
2. `text.py`: `normalize(s)`. Steps:
   - NFKC
   - rejoin words hyphenated across line breaks ("trans-\nportation" → "transportation")
   - straighten curly quotes and dashes
   - collapse all whitespace to single spaces, strip

   Also `normalize_with_map(s)` returning (normalized, index_map), where `index_map[i]` = index in the original string of normalized char i (for slicing original spans).
3. `tmmis.py`: `parse_item_page(html: str, ref: str) -> ItemRecord`. Fields:
   - ref, title (without the "TE32.46 - " prefix), wards (list[int], empty if All), city_wide (bool), status_text (e.g. "Amended")
   - tracking_status (text)
   - stages (chronological, oldest first): order, kind, body_name, start_date, end_date (date, end = start if one day), outcome (e.g. "Adopted with amendments" / "Adopted without amendment" / "Scheduled"), decision_text (text of the decision/recommendations section for that stage, numbered parts kept, whitespace normalized), source_url (item page URL)
   - a `staff_report` stage first, built from the "Origin" section's "(Month D, YYYY) Report from …" line, with that date and the author as body_name
   - documents: title, url, date (if shown), section name
   - public_submissions: count of entries across all Communications sections; speakers: count of entries across Speakers sections
   - participation: submit_comments_url (absolute URL or None)
   - upcoming meeting datetime/place if the item is not yet considered

   Plus `fetch_item_html(ref)`.
4. `pdf.py`: `extract_passages(pdf_bytes) -> list[Passage(page, text_original, text_normalized)]` using pdfplumber. Split each page into paragraph passages (blank line or large gap), drop passages under 40 normalized chars. Pages are 1-based.
5. `votes.py`: `parse_votes(records, ref) -> list[Vote]`:
   - keep only records whose `Agenda Item #` equals ref (normalize "," to ".")
   - group member rows into one vote per (Date/Time, Motion Type, Vote Description, Result)
   - fields: body_name (Committee), voted_at (datetime or date; parse "2026-05-21 11:35 AM", "2026-05-21 21:38 PM" (tolerate 24h hour with PM), and "2026-04-30"), motion_type, motion_kind ("amendment" if Motion Type starts with "Amend", "main_item" if it starts with "Adopt", else "other"), description, result, yes_count/no_count/absent_count (from member rows), and votes_for/against parsed from Result like "Carried, 23-1"
   - sort by voted_at

   Plus `fetch_vote_records(ref)` using `https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search` with resource_id `55ead013-2331-4686-9895-9e8145b94189`, q=<ref>, limit 2000.
6. `report_log.py`: `parse_report_log(xlsx_bytes, ref) -> list[ReportRequest]`:
   - rows where Item Number == ref, plus one level of follow-ups: rows whose Item Number equals the `Closed by` of a matched row
   - fields: item_ref, directive, status (as recorded, lowercase-trimmed; keep "NCF"), status_label (human text from the Glossary, e.g. "Not Carried Forward (NCF)": "Outstanding report requests are not carried forward to the next term report log."), closed_by, meeting_date (date from Excel serial), report_back_timing (date if serial, else the text), assigned_to, is_follow_up (bool)
   - helper `excel_serial_to_date(n)`
7. `checks.py`, each returning a list of flag dicts `{"type": ..., "detail": ...}` (empty = pass):
   - `match_quote(quote, passages, threshold=95) -> QuoteMatch(passed, score, passage_index, source_span)`: normalize both sides, use rapidfuzz `fuzz.partial_ratio_alignment`, map the best normalized span back to the ORIGINAL passage text via the index map, return that original span
   - `check_no_dates(sentence)`: flag month names followed by a day number, numeric dates, times like "9:30 AM", and words "deadline", "due by", "no later than"
   - `check_decision_words(sentence, stage)`: for stage `staff_report`, flag "approved", "adopted", "decided", "council agreed"; for `committee`/`community_council`/`board`, flag "City Council approved/adopted/decided"
   - `check_loaded_words(sentence)`: case-insensitive whole-word list: controversial, finally, only, massive, huge, just, clearly, obviously, unfortunately, sadly, shocking, radical, disastrous, landmark, historic, slammed, botched, sweeping, drastic. Detail = the word
   - `reading_grade(text) -> float` via textstat Flesch-Kincaid grade
8. `fingerprint.py`: `fingerprint_item(html)`: sha256 hex of the normalized text of the page's main content only (ignore scripts, styles, nav, and anything time-varying), so the same page gives the same hash and a changed decision text gives a different one.
9. Tests (one file per module) with these exact expectations from the fixtures:
   - TE32.46:
     - title "Pedestrianizing Church Street Pilot", wards [13], status_text "Amended"
     - stages = [community_council "Toronto and East York Community Council" 2026-04-30 outcome adopted without amendment, city_council 2026-05-20→2026-05-21 adopted with amendments] (no staff_report stage if there's no "Report from" origin; assert whatever the page shows and document it)
     - council decision_text has 4 numbered parts; part 1 contains "between Wellesley Street East and Alexander Street" and "June 19, 2026 to August 21, 2026"
     - public_submissions > 0; no output field contains "a submitter's name"
   - EX31.2:
     - city_wide True, wards []
     - stages = [staff_report 2026-05-08, committee "Executive Committee" 2026-05-12 amended, city_council 2026-05-20→21 amended]
     - council decision_text contains "$1,060,000" and "maximum heat bylaw"
   - 2027.PB1.6:
     - wards [4]; one board stage "Toronto Preservation Board" 2026-11-16, not yet considered
     - staff_report stage 2026-10-28
     - submit_comments_url not None
     - recommendations contain "16-storey mixed-use building"
   - Votes EX31.2: exactly 4 votes (all 2026-05-21; the CC42.12 June record is excluded):
     - "Matlow - motion 1" Lost 8-16, amendment
     - "motion 2a" Carried 23-1, amendment
     - "motion 2b" Carried 23-1, amendment
     - adopt as amended Carried 23-1, main_item
   - Votes TE32.46: exactly 3:
     - 2026-04-30 Adopt Item Carried 6-0, main_item
     - Bradford motion 1 Carried 16-8, amendment (its description contains the typo "TE32,46")
     - adopt as amended Carried 20-4, main_item
   - Report log EX31.2:
     - a row with status "closed", closed_by "2026.CC42.12", meeting_date 2026-05-21, report_back_timing 2026-06-24 (corrected after review: spec had an off-by-one)
     - a follow-up row from 2026.CC42.12 with status "ncf", report_back_timing "June 2027", is_follow_up True
   - `excel_serial_to_date(46163) == date(2026,5,20)`, `excel_serial_to_date(46197) == date(2026,6,23)`
   - PDF: passages non-empty, all pages ≥ 1, all normalized text ≥ 40 chars
   - normalize: "trans-\nportation" → "transportation"; curly quotes → straight
   - match_quote:
     - exact quote passes with score 100
     - quote differing only by line breaks, double spaces or curly quotes passes (≥95), and source_span equals the original-text slice
     - quote with "approved" changed to "rejected" fails
     - unrelated quote fails
   - check_no_dates: flags "Comments are due November 20" and "at 9:30 AM", passes "Council added money to the budget"
   - check_decision_words: flags "Council approved the closure" at staff_report; passes it at city_council
   - check_loaded_words: flags "the controversial closure" (detail "controversial"); passes "Council added $1,060,000 to the 2026 budget for this program"
   - reading_grade returns a float
   - fingerprint: same fixture twice → same hash; fixture with the decision text edited → different hash

DONE WHEN (run these and make them pass):
- From `pipeline/`: `..\.venv\Scripts\python.exe -m pytest -q` → all tests pass, 0 network calls
- `..\.venv\Scripts\python.exe -c "import civic.tmmis, civic.pdf, civic.votes, civic.report_log, civic.checks, civic.fingerprint"` succeeds

REPORT BACK:
- files changed or created, one line each
- command output for every DONE WHEN check, or the exact error if a check could not run
- whether Serena tools were available
- anything you were unsure about or deviated from (especially how stage outcomes and dates are parsed from the page)
