import { Suspense } from "react";
import { getAllItems } from "@/lib/data";
import { ItemList } from "@/components/ItemList";

export const metadata = { title: "All items" };

async function All() {
  return <ItemList items={await getAllItems()} />;
}

export default function Page() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">All items</h1>
      <Suspense fallback={<p>Loading items…</p>}><All /></Suspense>
    </div>
  );
}
