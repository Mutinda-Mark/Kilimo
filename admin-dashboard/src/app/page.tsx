import {
  Activity,
  ClipboardCheck,
  MessageSquareText,
  Users,
} from "lucide-react"

import {
  getDashboardSummary,
  getDiseaseStatistics,
  getRecentAssessments,
} from "@/lib/kilimo-api"

import {
  Card,
  CardContent,
  CardDescription,
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

import { Badge } from "@/components/ui/badge"


function percentage(
  value: number | null
) {
  if (value === null) {
    return "—"
  }

  return `${(value * 100).toFixed(1)}%`
}


function affectedArea(
  value: number
) {
  return `${value.toFixed(1)}%`
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
  ).format(
    new Date(value)
  )
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
    phoneNumber.slice(0, 6) +
    "****" +
    phoneNumber.slice(-3)
  )
}


export default async function DashboardPage() {
  const [
    summary,
    assessmentData,
    diseaseData,
  ] = await Promise.all([
    getDashboardSummary(),
    getRecentAssessments(10),
    getDiseaseStatistics(),
  ])

  return (
    <main className="min-h-screen bg-muted/30">

      <div className="mx-auto max-w-7xl p-6 lg:p-10">

        {/* Header */}

        <div className="mb-8">

          <p className="text-sm font-medium text-muted-foreground">
            KILIMO
          </p>

          <h1 className="text-3xl font-bold tracking-tight">
            Admin Dashboard
          </h1>

          <p className="mt-2 text-muted-foreground">
            Monitor farmer activity, tomato assessments,
            conversations and system usage.
          </p>

        </div>


        {/* Summary cards */}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <Card>

            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

              <CardTitle className="text-sm font-medium">
                Farmer Sessions
              </CardTitle>

              <Users className="h-4 w-4 text-muted-foreground" />

            </CardHeader>

            <CardContent>

              <div className="text-3xl font-bold">
                {summary.total_sessions}
              </div>

              <p className="text-xs text-muted-foreground">
                {summary.active_sessions_24h} active in the last 24 hours
              </p>

            </CardContent>

          </Card>


          <Card>

            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

              <CardTitle className="text-sm font-medium">
                Assessments
              </CardTitle>

              <ClipboardCheck className="h-4 w-4 text-muted-foreground" />

            </CardHeader>

            <CardContent>

              <div className="text-3xl font-bold">
                {summary.total_assessments}
              </div>

              <p className="text-xs text-muted-foreground">
                Tomato image assessments
              </p>

            </CardContent>

          </Card>


          <Card>

            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

              <CardTitle className="text-sm font-medium">
                Messages
              </CardTitle>

              <MessageSquareText className="h-4 w-4 text-muted-foreground" />

            </CardHeader>

            <CardContent>

              <div className="text-3xl font-bold">
                {summary.total_messages}
              </div>

              <p className="text-xs text-muted-foreground">
                Farmer and KILIMO messages
              </p>

            </CardContent>

          </Card>


          <Card>

            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

              <CardTitle className="text-sm font-medium">
                Average Confidence
              </CardTitle>

              <Activity className="h-4 w-4 text-muted-foreground" />

            </CardHeader>

            <CardContent>

              <div className="text-3xl font-bold">
                {percentage(
                  summary.average_confidence
                )}
              </div>

              <p className="text-xs text-muted-foreground">
                Across stored assessments
              </p>

            </CardContent>

          </Card>

        </div>


        {/* Main content */}

        <div className="mt-8 grid gap-6 lg:grid-cols-3">

          {/* Disease distribution */}

          <Card>

            <CardHeader>

              <CardTitle>
                Disease Distribution
              </CardTitle>

              <CardDescription>
                Stored image assessments by predicted condition.
              </CardDescription>

            </CardHeader>

            <CardContent className="space-y-4">

              {diseaseData.diseases.length === 0 ? (

                <p className="text-sm text-muted-foreground">
                  No assessments available yet.
                </p>

              ) : (

                diseaseData.diseases.map(
                  (item) => (

                    <div
                      key={item.disease}
                      className="flex items-center justify-between gap-4"
                    >

                      <div>

                        <p className="font-medium">
                          {item.disease}
                        </p>

                        <p className="text-xs text-muted-foreground">
                          Avg confidence:{" "}
                          {percentage(
                            item.average_confidence
                          )}
                        </p>

                      </div>

                      <Badge variant="secondary">
                        {item.count}
                      </Badge>

                    </div>

                  )
                )

              )}

            </CardContent>

          </Card>


          {/* Recent assessments */}

          <Card className="lg:col-span-2">

            <CardHeader>

              <CardTitle>
                Recent Assessments
              </CardTitle>

              <CardDescription>
                Latest tomato leaf analyses performed by KILIMO.
              </CardDescription>

            </CardHeader>

            <CardContent>

              <Table>

                <TableHeader>

                  <TableRow>

                    <TableHead>
                      Farmer
                    </TableHead>

                    <TableHead>
                      Prediction
                    </TableHead>

                    <TableHead>
                      Severity
                    </TableHead>

                    <TableHead>
                      Confidence
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
                      >

                        <TableCell className="font-mono text-xs">
                          {maskPhoneNumber(
                            assessment.phone_number
                          )}
                        </TableCell>

                        <TableCell className="font-medium">
                          {assessment.disease}
                        </TableCell>

                        <TableCell>

                          <Badge variant="outline">
                            {assessment.severity}
                          </Badge>

                        </TableCell>

                        <TableCell>
                          {percentage(
                            assessment.confidence
                          )}
                        </TableCell>

                        <TableCell className="capitalize">
                          {assessment.source}
                        </TableCell>

                        <TableCell className="text-right text-sm text-muted-foreground">
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

                <div className="py-8 text-center text-sm text-muted-foreground">
                  No assessments have been recorded yet.
                </div>

              )}

            </CardContent>

          </Card>

        </div>


        {/* Latest assessment */}

        {summary.latest_assessment && (

          <Card className="mt-6">

            <CardHeader>

              <CardTitle>
                Latest Assessment
              </CardTitle>

              <CardDescription>
                Most recently completed tomato image assessment.
              </CardDescription>

            </CardHeader>

            <CardContent>

              <div className="grid gap-6 md:grid-cols-5">

                <div>

                  <p className="text-sm text-muted-foreground">
                    Farmer
                  </p>

                  <p className="font-medium">
                    {maskPhoneNumber(
                      summary.latest_assessment.phone_number
                    )}
                  </p>

                </div>


                <div>

                  <p className="text-sm text-muted-foreground">
                    Prediction
                  </p>

                  <p className="font-medium">
                    {summary.latest_assessment.disease}
                  </p>

                </div>


                <div>

                  <p className="text-sm text-muted-foreground">
                    Confidence
                  </p>

                  <p className="font-medium">
                    {percentage(
                      summary.latest_assessment.confidence
                    )}
                  </p>

                </div>


                <div>

                  <p className="text-sm text-muted-foreground">
                    Severity
                  </p>

                  <p className="font-medium">
                    {summary.latest_assessment.severity}
                  </p>

                </div>


                <div>

                  <p className="text-sm text-muted-foreground">
                    Affected Area
                  </p>

                  <p className="font-medium">
                    {affectedArea(
                      summary.latest_assessment
                        .affected_area_percentage
                    )}
                  </p>

                </div>

              </div>

            </CardContent>

          </Card>

        )}

      </div>

    </main>
  )
}