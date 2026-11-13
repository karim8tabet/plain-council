from dataclasses import dataclass
import re
from rapidfuzz import fuzz
from textstat import textstat
from .text import normalize, normalize_with_map

@dataclass
class QuoteMatch:
    passed: bool
    score: float
    passage_index: int | None
    source_span: str | None

def match_quote(quote, passages, threshold=95):
    q = normalize(quote); best = (0.0, None, None)
    for index, passage in enumerate(passages):
        original = getattr(passage, "text_original", str(passage))
        normalized, mapping = normalize_with_map(original)
        alignment = fuzz.partial_ratio_alignment(q, normalized)
        if alignment.score > best[0]:
            lo = mapping[alignment.dest_start] if mapping else 0
            hi = mapping[alignment.dest_end - 1] + 1 if mapping and alignment.dest_end else len(original)
            best = alignment.score, index, original[lo:hi]
    return QuoteMatch(best[0] >= threshold, best[0], best[1], best[2])

_DATE_PATTERNS = [
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b\d{1,2}:\d{2}\s*(?:AM|PM|a\.m\.|p\.m\.)",
]
_DEADLINE_WORDS = r"\b(?:deadline|due by|due on|no later than|submit by|comments due)\b"


def check_no_dates(sentence, source_span=None):
    """Dates in AI text are allowed only if the same date is in the quoted source span.
    Deadline wording is always flagged: deadlines come only from official participation pages."""
    src = normalize(source_span or "").lower()
    flags = [{"type": "date", "detail": m.group()}
             for p in _DATE_PATTERNS for m in re.finditer(p, sentence, re.I)
             if normalize(m.group()).lower() not in src]
    flags += [{"type": "deadline_word", "detail": m.group()} for m in re.finditer(_DEADLINE_WORDS, sentence, re.I)]
    return flags

def check_decision_words(sentence, stage):
    pattern = r"\b(?:approved|adopted|decided|council agreed)\b" if stage == "staff_report" else (r"\bCity Council (?:approved|adopted|decided)\b" if stage in ("committee", "community_council", "board") else None)
    return [{"type": "decision_word", "detail": m.group()} for m in re.finditer(pattern, sentence, re.I)] if pattern else []

def check_loaded_words(sentence):
    words = "controversial finally only massive huge just clearly obviously unfortunately sadly shocking radical disastrous landmark historic slammed botched sweeping drastic".split()
    return [{"type": "loaded_word", "detail": m.group()} for word in words for m in re.finditer(r"\b" + re.escape(word) + r"\b", sentence, re.I)]

def reading_grade(text):
    return float(textstat.flesch_kincaid_grade(text))
