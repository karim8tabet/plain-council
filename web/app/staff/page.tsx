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

type Row = {
  id: number; item_ref: string; section: string; stage: "staff_report" | "committee" | "community_council" | "board" | "city_council";
  stage_date: string | null; text_en: string; ai_draft: string; quote_display: string | null; quote_ai?: string;
  flags: { type: string; detail: string }[]; status: string; reviewed_at: string | null; match_score: number | null;
};

async function Queue({ searchParams }: { searchParams: Promise<{ item?: string; demo?: string }> }) {
  const user = await requireStaff();
  const sp = await searchParams;
  const db = await staffClient();
  const { data: items } = await db.from("items").select("ref,title").eq("has_card", true).order("ref");
  const { data: all } = await db.from("claims").select("item_ref,status,flags");
  const ref = sp.item ?? items?.[0]?.ref;
  const { data: claims } = await db.from("claims").select("*").eq("item_ref", ref ?? "").order("sort_order");
  const { data: stages } = await db.from("stages").select("kind,body_name").eq("item_ref", ref ?? "");
  const body = new Map((stages ?? []).map((s) => [s.kind, s.body_name]));

  const counts = (r: string) => {
    const cs = (all ?? []).filter((c) => c.item_ref === r);
    return {
      total: cs.length,
      approved: cs.filter((c) => c.status === "approved").length,
      todo: cs.filter((c) => c.status === "unreviewed" || c.status === "needs_rereview").length,
      flagged: cs.filter((c) => c.status !== "rejected" && (c.flags as unknown[]).length > 0).length,
    };
  };
  // Flagged first, then the rest in card order; code-rejected last.
  const rows = ((claims ?? []) as Row[]).sort((a, b) => {
    const rank = (c: Row) => (c.status === "rejected" && c.flags.some((f) => f.type === "quote_not_found") ? 2 : c.flags.length ? 0 : 1);
    return rank(a) - rank(b);
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Review queue</h1>
        <form action={logout} className="text-sm">
          {user.email} ({user.role === "demo" ? "demo, read-only" : "clerk"}) · <button className="underline text-accent">Sign out</button>
        </form>
      </div>
      {(user.role === "demo" || sp.demo) && (
        <p role="status" className="rounded-lg border border-warn bg-warn-soft text-warn p-3 text-sm font-medium">
          Demo account: you can try everything, but changes aren&apos;t saved.
        </p>
      )}
      <nav aria-label="Items" className="flex flex-wrap gap-2">
        {(items ?? []).map((it) => {
          const k = counts(it.ref);
          return (
            <Link key={it.ref} href={`/staff?item=${it.ref}`}
              className={`rounded-lg border px-3 py-2 text-sm no-underline ${it.ref === ref ? "border-accent bg-accent-soft" : "border-line bg-card"}`}>
              <span className="font-medium text-ink">{it.ref}</span>
              <span className="block text-muted">{k.todo} to review · {k.flagged} flagged · {k.approved}/{k.total} approved</span>
            </Link>
          );
        })}
      </nav>
      {ref && <p className="text-sm"><Link href={`/item/${ref}`}>See the public card</Link> (shows approved sentences only)</p>}

      <ol className="space-y-4">
        {rows.map((c) => {
          const codeRejected = c.flags.some((f) => f.type === "quote_not_found");
          return (
            <li key={c.id} id={`c${c.id}`} className={`rounded-xl border bg-card p-4 space-y-3 ${c.flags.length && !codeRejected ? "border-warn" : "border-line"}`}>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded bg-accent-soft px-1.5 py-0.5">{SECTION_TITLES[c.section]}</span>
                <span className="rounded bg-paper border border-line px-1.5 py-0.5">{stageTag(c.stage, body.get(c.stage), c.stage_date)}</span>
                <span className="rounded border border-line px-1.5 py-0.5 font-medium">{c.status.replace("_", " ")}</span>
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
                <blockquote className="italic">“{c.quote_display ?? "(no matching passage found)"}”</blockquote>
              </figure>
              {codeRejected ? (
                <p className="text-sm text-muted">AI draft (not publishable): {c.text_en}</p>
              ) : (
                <form action={review} className="space-y-2">
                  <input type="hidden" name="id" value={c.id} />
                  <input type="hidden" name="ref" value={c.item_ref} />
                  <label className="block">
                    <span className="text-sm font-medium">Plain-language sentence (edit if needed)</span>
                    <textarea name="text" defaultValue={c.text_en} rows={2} className="mt-1 w-full rounded-lg border border-line bg-paper px-3 py-2" />
                  </label>
                  {c.text_en !== c.ai_draft && <p className="text-xs text-muted">Original AI draft: {c.ai_draft}</p>}
                  <div className="flex flex-wrap items-center gap-2">
                    <button name="action" value="approve" className="rounded-lg bg-council px-3 py-1.5 text-sm font-medium text-paper">Approve</button>
                    <button name="action" value="reject" className="rounded-lg border border-warn px-3 py-1.5 text-sm font-medium text-warn">Reject</button>
                    {user.role === "demo" && (
                      <span className="text-sm text-warn">Demo account: buttons work, but nothing is saved.</span>
                    )}
                  </div>
                </form>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default function Page(props: PageProps<"/staff">) {
  return (
    <Suspense fallback={<p>Loading the review queue…</p>}>
      <Queue searchParams={props.searchParams as Promise<{ item?: string; demo?: string }>} />
    </Suspense>
  );
}
