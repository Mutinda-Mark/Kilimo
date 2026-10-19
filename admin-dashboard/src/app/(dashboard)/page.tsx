import Link from "next/link"

import {
  Activity,
  ArrowRight,
  ClipboardCheck,
  Database,
  MessageSquareText,
  Users,
  Wifi,
  BrainCircuit,
} from "lucide-react"

import {
  getDashboardSummary,
  getDiseaseStatistics,
  getRecentAssessments,
  getDatabaseStatistics,
  getWhatsAppStatistics,
  getModelInformation,
} from "@/lib/kilimo-api"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import {
  Badge,
} from "@/components/ui/badge"


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
  phoneNumber: string | null
) {
  if (!phoneNumber) {
    return "API user"
  }

  if (phoneNumber.length < 8) {
    return phoneNumber
  }

  return (
    `${phoneNumber.slice(0, 6)}••••${phoneNumber.slice(-3)}`
  )
}


function severityClass(
  severity: string
) {
  const value =
    severity.toLowerCase()

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

  return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"
}


export default async function DashboardPage() {
  const [
    summary,
    assessmentData,
    diseaseData,
    database,
    whatsapp,
    model,
  ] =
    await Promise.all([
      getDashboardSummary(),
      getRecentAssessments(8),
      getDiseaseStatistics(),
      getDatabaseStatistics(),
      getWhatsAppStatistics(),
      getModelInformation(),
    ])

  const topDisease =
    diseaseData.diseases[0]

  return (
    <main className="min-h-screen">
      <div className="mx-auto w-full max-w-[1600px] px-6 py-8 lg:px-8 xl:px-10">

        <section className="flex flex-col gap-4 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Workspace overview
            </p>

            <h1 className="text-3xl font-semibold tracking-tight">
              Overview
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Monitor farmer activity, tomato disease assessments,
              messaging performance and platform health.
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-50" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>

            <span className="text-xs font-medium">
              All systems operational
            </span>
          </div>
        </section>


        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <Card className="shadow-none">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Farmers
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
                <span className="font-medium text-foreground">
                  {summary.active_sessions_24h}
                </span>{" "}
                active in the last 24 hours
              </p>
            </CardContent>
          </Card>


          <Card className="shadow-none">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Assessments
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {summary.total_assessments}
                  </p>
                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <ClipboardCheck className="size-4" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Tomato image analyses stored
              </p>
            </CardContent>
          </Card>


          <Card className="shadow-none">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Avg confidence
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {percentage(
                      summary.average_confidence
                    )}
                  </p>
                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <Activity className="size-4" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Across stored model predictions
              </p>
            </CardContent>
          </Card>


          <Card className="shadow-none">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Messages
                  </p>

                  <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
                    {summary.total_messages}
                  </p>
                </div>

                <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
                  <MessageSquareText className="size-4" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Farmer and system conversation records
              </p>
            </CardContent>
          </Card>

        </section>


        <section className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_0.55fr]">

          <Card className="shadow-none">
            <CardHeader className="flex flex-row items-center justify-between border-b">
              <div>
                <CardTitle className="text-base">
                  Recent assessments
                </CardTitle>

                <p className="mt-1 text-xs text-muted-foreground">
                  Latest tomato image analyses completed by KILIMO.
                </p>
              </div>

              <Link
                href="/assessments"
                className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                View all

                <ArrowRight className="size-3.5" />
              </Link>
            </CardHeader>

            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>
                        Farmer
                      </TableHead>

                      <TableHead>
                        Condition
                      </TableHead>

                      <TableHead>
                        Confidence
                      </TableHead>

                      <TableHead>
                        Severity
                      </TableHead>

                      <TableHead>
                        Source
                      </TableHead>

                      <TableHead className="text-right">
                        Time
                      </TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {assessmentData.assessments.map(
                      (assessment) => (
                        <TableRow
                          key={assessment.id}
                          className="transition-colors"
                        >
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {maskPhoneNumber(
                              assessment.phone_number
                            )}
                          </TableCell>

                          <TableCell className="font-medium">
                            {assessment.disease}
                          </TableCell>

                          <TableCell className="font-mono text-xs tabular-nums">
                            {percentage(
                              assessment.confidence
                            )}
                          </TableCell>

                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                severityClass(
                                  assessment.severity
                                )
                              }
                            >
                              {assessment.severity}
                            </Badge>
                          </TableCell>

                          <TableCell className="capitalize text-sm text-muted-foreground">
                            {assessment.source}
                          </TableCell>

                          <TableCell className="text-right font-mono text-xs text-muted-foreground">
                            {formatDate(
                              assessment.created_at
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    )}
                  </TableBody>
                </Table>

                {assessmentData.assessments.length === 0 && (
                  <div className="px-6 py-14 text-center">
                    <ClipboardCheck className="mx-auto size-5 text-muted-foreground" />

                    <p className="mt-3 text-sm font-medium">
                      No assessments yet
                    </p>

                    <p className="mt-1 text-xs text-muted-foreground">
                      Completed tomato assessments will appear here.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>


          <div className="space-y-6">

            <Card className="shadow-none">
              <CardHeader className="border-b">
                <CardTitle className="text-base">
                  System health
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-4 p-5">

                <HealthRow
                  icon={Database}
                  label="PostgreSQL"
                  detail={`${database.assessments} assessments`}
                  healthy={database.connected}
                />

                <HealthRow
                  icon={Wifi}
                  label="WhatsApp"
                  detail={`${whatsapp.failed} failed`}
                  healthy={whatsapp.failed === 0}
                />

                <HealthRow
                  icon={BrainCircuit}
                  label="Vision model"
                  detail={`${model.backbone} · ${model.num_classes} classes`}
                  healthy={model.status.toLowerCase() === "ready"}
                />

              </CardContent>
            </Card>


            <Card className="shadow-none">
              <CardHeader className="border-b">
                <CardTitle className="text-base">
                  Assessment snapshot
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-4 p-5">
                <div>
                  <p className="text-xs text-muted-foreground">
                    Most common condition
                  </p>

                  <p className="mt-1 text-sm font-medium">
                    {topDisease?.disease ?? "No data"}
                  </p>
                </div>

                <div className="h-px bg-border" />

                <div>
                  <p className="text-xs text-muted-foreground">
                    Total processed WhatsApp events
                  </p>

                  <p className="mt-1 font-mono text-lg font-semibold tabular-nums">
                    {whatsapp.total}
                  </p>
                </div>

                <div className="h-px bg-border" />

                <div>
                  <p className="text-xs text-muted-foreground">
                    Completed WhatsApp events
                  </p>

                  <p className="mt-1 font-mono text-lg font-semibold tabular-nums">
                    {whatsapp.completed}
                  </p>
                </div>
              </CardContent>
            </Card>

          </div>

        </section>

      </div>
    </main>
  )
}


function HealthRow({
  icon: Icon,
  label,
  detail,
  healthy,
}: {
  icon: React.ComponentType<{
    className?: string
  }>
  label: string
  detail: string
  healthy: boolean
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex size-8 items-center justify-center rounded-lg border bg-muted/40">
        <Icon className="size-3.5" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">
          {label}
        </p>

        <p className="truncate text-xs text-muted-foreground">
          {detail}
        </p>
      </div>

      <span
        className={
          healthy
            ? "size-2 rounded-full bg-emerald-500"
            : "size-2 rounded-full bg-amber-500"
        }
      />
    </div>
  )
}