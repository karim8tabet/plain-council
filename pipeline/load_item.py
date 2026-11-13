"""Load one drafted item into Supabase. Usage (from pipeline/):

    ../.venv/Scripts/python.exe load_item.py 2026.EX31.2

Reads out/<ref>.json (from draft_item.py), fetches the item's votes (Voting Record) and
report requests (Report Request Log) from Toronto Open Data, and writes everything with
the service key. Claims arrive as "unreviewed" (or "rejected" by code); nothing becomes
visible to residents until a clerk approves it.

Safety: if a person has already reviewed any claim for this item, the load stops instead
of overwriting their work.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

from civic.report_log import parse_report_log
from civic.text import normalize
from civic.votes import fetch_vote_records, parse_votes

ROOT = Path(__file__).resolve().parent
CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show"
REPORT_LOG_PACKAGE = "report-request-log-city-council-and-its-committees"
UA = {"User-Agent": "plain-council/0.1"}


# ---------------------------------------------------------------- time

def _nth_sunday(year, month, n):
    d = date(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def toronto_time(naive: datetime) -> datetime:
    """Attach Toronto's UTC offset (EDT from 2nd Sunday of March to 1st Sunday of November)."""
    y = naive.year
    dst = _nth_sunday(y, 3, 2) <= naive.date() < _nth_sunday(y, 11, 1)
    return naive.replace(tzinfo=timezone(timedelta(hours=-4 if dst else -5)))


# ---------------------------------------------------------------- rows (pure, tested)

def participation_row(ref, item):
    """'open' only when the official item page offers a way to comment; never a deadline."""
    url = (item.get("participation") or {}).get("submit_comments_url")
    upcoming = item.get("upcoming_meeting")
    page = f"https://secure.toronto.ca/council/agenda-item.do?item={ref}"
    if upcoming and url:
        return {"item_ref": ref, "status": "open",
                "method_text": "Send a written comment using the City's official form",
                "method_url": url, "method_source": page}
    if upcoming:
        return {"item_ref": ref, "status": "upcoming"}
    return {"item_ref": ref, "status": "decided"}


def build_rows(out, votes, requests):
    ref, item, stages = out["ref"], out["item"], out["stages"]
    last = stages[-1] if stages else {}
    return {
        "item": {
            "ref": ref, "title": item["title"], "wards": item["wards"], "city_wide": item["city_wide"],
            "decision_body": last.get("body_name"), "status_text": item["status_text"] or None,
            "item_url": f"https://secure.toronto.ca/council/agenda-item.do?item={ref}",
            "has_card": True, "source_fingerprint": out["source_fingerprint"], "source_changed": False,
            "reading_grade": out["report"]["reading_grade"], "public_submissions": item["public_submissions"],
        },
        "stages": [{
            "item_ref": ref, "stage_order": s["order"], "kind": s["kind"], "body_name": s["body_name"],
            "stage_date": s["end_date"] or s["start_date"], "outcome": s["outcome"] or None,
            "amended": s["amended"], "decision_text": s["decision_text"] or None, "source_url": s["source_url"],
        } for s in stages],
        "passages": [{
            "item_ref": ref, "doc_title": p["doc_title"], "doc_url": p["doc_url"], "stage": p["stage"],
            "doc_date": next((s["end_date"] or s["start_date"] for s in stages if s["kind"] == p["stage"]), None),
            "page": p["page"], "text_original": p["text_original"], "text_normalized": normalize(p["text_original"]),
        } for p in out["passages"]],
        # passage_id is filled in after passages are inserted (passage_index -> new id)
        "claims": [{
            "item_ref": ref, "section": c["section"], "sort_order": i, "stage": c["stage"],
            "stage_date": c["stage_date"], "text_en": c["text_en"], "ai_draft": c["ai_draft"],
            "passage_index": c["passage_index"], "quote_display": c["quote_display"],
            "match_score": c["match_score"], "flags": c["flags"], "status": c["status"], "model": c["model"],
        } for i, c in enumerate(out["claims"])],
        "votes": [{
            "item_ref": ref, "voted_at": toronto_time(v.voted_at).isoformat(), "body_name": v.body_name,
            "motion_type": v.motion_type, "motion_kind": v.motion_kind, "description": v.description,
            "result": v.result, "yes_count": v.yes_count, "no_count": v.no_count, "absent_count": v.absent_count,
        } for v in votes],
        "report_requests": [{
            "item_ref": ref, "directive": normalize(r.directive), "status": r.status,
            "closed_by": r.closed_by or None,
            "report_back_timing": r.report_back_timing.isoformat() if isinstance(r.report_back_timing, date) else r.report_back_timing,
            "assigned_to": r.assigned_to or None,
        } for r in requests],
        "participation": participation_row(ref, item),
    }


# ---------------------------------------------------------------- I/O

def fetch_report_log_xlsx():
    meta = httpx.get(CKAN, params={"id": REPORT_LOG_PACKAGE}, timeout=60, headers=UA).json()["result"]
    url = next(r["url"] for r in meta["resources"] if r["url"].lower().endswith(".xlsx"))
    return httpx.get(url, timeout=180, headers=UA, follow_redirects=True).content


def load(ref):
    from draft_item import load_env
    from supabase import create_client
    load_env()
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

    reviewed = db.table("claims").select("id").eq("item_ref", ref).not_.is_("reviewed_by", "null").execute().data
    if reviewed:
        sys.exit(f"{ref}: {len(reviewed)} claims already reviewed by a person; not overwriting. "
                 "(Changed sources are handled by the re-check job.)")

    out = json.loads((ROOT / "out" / f"{ref}.json").read_text(encoding="utf-8"))
    votes = parse_votes(fetch_vote_records(ref), ref)
    requests = parse_report_log(fetch_report_log_xlsx(), ref)
    rows = build_rows(out, votes, requests)

    # Replace this item's rows. Deleting the item cascades to every child table.
    db.table("items").delete().eq("ref", ref).execute()
    db.table("items").insert(rows["item"]).execute()
    db.table("stages").insert(rows["stages"]).execute()
    ids = [db.table("passages").insert(p).execute().data[0]["id"] for p in rows["passages"]]  # one by one: keeps order
    for c in rows["claims"]:
        i = c.pop("passage_index")
        c["passage_id"] = ids[i] if i is not None else None
    db.table("claims").insert(rows["claims"]).execute()
    if rows["votes"]:
        db.table("votes").insert(rows["votes"]).execute()
    if rows["report_requests"]:
        db.table("report_requests").insert(rows["report_requests"]).execute()
    db.table("participation").insert(rows["participation"]).execute()
    print(f"{ref}: loaded {len(rows['stages'])} stages, {len(ids)} passages, {len(rows['claims'])} claims, "
          f"{len(rows['votes'])} votes, {len(rows['report_requests'])} report requests, "
          f"participation={rows['participation']['status']}")


if __name__ == "__main__":
    load(sys.argv[1])
