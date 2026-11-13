# Where we left off

_Last updated: Fri Nov 13, 2026, 4:20 PM ET._ Read this first when resuming. Full plan in `PLAN.md`, tests in `TESTS.md`.

## ⚠ Deadline
Code freeze and Devpost submission: **Sat Nov 14, 2026, 10:00 AM ET.**
- Must-work path done by **Fri 10 PM**. ✅ Done Fri 4:20 PM (local; not yet deployed).
- No new features after **Sat 6 AM**.

## Done
- Supabase: migrations 001 (schema + row-level security), 002 (database stamps who reviewed what; source quotes can't be edited), 003 (permanent reject, locked by the database) all run and checked live.
- Keys in `.env` (publishable + secret Supabase keys, Groq). `web/.env.local` has only the two public values.
- Groq model `openai/gpt-oss-120b`, reasoning effort low (medium returned empty answers). Free tier 8K tokens/min.
- Pipeline (`pipeline/`, 52 tests): item page reader, votes, report log, PDF, checks (quote match incl. "..." pieces, dates, decision words, loaded words), drafting + second AI check, loader, postal-area → ward lookup.
- All 3 items drafted and loaded: EX31.2 (29: 25 clean, 3 flagged, 1 code-rejected), TE32.46 (9 clean), PB1.6 (25: 7 flagged).
  - Prompt history for the docs: run 1 copied legal wording (grade 17.7, `out/2026.EX31.2.run1-legal-wording.json`); run 2 grade 11.5; checker false positives on committee text fixed by labelling who said each source.
- Website (`web/`, Next.js 16 with Cache Components): home + postal code (3 chars only), ward list, Decision Card (status line, have-a-say, plain sentences with stage tags and tap-to-source, steps with votes, submission counts, follow-up report requests), about page.
- Staff: login (Supabase Auth), review queue with tabs To review / Published / Rejected, edit, undo, permanent reject, demo account read-only.
  - Accounts: clerk = Karim's email; demo = an old test account (since deleted) (password to be put in README/Devpost). Change any weak password before deploying.

## Waiting on you
- Review sentences for all 3 items in /staff (this is the "human review" evidence).
- Vercel account (for deploy).
- Serena: `.serena/project.yml` has `language_servers: []`. Add `python` and `typescript`.

## Next steps (PLAN.md order of work)
1. Step 4: "What changed" redline (staff → committee → Council), per-item pipeline counts for the docs.
2. Deploy to Vercel (needs account) and test from a fresh browser.
3. Step 6: poster/QR, French + Chinese, accessibility pass.
4. Step 7: scheduled jobs (GitHub Actions) + "Add item" box.
5. Steps 8–9: docs/UML, Readiness Report, Devpost text, video.
