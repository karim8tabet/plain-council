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

/** Approve (optionally with edited wording) or reject one sentence. */
export async function review(formData: FormData) {
  const user = await requireStaff();
  const id = Number(formData.get("id"));
  const ref = String(formData.get("ref"));
  const action = String(formData.get("action"));
  const text = String(formData.get("text") ?? "").trim();
  const back = `/staff?item=${encodeURIComponent(ref)}#c${id}`;

  if (user.role !== "clerk") redirect(`${back.split("#")[0]}&demo=1#c${id}`);
  if (!["approve", "reject"].includes(action) || !text) redirect(back);

  const db = await staffClient();
  const { data: before } = await db.from("claims").select("text_en,status").eq("id", id).single();
  if (!before) redirect(back);
  const edited = text !== before.text_en;
  const { data, error } = await db.from("claims")
    .update({ status: action === "approve" ? "approved" : "rejected", text_en: text })
    .eq("id", id).select("id");
  if (error) throw new Error(error.message);
  if (!data || data.length !== 1) throw new Error("Not saved: this account is not allowed to review.");
  await db.from("reviews").insert({
    claim_id: id, reviewer: user.id,
    action: action === "reject" ? "reject" : edited ? "edit" : "approve",
    before_text: before.text_en, after_text: text,
  });
  updateTag(`item:${ref}`);
  redirect(back);
}
