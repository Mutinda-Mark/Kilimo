import Link from "next/link"

import {
  Activity,
  CalendarDays,
  Gauge,
  Leaf,
  Smartphone,
} from "lucide-react"

import {
  getAssessmentActivity,
  getDashboardSummary,
  getDiseaseStatistics,
  getSeverityStatistics,
  getSourceStatistics,
} from "@/lib/kilimo-api"

import {
  AnalyticsCharts,
} from "@/components/analytics-charts"

import {
  Card,
  CardContent,
} from "@/components/ui/card"


function percentage(
  value: number | null
) {
  if (value === null) {
    return "—"
  }

  return `${(value * 100).toFixed(1)}%`
}


interface AnalyticsPageProps {
  searchParams: Promise<{
    days?: string
  }>
}


export default async function AnalyticsPage({
  searchParams,
}: AnalyticsPageProps) {
  const {
    days: daysParam,
  } = await searchParams

  const requestedDays =
    Number(daysParam)

  const days =
    [7, 14, 30].includes(
      requestedDays
    )
      ? requestedDays
      : 14


  const [
    summary,
    diseaseData,
    severityData,
    sourceData,
    activityData,
  ] =
    await Promise.all([
      getDashboardSummary(),
      getDiseaseStatistics(),
      getSeverityStatistics(),
      getSourceStatistics(),
      getAssessmentActivity(days),
    ])


  const mostCommonDisease =
    diseaseData.diseases[0] ??
    null

  const mostCommonSource =
    sourceData.sources[0] ??
    null


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1700px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Header */}

        <section className="flex flex-col gap-5 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Platform intelligence
            </p>

            <h1 className="text-3xl font-semibold tracking-tight">
              Analytics
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Explore assessment activity, disease patterns,
              confidence levels and system usage across KILIMO.
            </p>

          </div>


          <div className="flex items-center gap-1 rounded-lg border bg-card p-1">

            {[7, 14, 30].map(
              (period) => (

                <Link
                  key={period}
                  href={`/analytics?days=${period}`}
                  className={
                    `rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                      days === period
                        ? "bg-foreground text-background"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    }`
                  }
                >
                  {period} days
                </Link>

              )
            )}

          </div>

        </section>


        {/* Summary */}

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <MetricCard
            label="Assessments"
            value={
              String(
                summary.total_assessments
              )
            }
            description="Total stored predictions"
            icon={Activity}
          />

          <MetricCard
            label="Average confidence"
            value={
              percentage(
                summary.average_confidence
              )
            }
            description="Across stored assessments"
            icon={Gauge}
          />

          <MetricCard
            label="Top prediction"
            value={
              mostCommonDisease?.disease ??
              "—"
            }
            description={
              mostCommonDisease
                ? `${mostCommonDisease.count} assessments`
                : "No assessment data"
            }
            icon={Leaf}
            compactValue
          />

          <MetricCard
            label="Primary source"
            value={
              mostCommonSource?.source ??
              "—"
            }
            description={
              mostCommonSource
                ? `${mostCommonSource.count} assessments`
                : "No source data"
            }
            icon={Smartphone}
            compactValue
          />

        </section>


        {/* Period note */}

        <div className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">

          <CalendarDays className="size-3.5" />

          Assessment activity chart is showing the last{" "}
          <span className="font-mono font-medium text-foreground">
            {days}
          </span>{" "}
          days.

        </div>


        {/* Charts */}

        <section className="mt-4">

          <AnalyticsCharts
            diseases={
              diseaseData.diseases.map(
                (item) => ({
                  disease:
                    item.disease,
                  count:
                    item.count,
                })
              )
            }

            severities={
              severityData.severities
            }

            sources={
              sourceData.sources
            }

            activity={
              activityData.activity
            }
          />

        </section>

      </div>

    </main>
  )
}


function MetricCard({
  label,
  value,
  description,
  icon: Icon,
  compactValue = false,
}: {
  label: string
  value: string
  description: string
  icon: React.ComponentType<{
    className?: string
  }>
  compactValue?: boolean
}) {
  return (
    <Card className="shadow-none">

      <CardContent className="p-5">

        <div className="flex items-start justify-between gap-4">

          <div className="min-w-0">

            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {label}
            </p>

            <p
              className={
                `mt-3 font-semibold tracking-tight ${
                  compactValue
                    ? "truncate text-lg"
                    : "font-mono text-2xl tabular-nums"
                }`
              }
            >
              {value}
            </p>

          </div>


          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border bg-muted/40">

            <Icon className="size-4" />

          </div>

        </div>


        <p className="mt-3 text-xs text-muted-foreground">
          {description}
        </p>

      </CardContent>

    </Card>
  )
}