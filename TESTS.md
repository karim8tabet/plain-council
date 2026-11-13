# CIVIC Hack 2026: Final Test Checklist

Run everything here before the final commit (Sat Nov 14, before 10:00 AM ET).
Mark each row ✅ pass / ❌ fail / ⏭ skipped (say why). If a test fails and you can't fix it, list it under **Known limitations** in the README. Don't delete it.

**Kinds of test:**
- **Auto:** automated test in the repo. `pytest` for Python, and `npm test` / Playwright for the website.
- **Manual:** done by hand, following the steps.
- **Check:** inspect a page, file or setting.

---

## 1. Pipeline: reading the city's records

| ID | Kind | Test | Expected result |
|---|---|---|---|
| P1 | Auto | Fetch item page `2026.TE32.46` | HTTP 200. Title "Pedestrianizing Church Street Pilot". Ward 13. Status "Amended" |
| P2 | Auto | Read the stages of `2026.TE32.46` | 2 stages: Toronto and East York Community Council, Apr 30 2026 (adopted without amendment); City Council, May 20–21 2026 (adopted with amendments) |
| P3 | Auto | Read the stages of `2026.EX31.2` | 3 stages: staff report May 8 2026, Executive Committee May 12 2026 (amended), City Council May 20–21 2026 (amended) |
| P4 | Auto | Extract the City Council decision text of `2026.TE32.46` | 4 numbered parts. Part 1 contains "between Wellesley Street East and Alexander Street" and "June 19, 2026 to August 21, 2026" |
| P5 | Auto | Count communications on `2026.TE32.46` | A number > 0, stored. **No names stored** |
| P6 | Auto | Download and parse the EX31.2 staff report PDF | Text not empty. Every passage has a page number ≥ 1 |
| P7 | Auto | Parse a PDF with hyphenated line breaks (fixture) | "trans-\nportation" becomes "transportation" in normalized text. The original text is kept for display |
| P8 | Auto | Item that doesn't exist (`2026.XX99.99`) | Pipeline logs "item not found", stops cleanly, and writes nothing to the database |
| P9 | Auto | Load all items from a recent meeting (e.g. `2026.CC41`) | Every item saved with title, ward, status. `has_card = false` for items without a full card |
| P10 | Auto | Run the pipeline twice on the same item | Second run creates **no duplicates**. Same fingerprint, so nothing is re-drafted |
| P11 | Auto | Source page changed (fixture with edited text) | New fingerprint. Card marked `source_changed = true`. Approved sentences return to the "needs re-review" queue |
| P12 | Auto | Upcoming item whose page isn't published (fixture) | Saved as "Upcoming meeting" with the date from the agenda. Participation method = "not yet stated". No crash |
| P13 | Auto | Item `2027.PB1.6` | Ward 4. Meeting Nov 16, 2026. "Submit Comments" detected, so participation method = online comment form (linked). Deadline = none |
| P14 | Auto | Voting Record for `2026.EX31.2` | 4 Council votes on May 21: Matlow motion 1 **Lost 8–16** (amendment), Bravo 2a Carried 23–1 (amendment), Bravo 2b Carried 23–1 (amendment), adopt as amended Carried 23–1 (main item) |
| P15 | Auto | Voting Record for `2026.TE32.46`, including the "TE32,46" typo record | 3 votes found: Apr 30 adopt 6–0, Bradford motion 1 Carried 16–8 (amendment), adopt as amended Carried 20–4 (main item). The comma-typo record **is matched** |
| P16 | Auto | Report Request Log for `2026.EX31.2` | Part 6 status "closed", closed by `2026.CC42.12`. Follow-up request from CC42.12: report by June 2027, status "Not Carried Forward" |
| P17 | Auto | Excel serial dates in the Report Request Log | 46163 → 2026-05-20; 46197 → 2026-06-23 |

## 2. Checks on AI output

