# Where we left off

_Last updated: Fri Nov 13, 2026, 1:25 PM ET._ Read this first when resuming. Full plan in `PLAN.md`, tests in `TESTS.md`.

## ⚠ Deadline
Code freeze and Devpost submission: **Sat Nov 14, 2026, 10:00 AM ET.**
- Must-work path done by **Fri 10 PM**.
- No new features after **Sat 6 AM**.

## Done
- Planning, `PLAN.md`, `TESTS.md`.
- README with data sources and credits (versions and audit results).
- `supabase/migrations/001_schema.sql`: tables plus row-level security.
- Python packages installed in `.venv/` (pip-audit clean).
- Next.js site created in `web/`, plus Supabase, qrcode and ics packages (npm audit clean for production).

## Waiting on you
- Create Groq, Supabase and Vercel accounts.
- Copy `.env.example` to `.env` and fill it in.
- Run `001_schema.sql` in the Supabase SQL editor.
- Serena: `.serena/project.yml` has `language_servers: []`. Add `python` and `typescript`.

## Next steps
1. Pipeline: city page reader + Voting Record + Report Request Log for Church St (no keys needed).
2. Groq drafting + checks (needs `GROQ_API_KEY`).
3. Load into Supabase (needs Supabase keys).
4. Must-work path in the website.
5. Then "Order of work" in `PLAN.md` from step 4.
