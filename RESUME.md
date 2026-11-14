# Where we left off

_Last updated: Sat Nov 14, 2026, early morning ET._ Read this first when resuming. Full plan in `PLAN.md`, tests in `TESTS.md`.

## ⚠ Deadline
Code freeze and Devpost submission: **Sat Nov 14, 2026, 10:00 AM ET.**
- Must-work path done by **Fri 10 PM**. ✅ Done, and live at https://plain-council.vercel.app/ (auto-deploys from `main`).
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
  - Accounts: clerk = Karim's email (needs a strong password); demo = demo@plaincouncil.example (read-only; password goes in README/Devpost). Public sign-ups should be off.
- "What changed between steps" on every card: code-only word-by-word comparison of the official text at each step (`web/lib/redline.ts`, `npm --prefix web test`). Staff recommendations read from the report PDF.
- Repo: private GitHub `karim8tabet/plain-council` (make public before submitting). Residents' names removed from fixtures and all history.
- AI pre-check of all sentences for the human review: `out/review-notes.md` (not committed). Test review clicks were reset; review log is empty.

- All 56 sentences reviewed and published (7 rejected); reading level ~grade 7–10 on the live cards.
- Docs done: `docs/requirements.md`, `docs/architecture.md` (5 UML diagrams), `docs/ai-and-verification.md` (counts), README rewritten. `recheck.py` added.
- Readiness Report: `docs/Readiness-Report.pdf` (1 page; source `docs/readiness-report.html`, export with Edge headless). Video script: `out/video-script.md` (~382 words, ~2:45).

## Waiting on you
- Record the video (script in `out/video-script.md`), keep it under 3:00.
- Devpost: description, live + repo links, demo login password, video, report PDF. Compare the report with the Discord #resources template.
- Make the GitHub repo public. Final commit before 10:00 AM.
- Make sure "Allow new users to sign up" is off in Supabase, and the clerk password is strong.
- Serena: `.serena/project.yml` has `language_servers: []`. Add `python` and `typescript`.

## Next steps (PLAN.md order of work)
1. ✅ Redline. ✅ Deploy.
2. Per-item pipeline counts for the docs (after review).
3. Step 6: poster/QR, French + Chinese, accessibility pass.
4. Step 7: scheduled jobs (GitHub Actions) + "Add item" box.
5. Steps 8–9: docs/UML, Readiness Report, Devpost text, video.
