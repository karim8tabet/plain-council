import type { StageKind } from "./data";

// Ward names under Toronto's 25-ward model (City of Toronto, "City Wards" open data).
export const WARDS: Record<number, string> = {
  1: "Etobicoke North", 2: "Etobicoke Centre", 3: "Etobicoke-Lakeshore", 4: "Parkdale-High Park",
  5: "York South-Weston", 6: "York Centre", 7: "Humber River-Black Creek", 8: "Eglinton-Lawrence",
  9: "Davenport", 10: "Spadina-Fort York", 11: "University-Rosedale", 12: "Toronto-St. Paul's",
  13: "Toronto Centre", 14: "Toronto-Danforth", 15: "Don Valley West", 16: "Don Valley East",
  17: "Don Valley North", 18: "Willowdale", 19: "Beaches-East York", 20: "Scarborough Southwest",
  21: "Scarborough Centre", 22: "Scarborough-Agincourt", 23: "Scarborough North",
  24: "Scarborough-Guildwood", 25: "Scarborough-Rouge Park",
};

/** "2026-05-21" -> "May 21, 2026" (dates are calendar dates; never shifted by time zone). */
export function fmtDate(d: string | null | undefined): string {
  if (!d) return "";
  const day = new Date(d.slice(0, 10) + "T12:00:00Z");
  return day.toLocaleDateString("en-CA", { timeZone: "UTC", year: "numeric", month: "long", day: "numeric" });
}

export function fmtDateTime(d: string | null | undefined): string {
  if (!d) return "";
  return new Date(d).toLocaleString("en-CA", {
    timeZone: "America/Toronto", year: "numeric", month: "long", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

/** The tag shown on every sentence, so nobody mistakes a recommendation for a decision. */
export function stageTag(kind: StageKind, body: string | undefined, date: string | null): string {
  const when = date ? ` (${fmtDate(date)})` : "";
  switch (kind) {
    case "staff_report": return `From the staff report${when}`;
    case "city_council": return `From the City Council decision${when}`;
    default: return `From the ${body ?? "committee"} recommendation${when}`;
  }
}

/** Short role of each stage in plain words. */
export function stageRole(kind: StageKind): string {
  switch (kind) {
    case "staff_report": return "City staff wrote a report with recommendations.";
    case "city_council": return "City Council made the final decision.";
    case "board": return "This board gives advice before City Council decides.";
    default: return "This committee recommends what City Council should do. Council can change it.";
  }
}

export const SECTION_TITLES: Record<string, string> = {
  what: "What is proposed or decided",
  reasons: "Reasons given in the staff report",
  who_where: "Who and where it affects",
  conditions: "Conditions, limits and amounts",
  uncertainty: "Not yet known",
  change: "What changed along the way",
};
export const SECTION_ORDER = ["what", "who_where", "conditions", "change", "reasons", "uncertainty"];

export const REQUEST_STATUS: Record<string, string> = {
  open: "Open: the report has been requested and is not yet done.",
  closed: "Closed: City staff say a later agenda item answered this request.",
  ongoing: "Ongoing: staff report back on this regularly.",
  due: "Due: the report-back date has passed and no report has been submitted yet.",
  ncf: "Not carried forward: this request was still outstanding at the end of the council term and was not moved to the new term's log. This does not mean the work was done or cancelled.",
};