| ID | Kind | Test | Expected result |
|---|---|---|---|
| C1 | Auto | Quote matches the source exactly | Pass, similarity 100 |
| C2 | Auto | Quote differs only in line breaks, double spaces, curly quotes or hyphenation | Pass (similarity ≥ 95 after normalizing) |
| C3 | Auto | Quote with one changed word that changes the meaning ("approved" → "rejected") | **Fail** |
| C4 | Auto | Quote that isn't in the source at all | **Fail**. Sentence rejected, never shown to staff as passable |
| C5 | Auto | What's displayed for a passing quote | The **source text span**, not the AI's version of the quote |
| C6 | Auto | AI sentence containing a date or deadline ("comments due Nov 20") | Rejected: "dates must come from the official page" |
| C7 | Auto | AI sentence says "Council approved" for a staff-report sentence | Flagged: decision word doesn't match the stage |
| C8 | Auto | Sentence with a loaded word ("the controversial closure", "finally approved", "massive") | Flagged: "loaded language", with the word named |
| C9 | Auto | Neutral sentence ("Council added $1,060,000 to the 2026 budget for this program") | No neutrality flag |
| C10 | Auto | Every saved sentence has a stage tag | 100% of sentences have `stage` set to staff report / committee decision / council decision |
| C11 | Auto | Reading level of a finished card | Score computed and stored. Target Grade 6–8. Cards above Grade 9 are flagged in the staff screen |
| C12 | Auto | Second AI check returns "missing condition" | Sentence is flagged and appears **first** in the review queue |

## 3. AI service (Groq)

| ID | Kind | Test | Expected result |
|---|---|---|---|
| A1 | Auto | Model name read from a single config setting | Changing the setting switches the model with no code changes |
| A2 | Auto | Groq returns 429 (rate limit), simulated | Pipeline waits and retries, finishes, and nothing is lost |
| A3 | Auto | Groq returns invalid JSON, simulated | That chunk is retried once, then logged as failed. Other chunks continue |
| A4 | Auto | Groq key missing | Clear error "GROQ_API_KEY not set". No crash dump |
| A5 | Check | What is sent to Groq | Only public city documents. **No resident data** (search code for calls; confirm no postal codes or user input) |
| A6 | Manual | Full run on all 3–4 items | Finishes within free-tier limits. Count of calls and time taken recorded in docs |

## 4. Database and security (Supabase)

| ID | Kind | Test | Expected result |
|---|---|---|---|
| D1 | Auto | **Logged out**, read approved sentences | Returns approved sentences only |
| D2 | Auto | **Logged out**, read unreviewed or rejected sentences | Returns **0 rows** (row-level security blocks it) |
| D3 | Auto | **Logged out**, insert/update/delete any row | Denied |
| D4 | Auto | Logged-in clerk approves a sentence | Saved, with `reviewed_by` and `reviewed_at` |
| D5 | Auto | Demo clerk (read-only) tries to approve | Denied. The screen shows "Demo account: changes aren't saved" |
| D6 | Check | Browser network tab on the public site | Only approved content in responses. No service key in any file sent to the browser |
| D7 | Check | Git history | No `.env`, keys or tokens committed (`git log -p` search for "key", "secret") |
| D8 | Auto | Votes table | Each vote has `motion_type` = amendment or main item |

## 5. Staff side

| ID | Kind | Test | Expected result |
|---|---|---|---|
| S1 | Manual | Open the staff URL logged out | Redirected to the login page |
| S2 | Manual | Log in with a wrong password | "Wrong email or password." No hint which one |
| S3 | Manual | Review queue for EX31.2 | Flagged sentences first. Each shows sentence, stage tag, source quote, flag reason, reading level |
| S4 | Manual | Approve a sentence | Appears on the public card after refresh |
| S5 | Manual | Edit a sentence, then approve | Edited text appears publicly. The original AI draft is kept in history |
| S6 | Manual | Reject a sentence | Never appears publicly |
| S7 | Manual | "Add item": paste `2026.EX31.1` | Request saved as "queued". After the scheduled job runs, the item appears in the queue as "unreviewed" |
| S8 | Manual | "Add item" with a badly formatted ref (`hello`) | Inline error "Enter an item number like 2026.EX31.2" |
| S9 | Manual | "Source updated" queue | Shows any card with a changed source (from P11) |
| S10 | Manual | Demo clerk login from a fresh browser (credentials in README) | Logs in, sees the queue, can't change anything |

## 6. Scheduled jobs (GitHub Actions)

