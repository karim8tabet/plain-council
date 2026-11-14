# Architecture

Plain Council has three parts:

1. A **Python pipeline** that reads official records and drafts summaries, run once per item.
2. A **Supabase database** that stores everything and enforces who can see and change what.
3. A **Next.js website** for residents and staff.

The diagrams below are written in Mermaid, so they render on GitHub.

## 1. Components (UML component diagram)

```mermaid
flowchart LR
  subgraph City["City of Toronto (public sources)"]
    TMMIS["Council meeting site<br/>item pages + staff report PDFs"]
    OD["Toronto Open Data<br/>Voting Record, Report Request Log, ward boundaries"]
    SC["Statistics Canada<br/>postal area (FSA) boundaries"]
  end

  subgraph Pipeline["pipeline/ (Python, run by a person or a scheduled job)"]
    R["Readers (no AI)<br/>civic/tmmis.py, pdf.py, votes.py, report_log.py"]
    D["Drafter<br/>civic/draft.py"]
    C["Code checks<br/>civic/checks.py"]
    V["Second AI check<br/>draft.verify_claims"]
    L["Loader<br/>load_item.py"]
    RC["Re-check<br/>recheck.py"]
    G["Postal → ward builder<br/>build_fsa_wards.py"]
  end

  GROQ["Groq API<br/>gpt-oss-120b"]

  subgraph DB["Supabase (Postgres + Auth)"]
    T["Tables: items, stages, passages,<br/>claims, reviews, votes, report_requests, participation"]
    RLS["Row-level security + review trigger"]
  end

  subgraph Web["web/ (Next.js on Vercel)"]
    PUB["Resident pages<br/>home, ward, item card"]
    STAFF["Staff review<br/>/staff"]
    FSA["fsa-wards.json"]
  end

  TMMIS --> R
  OD --> R
  SC --> G --> FSA
  R --> D --> C --> V --> L
  D <--> GROQ
  V <--> GROQ
  L --> T
  RC --> TMMIS
  RC --> T
  T --- RLS
  PUB -- "publishable key: reads published only" --> RLS
  STAFF -- "staff login: approve / edit / reject" --> RLS
  PUB --- FSA
```

**Rule of thumb:** facts come from code and AI writes words.
- Code reads every date, stage, outcome, vote, ward, submission count and participation status from the official records.
- AI only drafts plain-language sentences, and each one must carry a quote that code finds in the source.

## 2. How a card is made (UML sequence diagram)

```mermaid
sequenceDiagram
  actor Op as Operator (clerk or scheduled job)
  participant P as draft_item.py
  participant City as City site (TMMIS)
  participant AI as Groq (gpt-oss-120b)
  participant Chk as checks.py
  participant Ld as load_item.py
  participant DB as Supabase
  actor Clerk as Clerk (staff screen)
  actor Res as Resident

  Op->>P: python draft_item.py 2026.EX31.2
  P->>City: item page + staff report PDF
  City-->>P: HTML, PDF
  P->>P: parse stages, decisions, passages, fingerprint
  loop each chunk of one stage's text (≤ 8,000 chars)
    P->>AI: draft sentences (each with quote + stage)
    AI-->>P: JSON (strict schema)
    P->>Chk: quote in this stage's source? dates? decision words? loaded words?
    Chk-->>P: keep, flag, or reject
  end
  P->>AI: second check: is each sentence supported by its quote?
  AI-->>P: supported / not supported / missing condition / not neutral
  P-->>Op: out/<ref>.json + counts
  Op->>Ld: python load_item.py 2026.EX31.2
  Ld->>DB: items, stages, passages, claims (all "unreviewed"), votes, requests, participation
  Clerk->>DB: approve / edit / reject (logged with who and when)
  Res->>DB: open card (publishable key)
  DB-->>Res: only approved sentences + official facts
```

## 3. Resident lookup (UML sequence diagram)

```mermaid
sequenceDiagram
  actor Res as Resident
  participant Px as proxy.ts
  participant Find as /find page
  participant Ward as /ward/[n]
  participant DB as Supabase

  Res->>Px: /find?pc=M5V (first 3 characters only)
  alt postal area is inside one ward
    Px-->>Res: redirect to /ward/10
  else crosses several wards
    Px->>Find: continue
    Find-->>Res: "Which one is yours?" (short list + City ward finder link)
  end
  Res->>Ward: open ward
  Ward->>DB: items naming this ward + city-wide items (cached for minutes)
  DB-->>Ward: list
  Note over Res,DB: The postal code is never stored or sent anywhere. The lookup table is a static file.
```

## 4. Data model (UML class diagram)

