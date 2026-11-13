// Staff session (Supabase Auth via cookies). Never cached: every request re-checks the
// user. All writes go through row-level security as the signed-in user, so a demo
// account or a logged-out visitor cannot change anything even if they call the action.
import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function staffClient() {
  // Staff screens always run per request. Without this, Next.js tries to prerender them and
  // trips over the Supabase client reading the clock (Date.now) to check token expiry.
  await connection();
  const store = await cookies();
  return createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list) => {
        try {
          list.forEach(({ name, value, options }) => store.set(name, value, options));
        } catch {
          // Called from a Server Component: cookies are read-only there; proxy.ts refreshes them.
        }
      },
    },
  });
}

export type StaffUser = { id: string; email: string; role: "clerk" | "demo" };

export async function requireStaff(): Promise<StaffUser> {
  const db = await staffClient();
  const { data: { user } } = await db.auth.getUser(); // verified with Supabase, not just the cookie
  if (!user) redirect("/staff/login");
  const { data: profile } = await db.from("staff_profiles").select("role").eq("user_id", user.id).maybeSingle();
  if (!profile) redirect("/staff/login?error=not-staff");
  return { id: user.id, email: user.email ?? "", role: profile.role };
}
