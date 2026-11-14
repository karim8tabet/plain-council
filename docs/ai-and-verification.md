# AI's role, its limits, and how outputs were checked

## Where AI is used

| Where | Model | What it does | What it never does |
|---|---|---|---|
| **In the product** (pipeline, offline) | **OpenAI gpt-oss-120b** (open-weight), via **Groq**. Set by `GROQ_MODEL`; reasoning effort "low"; strict JSON schema | 1. Drafts plain-language sentences from the official documents, each with a quote and the step it comes from. 2. A second call checks each sentence against its quote | Decide any date, vote, stage, ward, deadline or participation status (code reads those from the records). Publish anything (a person approves every sentence). See any resident data |
| **Building the product** | **Claude Code** (Anthropic, Claude Opus 5.5) | Planning, most of the code, docs, and a pre-check of the drafted sentences before human review (see below) | Approve sentences |
| **Building the product** | **Codex** (OpenAI) via the Codex plugin for Claude Code | First version of the pipeline readers and checks (`civic/tmmis.py`, `votes.py`, `report_log.py`, `pdf.py`, `checks.py` and their tests), from a written spec. Claude then reviewed and corrected it (log: `.claude/handoff-log.md`) | |

## The checks, in order

1. **The drafting rules** (`DRAFT_SYSTEM` in `pipeline/civic/draft.py`):
   - plain words, under about 20 words
   - attribute every sentence ("Staff recommend…", "The committee recommended…", "City Council decided…")
   - never state a staff proposal as fact
   - one continuous quote of 10–40 words
   - no deadlines, no names of members of the public
2. **One step at a time.** Text from different steps is never mixed in one request. A sentence's quote must be found in **that step's** source, or the sentence is rejected.
3. **Code checks** (`pipeline/civic/checks.py`):
   - **Quote match:** fuzzy match of 95 or more after normalizing spaces, hyphens and quote marks. A quote with "…" is split into pieces, and the pieces must appear in order in the same passage. The card shows the source's own words, never the AI's copy.
   - **Dates:** allowed only if the same date is in the quoted source. Deadline words are always flagged.
   - **Decision words:** "approved" or "decided" in a sentence from a step that only recommends is flagged.
   - **Loaded words:** a fixed list ("controversial", "finally", "massive", "historic"…).
   - **Reading level:** Flesch–Kincaid grade.
4. **Second AI check:** each sentence comes back as *supported*, *not supported*, *missing condition*, or *not neutral*. Each source is labelled with who said it, because without those labels the checker wrongly flagged committee text.
5. **Human review** in the staff screen:
   - Approve, edit, reject, move back to review, or reject permanently.
   - The database records who reviewed and when.
   - It blocks changes to the source quote and to the original AI draft.
   - Only approved sentences can be read by the public.

## Results on the three real items

Numbers come from the pipeline output (`pipeline/out/<ref>.json`, not committed; `draft_item.py` regenerates it) and the database's `reviews` table. Checked Nov 13, 2026.

| | EX31.2 Air Conditioner Benefit | TE32.46 Church St pilot | PB1.6 1337 Queen St W | **Total** |
|---|---|---|---|---|
| Sentences drafted by AI | 29 | 9 | 25 | **63** |
| Rejected by code (quote not in that step's source) | 1 | 0 | 0 | **1** |
| Flagged by code or second AI check | 3 (missing condition) | 0 | 7 (2 not supported, 5 loaded word) | **10** |
| Reworded at review (accuracy, attribution, neutrality) | 7 | 5 | 15 | **27** |
| Rejected at review (repeats or inaccurate) | 2 | 1 | 3 | **6** |
| Published | 26 | 8 | 22 | **56** |
| Published with the AI's exact wording | 2 | 1 | 5 | **8** |
| Reading level of published sentences: AI draft → published | 12.9 → 8.7 | 14.4 → 9.1 | 9.0 → 6.5 | |

Notes on the table:
- **Reworded at review** has two parts:
  - **Accuracy:** the 27 rewordings are the accuracy, attribution and neutrality fixes.
  - **Reading level:** afterwards, 37 published sentences were rewritten again to bring the reading level down. Same facts, re-approved one by one. That's why only 8 sentences kept the AI's exact wording.
- **Reading levels** use the textstat Flesch–Kincaid grade. The website shows its own estimate, which runs about 1 grade higher.

### What the review caught that the automatic checks did not

| Problem | Example | Caught by |
|---|---|---|
| **Wrong body or power** | "The Committee *asks* the City Manager…" (a committee can only recommend that Council do it) | Review |
| **Proposal stated as fact** | "The new building *will be*…" for a proposal not yet decided | Review |
| **Invented detail** | "…fits with the red brick on nearby heritage buildings" (not in the source) | Review |
| **Dropped condition** | Church St study sentences left out "risks and public safety impacts", which made the study sound one-sided | Review |
| **Contradiction** | One sentence said the new base "matches the height" of the heritage building next door; the staff report says it no longer does | Review |
| **Editorial word** | "would *actually* create a more consistent streetwall" | Review |
| **Detail not in the quote** | "500 low-income *seniors*" when the source says "eligible recipients" | Second AI check |
| **Unsupported reason** | "…*because* it is non-contributing" | Second AI check |
| **Sentence with no source** | A Council sentence whose quote wasn't in the Council text | Code (rejected) |

**False alarms:**
- "Historic" is on the loaded-word list, but heritage reports use it as a technical term (5 flags).
- One "missing condition" flag was wrong: the quote shown was cut short, and the full source did support the sentence.

## How the human review was done (stated plainly)

- **The reviewer was the developer** (one person, team of one), not an independent clerk.
- **AI pre-check.** Before review, Claude Code read every drafted sentence against its quote and wrote suggestions: keep, reword (with wording), or reject. These are the rewordings and rejections counted above.
- **Every decision was the developer's.** They read each sentence against its quote. The first round of 62 decisions was entered by a script on their instruction, under their account, after they had checked every sentence. The 37 simplified sentences were re-approved one by one in the staff screen.
- **What this means.** The published cards were checked by a person against the source quotes. They were not independently reviewed. A real pilot should have a clerk who did not write the code review each card, and should track their corrections over time.

## Known limits

- **Omissions.** Checks compare each sentence with its own quote. They cannot prove that the card covers everything important. The "What changed between steps" section shows the official wording of each amendment exactly, to cover that gap for amendments.
- **AI wording can still be subtly off.** That's why nothing is published without a person.
- **Reading level.** It's a formula. Short sentences can still use hard words, and official names (like "Transportation Services") are kept on purpose.
- **Public submissions** are counted, never summarized. Residents can't see what people argued without going to the City's page.
- **Model availability.** The model name is one setting. A model change means re-drafting and re-reviewing.

## Prompt history (what changed and why)

| Run | Change | Result |
|---|---|---|
| 1 | First prompt | Sentences copied legal wording (grade 17.7). Kept locally as `pipeline/out/2026.EX31.2.run1-legal-wording.json` |
| 2 | Plain-language rewrite rules added | Grade 11.5. Quotes with "…" were rejected, so piece-by-piece matching was added |
| 3 | Sources labelled with who said them | Ended the checker's false "not supported" flags on committee text |
