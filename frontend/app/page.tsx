import Link from "next/link";

import { BackendStatus } from "@/components/landing/backend-status";
import { buttonVariants } from "@/components/ui/button";

// Landing page (placeholder). Google sign-in comes here next.
export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">Swiggy Party Agent</h1>
      <p className="text-muted-foreground">
        Share one link, collect everyone&apos;s food preferences, and let the agent plan the
        order.
      </p>
      {/* A link styled as a button (this shadcn Button is Base UI and has no asChild). */}
      <Link href="/host" className={buttonVariants({ className: "w-full sm:w-auto" })}>
        Host a party
      </Link>
      <BackendStatus />
    </main>
  );
}
