// 1. /find: a postal code area inside a single ward goes straight to that ward. Done here,
//    before the page starts streaming, because a redirect from inside a streamed page can stall.
// 2. /staff: keeps staff login sessions fresh (Supabase tokens expire after an hour).
//    Public pages never touch cookies.
import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";
import FSA_WARDS from "@/lib/fsa-wards.json";

const LOOKUP = FSA_WARDS as Record<string, number[]>;

export async function proxy(request: NextRequest) {
  if (request.nextUrl.pathname === "/find") {
    const fsa = (request.nextUrl.searchParams.get("pc") ?? "").replace(/\s+/g, "").slice(0, 3).toUpperCase();
    const wards = LOOKUP[fsa] ?? [];
    if (wards.length === 1) return NextResponse.redirect(new URL(`/ward/${wards[0]}`, request.url));
    return NextResponse.next();
  }
  let response = NextResponse.next({ request });
  const db = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list) => {
        list.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        list.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });
  await db.auth.getUser();
  return response;
}

export const config = { matcher: ["/find", "/staff/:path*"] };
