"""Draft plain-language Decision Card sentences with an AI model, then check them.

Flow for one item:
  1. Build source passages, each tagged with its stage (staff report PDF pages,
     committee/board decision text, City Council decision text). Public letters are
     never used: they contain residents' names and are counted, not summarized.
  2. Ask the model for sentences, each with a section, a stage and a verbatim quote.
  3. Code checks every sentence (quote really in that stage's source, dates, decision
     words, loaded words). A sentence whose quote can't be found is rejected by code.
  4. A second model call checks each remaining sentence against its source span.
  5. Everything is saved as "unreviewed" (or "rejected" by code). A clerk decides.

The model is called through `llm(messages, schema) -> dict` so tests can pass a fake.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import json
import os

from .checks import (match_quote, check_no_dates, check_decision_words,
                     check_loaded_words, reading_grade)
from .text import normalize

SECTIONS = ["what", "reasons", "who_where", "conditions", "uncertainty", "change"]
STAGES = ["staff_report", "committee", "community_council", "board", "city_council"]
CHUNK_CHARS = 8000  # ~2,000 tokens; keeps each call under Groq's free 8K tokens/minute


@dataclass
class SourcePassage:
    stage: str
    doc_title: str
    doc_url: str
    page: int | None
    text_original: str

    @property
    def text_normalized(self) -> str:
        return normalize(self.text_original)


@dataclass
class Claim:
    section: str
    stage: str
    stage_date: str | None
    text_en: str
    ai_draft: str
    quote_ai: str
    passage_index: int | None = None
    quote_display: str | None = None
    match_score: float = 0.0
    flags: list = field(default_factory=list)
    status: str = "unreviewed"
    model: str = ""


# ---------------------------------------------------------------- prompts

DRAFT_SYSTEM = """You turn official City of Toronto council records into plain-language sentences for residents.

