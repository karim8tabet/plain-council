# Plain Council

Toronto council decisions in plain language: what's proposed and why, who and where it affects, where it is in the process, and whether you can still have a say. Every sentence links to the exact passage in the official record it came from, and a person approves every sentence before it is shown.

Built for **CIVIC Hack 2026** (Future Cities Institute, University of Waterloo). Challenge: *Making municipal decisions easier to understand*.

- **Live prototype:** https://plain-council.vercel.app/
- **Staff review screen:** https://plain-council.vercel.app/staff
- **Read-only demo login:** `demo@plaincouncil.example` · password: _given on the Devpost page_

  The demo account can open everything a clerk sees but can't change anything.

## What a resident sees

- **Find items by area.** Enter the first 3 characters of a postal code, or pick a ward.
  - If the area crosses ward lines, the site asks which ward is yours.
  - Nothing is stored.
- **Decision card** for each item:
  - **Status line**, for example: "Decided by City Council on May 21, 2026, with changes to what was recommended."
  - **Can I have a say?**
    - "Open" only when the City's item page links a comment form.
    - A deadline is shown only if the City's page states it; it is never guessed from a meeting date.
  - **In plain language:**
    - Short sentences, each tagged with its step: staff report, committee recommendation, or City Council decision.
    - Tap a sentence to see the exact source words, the document, the page and the date.
  - **What changed between steps:** the official wording of each step compared with the next, word by word, marked with words and not only colour.
  - **How it got here, step by step:**
    - Each step's outcome and its recorded votes, each labelled as a vote on an amendment or on the whole item.
    - The number of written submissions. They are counted, never summarized or named.
  - **Follow-up work Council asked for,** from the City's Report Request Log.
  - The card's **reading level**, and the date a person checked it.

## How it works

1. **Read the record (code, no AI).** The pipeline reads each item's official page and staff report PDF:
   - steps, dates, outcomes and decision text
   - wards and submission counts
   - the participation form
   - votes (Toronto Open Data)
   - follow-up requests (Report Request Log)
2. **Draft (AI).** OpenAI gpt-oss-120b on Groq drafts plain sentences, one step at a time. Each sentence must carry a quote from that step's source.
3. **Check (code, then a second AI call).**
   - Code rejects any sentence whose quote isn't in the source.
   - It flags dates not found in the quote, deadline words, decision words on a recommendation, and loaded words, and measures reading level.
   - A second AI call checks each sentence against its quote.
4. **Review (a person).**
   - A clerk approves, edits or rejects each sentence. The database records who and when.
   - The public can only read approved sentences, and the source quote can never be edited.
5. **Watch for changes.** `recheck.py` compares each item page with the version that was summarized. If it changed, the card tells residents to rely on the official page until it is checked again.

