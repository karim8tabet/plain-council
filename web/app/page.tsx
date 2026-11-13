import Link from "next/link";
import { WARDS } from "@/lib/labels";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold leading-tight">What is Toronto City Council deciding near you?</h1>
        <p className="text-muted max-w-prose">
          Plain-language summaries of council items: what is proposed, who it affects, where it is in the
          process, and whether you can still have a say. Every sentence links to the official record.
        </p>
      </section>

      <section aria-labelledby="find" className="rounded-xl border border-line bg-card p-5 space-y-3">
        <h2 id="find" className="text-xl font-semibold">Find your ward</h2>
        <form action="/find" method="get" className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium">First 3 characters of your postal code</span>
            <input
              name="pc" required minLength={3} maxLength={3} autoComplete="postal-code" inputMode="text"
              placeholder="e.g. M5V" pattern="[Mm]\s*\d\s*[A-Za-z].*"
              title="Toronto postal codes start with M, then a number and a letter (e.g. M5V)"
              className="w-40 rounded-lg border border-line bg-paper px-3 py-2 uppercase text-lg"
            />
          </label>
          <button className="rounded-lg bg-accent px-4 py-2 font-medium text-paper">Show my ward</button>
        </form>
        <p className="text-sm text-muted">
          Only the first 3 characters are used, and nothing is stored. Not sure? Use the City&apos;s{" "}
          <a href="https://www.toronto.ca/city-government/council/members-of-council/">official ward finder</a>.
        </p>
      </section>

      <section aria-labelledby="wards" className="space-y-3">
        <h2 id="wards" className="text-xl font-semibold">Or choose a ward</h2>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
          {Object.entries(WARDS).map(([n, name]) => (
            <li key={n}><Link href={`/ward/${n}`}>Ward {n}: {name}</Link></li>
          ))}
        </ul>
      </section>
    </div>
  );
}
