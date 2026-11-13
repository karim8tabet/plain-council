import type { Claim, Passage } from "@/lib/data";
import { stageTag } from "@/lib/labels";

const TAG_STYLE: Record<string, string> = {
  staff_report: "bg-staff-soft text-staff",
  committee: "bg-committee-soft text-committee",
  community_council: "bg-committee-soft text-committee",
  board: "bg-committee-soft text-committee",
  city_council: "bg-council-soft text-council",
};

/** One plain sentence, its stage tag, and the exact source passage behind it. */
export function Sentence({ c, n, passage, body }: { c: Claim; n: number; passage?: Passage; body?: string }) {
  return (
    <li>
      <details className="group">
        <summary className="list-none">
          <span>{c.text_en}</span>{" "}
          <sup className="text-accent font-medium underline">[{n}]</sup>
          <span className={`ml-2 inline-block text-xs rounded px-1.5 py-0.5 align-middle ${TAG_STYLE[c.stage]}`}>
            {stageTag(c.stage, body, c.stage_date)}
          </span>
        </summary>
        <figure className="mt-2 mb-3 ml-3 border-l-2 border-line pl-3 text-sm">
          <blockquote className="italic">“{c.quote_display}”</blockquote>
          <figcaption className="text-muted mt-1">
            Source [{n}]: {passage ? <a href={passage.doc_url}>{passage.doc_title}</a> : "official record"}
            {passage?.page ? `, page ${passage.page}` : ""}. Quoted exactly as it appears in the source.
          </figcaption>
        </figure>
      </details>
    </li>
  );
}
