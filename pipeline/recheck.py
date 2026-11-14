"""Re-check every item's official page and mark cards whose source has changed.

Each card stores a fingerprint (a hash of the item page's text) taken when it was drafted.
If today's page gives a different fingerprint, the card shows "The official record has
changed since this summary was reviewed" until someone re-drafts and re-reviews it.
Run by hand in this prototype (python recheck.py); a city would schedule it nightly.

Usage: python recheck.py            (reports and updates the database)
       python recheck.py --dry-run  (reports only)
"""
import os
import sys

from civic.fingerprint import fingerprint_item
from civic.tmmis import fetch_item_html


def changed_items(items, fetch_html):
    """items: rows with ref + source_fingerprint. Returns (ref, changed) for each item.
    A page that can't be fetched is reported as None (unknown) and never marks the card."""
    results = []
    for it in items:
        try:
            now = fingerprint_item(fetch_html(it["ref"]))
        except Exception as e:  # network or city site down: don't guess
            print(f"{it['ref']}: could not fetch ({e.__class__.__name__}); left as is")
            results.append((it["ref"], None))
            continue
        results.append((it["ref"], now != it["source_fingerprint"]))
    return results


def main(dry_run=False):
    from draft_item import load_env
    from supabase import create_client
    load_env()
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    items = db.table("items").select("ref,source_fingerprint").eq("has_card", True).execute().data
    for ref, changed in changed_items(items, fetch_item_html):
        if changed is None:
            continue
        print(f"{ref}: {'CHANGED, card marked' if changed else 'unchanged'}")
        if changed and not dry_run:
            db.table("items").update({"source_changed": True}).eq("ref", ref).execute()


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
