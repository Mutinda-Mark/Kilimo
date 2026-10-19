import Link from "next/link"

import {
  ArrowRight,
  Leaf,
  MessageSquareText,
  Search,
  Users,
} from "lucide-react"

import {
  getDashboardSummary,
  getFarmerSessions,
} from "@/lib/kilimo-api"

import {
  Badge,
} from "@/components/ui/badge"

import {
  Card,
  CardContent,
} from "@/components/ui/card"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"


function percentage(
  value: number | null
) {
  if (value === null) {
    return "—"
  }

  return `${(value * 100).toFixed(1)}%`
}


function formatDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-KE",
    {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Africa/Nairobi",
    }
  ).format(new Date(value))
}


function maskPhoneNumber(
  phoneNumber: string
) {
  if (phoneNumber.length < 8) {
    return phoneNumber
  }

  return (
    `${phoneNumber.slice(0, 6)}••••${phoneNumber.slice(-3)}`
  )
}


function severityClass(
  severity: string | null
) {
  const value =
    severity?.toLowerCase() ?? ""

  if (
    value.includes("high") ||
    value.includes("severe")
  ) {
    return "border-red-200 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
  }

  if (
    value.includes("moderate") ||
    value.includes("medium")
  ) {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300"
  }

  if (
    value.includes("low") ||
    value.includes("none")
  ) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"
  }

  return ""
}


interface FarmersPageProps {
  searchParams: Promise<{
    q?: string
  }>
}


export default async function FarmersPage({
  searchParams,
}: FarmersPageProps) {
  const {
    q = "",
  } =
    await searchParams

  const [
    data,
    summary,
  ] =
    await Promise.all([
      getFarmerSessions(
        100,
        0
      ),
      getDashboardSummary(),
    ])


  const assessedFarmers =
    data.sessions.filter(
      (session) =>
        session.last_disease !== null
    ).length


  const normalizedQuery =
    q.trim().toLowerCase()


  const filteredSessions =
    normalizedQuery
      ? data.sessions.filter(
          (session) =>
            session.phone_number
              .toLowerCase()
              .includes(
                normalizedQuery
              ) ||
            session.last_disease
              ?.toLowerCase()
              .includes(
                normalizedQuery
              ) ||
            session.last_severity
              ?.toLowerCase()
              .includes(
                normalizedQuery
              )
        )
      : data.sessions


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1600px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Page header */}

        <section className="flex flex-col gap-5 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Farmer operations
            </p>

            <h1 className="text-3xl font-semibold tracking-tight">
              Farmers
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Inspect farmer sessions, previous disease assessments,
              activity and contextual WhatsApp interactions.
            </p>

          </div>


          <form
            method="GET"
            className="relative w-full lg:w-80"
          >

            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

            <input
              name="q"
              defaultValue={q}
              placeholder="Search farmer or disease..."
              className="h-10 w-full rounded-lg border bg-background pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/20"
            />

          </form>

        </section>


        {/* Summary metrics */}

        <section className="mt-6 grid gap-4 md:grid-cols-3">

          <Card className="shadow-none">
            <CardContent className="p-5">

              <div className="flex items-start justify-between">

                <div>

                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Total sessions
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {summary.total_sessions}
                  </p>

                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <Users className="size-4" />
                </div>

              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Registered WhatsApp conversation sessions
              </p>

            </CardContent>
          </Card>


          <Card className="shadow-none">
            <CardContent className="p-5">

              <div className="flex items-start justify-between">

                <div>

                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    With assessments
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {assessedFarmers}
                  </p>

                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <Leaf className="size-4" />
                </div>

              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Farmers with a stored disease assessment
              </p>

            </CardContent>
          </Card>


          <Card className="shadow-none">
            <CardContent className="p-5">

              <div className="flex items-start justify-between">

                <div>

                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Active 24 hours
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {summary.active_sessions_24h}
                  </p>

                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <MessageSquareText className="size-4" />
                </div>

              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Sessions active during the last 24 hours
              </p>

            </CardContent>
          </Card>

        </section>


        {/* Farmer table */}

        <section className="mt-6 overflow-hidden rounded-xl border bg-card">

          <div className="flex items-center justify-between border-b px-5 py-4">

            <div>

              <h2 className="text-sm font-semibold">
                Farmer sessions
              </h2>

              <p className="mt-1 text-xs text-muted-foreground">
                Showing{" "}
                <span className="font-mono tabular-nums">
                  {filteredSessions.length}
                </span>{" "}
                session
                {filteredSessions.length === 1
                  ? ""
                  : "s"}
              </p>

            </div>

          </div>


          <div className="overflow-x-auto">

            <Table>

              <TableHeader>

                <TableRow className="hover:bg-transparent">

                  <TableHead>
                    Farmer
                  </TableHead>

                  <TableHead>
                    Language
                  </TableHead>

                  <TableHead>
                    Latest assessment
                  </TableHead>

                  <TableHead>
                    Severity
                  </TableHead>

                  <TableHead>
                    Confidence
                  </TableHead>

                  <TableHead>
                    Last active
                  </TableHead>

                  <TableHead className="w-20" />

                </TableRow>

              </TableHeader>


              <TableBody>

                {filteredSessions.map(
                  (session) => (

                    <TableRow
                      key={
                        session.phone_number
                      }
                      className="group transition-colors"
                    >

                      <TableCell>

                        <div>

                          <p className="font-mono text-xs font-medium">
                            {maskPhoneNumber(
                              session.phone_number
                            )}
                          </p>

                          <p className="mt-1 text-[11px] text-muted-foreground">
                            WhatsApp farmer
                          </p>

                        </div>

                      </TableCell>


                      <TableCell>

                        <Badge
                          variant="outline"
                          className="font-mono text-[10px] uppercase"
                        >
                          {session.language}
                        </Badge>

                      </TableCell>


                      <TableCell>

                        {session.last_disease ? (

                          <span className="text-sm font-medium">
                            {session.last_disease}
                          </span>

                        ) : (

                          <span className="text-sm text-muted-foreground">
                            No assessment
                          </span>

                        )}

                      </TableCell>


                      <TableCell>

                        {session.last_severity ? (

                          <Badge
                            variant="outline"
                            className={
                              severityClass(
                                session.last_severity
                              )
                            }
                          >
                            {session.last_severity}
                          </Badge>

                        ) : (

                          <span className="text-muted-foreground">
                            —
                          </span>

                        )}

                      </TableCell>


                      <TableCell className="font-mono text-xs tabular-nums">

                        {percentage(
                          session.last_confidence
                        )}

                      </TableCell>


                      <TableCell className="font-mono text-xs text-muted-foreground">

                        {formatDate(
                          session.last_active_at
                        )}

                      </TableCell>


                      <TableCell className="text-right">

                        <Link
                          href={
                            `/farmers/${
                              encodeURIComponent(
                                session.phone_number
                              )
                            }`
                          }
                          aria-label="View farmer session"
                          className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                        >
                          <ArrowRight className="size-4" />
                        </Link>

                      </TableCell>

                    </TableRow>

                  )
                )}

              </TableBody>

            </Table>


            {filteredSessions.length === 0 && (

              <div className="px-6 py-16 text-center">

                <Users className="mx-auto size-6 text-muted-foreground" />

                <p className="mt-4 text-sm font-medium">
                  No farmer sessions found
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Try adjusting your search query.
                </p>

              </div>

            )}

          </div>

        </section>

      </div>

    </main>
  )
}