More detail:
- [Requirements](docs/requirements.md)
- [Architecture and UML](docs/architecture.md)
- [AI's role and how outputs were checked (with counts)](docs/ai-and-verification.md)

## Items with full cards

| Item | What | Stage (Nov 13, 2026) |
|---|---|---|
| [2026.EX31.2](https://secure.toronto.ca/council/agenda-item.do?item=2026.EX31.2) | Standardizing the Air Conditioner Benefit (Pilot) | Decided May 21, 2026. Amended at committee and at Council |
| [2026.TE32.46](https://secure.toronto.ca/council/agenda-item.do?item=2026.TE32.46) | Pedestrianizing Church Street Pilot | Decided May 21, 2026. Council added a cancellation power |
| [2027.PB1.6](https://secure.toronto.ca/council/agenda-item.do?item=2027.PB1.6) | 1337 Queen Street West: heritage permit for demolition and a new 16-storey building | Upcoming: Toronto Preservation Board, Nov 16, 2026. Comments open via the City's form |

## Repository layout

| Folder | What's in it |
|---|---|
| `pipeline/` | Python: reads City records, drafts and checks sentences, loads the database, re-checks sources, builds the postal-area → ward table |
| `pipeline/civic/` | The parts: `tmmis.py` (item page reader), `pdf.py`, `votes.py`, `report_log.py`, `draft.py` (AI drafting and second check), `checks.py` (code checks), `fingerprint.py` |
| `pipeline/tests/` | 56 tests, with saved City pages as fixtures (names of members of the public removed) |
| `web/` | Next.js website: resident pages and the staff review screen |
| `web/lib/redline.ts` | The "What changed between steps" comparison (tests in `web/tests/`) |
| `supabase/migrations/` | Database tables, security rules and the review audit trigger (run in order) |
| `docs/` | Requirements, architecture and UML, AI's role and verification |
| `PLAN.md`, `TESTS.md` | Build plan and decisions; test checklist with results |

## Setup

You need Python 3.12+ (built with 3.14), Node.js 20+ (built with 24), a free [Supabase](https://supabase.com) project and a free [Groq](https://console.groq.com) API key.

**1. Database.** In the Supabase SQL editor, run these in order:
- `supabase/migrations/001_schema.sql`
- `002_review_audit.sql`
- `003_permanent_reject.sql`

Then, under Authentication → Sign In / Providers, turn off "Allow new users to sign up". Staff accounts are created by an administrator.

**2. Keys.** Copy `.env.example` to `.env` and fill it in:
- the Supabase URL and **secret** key, for the pipeline only
- the Groq key

`.env` is git-ignored. Never put the secret or Groq key in the website.

**3. Pipeline.**
```bash
python -m venv .venv
.venv/Scripts/pip install -r pipeline/requirements.txt      # macOS/Linux: .venv/bin/pip
cd pipeline
../.venv/Scripts/python -m pytest -q                       # 56 tests
../.venv/Scripts/python draft_item.py 2026.EX31.2          # read + draft + check -> out/2026.EX31.2.json
../.venv/Scripts/python load_item.py 2026.EX31.2           # load into the database as "unreviewed"
../.venv/Scripts/python recheck.py --dry-run               # has any item page changed?
```
`load_item.py` refuses to overwrite an item once anyone has reviewed it.

**4. Staff accounts.**
1. Create the user in Supabase → Authentication → Users.
2. Give them a role:
```bash
../.venv/Scripts/python set_staff.py person@example.org clerk   # or: demo (read-only)
```

**5. Website.**
1. Create `web/.env.local` with two public values:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` (the **publishable** key)
2. Run:
```bash
cd web
npm install
npm test          # "What changed" comparison tests
npm run dev       # http://localhost:3000
```

**Deploy (Vercel):**
1. Import the GitHub repo and set the root directory to `web`.
2. Add the same two environment variables.
3. Every push to `main` redeploys.

**Postal area → ward table** (only if ward boundaries change):
1. Download the two boundary files listed under Data sources into `pipeline/cache/geo/`.
2. Run `python build_fsa_wards.py`. It writes `web/lib/fsa-wards.json`.

## Data sources

All data is public. Dates show when each source was checked or downloaded.

| Source | Used for | Checked |
|---|---|---|
| [City of Toronto meeting site (TMMIS)](https://secure.toronto.ca/council/) | Item pages, steps, decisions, staff reports, submission counts, comment forms | Nov 13, 2026 |
| [Members of Toronto City Council: Voting Record](https://open.toronto.ca/dataset/members-of-toronto-city-council-voting-record/) | Recorded votes (amendment vs. whole item) | Refreshed by the City Nov 7, 2026 |
| [Report Request Log: City Council and its Committees](https://open.toronto.ca/dataset/report-request-log-city-council-and-its-committees/) | Follow-up work Council asked for | Refreshed by the City Aug 26, 2026 |
| Toronto ward boundaries (Toronto Open Data, "City Wards", 25-ward model, `city-wards-data-4326.geojson`) | Postal area → ward | Downloaded Nov 13, 2026 |
| 2021 Census forward sortation area boundaries (Statistics Canada, `lfsa000b21a_e`, cartographic). Statistics Canada Open Licence; postal-code geography © Canada Post | Postal area → ward (96 Toronto areas; 48 cross ward lines) | Downloaded Nov 13, 2026 |

Toronto data is used under the Open Government Licence – Toronto.

## Assumptions and limitations

- **One reviewer.** The reviewer of the published cards was the developer, not an independent clerk. An AI assistant pre-checked the sentences first. See [how the review was done](docs/ai-and-verification.md#how-the-human-review-was-done-stated-plainly).
- **Omissions.** Checks compare each sentence with its own quote. They can't prove the card covers everything important. "What changed between steps" shows amendments in the official wording to cover that gap.
- **Votes.** The Voting Record contains **recorded votes only**, and not every decision has one.
- **Follow-up requests.** A "closed" report request doesn't prove the wider commitment was delivered; the card says so.
- **Public submissions** are counted, never summarized, to avoid exposing personal information and to avoid bias. So residents don't see what others argued.
- **Postal code → ward is approximate.** One postal area can cross several wards, so the resident picks one. The City's address-based ward finder is linked.
- **Reading level** is a formula (Flesch–Kincaid). Official names are kept on purpose, even though they raise the grade.
- **Run by hand.** Drafting, loading and re-checking are run by hand in this prototype; scheduled jobs are designed for, not built.
- **Cut for time:** translation (French, Simplified Chinese), a printable community poster, and an "Add item" box for staff.
- **Toronto only.** Only the item page reader and Report Request Log reader are Toronto-specific. See [Scaling and adapting](docs/architecture.md#7-scaling-and-adapting).

## Credits

### AI assistance
- **Claude Code** (Anthropic, Claude Opus 5.5):
  - planning, most of the code, docs and tests
  - a pre-check of drafted sentences before human review (suggestions only; a person decided)
- **Codex** (OpenAI, through the Codex plugin for Claude Code): the first version of the pipeline readers and checks, from a written spec. Claude Code reviewed and corrected it (`.claude/handoff-log.md`).
- **Groq** running **OpenAI gpt-oss-120b** (open-weight model; set by `GROQ_MODEL`; checked available Nov 13, 2026): runs inside the product to draft card sentences and check them against their sources.

### Open-source libraries
**Pipeline (Python):**
- httpx (downloads pages)
- beautifulsoup4 (reads item pages)
- pdfplumber (PDF text with page numbers)
- RapidFuzz (quote matching)
- textstat (reading level)
- groq (Groq client)
- supabase (database client)
- openpyxl (Report Request Log spreadsheet)
- shapely (postal area × ward overlap)
- numpy
- pyshp 3.1.8 (Statistics Canada shapefile)
- pyproj 3.8.0 (map projections)
- pytest (tests)
- pip-audit (security check)

**Website:**
- Next.js 16.4.6
- React 19.3.0
- Tailwind CSS 4.3.3
- @supabase/supabase-js 2.119 and @supabase/ssr 0.12 (data and staff login)
- TypeScript, ESLint

**Security check (Nov 13, 2026):**
- pip-audit: no known vulnerabilities.
- npm audit: 0 vulnerabilities in what ships to the site.
- 7 moderate advisories in development-only ESLint dependencies.

### Datasets
See **Data sources** above.
