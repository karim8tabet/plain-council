import { notFound } from "next/navigation";
import { Suspense } from "react";
import Link from "next/link";
import { getItemsForWard } from "@/lib/data";
import { WARDS } from "@/lib/labels";
import { ItemList } from "@/components/ItemList";

export function generateStaticParams() {
  return Object.keys(WARDS).map((ward) => ({ ward }));
}

async function WardItems({ params }: { params: Promise<{ ward: string }> }) {
  const n = Number((await params).ward);
  if (!WARDS[n]) notFound();
  const items = await getItemsForWard(n);
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm"><Link href="/">← Choose another ward</Link></p>
        <h1 className="text-2xl font-semibold mt-2">Ward {n}: {WARDS[n]}</h1>
        <p className="text-muted">Council items that name this ward, plus city-wide items.</p>
      </div>
      <ItemList items={items} />
    </div>
  );
}

export default function Page(props: PageProps<"/ward/[ward]">) {
  return (
    <Suspense fallback={<p>Loading items…</p>}>
      <WardItems params={props.params} />
    </Suspense>
  );
}
