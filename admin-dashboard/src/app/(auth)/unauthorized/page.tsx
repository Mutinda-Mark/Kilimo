import {
  Ban,
  Leaf,
} from "lucide-react"

import Link from "next/link"

export const metadata = {
  title:
    "Access restricted",
}


export default function UnauthorizedPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/20 px-6">

      <div className="w-full max-w-md text-center">

        <div className="mb-8 flex justify-center">
          <div className="flex size-12 items-center justify-center rounded-xl border bg-background">
            <Leaf className="size-5" />
          </div>
        </div>


        <div className="mx-auto mb-5 flex size-12 items-center justify-center rounded-full bg-destructive/10">
          <Ban className="size-5 text-destructive" />
        </div>


        <h1 className="text-2xl font-semibold tracking-tight">
          Administrator access required
        </h1>

        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          Your Google account was authenticated successfully,
          but it is not currently authorised to access the
          KILIMO administration console.
        </p>


        <Link
            href="/sign-in"
            className="mt-8 inline-flex h-9 items-center justify-center rounded-md border bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
            Return to sign in
        </Link>

      </div>

    </main>
  )
}