import Link from "next/link"

import {
  ArrowLeft,
  BrainCircuit,
  CalendarClock,
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
} from "@/components/ui/card"


export const instant = false


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
  } =
    await params

  const id =
    Number(
      assessmentId
    )

  const assessment =
    await getAssessment(id)


  const scores =
    Object.entries(
      assessment.all_scores ??
      {}
    )
      .map(
        ([
          disease,
          score,
        ]) => ({
          disease,
          score:
            Number(score),
        })
      )
      .sort(
        (
          first,
          second
        ) =>
          second.score -
          first.score
      )


  const secondChoice =
    scores.length > 1
      ? scores[1]
      : null


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1500px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Back */}

        <Link
          href="/assessments"
          className="mb-6 inline-flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          Assessments
        </Link>


        {/* Header */}

        <section className="flex flex-col gap-5 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Computer vision assessment
            </p>

            <div className="flex flex-wrap items-center gap-3">

              <h1 className="font-mono text-2xl font-semibold tracking-tight lg:text-3xl">
                Assessment A-
                {assessment.id}
              </h1>

              <Badge
                variant="secondary"
                className="capitalize"
              >
                {assessment.source}
              </Badge>

            </div>

            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">

              <CalendarClock className="size-3.5" />

              <span className="font-mono">
                {formatDate(
                  assessment.created_at
                )}
              </span>

            </div>

          </div>

        </section>


        {/* Primary diagnosis */}

        <section className="mt-6 overflow-hidden rounded-xl border bg-card">

          <div className="grid lg:grid-cols-[1.3fr_0.7fr]">

            <div className="p-6 lg:p-8">

              <div className="flex items-start gap-4">

                <div className="flex size-11 shrink-0 items-center justify-center rounded-xl border bg-muted/40">
                  <Leaf className="size-5" />
                </div>

                <div>

                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Primary prediction
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                    {assessment.disease}
                  </h2>

                  <div className="mt-4 flex flex-wrap gap-2">

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

                    <Badge variant="secondary">
                      {percentage(
                        assessment.confidence
                      )}{" "}
                      confidence
                    </Badge>

                  </div>

                </div>

              </div>

            </div>


            <div className="grid grid-cols-2 border-t lg:border-l lg:border-t-0">

              <div className="border-r p-5">

                <p className="text-xs text-muted-foreground">
                  Confidence
                </p>

                <p className="mt-2 font-mono text-xl font-semibold tabular-nums">
                  {percentage(
                    assessment.confidence
                  )}
                </p>

              </div>


              <div className="p-5">

                <p className="text-xs text-muted-foreground">
                  Affected area
                </p>

                <p className="mt-2 font-mono text-xl font-semibold tabular-nums">
                  {affectedArea(
                    assessment
                      .affected_area_percentage
                  )}
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* Main content */}

        <section className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">

          {/* Model Scores */}

          <Card className="shadow-none">

            <CardContent className="p-0">

              <div className="border-b px-5 py-4">

                <div className="flex items-center gap-2">

                  <BrainCircuit className="size-4 text-muted-foreground" />

                  <h2 className="text-sm font-semibold">
                    Model class probabilities
                  </h2>

                </div>

                <p className="mt-1 text-xs text-muted-foreground">
                  Confidence distribution across supported tomato conditions.
                </p>

              </div>


              <div className="p-5">

                {scores.length === 0 ? (

                  <div className="py-12 text-center text-sm text-muted-foreground">
                    No class score information was stored for this assessment.
                  </div>

                ) : (

                  <div className="space-y-5">

                    {scores.map(
                      (
                        item,
                        index
                      ) => {

                        const width =
                          Math.min(
                            Math.max(
                              item.score *
                                100,
                              0
                            ),
                            100
                          )

                        return (
                          <div
                            key={
                              item.disease
                            }
                          >

                            <div className="mb-2 flex items-center justify-between gap-4">

                              <div className="flex min-w-0 items-center gap-2">

                                <span className="w-5 font-mono text-[10px] text-muted-foreground">
                                  {String(
                                    index +
                                      1
                                  ).padStart(
                                    2,
                                    "0"
                                  )}
                                </span>

                                <span className="truncate text-sm font-medium">
                                  {item.disease}
                                </span>

                              </div>

                              <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                                {percentage(
                                  item.score
                                )}
                              </span>

                            </div>


                            <div className="ml-7 h-1.5 overflow-hidden rounded-full bg-muted">

                              <div
                                className={
                                  `h-full rounded-full ${
                                    index === 0
                                      ? "bg-emerald-500"
                                      : "bg-foreground/25"
                                  }`
                                }
                                style={{
                                  width:
                                    `${width}%`,
                                }}
                              />

                            </div>

                          </div>
                        )
                      }
                    )}

                  </div>

                )}

              </div>

            </CardContent>

          </Card>


          {/* Metadata */}

          <div className="space-y-6">

            <Card className="shadow-none">

              <CardContent className="p-5">

                <h2 className="text-sm font-semibold">
                  Assessment metadata
                </h2>

                <div className="mt-5 space-y-4">

                  <MetadataRow
                    icon={UserRound}
                    label="Farmer"
                    value={
                      maskPhoneNumber(
                        assessment.phone_number
                      )
                    }
                    href={
                      assessment.phone_number
                        ? `/farmers/${
                            encodeURIComponent(
                              assessment.phone_number
                            )
                          }`
                        : undefined
                    }
                    mono
                  />

                  <MetadataRow
                    icon={Smartphone}
                    label="Source"
                    value={
                      assessment.source
                    }
                  />

                  <MetadataRow
                    icon={Gauge}
                    label="Class index"
                    value={
                      assessment.label_index ===
                      null
                        ? "—"
                        : String(
                            assessment.label_index
                          )
                    }
                    mono
                  />

                  <MetadataRow
                    icon={BrainCircuit}
                    label="Assessment ID"
                    value={
                      `A-${assessment.id}`
                    }
                    mono
                  />

                </div>

              </CardContent>

            </Card>


            <Card className="shadow-none">

              <CardContent className="p-5">

                <h2 className="text-sm font-semibold">
                  Prediction context
                </h2>

                <div className="mt-5 space-y-4">

                  <div>

                    <p className="text-xs text-muted-foreground">
                      Primary prediction
                    </p>

                    <p className="mt-1 text-sm font-medium">
                      {assessment.disease}
                    </p>

                  </div>


                  <div className="h-px bg-border" />


                  <div>

                    <p className="text-xs text-muted-foreground">
                      Next most likely class
                    </p>

                    <p className="mt-1 text-sm font-medium">
                      {secondChoice
                        ? secondChoice.disease
                        : "—"}
                    </p>

                    {secondChoice && (
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        {percentage(
                          secondChoice.score
                        )}
                      </p>
                    )}

                  </div>


                  <div className="h-px bg-border" />


                  <div>

                    <p className="text-xs text-muted-foreground">
                      Severity estimate
                    </p>

                    <div className="mt-2">

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

                    </div>

                  </div>

                </div>

              </CardContent>

            </Card>

          </div>

        </section>


        {/* Interpretation */}

        <section className="mt-6 rounded-xl border bg-muted/20 p-5">

          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Interpretation note
          </p>

          <p className="mt-3 max-w-4xl text-sm leading-6 text-muted-foreground">
            This record represents an automated KILIMO computer-vision
            assessment rather than a laboratory-confirmed diagnosis.
            Severity and affected-area values are estimates produced by
            the image-analysis pipeline and should be interpreted as
            advisory information.
          </p>

        </section>

      </div>

    </main>
  )
}


function MetadataRow({
  icon: Icon,
  label,
  value,
  href,
  mono = false,
}: {
  icon: React.ComponentType<{
    className?: string
  }>
  label: string
  value: string
  href?: string
  mono?: boolean
}) {
  const content = (
    <span
      className={
        `text-right text-xs font-medium ${
          mono
            ? "font-mono tabular-nums"
            : ""
        }`
      }
    >
      {value}
    </span>
  )

  return (
    <div className="flex items-center justify-between gap-5 border-b pb-4 last:border-0 last:pb-0">

      <div className="flex items-center gap-2 text-xs text-muted-foreground">

        <Icon className="size-3.5" />

        <span>
          {label}
        </span>

      </div>

      {href ? (
        <Link
          href={href}
          className="transition-colors hover:text-foreground"
        >
          {content}
        </Link>
      ) : (
        content
      )}

    </div>
  )
}