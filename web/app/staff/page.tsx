import { Suspense } from "react";
import Link from "next/link";
import { requireStaff, staffClient } from "@/lib/staff";
import { SECTION_TITLES, stageTag } from "@/lib/labels";
import { logout, review } from "./actions";

export const metadata = { title: "Review queue" };

const FLAG_TEXT: Record<string, string> = {
  quote_not_found: "Rejected by code: the quote was not found in this step's source",
  date: "Date not found in the quoted source",
  deadline_word: "Deadline wording (deadlines must come from the official page)",
  decision_word: "Says decided/approved, but this step only recommends",
  loaded_word: "Loaded word",
  not_supported: "Checker: not supported by the source",
  missing_condition: "Checker: drops a condition",
  loaded_language: "Checker: wording not neutral",
  checker_missing: "Checker gave no verdict",
};

const DONE_TEXT: Record<string, string> = {
  approve: "Approved. It is now on the public card.",
  reject: "Rejected. It moved to the Rejected tab, where you can undo it.",
  restore: "Moved back to the review queue.",
  unpublish: "Taken off the public card and moved back to the review queue.",
  discard: "Permanently rejected. It is kept in the review record but can never be published.",
};

type Tab = "review" | "published" | "rejected";
type Row = {
  id: number; item_ref: string; section: string; stage: "staff_report" | "committee" | "community_council" | "board" | "city_council";
  stage_date: string | null; text_en: string; ai_draft: string; quote_display: string | null;
  flags: { type: string; detail: string }[]; status: string; reviewed_at: string | null; match_score: number | null;
};

const codeRejected = (c: Row) => c.flags.some((f) => f.type === "quote_not_found");
const tabOf = (c: { status: string }): Tab | null =>
  c.status === "approved" ? "published" : c.status === "rejected" ? "rejected" : c.status === "discarded" ? null : "review";

const btn = "rounded-lg px-3 py-1.5 text-sm font-medium";

function Hidden({ c, tab }: { c: Row; tab: Tab }) {
  return (<><input type="hidden" name="id" value={c.id} /><input type="hidden" name="ref" value={c.item_ref} /><input type="hidden" name="tab" value={tab} /></>);
}

