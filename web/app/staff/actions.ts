"use server";
import { redirect } from "next/navigation";
import { updateTag } from "next/cache";
import { requireStaff, staffClient } from "@/lib/staff";

export async function login(formData: FormData) {
  const db = await staffClient();
  const { error } = await db.auth.signInWithPassword({
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
  });
  if (error) redirect("/staff/login?error=login");
  redirect("/staff");
}

export async function logout() {
  const db = await staffClient();
  await db.auth.signOut();
  redirect("/staff/login");
}

// What each button does: the status it moves the sentence to, and which tab may use it.
const ACTIONS: Record<string, { to: string; from: string[] }> = {
  approve:   { to: "approved",   from: ["unreviewed", "needs_rereview"] },
  reject:    { to: "rejected",   from: ["unreviewed", "needs_rereview"] },
  restore:   { to: "unreviewed", from: ["rejected"] },   // rejected by mistake -> back to review
  unpublish: { to: "unreviewed", from: ["approved"] },   // take it off the public card
  discard:   { to: "discarded",  from: ["rejected"] },   // permanent; the database then locks it
};

/** One review action on one sentence. Wording can be edited only when approving. */
export async function review(formData: FormData) {
  const user = await requireStaff();
  const id = Number(formData.get("id"));
  const ref = String(formData.get("ref"));
  const tab = String(formData.get("tab") ?? "review");
  const action = String(formData.get("action"));
  const back = `/staff?item=${encodeURIComponent(ref)}&tab=${tab}`;

  if (user.role !== "clerk") redirect(`${back}&demo=1`);
  const rule = ACTIONS[action];
  if (!rule) redirect(back);

  const db = await staffClient();
  const { data: before } = await db.from("claims").select("text_en,status").eq("id", id).single();
  if (!before || !rule.from.includes(before.status)) redirect(back);
  const text = action === "approve" ? String(formData.get("text") ?? "").trim() || before.text_en : before.text_en;
  const edited = text !== before.text_en;

  const { data, error } = await db.from("claims").update({ status: rule.to, text_en: text }).eq("id", id).select("id");
  if (error) throw new Error(error.message);
  if (!data || data.length !== 1) throw new Error("Not saved: this account is not allowed to review.");
  await db.from("reviews").insert({
    claim_id: id, reviewer: user.id, action: action === "approve" && edited ? "edit" : action,
    before_text: before.text_en, after_text: text,
  });
  updateTag(`item:${ref}`);
  redirect(`${back}&done=${action}`);
}
