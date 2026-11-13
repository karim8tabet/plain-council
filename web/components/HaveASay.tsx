import type { Participation, Stage } from "@/lib/data";
import { fmtDate } from "@/lib/labels";

/** Only says input is open when an official page states how to take part. Never guesses a deadline. */
export function HaveASay({ p, stages, itemUrl }: { p: Participation | null; stages: Stage[]; itemUrl: string }) {
  const next = stages.find((s) => s.outcome === "Scheduled");
  const status = p?.status ?? "decided";
  return (
    <section aria-labelledby="say" className={`rounded-xl border p-5 space-y-2 ${status === "open" ? "border-council bg-council-soft" : "border-line bg-card"}`}>
      <h2 id="say" className="text-xl font-semibold">Can I have a say?</h2>
      {status === "open" && p && (
        <>
          <p className="font-medium">Yes. The City is accepting written comments on this item.</p>
          {next && <p>It goes to the {next.body_name} on {fmtDate(next.stage_date)}.</p>}
          <p><a className="font-medium" href={p.method_url!}>{p.method_text}</a></p>
          {p.deadline_text ? (
            <p>Deadline, as stated by the City: {p.deadline_text} (<a href={p.deadline_source!}>source</a>)</p>
          ) : (
            <p className="text-sm">The City&apos;s page does not state a comment deadline, so we don&apos;t show one. Check the <a href={itemUrl}>official item page</a> before you send.</p>
          )}
          <p className="text-sm">Before you send: the City may publish your name with your comment. Read the notice on the City&apos;s form.</p>
          <p className="text-xs text-muted">How to take part was taken from the <a href={p.method_source!}>official item page</a>.</p>
        </>
      )}
      {status === "upcoming" && (
        <p>This item is on an upcoming agenda{next ? ` (${next.body_name}, ${fmtDate(next.stage_date)})` : ""}. The official page does not yet say how to take part. Check the <a href={itemUrl}>official item page</a>.</p>
      )}
      {status === "decided" && (
        <p>A decision has been made on this item and the official page lists no open comment period. You can still contact your councillor, or watch for any follow-up report.</p>
      )}
    </section>
  );
}