async function Queue({ searchParams }: { searchParams: Promise<{ item?: string; tab?: string; demo?: string; done?: string }> }) {
  const user = await requireStaff();
  const sp = await searchParams;
  const tab: Tab = sp.tab === "published" || sp.tab === "rejected" ? sp.tab : "review";
  const db = await staffClient();
  const { data: items } = await db.from("items").select("ref,title").eq("has_card", true).order("ref");
  const { data: all } = await db.from("claims").select("item_ref,status,flags");
  const ref = sp.item ?? items?.[0]?.ref ?? "";
  const { data: claims } = await db.from("claims").select("*").eq("item_ref", ref).order("sort_order");
  const { data: stages } = await db.from("stages").select("kind,body_name").eq("item_ref", ref);
  const body = new Map((stages ?? []).map((s) => [s.kind, s.body_name]));

  const mine = (all ?? []).filter((c) => c.item_ref === ref);
  const count = (t: Tab) => mine.filter((c) => tabOf(c) === t).length;
  const discarded = mine.filter((c) => c.status === "discarded").length;
  const todoOf = (r: string) => (all ?? []).filter((c) => c.item_ref === r && tabOf(c) === "review").length;

  let rows = ((claims ?? []) as Row[]).filter((c) => tabOf(c) === tab);
  if (tab === "review") rows = rows.sort((a, b) => Number(b.flags.length > 0) - Number(a.flags.length > 0)); // flagged first
  const byHand = rows.filter((c) => !codeRejected(c));
  const byCode = rows.filter(codeRejected);

  const tabLink = (t: Tab, label: string) => (
    <Link href={`/staff?item=${ref}&tab=${t}`} aria-current={t === tab ? "page" : undefined}
      className={`rounded-t-lg border border-b-0 px-4 py-2 text-sm no-underline ${t === tab ? "bg-card border-line font-semibold text-ink" : "border-transparent text-accent"}`}>
      {label} ({count(t)})
    </Link>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Review queue</h1>
        <form action={logout} className="text-sm">
          Signed in as {user.email} ({user.role === "demo" ? "demo, read-only" : "clerk"}) ·{" "}
          <button className="underline text-accent">Sign out</button>
        </form>
      </div>
      {(user.role === "demo" || sp.demo) && (
        <p role="status" className="rounded-lg border border-warn bg-warn-soft text-warn p-3 text-sm font-medium">
          Demo account: you can try everything, but changes aren&apos;t saved.
        </p>
      )}
      {sp.done && DONE_TEXT[sp.done] && !sp.demo && (
        <p role="status" className="rounded-lg border border-council bg-council-soft text-council p-3 text-sm font-medium">{DONE_TEXT[sp.done]}</p>
      )}

      <nav aria-label="Items" className="flex flex-wrap gap-2">
        {(items ?? []).map((it) => (
          <Link key={it.ref} href={`/staff?item=${it.ref}&tab=${tab}`}
            className={`rounded-lg border px-3 py-2 text-sm no-underline ${it.ref === ref ? "border-accent bg-accent-soft" : "border-line bg-card"}`}>
            <span className="font-medium text-ink">{it.ref}</span>
            <span className="block text-muted">{todoOf(it.ref)} to review</span>
          </Link>
        ))}
      </nav>

      <div>
        <nav aria-label="Sentence status" className="flex gap-1 border-b border-line">
          {tabLink("review", "To review")}
          {tabLink("published", "Published")}
          {tabLink("rejected", "Rejected")}
        </nav>
        <p className="text-sm text-muted mt-3">
          {tab === "review" && "Approve to publish a sentence on the public card, or reject it. Flagged sentences are shown first."}
          {tab === "published" && <>These sentences are on the <Link href={`/item/${ref}`}>public card</Link> now. Take one off if it was approved by mistake.</>}
          {tab === "rejected" && "Rejected sentences are not shown to the public. Move one back if it was rejected by mistake, or reject it permanently."}
          {tab === "rejected" && discarded > 0 && ` ${discarded} permanently rejected (kept in the record, not shown).`}
        </p>
      </div>

      {byHand.length === 0 && byCode.length === 0 && <p className="text-muted">Nothing here.</p>}

      <ol className="space-y-4">
        {byHand.map((c) => (
          <li key={c.id} id={`c${c.id}`} className={`rounded-xl border bg-card p-4 space-y-3 ${tab === "review" && c.flags.length ? "border-warn" : "border-line"}`}>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded bg-accent-soft px-1.5 py-0.5">{SECTION_TITLES[c.section]}</span>
              <span className="rounded bg-paper border border-line px-1.5 py-0.5">{stageTag(c.stage, body.get(c.stage), c.stage_date)}</span>
            </div>
            {c.flags.length > 0 && (
              <ul className="text-sm space-y-1">
                {c.flags.map((f, i) => (
                  <li key={i} className="text-warn"><span className="font-medium">⚑ {FLAG_TEXT[f.type] ?? f.type}:</span> {f.detail}</li>
                ))}
              </ul>
            )}
            <figure className="border-l-2 border-line pl-3 text-sm">
              <figcaption className="text-muted">Source passage{c.match_score ? ` (match ${Math.round(c.match_score)}%)` : ""}</figcaption>
              <blockquote className="italic">“{c.quote_display}”</blockquote>
            </figure>

            {tab === "review" ? (
              <form action={review} className="space-y-2">
                <Hidden c={c} tab={tab} />
                <label className="block">
                  <span className="text-sm font-medium">Plain-language sentence (edit if needed)</span>
                  <textarea name="text" defaultValue={c.text_en} rows={2} className="mt-1 w-full rounded-lg border border-line bg-paper px-3 py-2" />
                </label>
                {c.text_en !== c.ai_draft && <p className="text-xs text-muted">Original AI draft: {c.ai_draft}</p>}
                <div className="flex flex-wrap items-center gap-2">
                  <button name="action" value="approve" className={`${btn} bg-council text-paper`}>Approve</button>
                  <button name="action" value="reject" className={`${btn} border border-warn text-warn`}>Reject</button>
                  {user.role === "demo" && <span className="text-sm text-warn">Demo account: buttons work, but nothing is saved.</span>}
                </div>
              </form>
            ) : (
              <div className="space-y-2">
                <p>{c.text_en}</p>
                {c.text_en !== c.ai_draft && <p className="text-xs text-muted">Original AI draft: {c.ai_draft}</p>}
                <div className="flex flex-wrap items-center gap-2">
                  {tab === "published" && (
                    <form action={review}><Hidden c={c} tab={tab} />
                      <button name="action" value="unpublish" className={`${btn} border border-line text-ink`}>Take off the public card</button>
                    </form>
                  )}
                  {tab === "rejected" && (
                    <>
                      <form action={review}><Hidden c={c} tab={tab} />
                        <button name="action" value="restore" className={`${btn} border border-accent text-accent`}>Move back to review</button>
                      </form>
                      <details>
                        <summary className={`${btn} border border-warn text-warn inline-block`}>Reject permanently…</summary>
                        <form action={review} className="mt-2 rounded-lg border border-warn bg-warn-soft p-3 text-sm space-y-2">
                          <Hidden c={c} tab={tab} />
                          <p className="text-warn">This can&apos;t be undone. The sentence stays in the review record but can never be published.</p>
                          <button name="action" value="discard" className={`${btn} bg-warn text-paper`}>Yes, reject permanently</button>
                        </form>
                      </details>
                    </>
                  )}
                  {user.role === "demo" && <span className="text-sm text-warn">Demo account: nothing is saved.</span>}
                </div>
              </div>
            )}
          </li>
        ))}
      </ol>

      {tab === "rejected" && byCode.length > 0 && (
        <details className="rounded-xl border border-line bg-card p-4">
          <summary className="font-medium">Rejected by code ({byCode.length}): the AI&apos;s quote was not found in the source</summary>
          <p className="text-sm text-muted mt-2">These can&apos;t be published, because there is no exact source passage to show residents.</p>
          <ul className="mt-2 space-y-2 text-sm">
            {byCode.map((c) => <li key={c.id}>{c.text_en}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
}

export default function Page(props: PageProps<"/staff">) {
  return (
    <Suspense fallback={<p>Loading the review queue…</p>}>
      <Queue searchParams={props.searchParams as Promise<{ item?: string; tab?: string; demo?: string; done?: string }>} />
    </Suspense>
  );
}
