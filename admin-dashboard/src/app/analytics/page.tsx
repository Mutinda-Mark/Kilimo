import {
  Activity,
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
  CardHeader,
  CardTitle,
} from "@/components/ui/card"


function percentage(
  value: number | null
) {
  if (value === null) {
    return "—"
  }

  return `${(
    value * 100
  ).toFixed(1)}%`
}


export default async function AnalyticsPage() {

  const [
    summary,
    diseaseData,
    severityData,
    sourceData,
    activityData,
  ] = await Promise.all([
    getDashboardSummary(),
    getDiseaseStatistics(),
    getSeverityStatistics(),
    getSourceStatistics(),
    getAssessmentActivity(14),
  ])

  const mostCommonDisease =
    diseaseData.diseases.length > 0
      ? diseaseData.diseases[0]
      : null

  const mostCommonSource =
    sourceData.sources.length > 0
      ? sourceData.sources[0]
      : null

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Header */}

      <div className="mb-8">

        <h1 className="text-3xl font-bold tracking-tight">
          Analytics
        </h1>

        <p className="mt-2 text-muted-foreground">
          Explore assessment trends, disease patterns,
          severity levels and system usage.
        </p>

      </div>


      {/* Analytics summary */}

      <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Total Assessments
            </CardTitle>

            <Activity className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {summary.total_assessments}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Average Confidence
            </CardTitle>

            <Gauge className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {percentage(
                summary.average_confidence
              )}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Most Common Prediction
            </CardTitle>

            <Leaf className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-xl font-bold">
              {
                mostCommonDisease
                  ? mostCommonDisease.disease
                  : "—"
              }
            </div>

            {mostCommonDisease && (

              <p className="text-xs text-muted-foreground">
                {mostCommonDisease.count} assessments
              </p>

            )}

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Main Source
            </CardTitle>

            <Smartphone className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-xl font-bold capitalize">
              {
                mostCommonSource
                  ? mostCommonSource.source
                  : "—"
              }
            </div>

            {mostCommonSource && (

              <p className="text-xs text-muted-foreground">
                {mostCommonSource.count} assessments
              </p>

            )}

          </CardContent>

        </Card>

      </div>


      {/* Charts */}

      <AnalyticsCharts
        diseases={
          diseaseData.diseases.map(
            (item) => ({
              disease: item.disease,
              count: item.count,
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

    </main>
  )
}