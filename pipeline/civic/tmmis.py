"""Read one item page from Toronto's council meeting site (TMMIS) into plain data.

Facts here come from the page structure, not from AI. Stage outcomes come from each
stage card's own "Status:" line; whether a stage is still upcoming comes from the
page's "Tracking Status" text ("will be considered by ..."), never from today's date.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .text import normalize

BASE = "https://secure.toronto.ca/council/agenda-item.do?item="
# The "Submit Comments" button runs JavaScript; this is the page it opens (checked Nov 13, 2026).
COMMENTS_URL = "https://secure.toronto.ca/council/#/public-participation/{ref}/comments"

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_ENTRY = re.compile(rf"\((?:{_MONTHS}) \d{{1,2}}, \d{{4}}\)")


@dataclass
class Stage:
    order: int
    kind: str  # staff_report | committee | community_council | board | city_council
    body_name: str
    start_date: date | None
    end_date: date | None
    outcome: str  # "Adopted with amendments" | "Adopted without amendment" | "Scheduled" | "" (staff report)
    amended: bool | None
    decision_text: str
    source_url: str


@dataclass
class ItemRecord:
    ref: str
    title: str
    wards: list[int]
    city_wide: bool
    status_text: str
    tracking_status: str
    stages: list[Stage]
    documents: list[dict] = field(default_factory=list)
    public_submissions: int = 0
    speakers: int = 0
    participation: dict = field(default_factory=dict)
    upcoming_meeting: dict | None = None
    origin: dict | None = None


def _date(month: str, day: str, year: str) -> date:
    return datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()


def _kind(body: str) -> str:
    if body == "City Council":
        return "city_council"
    if "Community Council" in body:
        return "community_council"
    if "Board" in body:
        return "board"
    return "committee"


def _section_text(h4) -> str:
    """Text between an <h4> and the next heading."""
    parts, node = [], h4.find_next_sibling()
    while node is not None and node.name not in ("h3", "h4"):
        parts.append(node.get_text("\n", strip=True))
        node = node.find_next_sibling()
    return "\n".join(parts)


def _sections(card) -> dict[str, str]:
    return {" ".join(h.get_text(" ", strip=True).split()): _section_text(h) for h in card.find_all("h4")}


_DECISION_HEADINGS = ("City Council Decision", "Committee Recommendations",
                      "Community Council Recommendations", "Board Recommendations", "Recommendations")


def parse_item_page(html: str, ref: str) -> ItemRecord:
    soup = BeautifulSoup(html, "html.parser")
    url = BASE + ref

    heading = next((h.get_text(" ", strip=True) for h in soup.select("h3.heading")), ref)
    short_ref = ref.split(".", 1)[1]
    title = normalize(re.sub(r"^" + re.escape(short_ref) + r"\s*-\s*", "", heading))

    tracking = ""
    tr = soup.find(lambda t: t.name == "h2" and "Tracking Status" in t.get_text())
    if tr is not None:
        tracking = normalize(tr.parent.get_text(" ", strip=True))
        tracking = re.sub(r"^.*?Tracking Status\s*", "", tracking)
        tracking = re.split(r"\s+Expand All\b", tracking)[0]

    stages: list[Stage] = []
    status_text, wards, city_wide, upcoming = "", set(), False, None
    submissions, speaker_names = set(), set()

    for card in soup.select(".card"):
        button = card.select_one(".accordin-heading")
        if button is None:
            continue
        label = normalize(button.get_text(" ", strip=True))
        m = re.search(rf"(.+?) consideration on ({_MONTHS}) (\d+)(?: and (\d+))?, (\d{{4}})", label)
        if not m:
            continue
        body, month, day, day2, year = m.groups()
        start = _date(month, day, year)
        end = _date(month, day2, year) if day2 else start
        text = normalize(card.get_text(" ", strip=True))

        wm = re.search(r"Wards?:\s*(All|[\d ,]+)", text)
        if wm:
            if wm.group(1) == "All":
                city_wide = True
            else:
                wards.update(int(x) for x in re.findall(r"\d+", wm.group(1)))

        sm = re.search(r"\bStatus:\s*(\w+)", text)
        card_status = sm.group(1) if sm else ""
        if card_status and not status_text:
            status_text = card_status  # newest card first
        if card_status == "Amended":
            outcome, amended = "Adopted with amendments", True
        elif card_status == "Adopted":
            outcome, amended = "Adopted without amendment", False
        elif re.search(rf"will be considered by (?:the )?{re.escape(body)} on", tracking) and not card_status:
            outcome, amended = "Scheduled", None
            upcoming = {"date": start, "body": body}
        else:
            outcome, amended = card_status, None

        secs = _sections(card)
        # A scheduled meeting has made no decision yet; its card only repeats the staff recommendations.
        decision = "" if outcome == "Scheduled" else next(
            (normalize(secs[h]) for h in _DECISION_HEADINGS if h in secs), "")

        for name, body_text in secs.items():
            if name.startswith("Communications"):
                for entry in re.split(rf"(?={_ENTRY.pattern})", body_text):
                    entry = normalize(entry)
                    if _ENTRY.match(entry):
                        submissions.add(entry)  # dedupe: Council cards repeat committee letters
            elif name == "Speakers":
                speaker_names.update(line.strip() for line in body_text.split("\n") if line.strip())

        stages.append(Stage(0, _kind(body), body, start, end, outcome, amended, decision, url))

    # Staff report stage, from the "Origin" section: "(October 28, 2026) Report from the ..."
    origin = next((_section_text(h) for h in soup.find_all("h4") if h.get_text(strip=True) == "Origin"), "")
    # Only a staff "Report from" counts as a staff stage; an item can also start from a
    # councillor's letter, which is recorded as the origin but is not a staff recommendation.
    origin_info = None
    om = re.search(rf"\(({_MONTHS}) (\d+), (\d{{4}})\)\s*(\w+(?:-\w+)?) from (?:the )?(.+)", normalize(origin))
    if om:
        d = _date(*om.group(1, 2, 3))
        source = normalize(om.group(5)).rstrip(" ,;.")
        origin_info = {"type": om.group(4), "from": source, "date": d}
        if om.group(4) == "Report":
            stages.append(Stage(0, "staff_report", source, d, d, "", None, _staff_recommendations(soup), url))

    stages.sort(key=lambda s: (s.start_date or date.min, s.kind != "staff_report"))
    for i, s in enumerate(stages, 1):
        s.order = i

    docs = [{"title": normalize(a.get_text(" ", strip=True)), "url": urljoin(url, a["href"])}
            for a in soup.select("a[href$='.pdf']")]

    has_comments = soup.find(id="btSbComments") is not None
    participation = {"submit_comments_url": COMMENTS_URL.format(ref=ref) if has_comments else None}

    # Speaker names are only used to count; they are never returned.
    return ItemRecord(ref, title, sorted(wards), city_wide, status_text, tracking, stages, docs,
                      len(submissions), len(speaker_names), participation, upcoming, origin_info)


def _staff_recommendations(soup) -> str:
    """The staff report's recommendations as printed on the item page (usually the oldest card)."""
    for h in reversed(soup.find_all("h4")):
        if h.get_text(strip=True) == "Recommendations":
            return normalize(_section_text(h))
    return ""


def fetch_item_html(ref: str) -> str:
    r = httpx.get(BASE + ref, timeout=60, headers={"User-Agent": "plain-council/0.1"})
    r.raise_for_status()
    return r.text
