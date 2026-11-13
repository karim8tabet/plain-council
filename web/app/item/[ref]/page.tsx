import { notFound } from "next/navigation";
import { Suspense } from "react";
import { getCard } from "@/lib/data";
import { fmtDate, REQUEST_STATUS, SECTION_ORDER, SECTION_TITLES, WARDS, whereItStands } from "@/lib/labels";
import { Sentence } from "@/components/Sentence";
import { Timeline } from "@/components/Timeline";
import { HaveASay } from "@/components/HaveASay";
import { WhatChanged } from "@/components/WhatChanged";
import { readingGrade } from "@/lib/reading";

async function DecisionCard({ params }: { params: Promise<{ ref: string }> }) {
  const { ref } = await params;
  const card = await getCard(decodeURIComponent(ref));
  if (!card) notFound();
  const { item, stages, claims, passages, votes, requests, participation } = card;
  const byPassage = new Map(passages.map((p) => [p.id, p]));
  const bodyOf = new Map(stages.map((s) => [s.kind, s.body_name]));
  const numbered = claims.map((c, i) => ({ c, n: i + 1 }));
  const grade = readingGrade(claims.map((c) => c.text_en));

  return (
    <article className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm text-muted">
          {item.ref} · {item.city_wide ? "City-wide" : item.wards.map((w) => `Ward ${w} (${WARDS[w]})`).join(", ")}
        </p>
        <h1 className="text-3xl font-semibold leading-tight">{item.title}</h1>
        <p className="text-lg font-medium">{whereItStands(stages)} <a className="text-sm font-normal" href="#steps">See the steps</a></p>
        <p className="text-sm"><a href={item.item_url}>Official item page (City of Toronto)</a></p>
        {item.source_changed && (
          <p role="status" className="rounded-lg border border-warn bg-warn-soft text-warn p-3 text-sm font-medium">
            The official record has changed since this summary was reviewed. It is being checked again. Until then,
            rely on the official item page.
          </p>
        )}
      </header>

      <HaveASay p={participation} stages={stages} itemUrl={item.item_url} />

      <section aria-labelledby="plain" className="space-y-4">
        <h2 id="plain" className="text-xl font-semibold">In plain language</h2>
        {claims.length === 0 ? (
          <p className="rounded-lg border border-line bg-card p-4">
            A plain-language summary has been drafted but has not been reviewed by a person yet, so it is not shown.
            The steps and votes below come straight from the official records.
          </p>
        ) : (
          <>
            <p className="text-sm text-muted">Tap a sentence to see the exact words it comes from. Each sentence says which step it is from: a staff recommendation, a committee recommendation, or the final Council decision.</p>
            {SECTION_ORDER.filter((s) => numbered.some(({ c }) => c.section === s)).map((s) => (
              <div key={s} className="space-y-2">
                <h3 className="font-semibold">{SECTION_TITLES[s]}</h3>
                <ul className="space-y-2 list-disc pl-5">
                  {numbered.filter(({ c }) => c.section === s).map(({ c, n }) => (
                    <Sentence key={c.id} c={c} n={n} passage={c.passage_id ? byPassage.get(c.passage_id) : undefined} body={bodyOf.get(c.stage)} />
                  ))}
                </ul>
              </div>
            ))}
            <p className="text-xs text-muted">
              Drafted with AI from the official records, checked by code and a second AI pass, and approved by a person
              {item.checked_at ? ` on ${fmtDate(item.checked_at)}` : ""}.
              {grade !== null ? ` Reading level of these sentences: about grade ${Math.max(1, Math.round(grade))}.` : ""}
            </p>
          </>
        )}
      </section>

      <WhatChanged stages={stages} />

      <section aria-labelledby="steps" className="space-y-3">
        <h2 id="steps" className="text-xl font-semibold">How it got here, step by step</h2>
        <p className="text-sm text-muted max-w-prose">
          Council items move through steps. Usually City staff write a report with recommendations (some items start from a councillor&apos;s letter instead). A committee (or board)
          considers it and recommends what City Council should do. City Council makes the final decision and can change
          what was recommended. The coloured tags on the sentences above say which of these steps each one comes from.
        </p>
        <Timeline stages={stages} votes={votes} />
        {item.public_submissions ? (
          <p className="text-sm">
            The City received <strong>{item.public_submissions}</strong> written submissions on this item. We count them
            but do not summarize them, to protect privacy and avoid picking sides.
          </p>
        ) : null}
      </section>

      {requests.length > 0 && (
        <section aria-labelledby="next" className="space-y-3">
          <h2 id="next" className="text-xl font-semibold">Follow-up work Council asked for</h2>
          <p className="text-sm text-muted max-w-prose">When it decided, City Council asked City staff to come back later with more work on this topic. Here is what was asked, and where it stands in the City Clerk&apos;s Report Request Log.</p>
          <ul className="space-y-3">
            {requests.map((r) => (
              <li key={r.id} className="rounded-xl border border-line bg-card p-4 text-sm space-y-1">
                <p><span className="font-medium">Asked of:</span> {r.assigned_to ?? "not stated"}</p>
                <p><span className="font-medium">Report back:</span> {r.report_back_timing && /^\d{4}-\d{2}-\d{2}$/.test(r.report_back_timing) ? fmtDate(r.report_back_timing) : r.report_back_timing ?? "not stated"}</p>
                <p><span className="font-medium">Status:</span> {REQUEST_STATUS[r.status] ?? r.status}</p>
                {r.closed_by && <p><span className="font-medium">Answered by item:</span> <a href={`https://secure.toronto.ca/council/agenda-item.do?item=${r.closed_by}`}>{r.closed_by}</a> (official City page)</p>}
                <details><summary className="text-accent">Request as written</summary><p className="mt-1 text-muted">{r.directive}</p></details>
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted">Source: {requests[0].source}. A closed request means staff linked it to a later item; it does not prove every part was delivered.</p>
        </section>
      )}
    </article>
  );
}

export default function Page(props: PageProps<"/item/[ref]">) {
  return (
    <Suspense fallback={<p>Loading the decision card…</p>}>
      <DecisionCard params={props.params} />
    </Suspense>
  );
}
