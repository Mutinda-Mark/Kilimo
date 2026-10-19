"use client"

import {
  AlertTriangle,
  RefreshCw,
} from "lucide-react"


export default function DashboardError({
  reset,
}: {
  error: Error & {
    digest?: string
  }
  reset: () => void
}) {
  return (
    <main className="flex min-h-[70vh] items-center justify-center px-6">

      <div className="max-w-md text-center">

        <div className="mx-auto flex size-12 items-center justify-center rounded-xl border bg-muted/40">

          <AlertTriangle className="size-5 text-amber-600 dark:text-amber-400" />

        </div>


        <h1 className="mt-5 text-xl font-semibold tracking-tight">
          Unable to load this view
        </h1>


        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          KILIMO could not retrieve the information required
          for this page. The backend or an external service
          may be temporarily unavailable.
        </p>


        <button
          type="button"
          onClick={
            reset
          }
          className="mt-6 inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
        >

          <RefreshCw className="size-4" />

          Try again

        </button>

      </div>

    </main>
  )
}