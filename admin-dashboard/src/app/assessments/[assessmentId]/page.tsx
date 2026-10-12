import Link from "next/link"

import {
  ArrowLeft,
  Activity,
  Gauge,
  Leaf,
  Smartphone,
  UserRound,
} from "lucide-react"

import {
  getAssessment,
} from "@/lib/kilimo-api"

import {
  Badge,
} from "@/components/ui/badge"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"


function percentage(
  value: number
) {
  return `${(value * 100).toFixed(2)}%`
}


function affectedArea(
  value: number
) {
  return `${value.toFixed(2)}%`
}


function formatDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-KE",
    {
      dateStyle: "full",
      timeStyle: "medium",
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
    phoneNumber.slice(0, 6)
    + "****"
    + phoneNumber.slice(-3)
  )
}


interface AssessmentPageProps {
  params: Promise<{
    assessmentId: string
  }>
}


export default async function AssessmentPage({
  params,
}: AssessmentPageProps) {

  const {
    assessmentId,
  } = await params

  const id = Number(
    assessmentId
  )

  const assessment =
    await getAssessment(id)

  const scores = Object.entries(
    assessment.all_scores ?? {}
  ).sort(
    (
      [, first],
      [, second]
    ) =>
      Number(second)
      - Number(first)
  )

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Back */}

      <Link
        href="/assessments"
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >

        <ArrowLeft className="size-4" />

        Back to assessments

      </Link>


      {/* Header */}

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <h1 className="text-3xl font-bold tracking-tight">
            Assessment #{assessment.id}
          </h1>

          <Badge variant="secondary">
            {assessment.source}
          </Badge>

        </div>

        <p className="mt-2 text-muted-foreground">
          {formatDate(
            assessment.created_at
          )}
        </p>

      </div>


      {/* Main statistics */}

      <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Prediction
            </CardTitle>

            <Leaf className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <p className="text-2xl font-bold">
              {assessment.disease}
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Confidence
            </CardTitle>

            <Gauge className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <p className="text-2xl font-bold">
              {percentage(
                assessment.confidence
              )}
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Severity
            </CardTitle>

            <Activity className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <p className="text-2xl font-bold">
              {assessment.severity}
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Affected Area
            </CardTitle>

            <Leaf className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <p className="text-2xl font-bold">
              {affectedArea(
                assessment
                  .affected_area_percentage
              )}
            </p>

          </CardContent>

        </Card>

      </div>


      {/* Metadata */}

      <div className="mb-8 grid gap-6 lg:grid-cols-2">

        <Card>

          <CardHeader>

            <CardTitle>
              Assessment Information
            </CardTitle>

          </CardHeader>

          <CardContent className="space-y-5">

            <div className="flex items-center justify-between border-b pb-4">

              <div className="flex items-center gap-2 text-muted-foreground">

                <UserRound className="size-4" />

                Farmer

              </div>

              {assessment.phone_number ? (

                <Link
                  href={
                    `/farmers/${encodeURIComponent(
                      assessment.phone_number
                    )}`
                  }
                  className="font-medium hover:underline"
                >
                  {maskPhoneNumber(
                    assessment.phone_number
                  )}
                </Link>

              ) : (

                <span className="font-medium">
                  API user
                </span>

              )}

            </div>


            <div className="flex items-center justify-between border-b pb-4">

              <div className="flex items-center gap-2 text-muted-foreground">

                <Smartphone className="size-4" />

                Source

              </div>

              <Badge variant="outline">
                {assessment.source}
              </Badge>

            </div>


            <div className="flex items-center justify-between border-b pb-4">

              <span className="text-muted-foreground">
                Class Index
              </span>

              <span className="font-medium">
                {
                  assessment.label_index
                  ?? "—"
                }
              </span>

            </div>


            <div className="flex items-center justify-between">

              <span className="text-muted-foreground">
                Assessment ID
              </span>

              <span className="font-mono text-sm">
                #{assessment.id}
              </span>

            </div>

          </CardContent>

        </Card>


        {/* Model scores */}

        <Card>

          <CardHeader>

            <CardTitle>
              Model Class Scores
            </CardTitle>

            <CardDescription>
              Probability scores returned across
              supported tomato conditions.
            </CardDescription>

          </CardHeader>

          <CardContent>

            {scores.length === 0 ? (

              <p className="text-sm text-muted-foreground">
                No class score data was stored.
              </p>

            ) : (

              <div className="space-y-4">

                {scores.map(
                  ([
                    disease,
                    score,
                  ]) => {

                    const numericScore =
                      Number(score)

                    return (
                      <div
                        key={disease}
                      >

                        <div className="mb-1 flex items-center justify-between gap-4">

                          <span className="text-sm">
                            {disease}
                          </span>

                          <span className="text-sm font-medium">
                            {percentage(
                              numericScore
                            )}
                          </span>

                        </div>


                        <div className="h-2 overflow-hidden rounded-full bg-muted">

                          <div
                            className="h-full rounded-full bg-primary"
                            style={{
                              width: `${
                                Math.min(
                                  Math.max(
                                    numericScore
                                    * 100,
                                    0
                                  ),
                                  100
                                )
                              }%`,
                            }}
                          />

                        </div>

                      </div>
                    )
                  }
                )}

              </div>

            )}

          </CardContent>

        </Card>

      </div>


      {/* Interpretation note */}

      <Card>

        <CardHeader>

          <CardTitle>
            Interpretation
          </CardTitle>

        </CardHeader>

        <CardContent className="space-y-3 text-sm text-muted-foreground">

          <p>
            This assessment was produced by the KILIMO
            computer-vision pipeline and represents a model
            prediction rather than a laboratory-confirmed
            diagnosis.
          </p>

          <p>
            Severity and affected-area values are estimates
            produced by the image-analysis pipeline and should
            be interpreted as advisory information.
          </p>

        </CardContent>

      </Card>

    </main>
  )
}