| ID | Kind | Test | Expected result |
|---|---|---|---|
| J1 | Manual | Run the "process requests" job by hand | Queued requests processed. Status becomes "done" or "failed" with a reason |
| J2 | Manual | Run the "re-check sources" job | Changed sources flagged (see P11). Unchanged ones untouched |
| J3 | Check | Job secrets | Keys stored as GitHub secrets, never printed in logs |
| J4 | Check | Job schedule | Runs on its cron schedule. Last run time is visible in the staff screen |

## 7. Resident side: website

### Finding your ward
| ID | Kind | Test | Expected result |
|---|---|---|---|
| F1 | Auto | Postal code `M4Y 1Z5` | Candidate wards include Ward 13 Toronto Centre |
| F2 | Auto | Postal code typed as `m4y1z5` (lowercase, no space) | Same result as F1 |
| F3 | Auto | Postal code spanning several wards | A short list of ward names to pick from |
| F4 | Auto | Invalid input `12345` | Inline error "Enter a postal code like M6K 3C1". Page doesn't move on |
| F5 | Auto | Postal code outside Toronto (`K1A 0B1`) | "This postal code isn't in Toronto", plus a link to browse all items |
| F6 | Check | Postal code privacy | Not in the URL, not saved in the database, not sent to any third party (network tab) |
| F7 | Manual | Link to the city's official ward finder | Opens the official City of Toronto page |

### Ward list
| ID | Kind | Test | Expected result |
|---|---|---|---|
| L1 | Manual | Ward 13 list | Church St card listed with badge "Decided May 21, 2026". Other real Ward 13 items listed too |
| L2 | Manual | Item without a full card | Shows "Plain-language card not available yet" and links to the official page |
| L3 | Manual | City-wide section | EX31.2 appears for every ward |
| L4 | Manual | Badge wording | Only "Upcoming meeting", "Open for input" (only per rule 3), or "Decided [date]" |

### Decision Card (test on every full-card item)
| ID | Kind | Test | Expected result |
|---|---|---|---|
| K1 | Manual | Header | Title, status badge, item ref, "Checked against official records [date]" |
| K2 | Manual | Every sentence | Has a stage tag ("From the Council decision, May 21") and a footnote |
| K3 | Manual | Tap a footnote | Shows the source text span, document name, page, date, and a working link to the official source |
| K4 | Manual | Section heading for reasons | Reads "Reasons given in the staff report", never a bare "Why" |
| K5 | Manual | Conditions | Church St: shows that the city can cancel the closure for safety or emergency reasons |
| K6 | Manual | Timeline | Every stage with its date. Shows whether it was changed |
| K7 | Manual | Votes in timeline | Each vote says amendment or main item, with the result (e.g. "carried 19–5") and a source |
| K8 | Manual | "What changed" redline (EX31.2) | Staff → Executive Committee → Council changes shown paragraph by paragraph. Additions and removals labelled with **words** ("Added:", "Removed:"), not colour alone. One plain sentence per change |
| K9 | Manual | Public input | Shows counts only (e.g. "14 written submissions"), placed beside the changes, **with no claim that input caused them** |
| K10 | Manual | "What happens next" (EX31.2) | Shows that the heat by-law framework request was addressed by 2026.CC42.12 (June 2026), and that Council then asked for a maximum indoor temperature by-law by June 2027, listed as "not carried forward" to the new term's log. **Never** says the by-law was delivered or cancelled. Source: Report Request Log |
| K10b | Manual | "Can I have a say?" on 2027.PB1.6 | "Open for input": official comment form linked; no deadline shown; warning that "your name will be part of the public record and posted online" shown **before** the link |
| K11 | Manual | "Can I have a say?" on a decided item | "Closed. City Council has already decided this item." |
| K12 | Manual | "Can I have a say?" on an upcoming item with no stated method | "Upcoming meeting." Method: "Not yet stated on the official page", plus a link. **No date guessed** |
| K13 | Manual | Any item whose page states a participation method | "Open for input", with the method quoted and linked to the official page |
| K14 | Manual | Calendar button | Only on upcoming items. Downloads a `.ics` for the meeting. Never offered for an unconfirmed deadline |
| K15 | Manual | Open the `.ics` file | Correct date, time, location, and a link to the item page |
| K16 | Manual | Reading level | Shown on the card. Grade 6–8 for each full card |
| K17 | Manual | Stale source | A card with a changed source shows "Source updated since last review" |
| K18 | Manual | No personal info | No names from public comments anywhere on the card |

