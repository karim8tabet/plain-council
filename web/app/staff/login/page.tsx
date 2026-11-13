import { Suspense } from "react";
import { login } from "../actions";

export const metadata = { title: "Staff sign in" };

async function ErrorNote({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const e = (await searchParams).error;
  if (!e) return null;
  return (
    <p role="alert" className="rounded-lg border border-warn bg-warn-soft text-warn p-3 text-sm">
      {e === "not-staff" ? "This account is not set up as staff." : "Email or password is not correct."}
    </p>
  );
}

export default function Page(props: PageProps<"/staff/login">) {
  return (
    <div className="max-w-sm space-y-4">
      <h1 className="text-2xl font-semibold">Staff sign in</h1>
      <p className="text-sm text-muted">For City staff who review plain-language summaries before they are published.</p>
      <Suspense fallback={null}><ErrorNote searchParams={props.searchParams as Promise<{ error?: string }>} /></Suspense>
      <form action={login} className="space-y-3">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Email</span>
          <input name="email" type="email" required autoComplete="username" className="rounded-lg border border-line bg-paper px-3 py-2" />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Password</span>
          <input name="password" type="password" required autoComplete="current-password" className="rounded-lg border border-line bg-paper px-3 py-2" />
        </label>
        <button className="rounded-lg bg-accent px-4 py-2 font-medium text-paper">Sign in</button>
      </form>
    </div>
  );
}
