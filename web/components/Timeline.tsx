import type { Stage, Vote } from "@/lib/data";
import { fmtDate, fmtDateTime, stageRole } from "@/lib/labels";

const STAGE_STYLE: Record<string, string> = {
  staff_report: "border-staff bg-staff-soft text-staff",
  committee: "border-committee bg-committee-soft text-committee",
  community_council: "border-committee bg-committee-soft text-committee",
  board: "border-committee bg-committee-soft text-committee",
  city_council: "border-council bg-council-soft text-council",
};

function VoteLine({ v }: { v: Vote }) {
  const what = v.motion_kind === "amendment" ? "Vote on a change (amendment)"
    : v.motion_kind === "main_item" ? "Vote on the whole item" : "Vote";
  const [outcome, tally] = v.result.split(",").map((s) => s.trim());
  return (
    <li className="text-sm">
      <details>
        <summary>
          <span className="font-medium">{what}:</span> {outcome}{tally ? `, ${tally.replace("-", "–")}` : ""}
          <span className="text-muted"> ({v.motion_type}) · details</span>
        </summary>
        <div className="mt-1 ml-4 text-muted space-y-1">
          {v.description && <p>Motion as recorded: “{v.description}”</p>}
          <p>{fmtDateTime(v.voted_at).replace(/\.$/, "")}. Source: {v.source}.</p>
        </div>
      </details>
    </li>
  );
}

export function Timeline({ stages, votes }: { stages: Stage[]; votes: Vote[] }) {
  return (
    <ol className="space-y-4">
      {stages.map((s, i) => {
        const vs = votes.filter((v) => v.body_name === s.body_name);
        const scheduled = s.outcome === "Scheduled";
        return (
          <li key={s.id} className={`rounded-xl border-l-4 border bg-card p-4 ${scheduled ? "border-dashed" : ""} ${STAGE_STYLE[s.kind].split(" ")[0]}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-semibold">
                <span className="text-muted font-normal">Step {i + 1}. </span>{s.kind === "staff_report" ? "Staff report" : s.body_name}
              </h3>
              <span className={`text-xs font-medium rounded-full border px-2 py-0.5 ${STAGE_STYLE[s.kind]}`}>
                {scheduled ? "Upcoming" : s.kind === "staff_report" ? "Recommendation" : s.kind === "city_council" ? "Final decision" : "Recommendation"}
              </span>
            </div>
            <p className="text-sm text-muted">{scheduled ? "Meeting on " : ""}{fmtDate(s.stage_date)}{s.kind === "staff_report" ? ` · by ${s.body_name}` : ""}</p>
            <p className="text-sm mt-1">{stageRole(s.kind)}</p>
            {s.outcome && !scheduled && <p className="text-sm mt-1"><span className="font-medium">Result:</span> {s.outcome}</p>}
            {vs.length > 0 && <ul className="mt-2 space-y-1">{vs.map((v) => <VoteLine key={v.id} v={v} />)}</ul>}
            <p className="text-sm mt-2"><a href={s.source_url}>Official record for this step</a></p>
          </li>
        );
      })}
    </ol>
  );
}
