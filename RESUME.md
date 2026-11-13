# Where we left off

_Last updated: Fri Nov 13, 2026._ Read this first when resuming. Full plan in `PLAN.md`, tests in `TESTS.md`.

## ⚠ Deadline
Code freeze and Devpost submission: **Sat Nov 14, 2026, 10:00 AM ET.** Nothing counts after that.

## Done
- Planning finished. All decisions and verified findings are in `PLAN.md`.
- `TESTS.md`: final test checklist with expected results.
- Repo set up and committed:
  - README skeleton
  - `.env.example`, `.gitignore`
  - `supabase/migrations/001_schema.sql`: all tables plus row-level security
- `pipeline/requirements.txt` written.

## In progress (stopped on purpose, safe to redo)
- Python package install into `.venv/`. It was stopped mid-way, so delete `.venv` and run it again:

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt pip-audit
.\.venv\Scripts\pip-audit.exe
```

## Next steps, in order
1. Finish the Python install (above), run `pip-audit`, report high/critical issues.
2. Create the Next.js site in `web/`, add `@supabase/supabase-js`, `@supabase/ssr`, `qrcode`, `ics`, run `npm audit`.
3. You: create Groq, Supabase and Vercel accounts, fill `.env`, run `001_schema.sql` in the Supabase SQL editor.
4. Build the **must-work path** end to end: postal code → ward list → Church St card with stage tags → tap a footnote → timeline with votes → staff review catching a real flagged sentence.
5. Then follow "Order of work" in `PLAN.md` from step 4 on.

## Hand-offs to Codex (test-checkable pieces)
- Quote matcher, neutral words, date ban, reading level (tests C1–C11)
- Postal code → ward (F1–F5)
- City page reader + item list loader (P1–P17)
- Redline comparison, calendar file (K8, K14–K15)
