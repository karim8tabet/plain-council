# CIVIC Hack 2026: Build Plan v2 (solo)

## Context
Challenge: help Toronto residents understand a proposed council decision, whether it affects them, and when/how to have a say. Judges are municipal leaders who want something a city could pilot **without our team**. Deadline **Sat Nov 14, 10:00 AM ET** (code freeze). About 20 working hours remain. v2 folds in an outside review and a judge-style critique.

## The product in one line
For each council item, code reads the official records, AI drafts a plain-language **Decision Card** with every sentence tied to its source and stage, code and a second AI check it (accuracy and neutrality), a clerk approves it, and residents find it by ward, see exactly what changed at each stage, and learn how to take part, on screen or on a poster.

## Decisions
| Topic | Choice | Why |
|---|---|---|
| Full-card items | **2026.TE32.46** Church St pilot (decided, amended at Council) · **2026.EX31.2** Air Conditioner Benefit (amended twice, report-back requested) · **2027.PB1.6** 1337 Queen St W (upcoming, Nov 16; note the **2027** prefix used by the new term) | Mix of stages and types. PB1.6 is live and verified (see Findings), so no backup item is needed |
| Other items | Titles, wards and status of **every item** from recent meetings, loaded by code (no AI) | Makes the ward list real and shows the tool scales. These items show "Plain-language card not available yet" and link to the official page |
| Product AI | **Groq** free tier, model name in one setting | Free, swappable. Only public documents are sent to it, never resident data |
| Build tool | Claude Code (credited) | |
| Data + staff login | **Supabase** (Postgres + Auth + **row-level security**) | Many items, many staff, audit trail. The public can read approved content only |
| Website | Next.js on **Vercel** | |
| Scheduled jobs | GitHub Actions (cron) | Processes new-item requests and re-checks sources, so no one has to run scripts |
| Languages | French (reviewed) + Simplified Chinese (labelled "machine-translated, not reviewed", with a per-sentence "show English original") | Covers both the official language and the newcomers the brief names. The trade-off is explained in the report |
| Cut | AI helper (only if time is left) and the map-based ward picker | Scope |

