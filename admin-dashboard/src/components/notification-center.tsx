"use client"

import Link from "next/link"

import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Database,
  Info,
  LoaderCircle,
} from "lucide-react"

import {
  useEffect,
  useRef,
  useState,
} from "react"


interface NotificationItem {
  id: string
  severity:
    | "critical"
    | "warning"
    | "info"
  title: string
  description: string
  href: string
}


interface NotificationResponse {
  count: number
  notifications:
    NotificationItem[]
}


export function NotificationCenter() {
  const containerRef =
    useRef<HTMLDivElement>(
      null
    )

  const [
    open,
    setOpen,
  ] =
    useState(false)

  const [
    loading,
    setLoading,
  ] =
    useState(false)

  const [
    data,
    setData,
  ] =
    useState<NotificationResponse>({
      count: 0,
      notifications: [],
    })


  async function loadNotifications() {
    setLoading(true)

    try {
      const response =
        await fetch(
          "/api/notifications",
          {
            cache: "no-store",
          }
        )

      if (!response.ok) {
        return
      }

      const result =
        await response.json() as NotificationResponse

      setData(result)
    } catch (error) {
      console.error(
        "Unable to load notifications:",
        error
      )
    } finally {
      setLoading(false)
    }
  }


  useEffect(() => {
    function close(
      event: MouseEvent
    ) {
      if (
        containerRef.current &&
        !containerRef.current.contains(
          event.target as Node
        )
      ) {
        setOpen(false)
      }
    }

    document.addEventListener(
      "mousedown",
      close
    )

    return () =>
      document.removeEventListener(
        "mousedown",
        close
      )
  }, [])


  async function toggle() {
    const nextOpen =
      !open

    setOpen(nextOpen)

    if (nextOpen) {
      await loadNotifications()
    }
  }


  return (
    <div
      ref={containerRef}
      className="relative"
    >

      <button
        type="button"
        aria-label="System notifications"
        aria-expanded={open}
        onClick={toggle}
        className="relative flex size-9 items-center justify-center rounded-lg border bg-background text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >

        <Bell className="size-4" />


        {data.count > 0 && (

          <span className="absolute -right-1 -top-1 flex min-w-4 items-center justify-center rounded-full bg-red-500 px-1 font-mono text-[9px] font-semibold leading-4 text-white">
            {data.count > 9
              ? "9+"
              : data.count}
          </span>

        )}

      </button>


      {open && (

        <div className="absolute right-0 top-12 z-50 w-[360px] overflow-hidden rounded-xl border bg-popover shadow-xl">

          <div className="flex items-center justify-between border-b px-4 py-3">

            <div>

              <p className="text-sm font-semibold">
                System notifications
              </p>

              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Current operational alerts
              </p>

            </div>


            {loading && (
              <LoaderCircle className="size-4 animate-spin text-muted-foreground" />
            )}

          </div>


          <div className="max-h-[380px] overflow-y-auto p-2">

            {!loading &&
            data.notifications.length ===
              0 ? (

              <div className="px-4 py-10 text-center">

                <div className="mx-auto flex size-10 items-center justify-center rounded-full border bg-emerald-50 dark:bg-emerald-950/30">

                  <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />

                </div>

                <p className="mt-3 text-sm font-medium">
                  No active alerts
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  KILIMO has no current operational warnings.
                </p>

              </div>

            ) : (

              <div className="space-y-1">

                {data.notifications.map(
                  (notification) => (

                    <Link
                      key={
                        notification.id
                      }
                      href={
                        notification.href
                      }
                      onClick={() =>
                        setOpen(false)
                      }
                      className="flex gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-accent"
                    >

                      <NotificationIcon
                        severity={
                          notification.severity
                        }
                      />


                      <div className="min-w-0">

                        <p className="text-xs font-semibold">
                          {notification.title}
                        </p>

                        <p className="mt-1 text-[11px] leading-4 text-muted-foreground">
                          {notification.description}
                        </p>

                      </div>

                    </Link>

                  )
                )}

              </div>

            )}

          </div>


          <div className="border-t p-2">

            <Link
              href="/system"
              onClick={() =>
                setOpen(false)
              }
              className="flex h-9 items-center justify-center rounded-lg text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              Open system console
            </Link>

          </div>

        </div>

      )}

    </div>
  )
}


function NotificationIcon({
  severity,
}: {
  severity:
    | "critical"
    | "warning"
    | "info"
}) {
  if (
    severity === "critical"
  ) {
    return (
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-red-200 bg-red-50 dark:border-red-900/60 dark:bg-red-950/30">

        <Database className="size-3.5 text-red-600 dark:text-red-400" />

      </div>
    )
  }


  if (
    severity === "warning"
  ) {
    return (
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/30">

        <AlertTriangle className="size-3.5 text-amber-600 dark:text-amber-400" />

      </div>
    )
  }


  return (
    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/40">

      <Info className="size-3.5 text-muted-foreground" />

    </div>
  )
}