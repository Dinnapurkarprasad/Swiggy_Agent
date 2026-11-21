import { Suspense } from "react";

// Guest form (placeholder). Public: guests open the shared link on their phones, no login.
export default function GuestPage({ params }: PageProps<"/p/[partyId]">) {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-4
     py-8">
      <h1 className="text-2xl font-semibold">You&apos;re invited!</h1>
      {/* params is request-time data, so it is read inside Suspense (Cache Components). */}
      <Suspense fallback={<p className="text-muted-foreground">Loading…</p>}>
        <PartyId params={params} />
      </Suspense>
    </main>
  );
}

async function PartyId({ params }: { params: PageProps<"/p/[partyId]">["params"] }) {
  const { partyId } = await params;
  return (
    <p className="text-muted-foreground">
      The food preference form for party <span className="font-mono">{partyId}</span> will
      appear here.
    </p>
  );
}
