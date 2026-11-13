# Where we left off

_Last updated: Fri Nov 13, 2026, afternoon ET._ Read this first when resuming. Full plan in `PLAN.md`, tests in `TESTS.md`.

## ⚠ Deadline
Code freeze and Devpost submission: **Sat Nov 14, 2026, 10:00 AM ET.**
- Must-work path done by **Fri 10 PM**.
- No new features after **Sat 6 AM**.

## Done
- Planning, `PLAN.md`, `TESTS.md`.
- README with data sources and credits (versions and audit results).
- `supabase/migrations/001_schema.sql` run in Supabase; every table has row-level security (TESTS D0). Live logged-out tests D1–D3 passed with the new publishable/secret keys.
- `.env` filled (Supabase publishable + secret keys, Groq key). Groq model: `openai/gpt-oss-120b` (llama-3.3-70b is no longer offered). Free tier: 8,000 tokens/minute, 1,000 requests/day.
- Pipeline readers and checks in `pipeline/civic/` (item page, votes, report log, PDF, checks, fingerprint). 31 tests on real fixtures.
- AI drafting: `pipeline/civic/draft.py` (draft → code checks → second AI check) + `pipeline/draft_item.py <ref>` → `pipeline/out/<ref>.json`. Tests use a fake model.

## Waiting on you
- Vercel account.
- Serena: `.serena/project.yml` has `language_servers: []`. Add `python` and `typescript`.

## Next steps
1. Re-run `draft_item.py 2026.EX31.2` (prompt now has plain-language rules; run 1 scored grade 17.7 because it copied legal wording; kept as `out/2026.EX31.2.run1-legal-wording.json` for the docs; `pipeline/out/` is gitignored, decide whether to commit drafts). Run 1 checker caught a real error: sentence 5 invented uncertainty (good demo example).
2. Loader: `out/<ref>.json` + votes + report log → Supabase.
3. Must-work path in the website.
4. Then "Order of work" in `PLAN.md` from step 4.