## Findings from checks (Nov 13, 2026)
- **2027.PB1.6 is live.** Staff report dated Oct 28, 2026 ([PDF](https://www.toronto.ca/legdocs/mmis/2027/pb/bgrd/backgroundfile-290746.pdf)).
  - Recommends approving demolition of a non-contributing building and a new **16-storey mixed-use building with purpose-built affordable housing**, City-owned (West Block of the **Parkdale Hub**), with one condition: built substantially per the LGA Architectural Partners plans of Sept 25, 2026.
  - A heritage permit was already approved by Council on **June 24–25, 2026**. It's needed again because the podium is now 1.2 m taller and lacks the 5.0 m step-back the district plan requires. Staff say this doesn't harm the district.
  - **Participation is verified:** the item page has an official **"Submit Comments"** form. **No deadline is stated** (so we show none).
  - The city's notice says the **commenter's name becomes public record and appears online**. The card must warn residents of this before they click.
  - The next stage after the Board isn't stated, so it's shown as "not yet stated".
- **Voting Record** (refreshed Nov 7, 2026; datastore resource `55ead013-2331-4686-9895-9e8145b94189`, searchable by API, no download needed) has both items:
  - **EX31.2, Council May 21:** Matlow amendment 1 **lost 8–16**; Bravo amendment 2a carried 23–1; Bravo amendment 2b carried 23–1; adopted as amended 23–1.
  - **TE32.46:** Community Council Apr 30, adopted 6–0. Council May 21: Bradford amendment 1 carried 16–8; adopted as amended 20–4.
  - The `Motion Type` field already says whether a vote was on an amendment or the main item.
  - **Data quirk:** one record says "TE32,46" (comma), so item matching must normalize.
- **Report Request Log** (XLSX, refreshed Aug 26, 2026; `Status` / `Closed by` / `Report Back Timing` columns; dates are Excel serial numbers):
  - EX31.2 Part 6 (heat by-law framework, report to June 2026 Council) is **"closed" by 2026.CC42.12** (June 23, 2026).
  - 2026.CC42.12 then asked the City Manager for a **maximum indoor temperature by-law by June 2027**, status **"Not Carried Forward"**. Per the log's glossary, outstanding requests aren't carried into the next term's log.
  - **Card wording must be careful:** "Council asked for a by-law by June 2027. The Clerk's log lists this request as 'not carried forward' to the new term's log. That alone doesn't say whether the report will happen." This matches the brief's warning that "closed" doesn't prove delivery.
- **Other upcoming meetings:** Toronto and East York Community Council (Nov 25) and Planning and Housing (Nov 26) haven't published agendas yet.

## Rules the product enforces (map these to the brief)
1. **Stage tag on every sentence:** "From the staff report (May 8)" / "From the Executive Committee decision (May 12)" / "From the Council decision (May 21)".
2. **"Reasons given in the staff report"**, never a bare "Why". Public submissions are counted, never summarized (privacy and bias), and this is listed as a limitation.
3. **Participation status.** "Upcoming meeting" when an item is on a future agenda. "Open for input" **only** when the item page, or the city's official participation page (cited and linked), states how to take part. A deadline appears only if quoted from the official page. The calendar file (.ics) is offered for the **meeting** (a verified fact), and for a deadline only if one is quoted.
4. **Source quotes shown as they appear in the source**, never the AI's copy. Matching is loose (normalize spaces, hyphens and quote marks, then ≥95% similarity), but what's displayed is the source span.
5. **Stale-source detection.** Each source page's fingerprint is stored. If it changes, the card shows "Source updated since last review" until a clerk re-approves it.
6. **Votes shown precisely.** From the Voting Record (or the item page if the dataset lags): "Council vote on amendment 2: carried 19–5", always saying whether a vote was on an **amendment** or the **main item**.
7. **Neutral language.** A word list in code plus the checker's instruction flag loaded words ("controversial", "finally", "only", "massive"…).
8. **Reading level** scored per card (target Grade 6–8), shown on the card and in the staff screen.

## What gets built
**A. Pipeline (Python; run by a scheduled job, can also be run by hand)**
- Source adapter for Toronto's meeting system (swappable for eSCRIBE/Granicus later): item page → stages, dates, staff recommendations, committee decision, Council decision text, ward, communications count, PDFs.
- Item list loader: every item of recent meetings (titles, wards, status only).
- Groq drafts plain sentences from the PDFs, each with a quote and a stage. Code checks: loose quote match, no dates/deadlines, decision words match the decision section, neutral word list, reading level. A second Groq call checks: supported / not supported / missing condition / loaded language.
- **Redline:** paragraph-by-paragraph comparison of staff recommendations → committee decision → Council decision (code, no AI), plus one AI-drafted, checked plain sentence per change.
- Translation of approved sentences (French, Chinese).
- Fingerprint every source. Save everything as "unreviewed".

**B. Staff side (login)**
- Review queue: sentence, stage tag, source quote, flags. Approve / Edit / Reject, recording who and when.
- **"Add item" box** (paste `2026.XX.N`) creates a request the scheduled job processes.
- "Source updated" queue for re-review.
- **Read-only demo clerk login** for judges (README + Devpost).

**C. Resident side (no login, mobile-first, WCAG basics)**
- Postal code → candidate wards (precomputed from the postal code's first 3 characters) → pick from a short list, plus a link to the city's official ward finder. Nothing stored.
- Ward list: all real items with status badges. Full cards for the chosen items.
- **Decision Card:** plain sentences with stage tags and tap-to-source; who/where; conditions and uncertainty; **"What changed" redline** (additions and removals marked with text labels, not colour alone); timeline with votes; public input counts next to the changes (no claim that one caused the other); **"What happens next"** from the Report Request Log; "Can I have a say?" following rule 3; calendar file; reading level; "checked on" date; French/Chinese toggle.
- **Community poster:** one page, large text, QR code, for libraries, tenant associations and laundromats.

## Order of work
**Hard rule:** if the must-work path isn't done by **Fri 6 PM**, everything after it is cut.

1. ~~Checks that could change the plan~~: **done** (see Findings).
2. Setup: repo, README with credits, Supabase tables (`items`, `stages`, `passages`, `claims`, `votes`, `reviews`, `requests`, `sources`) with **row-level security** and a logged-out read test. (~1.5h)
3. **Must-work path, end to end:** postal code → ward list → Church St card with stage tags → tap a footnote → timeline with votes → staff review catching one real flagged sentence. (~7h)
4. EX31.2 + redline, public input counts, "What happens next". (~3h)
5. Backup upcoming item + PB1.6 (if live); participation rule; calendar file. (~1.5h)
6. Poster/QR, reading level, French, Chinese, accessibility pass, deploy. (~2h)
7. Scheduled jobs: request processing + source re-check; "Add item" box; demo clerk login. (~1.5h)
8. Docs: requirements, UML (components, sequence, deployment), architecture rationale, AI role, **counts** of corrections (reviewer = developer, stated), limitations, what was run by hand. (~1.5h)
9. Readiness Report (incl. paid-tier cost, "no resident data sent to AI", how to adapt to other cities), Devpost text, pre-recorded video (no staged errors). Test with 1–2 real people. (~3h)
10. Final commit before 10:00 AM Sat. AI helper only if everything above is done.

## Things you do yourself
- Create Groq, Supabase and Vercel accounts and add keys to `.env` / GitHub secrets.
- Review sentences in the staff screen.
- Record the video.

## Setup notes
- Project folder: `C:\Users\Karim\OneDrive\Desktop\karim\civic-hack`, git, commit often.
- Dependencies (confirm each before installing): Next.js, @supabase/supabase-js, pdfplumber, groq, supabase-py, rapidfuzz (loose matching), textstat (reading level), a QR library, ics (calendar file). Run npm audit / pip-audit after.
- Serena: Python + TypeScript; onboarding in Codex.

## Verification
- Tests:
  - quote matcher (normalized pass, wrong quote fail)
  - no deadline unless quoted from the official page
  - "Open for input" only with a stated method
  - logged-out users can read approved sentences only, and not drafts
  - vote labelled amendment vs main item
  - stale fingerprint flags the card
  - postal code → candidate wards
  - neutral word list
- Per-item pipeline report: drafted / rejected by code / flagged by checker / corrected by reviewer.
- Manual:
  - each card read against its sources for accuracy and neutrality
  - phone width, print and poster preview
  - redline readable without colour
  - Lighthouse accessibility ≥ 90
  - demo login works from a fresh browser