```mermaid
classDiagram
  class items {
    ref: "2026.EX31.2" (key)
    title, wards[], city_wide
    source_fingerprint, source_changed
    public_submissions (count only)
    checked_at
  }
  class stages {
    stage_order, kind: staff_report|committee|community_council|board|city_council
    body_name, stage_date, outcome, amended
    decision_text, source_url
  }
  class passages {
    doc_title, doc_url, doc_date, stage, page
    text_original
  }
  class claims {
    section, stage, text_en
    ai_draft (never changes)
    quote_display (source span, locked)
    flags, status: unreviewed|approved|rejected|needs_rereview|discarded
    reviewed_by, reviewed_at, model
  }
  class reviews {
    action, before_text, after_text
    reviewer, created_at
  }
  class votes {
    voted_at, body_name, motion_kind: amendment|main_item
    result, yes_count, no_count, absent_count
  }
  class report_requests {
    directive, assigned_to, report_back_timing, status, closed_by
  }
  class participation {
    status: decided|upcoming|open
    meeting_at, method_url, method_source
    deadline_text (only if quoted, needs deadline_source)
  }
  class staff_profiles {
    user_id, role: clerk|demo
  }
  items "1" --> "*" stages
  items "1" --> "*" passages
  items "1" --> "*" claims
  claims "*" --> "0..1" passages : quotes
  claims "1" --> "*" reviews
  items "1" --> "*" votes
  items "1" --> "*" report_requests
  items "1" --> "0..1" participation
  staff_profiles "1" --> "*" reviews : makes
```

`changes`, `requests` and `job_runs` also exist in the schema. They're reserved for features this prototype runs by hand: stored redline sentences, the "Add item" queue, and the scheduled-job log.

## 5. Deployment (UML deployment diagram)

```mermaid
flowchart TB
  subgraph Dev["Operator's computer (or a scheduled GitHub Action)"]
    PY["Python 3.14 pipeline<br/>.env: Supabase secret key, Groq key"]
  end
  subgraph Vercel["Vercel (free tier)"]
    NX["Next.js 16 server + CDN<br/>env: Supabase URL + publishable key only"]
  end
  subgraph Supa["Supabase (free tier, hosted Postgres)"]
    PG[("Postgres<br/>row-level security")]
    AU["Auth (staff only)"]
  end
  GQ["Groq cloud (free tier)"]
  GH["GitHub repo<br/>push to main = deploy"]
  PY -- "secret key (bypasses RLS, server-side only)" --> PG
  PY -- "public documents only" --> GQ
  NX -- "publishable key + staff session" --> PG
  NX --> AU
  GH --> NX
  B["Resident / staff browser"] --> NX
```

## 6. Why it's built this way

| Decision | Why | Alternatives considered |
|---|---|---|
| **AI runs offline, once per item**, and a person approves every sentence | The brief says a wrong summary is worse than none. Pre-processing makes every published sentence reviewable, keeps cost flat no matter how many residents visit, and means no resident data ever reaches an AI service | A live chatbot that answers questions on demand. Rejected: its answers can't be reviewed before residents see them, and it costs money per question |
| **Facts from code, words from AI** | Dates, votes, stages and deadlines are where errors do the most harm, and they are already structured in the records | Letting the AI extract everything. Rejected after run 1 copied legal wording and could not be trusted on dates |
| **Quote check against the same step's source** | A sentence can't claim to be "from the committee" while quoting the staff report. Rejecting unsourced sentences is cheap and reliable | Trusting AI citations. Rejected: models invent or blend quotes |
| **Supabase (Postgres + row-level security)** | The rule "the public sees only approved sentences" is enforced by the database, not just by website code. Auth and an audit trigger come built in | JSON files in the repo: simpler, but there's no staff login and no enforced review |
| **Database trigger on review** | Records who reviewed and when. Stops anyone (even a logged-in clerk) from changing a sentence's source quote or the original AI draft. Makes permanent rejection final | Recording this in website code only. Rejected: a direct database call would bypass it |
| **Next.js with cached pages on Vercel** | Cards are mostly static. Caching makes them fast and cheap; a clerk's action refreshes that card at once | A single-page app calling the database from the browser. Slower on phones and more exposed |
| **Postal area (first 3 characters) → ward, precomputed** | Residents usually know their postal code but not their ward. The first 3 characters identify an area, not a household. A static file means nothing is sent or stored | Full address geocoding: more precise, but sends a resident's address to a third party |
| **Word-level redline in code, no AI** | Amendments are where meaning changes, so the official wording is shown exactly | An AI summary of each change. Possible later, but it would also need review |
| **Groq + open-weight model behind one setting** (`GROQ_MODEL`) | Free tier, fast, and swappable. A city could point it at a provider or model its procurement allows | A closed model: also fine, but it ties the city to one vendor |

## 7. Scaling and adapting

- **More items.** The pipeline cost is about 5–10 Groq calls per item, once. The website's cost doesn't grow with the number of items. For all of Toronto's agenda items (a few thousand a year), Groq's paid tier would cost a few dollars a month. Supabase's free tier holds this prototype's data many times over.
- **Review effort is the real cost.** Each item takes a clerk about 10–20 minutes. In this prototype, code and the checker flagged 11 of 63 drafted sentences. The rest still need a person, because the review found problems the checks missed (see [ai-and-verification.md](ai-and-verification.md)).
- **Other municipalities.**
  - Only `civic/tmmis.py` (the item page reader) and `report_log.py` are Toronto-specific.
  - A city on eSCRIBE or Granicus would write one reader that returns the same `ItemRecord` (title, wards, stages with decision text, documents).
  - The ward lookup is rebuilt with `build_fsa_wards.py` from that city's ward boundaries.
- **Scheduled jobs.**
  - `recheck.py` and the draft/load scripts are plain command-line tools, so a nightly GitHub Action or Supabase cron can run them.
  - Anything ingested automatically stays "unreviewed" until a person approves it.
