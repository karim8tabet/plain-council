import Link from "next/link";
import type { Item } from "@/lib/data";

export function ItemList({ items }: { items: Item[] }) {
  if (items.length === 0) return <p className="text-muted">No items loaded for this area yet.</p>;
  return (
    <ul className="space-y-3">
      {items.map((it) => (
        <li key={it.ref} className="rounded-xl border border-line bg-card p-4">
          <Link href={`/item/${it.ref}`} className="font-medium text-lg leading-snug">{it.title}</Link>
          <p className="text-sm text-muted mt-1">
            {it.ref} · {it.city_wide ? "City-wide" : `Ward ${it.wards.join(", ")}`}
            {it.decision_body ? ` · Latest: ${it.decision_body}` : ""}
          </p>
          {!it.has_card && <p className="text-sm mt-1">Plain-language summary not available yet. Official page linked inside.</p>}
        </li>
      ))}
    </ul>
  );
}