### Languages
| ID | Kind | Test | Expected result |
|---|---|---|---|
| T1 | Manual | Switch to French | Whole card in French. Label "Machine-translated, then reviewed. The English text is the official version." |
| T2 | Manual | Switch to Simplified Chinese | Card in Chinese, labelled "Machine-translated, not reviewed". Each sentence has "Show English original" |
| T3 | Manual | Footnotes in other languages | Source quotes stay in the original English |
| T4 | Manual | Switch back to English | Same card, nothing lost |

### Poster
| ID | Kind | Test | Expected result |
|---|---|---|---|
| R1 | Manual | Open the poster for the Church St card | Fits on **one** letter-size page. Large text |
| R2 | Manual | Scan the QR code with a phone | Opens the official item page (or the card) |
| R3 | Manual | Print preview in the browser | No cut-off text, no navigation bars printed |

## 8. Accessibility and devices

| ID | Kind | Test | Expected result |
|---|---|---|---|
| X1 | Check | Lighthouse accessibility on home, ward list and card | Score ≥ 90 on each |
| X2 | Manual | Keyboard only (Tab, Enter, Esc) | Every button, footnote and toggle reachable. Visible focus outline |
| X3 | Manual | Screen reader (Windows Narrator) on the card | Headings read in order. Footnotes announced. Redline additions and removals announced in words |
| X4 | Manual | Phone width (375 px) | No sideways scrolling. Buttons easy to tap |
| X5 | Manual | Zoom to 200% | Still readable, nothing overlapping |
| X6 | Manual | Dark mode, if supported | All text readable |
| X7 | Manual | Slow network (browser throttling "Slow 4G") | Card loads within a few seconds. Loading state shown |

## 9. Deployment

| ID | Kind | Test | Expected result |
|---|---|---|---|
| V1 | Manual | Open the live Vercel link on a phone (mobile data, not Wi-Fi) | Home page loads |
| V2 | Manual | The full must-work path on the live site | postal code → ward list → Church St card → footnote → timeline with votes → staff review showing a real flagged sentence |
| V3 | Check | Environment variables on Vercel | Only the public Supabase URL and public key. No service key, no Groq key |
| V4 | Manual | Visit a wrong URL (`/card/nonsense`) | Friendly "Item not found" page with a link home |

## 10. Accuracy and neutrality: human review

| ID | Kind | Test | Expected result |
|---|---|---|---|
| H1 | Manual | Read every published sentence against its source | Every sentence matches its source. No missing conditions or amendments |
| H2 | Manual | Read each card for tone | No opinion, no loaded words, no implied verdict |
| H3 | Manual | Staff vs committee vs Council | No sentence presents a staff recommendation as the final decision |
| H4 | Manual | Dates | Every date on the card is from an official page. No deadline inferred from a meeting date |
| H5 | Check | Counts per item recorded in docs | Drafted / rejected by code / flagged by checker / corrected by reviewer. Reviewer = developer (stated) |
| H6 | Manual | Show one card to 1–2 real people | Note what confused them and one fix made. Recorded in docs |

## 11. Submission checklist

| ID | Test | Expected result |
|---|---|---|
| Z1 | README | Setup steps, data sources with dates, assumptions, limitations, what was run by hand, demo login, **Credits** (libraries, datasets, Groq + model names, Claude Code) |
| Z2 | `docs/` | Requirements, UML (components, sequence, deployment), architecture rationale, AI role and limits, how outputs were checked |
| Z3 | Readiness Report PDF | 1 page. Users, data/resources, cost (free tier + paid estimate), privacy ("no resident data sent to AI", question/postal code handling), what residents should know, adapting to other cities (eSCRIBE/Granicus adapters) |
| Z4 | Demo video | **Under 3:00** (check the file length). Names the AI model and how outputs were checked. Shows a **real** flagged sentence, never a staged one. Ends with pilot steps |
| Z5 | Devpost description | Problem, users, solution, next steps. Live link and repo link work. Demo login included |
| Z6 | Git | Many commits over time. Final commit before **10:00 AM ET Sat Nov 14**. Nothing after |
| Z7 | Fresh clone | Following the README from scratch on a clean folder, tests run and the site starts |
| Z8 | Explain the code | You can explain the pipeline, the checks, the security rules and the redline without notes (finalist Q&A) |
