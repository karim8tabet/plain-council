// Public data reads. Uses the publishable (anon) key, so row-level security applies:
// residents can only ever receive approved sentences. Cached for a few minutes and
// tagged per item so a clerk's approval can refresh a card immediately.
import "server-only";
import { createClient } from "@supabase/supabase-js";
import { cacheLife, cacheTag } from "next/cache";

function db() {
  return createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    auth: { persistSession: false },
  });
}

export type StageKind = "staff_report" | "committee" | "community_council" | "board" | "city_council";

export type Item = {
  ref: string; title: string; wards: number[]; city_wide: boolean; decision_body: string | null;
  status_text: string | null; item_url: string; has_card: boolean; source_changed: boolean;
  checked_at: string | null; reading_grade: number | null; public_submissions: number | null; updated_at: string;
};
export type Stage = {
  id: number; stage_order: number; kind: StageKind; body_name: string; stage_date: string | null;
  outcome: string | null; amended: boolean | null; decision_text: string | null; source_url: string;
};
export type Passage = { id: number; doc_title: string; doc_url: string; doc_date: string | null; stage: StageKind; page: number | null };
export type Claim = {
  id: number; section: string; sort_order: number; stage: StageKind; stage_date: string | null;
  text_en: string; text_fr: string | null; text_zh: string | null; passage_id: number | null; quote_display: string | null;
};
export type Vote = {
  id: number; voted_at: string | null; body_name: string; motion_type: string; motion_kind: "amendment" | "main_item" | "other";
  description: string | null; result: string; yes_count: number | null; no_count: number | null; source: string;
};
export type ReportRequest = { id: number; directive: string; status: string; closed_by: string | null; report_back_timing: string | null; assigned_to: string | null; source: string };
export type Participation = {
  status: "decided" | "upcoming" | "open"; meeting_at: string | null; meeting_place: string | null;
  method_text: string | null; method_url: string | null; method_source: string | null;
  deadline_text: string | null; deadline_source: string | null; privacy_notice: string | null;
};

export async function getItemsForWard(ward: number): Promise<Item[]> {
  "use cache";
  cacheLife("minutes");
  cacheTag("items");
  const { data, error } = await db().from("items").select("*")
    .or(`wards.cs.{${ward}},city_wide.eq.true`).order("updated_at", { ascending: false });
  if (error) throw error;
  return data as Item[];
}

export async function getAllItems(): Promise<Item[]> {
  "use cache";
  cacheLife("minutes");
  cacheTag("items");
  const { data, error } = await db().from("items").select("*").order("updated_at", { ascending: false });
  if (error) throw error;
  return data as Item[];
}

export type Card = {
  item: Item; stages: Stage[]; claims: Claim[]; passages: Passage[]; votes: Vote[];
  requests: ReportRequest[]; participation: Participation | null;
};

export async function getCard(ref: string): Promise<Card | null> {
  "use cache";
  cacheLife("minutes");
  cacheTag(`item:${ref}`);
  const c = db();
  const [item, stages, claims, passages, votes, requests, part] = await Promise.all([
    c.from("items").select("*").eq("ref", ref).maybeSingle(),
    c.from("stages").select("id,stage_order,kind,body_name,stage_date,outcome,amended,decision_text,source_url").eq("item_ref", ref).order("stage_order"),
    c.from("claims").select("id,section,sort_order,stage,stage_date,text_en,text_fr,text_zh,passage_id,quote_display").eq("item_ref", ref).order("sort_order"),
    c.from("passages").select("id,doc_title,doc_url,doc_date,stage,page").eq("item_ref", ref),
    c.from("votes").select("*").eq("item_ref", ref).order("voted_at"),
    c.from("report_requests").select("*").eq("item_ref", ref).order("id"),
    c.from("participation").select("*").eq("item_ref", ref).maybeSingle(),
  ]);
  for (const r of [item, stages, claims, passages, votes, requests, part]) if (r.error) throw r.error;
  if (!item.data) return null;
  return {
    item: item.data as Item, stages: stages.data as Stage[], claims: claims.data as Claim[],
    passages: passages.data as Passage[], votes: votes.data as Vote[], requests: requests.data as ReportRequest[],
    participation: part.data as Participation | null,
  };
}