Rules (all required):
- Use ONLY the SOURCE text you are given. Never add facts, numbers, places or reasons that are not in it.
- Each sentence states one fact, short (under 20 words) and neutral, at about a Grade 6-8 reading level.
- REWRITE in everyday words; never copy the quote into "text". Say "this year's budget" not "2026 Operating Budget"; "money set aside for extreme weather" not "Corporate Extreme Weather Reserve"; "the City's environment and climate staff" not long job titles. Leave out contract numbers, "gross/net" and legal phrases like "authorize" or "in coordination with". Keep exact amounts and counts.
- Every sentence needs "quote": ONE continuous piece of the SOURCE (10-40 words), copied EXACTLY, word for word, that supports it. Never use "..." or skip words inside a quote; if the support is long, quote the most important continuous part.
- "stage" must be the stage label of the SOURCE block the quote comes from.
- Say who said it, matching the stage: staff_report -> "Staff recommend..."; committee, community_council or board -> "The [body] recommended..."; city_council -> "City Council decided...". Never say a recommendation was approved or decided unless the quote is a City Council decision.
- Keep important conditions, limits, amounts and exceptions. If something is uncertain or still to be decided, say so (section "uncertainty").
- Do not write deadlines or say when people can comment. Do not mention dates unless the date is in your quote.
- No opinions and no loaded words (e.g. controversial, finally, only, massive, landmark, sadly).
- Never name or describe members of the public. Do not summarize public letters.
- Sections: what = what is proposed or decided; reasons = reasons given in the staff report; who_where = who or which places are affected; conditions = conditions, limits or amounts; uncertainty = what is not yet known or still to be decided; change = something added, removed or changed at this stage compared with the earlier recommendation.
- Write 4 to 10 sentences per SOURCE chunk. Skip procedural text (confidential attachments, legal boilerplate)."""

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {"sentences": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "section": {"type": "string", "enum": SECTIONS},
            "stage": {"type": "string", "enum": STAGES},
            "text": {"type": "string"},
            "quote": {"type": "string"},
        },
        "required": ["section", "stage", "text", "quote"],
        "additionalProperties": False,
    }}},
    "required": ["sentences"],
    "additionalProperties": False,
}

VERIFY_SYSTEM = """You check plain-language sentences against the official source text they cite.
For each item, compare SENTENCE with SOURCE only and give one verdict:
- supported: everything in the sentence is stated in the source, with the same meaning.
- not_supported: the sentence adds, changes or contradicts something (wrong number, wrong body, says decided when only recommended, etc.).
- missing_condition: the sentence is true but drops a condition, limit or exception in the source that changes its meaning.
- loaded_language: the facts are right but the wording is not neutral.
Give a short reason (under 25 words). Judge strictly: a summary that misstates a decision is worse than none."""

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "verdict": {"type": "string", "enum": ["supported", "not_supported", "missing_condition", "loaded_language"]},
            "reason": {"type": "string"},
        },
        "required": ["id", "verdict", "reason"],
        "additionalProperties": False,
    }}},
    "required": ["results"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------- passages

def stage_passages(item) -> list[SourcePassage]:
    """Official decision text of each stage that has one, as passages."""
    out = []
    for s in item.stages:
        if s.decision_text and s.kind != "staff_report":
            out.append(SourcePassage(s.kind, f"{s.body_name} decision ({s.start_date})", s.source_url, None, s.decision_text))
        elif s.decision_text and s.kind == "staff_report":
            out.append(SourcePassage(s.kind, "Staff recommendations (item page)", s.source_url, None, s.decision_text))
    return out


def chunk(passages: list[SourcePassage], limit: int = CHUNK_CHARS) -> list[list[int]]:
    """Group passage indexes into chunks under `limit` characters, never mixing stages."""
    chunks, cur, size, stage = [], [], 0, None
    for i, p in enumerate(passages):
        n = len(p.text_normalized)
        if cur and (size + n > limit or p.stage != stage):
            chunks.append(cur); cur, size = [], 0
        cur.append(i); size += n; stage = p.stage
    if cur:
        chunks.append(cur)
    return chunks


def _source_block(passages, idxs, stage_names) -> str:
    stage = passages[idxs[0]].stage
    head = f"=== SOURCE (stage: {stage}; body: {stage_names.get(stage, stage)}) ==="
    return head + "\n" + "\n\n".join(passages[i].text_normalized for i in idxs)


# ---------------------------------------------------------------- main steps

def draft_claims(item, passages: list[SourcePassage], llm, model: str = "") -> list[Claim]:
    stage_names = {s.kind: s.body_name for s in item.stages}
    stage_dates = {s.kind: (s.end_date or s.start_date) for s in item.stages}
    claims: list[Claim] = []
    for idxs in chunk(passages):
        user = f"Item {item.ref}: {item.title}\n\n" + _source_block(passages, idxs, stage_names)
        data = llm([{"role": "system", "content": DRAFT_SYSTEM}, {"role": "user", "content": user}], DRAFT_SCHEMA)
        allowed = {i for i in idxs}
        for s in data.get("sentences", []):
            c = Claim(s["section"], s["stage"], None, s["text"].strip(), s["text"].strip(), s["quote"].strip(), model=model)
            d = stage_dates.get(c.stage)
            c.stage_date = d.isoformat() if d else None
            check_claim(c, passages, allowed)
            claims.append(c)
    return _dedupe(claims)


def check_claim(c: Claim, passages: list[SourcePassage], allowed: set[int] | None = None) -> Claim:
    """Code checks. The quote must be found in a passage of the SAME stage the sentence claims."""
    pool = [i for i, p in enumerate(passages) if p.stage == c.stage and (allowed is None or i in allowed)]
    m = match_quote(c.quote_ai, [passages[i] for i in pool]) if pool else None
    if m and m.passed:
        c.passage_index, c.quote_display, c.match_score = pool[m.passage_index], m.source_span, m.score
    else:
        c.match_score = m.score if m else 0.0
        c.flags.append({"type": "quote_not_found", "detail": "Quote not found in this stage's source"})
        c.status = "rejected"  # rejected by code; kept so the run report can count it
    c.flags += check_no_dates(c.text_en, c.quote_display)
    c.flags += check_decision_words(c.text_en, c.stage)
    c.flags += check_loaded_words(c.text_en)
    return c


def verify_claims(claims: list[Claim], llm) -> None:
    """Second AI check, only on sentences that passed the quote check."""
    todo = [(i, c) for i, c in enumerate(claims) if c.status != "rejected"]
    for start in range(0, len(todo), 12):
        batch = todo[start:start + 12]
        body = "\n\n".join(f"ID {i}\nSENTENCE: {c.text_en}\nSOURCE: {c.quote_display}" for i, c in batch)
        data = llm([{"role": "system", "content": VERIFY_SYSTEM}, {"role": "user", "content": body}], VERIFY_SCHEMA)
        got = {r["id"]: r for r in data.get("results", [])}
        for i, c in batch:
            r = got.get(i)
            if r is None:
                c.flags.append({"type": "checker_missing", "detail": "Checker gave no verdict"})
            elif r["verdict"] != "supported":
                c.flags.append({"type": r["verdict"], "detail": r["reason"]})


def _dedupe(claims: list[Claim]) -> list[Claim]:
    seen, out = set(), []
    for c in claims:
        key = (c.stage, normalize(c.text_en).lower())
        if key not in seen:
            seen.add(key); out.append(c)
    return out


def run_report(claims: list[Claim]) -> dict:
    kept = [c for c in claims if c.status != "rejected"]
    return {
        "drafted": len(claims),
        "rejected_by_code": len(claims) - len(kept),
        "flagged": sum(1 for c in kept if c.flags),
        "clean": sum(1 for c in kept if not c.flags),
        "reading_grade": round(reading_grade(" ".join(c.text_en for c in kept)), 1) if kept else None,
    }


# ---------------------------------------------------------------- Groq

def groq_llm(model: str | None = None, reasoning_effort: str = "low"):
    """Return an `llm(messages, schema)` function backed by Groq structured outputs.
    Reasoning effort is "low": at "medium" the model can spend its whole output budget on
    hidden reasoning and return nothing, and the free tier allows only 8K tokens/minute."""
    from groq import Groq, BadRequestError
    client = Groq(api_key=os.environ["GROQ_API_KEY"], max_retries=6)  # SDK waits on 429 (retry-after)
    model = model or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

    def llm(messages, schema):
        for attempt in range(2):
            try:
                r = client.chat.completions.create(
                    model=model, messages=messages, temperature=0, max_completion_tokens=4000,
                    reasoning_effort=reasoning_effort,
                    response_format={"type": "json_schema", "json_schema": {"name": "out", "strict": True, "schema": schema}},
                )
                return json.loads(r.choices[0].message.content)
            except BadRequestError as e:  # model output failed the schema; retry once
                if attempt == 1 or "json_validate_failed" not in str(e):
                    raise

    llm.model = model
    return llm


def claims_to_json(claims: list[Claim]) -> list[dict]:
    return [asdict(c) for c in claims]
