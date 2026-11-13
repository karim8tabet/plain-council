from dataclasses import dataclass
from datetime import datetime
import re
import httpx

@dataclass
class Vote:
    body_name: str
    voted_at: datetime
    motion_type: str
    motion_kind: str
    description: str
    result: str
    yes_count: int
    no_count: int
    absent_count: int
    votes_for: int | None
    votes_against: int | None

def parse_votes(records, ref):
    grouped = {}
    for row in records:
        if str(row.get("Agenda Item #", "")).replace(",", ".") != ref.replace(",", "."): continue
        key = tuple(row.get(k, "") for k in ("Date/Time", "Motion Type", "Vote Description", "Result"))
        grouped.setdefault(key, []).append(row)
    result = []
    for (when, motion, desc, outcome), rows in grouped.items():
        dt = None
        for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M %p", "%Y-%m-%d"):
            try: dt = datetime.strptime(str(when), fmt); break
            except ValueError: pass
        if dt is None: continue
        kind = "amendment" if motion.lower().startswith("amend") else ("main_item" if motion.lower().startswith("adopt") else "other")
        member_votes = [str(row.get("Vote", "")).strip().lower() for row in rows]
        score = re.search(r"(\d+)\s*-\s*(\d+)", str(outcome))
        result.append(Vote(rows[0].get("Committee", ""), dt, motion, kind, desc, outcome,
            sum(v == "yes" for v in member_votes), sum(v == "no" for v in member_votes), sum(v == "absent" for v in member_votes),
            int(score.group(1)) if score else None, int(score.group(2)) if score else None))
    return sorted(result, key=lambda v: v.voted_at)

def fetch_vote_records(ref):
    url = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search"
    response = httpx.get(url, params={"resource_id": "55ead013-2331-4686-9895-9e8145b94189", "q": ref, "limit": 2000}, timeout=60, headers={"User-Agent": "plain-council/0.1"})
    response.raise_for_status()
    return response.json()["result"]["records"]
