import type { Stage } from "@/lib/data";
import { fmtDate } from "@/lib/labels";
import { compareSteps, type PartChange, type Seg } from "@/lib/redline";

function stepName(s: Stage): string {
  return s.kind === "staff_report" ? "the staff report" : `the ${s.body_name}`;
}

function list(ns: number[]): string {
  if (ns.length === 0) return "none";
  return `${ns.length === 1 ? "part" : "parts"} ${ns.join(", ")}`;
}

// Removed and added words are marked with strike-through / underline AND screen-reader text,
// never colour alone.
function Words({ segs }: { segs: Seg[] }) {
  return (
    <>
      {segs.map((s, i) =>
        s.op === "same" ? <span key={i}>{s.text}</span>
        : s.op === "del" ? <del key={i} className="line-through decoration-2 bg-warn-soft"><span className="sr-only">[removed: </span>{s.text}<span className="sr-only">]</span></del>
        : <ins key={i} className="underline decoration-2 underline-offset-2 bg-accent-soft font-medium"><span className="sr-only">[added: </span>{s.text}<span className="sr-only">]</span></ins>,
      )}
    </>
  );
}

function Change({ c }: { c: PartChange }) {
  if (c.kind === "same") return null;
  const label = c.kind === "added" ? `Added: new part ${c.newN}`
    : c.kind === "removed" ? `Removed: part ${c.oldN} was dropped`
    : `Reworded: part ${c.newN}${c.oldN !== c.newN ? ` (was part ${c.oldN})` : ""}`;
  return (
    <li className="rounded-xl border border-line bg-card p-4 space-y-2 text-sm">
      <p className="font-semibold">{label}</p>
      {c.kind === "changed" ? (
        <p className="leading-relaxed"><Words segs={c.segs} /></p>
      ) : (
        // A whole part added or dropped: plain text (the label says which), easier to read than a long underline.
        <p className={`leading-relaxed border-l-4 pl-3 ${c.kind === "added" ? "border-accent" : "border-warn text-muted"}`}>{c.text}</p>
      )}
    </li>
  );
}

export function WhatChanged({ stages }: { stages: Stage[] }) {
  const withText = stages.filter((s) => s.decision_text);
  const pairs = withText.slice(1).map((s, i) => ({ from: withText[i], to: s, changes: compareSteps(withText[i].decision_text!, s.decision_text!) }));
  const upcoming = stages.find((s) => s.outcome === "Scheduled");
  if (pairs.length === 0 && !upcoming) return null;

  return (
    <section aria-labelledby="changes" className="space-y-4">
      <h2 id="changes" className="text-xl font-semibold">What changed between steps</h2>
      <p className="text-sm text-muted max-w-prose">
        Code compares the official wording of each step with the next, part by part (no AI). It shows changes in
        wording only; for what a change means, read the official record. <del className="line-through decoration-2 bg-warn-soft">Struck-through words</del> were
        removed. <ins className="underline decoration-2 underline-offset-2 bg-accent-soft font-medium">Underlined words</ins> were added.
      </p>
      {pairs.map(({ from, to, changes }) => {
        const kept = changes.filter((c) => c.kind === "same").map((c) => c.newN!);
        const reworded = changes.filter((c) => c.kind === "changed").map((c) => c.newN!);
        const added = changes.filter((c) => c.kind === "added").map((c) => c.newN!);
        const removed = changes.filter((c) => c.kind === "removed").map((c) => c.oldN!);
        return (
          <div key={to.id} className="space-y-2">
            <h3 className="font-semibold">From {stepName(from)} to {stepName(to)}{to.stage_date ? ` (${fmtDate(to.stage_date)})` : ""}</h3>
            {changes.length === 0 ? (
              <p className="text-sm">The texts could not be split into numbered parts to compare. See the official record.</p>
            ) : (
              <>
                <p className="text-sm">
                  Kept word for word: {list(kept)}. Reworded: {list(reworded)}. Added: {list(added)}. Removed: {list(removed)}.
                  {" "}Part numbers are those in {stepName(to)}{removed.length ? `, except removed parts, which are numbered as in ${stepName(from)}` : ""}.
                </p>
                <ul className="space-y-2">{changes.map((c, i) => <Change key={i} c={c} />)}</ul>
              </>
            )}
            <p className="text-xs text-muted"><a href={to.source_url}>Official record for {stepName(to)}</a></p>
          </div>
        );
      })}
      {upcoming && (
        <p className="text-sm">
          Nothing to compare yet for {stepName(upcoming)}: it meets on {fmtDate(upcoming.stage_date)}. Once it decides, this section will show what it kept or changed.
        </p>
      )}
    </section>
  );
}
