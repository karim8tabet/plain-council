"""Draft and check a Decision Card for one item. Usage (from pipeline/):

    ../.venv/Scripts/python.exe draft_item.py 2026.EX31.2

Writes out/<ref>.json: item facts, stages, source passages, claims (all unreviewed or
rejected by code) and a run report. Nothing here is shown to residents until a clerk
approves it in the staff screen.
"""
import json
import os
import re
import sys
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

from civic.draft import SourcePassage, draft_claims, groq_llm, run_report, stage_passages, verify_claims
from civic.fingerprint import fingerprint_item
from civic.pdf import extract_passages
from civic.tmmis import fetch_item_html, parse_item_page

ROOT = Path(__file__).resolve().parent
UA = {"User-Agent": "plain-council/0.1"}


def load_env(path=ROOT.parent / ".env"):
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z_]+)=(.*)$", line.strip())
        if m and m[2].strip() and m[1] not in os.environ:
            os.environ[m[1]] = m[2].strip()


def staff_report_passages(item):
    """Find the staff report among the item's background PDFs: it must carry the report's date.
    Only /bgrd/ (background) PDFs are considered; /comm/ PDFs are public letters and never used."""
    stage = next((s for s in item.stages if s.kind == "staff_report"), None)
    if stage is None:
        return [], None
    want = f"{stage.start_date:%B} {stage.start_date.day}, {stage.start_date.year}"
    for doc in item.documents:
        if "/bgrd/" not in doc["url"]:
            continue
        pdf = httpx.get(doc["url"], timeout=120, headers=UA, follow_redirects=True).content
        pages = extract_passages(pdf)
        if pages and want in pages[0].text_normalized:
            return [SourcePassage("staff_report", f"Staff report ({want})", doc["url"], p.page, p.text_original)
                    for p in pages], doc["url"]
    return [], None


def jsonable(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(type(o))


def main(ref):
    load_env()
    html = fetch_item_html(ref)
    item = parse_item_page(html, ref)
    staff, staff_url = staff_report_passages(item)
    passages = staff + stage_passages(item)
    print(f"{ref}: {len(item.stages)} stages, {len(passages)} passages "
          f"({'staff report found' if staff_url else 'no staff report PDF'})", flush=True)

    llm = groq_llm()
    claims = draft_claims(item, passages, llm, model=llm.model)
    print(f"drafted {len(claims)} sentences; verifying...", flush=True)
    verify_claims(claims, llm)

    out = {
        "ref": ref,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": llm.model,
        "source_fingerprint": fingerprint_item(html),
        "item": {k: v for k, v in asdict(item).items() if k != "stages"},
        "stages": [asdict(s) for s in item.stages],
        "passages": [asdict(p) for p in passages],
        "claims": [asdict(c) for c in claims],
        "report": run_report(claims),
    }
    (ROOT / "out").mkdir(exist_ok=True)
    path = ROOT / "out" / f"{ref}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=jsonable), encoding="utf-8")
    print(json.dumps(out["report"]), "->", path.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1])
