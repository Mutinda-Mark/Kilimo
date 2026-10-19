"use client"

import {
  RefreshCw,
} from "lucide-react"

import {
  useRouter,
} from "next/navigation"

import {
  useState,
} from "react"


export function DashboardRefresh() {
  const router =
    useRouter()

  const [
    refreshing,
    setRefreshing,
  ] =
    useState(false)

  const [
    updatedAt,
    setUpdatedAt,
  ] =
    useState(
      () =>
        new Date()
    )


  async function refresh() {
    setRefreshing(true)

    router.refresh()

    setUpdatedAt(
      new Date()
    )

    window.setTimeout(
      () =>
        setRefreshing(false),
      500
    )
  }


  return (
    <div className="hidden items-center gap-2 2xl:flex">

      <span className="font-mono text-[10px] text-muted-foreground">
        Updated{" "}
        {updatedAt.toLocaleTimeString(
          "en-KE",
          {
            hour:
              "2-digit",
            minute:
              "2-digit",
          }
        )}
      </span>


      <button
        type="button"
        aria-label="Refresh dashboard data"
        title="Refresh"
        disabled={
          refreshing
        }
        onClick={
          refresh
        }
        className="flex size-9 items-center justify-center rounded-lg border bg-background text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
      >

        <RefreshCw
          className={
            `size-3.5 ${
              refreshing
                ? "animate-spin"
                : ""
            }`
          }
        />

      </button>

    </div>
  )
}