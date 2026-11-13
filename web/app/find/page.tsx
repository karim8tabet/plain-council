import { Suspense } from "react";
import Link from "next/link";
import { redirect } from "next/navigation";
import FSA_WARDS from "@/lib/fsa-wards.json";
import { WARDS } from "@/lib/labels";

// Postal code area (first 3 characters, "FSA") -> wards it overlaps. Precomputed from
// public boundary files; one area can touch several wards, so the resident picks.
const LOOKUP = FSA_WARDS as Record<string, number[]>;

async function Result({ searchParams }: { searchParams: Promise<{ pc?: string }> }) {
  const fsa = ((await searchParams).pc ?? "").replace(/\s+/g, "").slice(0, 3).toUpperCase();
  const wards = LOOKUP[fsa] ?? [];
  if (wards.length === 1) redirect(`/ward/${wards[0]}`);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Postal code area {fsa || "?"}</h1>
      {wards.length > 1 ? (
        <>
          <p>This postal code area crosses more than one ward. Which one is yours?</p>
          <ul className="space-y-1">
            {wards.map((w) => <li key={w}><Link href={`/ward/${w}`}>Ward {w}: {WARDS[w]}</Link></li>)}
          </ul>
        </>
      ) : (
        <p>We couldn&apos;t match that postal code area. Please <Link href="/">choose your ward from the list</Link>.</p>
      )}
      <p className="text-sm text-muted">
        Not sure which is yours? Enter your full address on the City&apos;s <a href="https://www.toronto.ca/city-government/council/members-of-council/">Members of Council page</a> to find your ward and councillor.
      </p>
    </div>
  );
}

export default function Page(props: PageProps<"/find">) {
  return (
    <Suspense fallback={<p>Finding your ward…</p>}>
      <Result searchParams={props.searchParams as Promise<{ pc?: string }>} />
    </Suspense>
  );
}
