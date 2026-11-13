# Plain Council

Toronto council decisions in plain language: what's proposed and why, who and where it affects, what stage it's at, and how to have a say. Every sentence links to the exact passage in the official record it came from.

Built for **CIVIC Hack 2026** (Future Cities Institute, University of Waterloo), challenge: *Making municipal decisions easier to understand*.

> Status: in development. Sections marked _TODO_ get filled in as the build progresses.

## How it works

1. **Read the record (code, no AI).** The pipeline reads each item's official page on Toronto's council site: stages, dates, staff recommendations, committee and Council decision text, ward, count of public submissions, and the staff report PDFs.
2. **Draft (AI).** An open model on Groq drafts plain-language sentences from the documents. Each sentence comes with a quote and the stage it comes from.
3. **Check (code + a second AI call).**
   - Code checks that every quote really appears in the source, that no dates or deadlines appear in AI text, that decision words match the actual decision, that no loaded words are used, and the reading level.
   - A second AI call checks whether each sentence is supported by its quote.
4. **Review (a person).** A clerk approves, edits or rejects sentences in the staff screen. Only approved sentences are published.
5. **Publish.** Residents find items by postal code. Each card shows stage-tagged sentences with tap-to-source, a "what changed" comparison across stages, recorded votes, public input counts, what happens next, and how to take part. It also has a printable community poster, French, and Simplified Chinese (labelled as not reviewed).

## Repository layout

| Folder | What's in it |
|---|---|
| `pipeline/` | Python: reads city records, drafts and checks sentences, loads the database |
| `web/` | Next.js website: resident pages and the staff review screen |
| `supabase/migrations/` | Database tables and security rules |
| `.github/workflows/` | Scheduled jobs: process new-item requests, re-check sources |
| `docs/` | Requirements, UML diagrams, architecture rationale, AI role and limits |
| `PLAN.md` | Build plan and decisions |
| `TESTS.md` | Final test checklist with expected results |

## Setup

_TODO: filled in as each part is built._

1. Copy `.env.example` to `.env` and add your Supabase and Groq keys.
2. Apply `supabase/migrations/*.sql` in the Supabase SQL editor (or with the Supabase CLI).
3. Pipeline: _TODO_
4. Website: _TODO_

**Demo staff login (read-only):** _TODO_

## Data sources

All data is public. Dates show when each source was checked.

| Source | Used for | Checked |
|---|---|---|
| [City of Toronto meeting site (TMMIS)](https://secure.toronto.ca/council/) | Item pages, stages, decisions, staff reports, communications counts, participation forms | Nov 13, 2026 |
| [Members of Toronto City Council: Voting Record](https://open.toronto.ca/dataset/members-of-toronto-city-council-voting-record/) | Recorded votes (amendment vs. main item) | Refreshed by the city Nov 7, 2026 |
| [Report Request Log: City Council and its Committees](https://open.toronto.ca/dataset/report-request-log-city-council-and-its-committees/) | "What happens next" (report-back requests) | Refreshed by the city Aug 26, 2026 |
| Toronto ward boundaries (Toronto Open Data, "City Wards", 25-ward model, `city-wards-data-4326.geojson`) | Postal code → ward | Downloaded Nov 13, 2026 |
| 2021 Census forward sortation area boundaries (Statistics Canada, `lfsa000b21a_e`, cartographic). Used under the Statistics Canada Open Licence; postal-code geography © Canada Post | Postal code → ward (96 Toronto areas; 48 cross ward lines) | Downloaded Nov 13, 2026 |

### Items with full cards
- `2026.TE32.46`: Pedestrianizing Church Street Pilot (decided, amended at Council)
- `2026.EX31.2`: Standardizing the Air Conditioner Benefit (Pilot) (decided, amended at committee and at Council)
- `2027.PB1.6`: 1337 Queen Street West, demolition and new construction on a heritage property (upcoming, Nov 16, 2026)

## Assumptions and limitations

_TODO: kept up to date during the build._

- The Voting Record contains **recorded votes only**. Not every decision has one.
- A "closed" report request in the Report Request Log doesn't prove the wider commitment was delivered.
- Public submissions are **counted, never summarized**, to avoid exposing personal information and to avoid bias.
- Postal code → ward is approximate: one postal area can span several wards, so the user picks from a short list.
- Accuracy figures come from review by the developer, not an independent reviewer.

## Credits

### AI assistance
- **Claude Code** (Anthropic, model Claude Opus 5.5): planning, code generation and review.
- **Codex** (OpenAI): code generation for well-defined, test-checked parts. _TODO: model and which parts._
- **Groq** running **OpenAI gpt-oss-120b** (open-weight model; set by `GROQ_MODEL`, checked available Nov 13, 2026): runs inside the product to draft, check and translate card text.

### Open-source libraries
**Pipeline (Python 3.14):**
- httpx 0.28.1 (downloads pages)
- beautifulsoup4 4.15.0 (reads item pages)
- pdfplumber 0.11.10 (PDF text with page numbers)
- RapidFuzz 3.14.6 (quote matching)
- textstat 0.7.13 (reading level)
- groq 1.7.0 (Groq client)
- supabase 2.34.1 (database client)
- openpyxl 3.1.5 (Report Request Log spreadsheet)
- shapely 2.2.0 (postal area × ward overlap)
- pyshp 3.1.8 (reads the Statistics Canada shapefile)
- pyproj 3.8.0 (converts map projections so the two boundary files line up)
- pytest 9.2.0 (tests)
- pip-audit (security check)

**Website:**
- Next.js 16.4.6
- React 19.3.0
- Tailwind CSS 4.3.3
- @supabase/supabase-js 2.119.0 + @supabase/ssr 0.12.7 (data and staff login)
- qrcode 1.5.4 (poster QR code)
- ics 3.12.1 (calendar files)
- TypeScript, ESLint

**Security check (Nov 13, 2026):**
- pip-audit: no known vulnerabilities.
- npm audit (production): 0 vulnerabilities.
- 7 moderate advisories in development-only ESLint dependencies. They don't ship to the site.

### Datasets
See **Data sources** above. Open Government Licence – Toronto.
