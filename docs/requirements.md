# Requirements

Plain Council helps Toronto residents understand a proposed council decision, how it could affect them, and when they can have a say. This page lists who it is for, what it must do, and where each requirement is met in the code.

## Users

| User | Needs | How they use it |
|---|---|---|
| **Residents**, especially renters, newcomers, students, seniors, shift workers and people with lower literacy | Find items near them; understand them without council jargon; know whether they can still take part | Public site, no account. Postal code (first 3 characters) or ward list → item card |
| **City clerks / engagement staff** | Publish accurate, neutral summaries without writing them from scratch; a record of who approved what | Staff login → review queue (approve, edit, reject, undo) |
| **Councillors' offices, community groups, journalists** | A shareable, sourced summary of where an item stands | Public card link; every sentence links to its source |
| **Judges / evaluators** | See the review side without changing data | Read-only demo staff account |

## Functional requirements

The first column uses the success criteria from the CIVIC Hack brief.

| # | Requirement | How it is met | Where |
|---|---|---|---|
| F1 | Say **what is proposed and why**, in plain language | AI-drafted sentences grouped as *What is proposed or decided*, *Reasons given in the staff report*, *Conditions, limits and amounts*, *Not yet known*. Target reading level grade 6–8, measured on every card | `pipeline/civic/draft.py`, `web/app/item/[ref]/page.tsx`, `web/lib/reading.ts` |
| F2 | Say **who and where** it affects | Ward(s) or "City-wide" from the official page; a *Who and where it affects* section; postal code → ward lookup | `pipeline/civic/tmmis.py`, `pipeline/build_fsa_wards.py`, `web/app/find/page.tsx` |
| F3 | Show **key dates, and how and when to have a say** | "Can I have a say?" box: *open* only when the official item page links a comment form; *upcoming* when a meeting is scheduled; *decided* otherwise. A deadline is never inferred from a meeting date | `pipeline/load_item.py` (`participation_row`), `web/components/HaveASay.tsx` |
| F4 | Link **every claim to the exact source passage** | Each sentence opens to the quoted source span (shown as it is in the source, not the AI's copy), document, page and date. A sentence whose quote is not in the source is rejected by code | `pipeline/civic/checks.py` (`match_quote`), `web/components/Sentence.tsx` |
| F5 | **Distinguish staff recommendations, committee recommendations and final Council decisions** | Every sentence carries a stage tag ("From the staff report (May 8, 2026)"); the drafting prompt requires attribution; code flags decision words used for a recommendation | `web/lib/labels.ts` (`stageTag`), `checks.check_decision_words` |
| F6 | Show **important amendments and conditions** | "What changed between steps" compares the official wording of each step with the next, part by part and word by word (code only) | `web/lib/redline.ts`, `web/components/WhatChanged.tsx` |
| F7 | Show **where the item is in the process** | One status line at the top; step-by-step timeline with outcomes and recorded votes, each labelled as a vote on an amendment or on the whole item | `web/lib/labels.ts` (`whereItStands`), `web/components/Timeline.tsx`, `pipeline/civic/votes.py` |
| F8 | Show **what happens next** after a decision | "Follow-up work Council asked for" from the Report Request Log, with plain status meanings and their limits | `pipeline/civic/report_log.py` |
| F9 | **Human review before publishing** | Only `approved` sentences are readable by the public (database rule). Staff approve, edit, reject, restore or permanently reject; each action is logged with who and when | `supabase/migrations/001–003`, `web/app/staff/` |
| F10 | **Flag stale summaries** | Each card stores a fingerprint of the item page. `recheck.py` marks cards whose page changed; the card then tells residents to rely on the official page | `pipeline/recheck.py`, `pipeline/civic/fingerprint.py` |
| F11 | A municipal leader can **use it without our team** | Staff screen needs no technical knowledge; demo account; README setup; one script per item | `web/app/staff/`, `README.md` |

## Non-functional requirements

| # | Requirement | How it is met |
|---|---|---|
| N1 | **Accuracy over coverage**: "a summary that mis-states a decision is worse than no summary" | Quote check + second AI check + human review; no sentence is shown until approved; facts like dates, votes and stages come from records, never from AI |
| N2 | **Neutral, non-partisan** | Loaded-word list in code; checker flags non-neutral wording; public submissions are counted, never summarized |
| N3 | **Privacy / data minimization** | No resident accounts; only the first 3 postal code characters are used and never stored; nothing about residents is sent to AI; names of people who wrote in or spoke are never stored or shown (even removed from test files and git history) |
| N4 | **Accessibility** | Mobile-first layout; semantic headings; changes marked with words and screen-reader text, not colour alone; light and dark themes; reading level shown |
| N5 | **Security** | Database row-level security; the public key can only read published content; database trigger stops anyone changing a sentence's source quote; AI and admin keys live only in the pipeline's `.env`, never in the website or git |
| N6 | **Low cost** | Free tiers (Groq, Supabase, Vercel). AI runs once per item, offline, not per visitor |
| N7 | **Adaptable** | City-specific code is in one reader (`civic/tmmis.py`); the rest works with any council system that publishes items, stages and documents |

## Constraints (from the brief)

- Verify participation info on the official item page; **never infer a submission deadline from a meeting date**.
- Show the **source and date** for each explanation.
- Preserve important **conditions and uncertainty**.
- No unnecessary personal information from public correspondence.

## Out of scope for this prototype

- Translation (French, Simplified Chinese) and a printable community poster were planned but cut for time.
- Scheduled jobs: re-check and new-item processing are run by hand (`recheck.py`, `draft_item.py`, `load_item.py`); the database tables `requests` and `job_runs` are reserved for them.
- Alerts / subscriptions (would need contact details, which conflicts with N3 for a prototype).
- A live AI question-and-answer box.
