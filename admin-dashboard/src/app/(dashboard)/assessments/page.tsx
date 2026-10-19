import Link from "next/link"

import {
  ArrowRight,
  ClipboardCheck,
  Filter,
  Search,
  ShieldAlert,
  Smartphone,
} from "lucide-react"

import {
  getRecentAssessments,
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
  value: number
) {
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


interface AssessmentsPageProps {
  searchParams: Promise<{
    q?: string
    disease?: string
    severity?: string
    source?: string
  }>
}


export default async function AssessmentsPage({
  searchParams,
}: AssessmentsPageProps) {
  const filters =
    await searchParams

  const data =
    await getRecentAssessments(
      100,
      0
    )


  const diseases =
    Array.from(
      new Set(
        data.assessments.map(
          (item) =>
            item.disease
        )
      )
    ).sort()


  const severities =
    Array.from(
      new Set(
        data.assessments.map(
          (item) =>
            item.severity
        )
      )
    ).sort()


  const sources =
    Array.from(
      new Set(
        data.assessments.map(
          (item) =>
            item.source
        )
      )
    ).sort()


  const query =
    filters.q
      ?.trim()
      .toLowerCase() ??
    ""


  const filteredAssessments =
    data.assessments.filter(
      (assessment) => {

        if (
          query &&
          !assessment.disease
            .toLowerCase()
            .includes(query) &&
          !assessment.phone_number
            ?.toLowerCase()
            .includes(query) &&
          !String(
            assessment.id
          ).includes(query)
        ) {
          return false
        }


        if (
          filters.disease &&
          assessment.disease !==
            filters.disease
        ) {
          return false
        }


        if (
          filters.severity &&
          assessment.severity !==
            filters.severity
        ) {
          return false
        }


        if (
          filters.source &&
          assessment.source !==
            filters.source
        ) {
          return false
        }


        return true
      }
    )


  const severeCount =
    data.assessments.filter(
      (item) =>
        item.severity ===
          "Severe" ||
        item.severity ===
          "High"
    ).length


  const whatsappCount =
    data.assessments.filter(
      (item) =>
        item.source.toLowerCase() ===
        "whatsapp"
    ).length


  const averageConfidence =
    data.assessments.length > 0
      ? data.assessments.reduce(
          (total, item) =>
            total +
            item.confidence,
          0
        ) /
        data.assessments.length
      : null


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1700px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Header */}

        <section className="border-b pb-7">

          <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Computer vision records
          </p>

          <h1 className="text-3xl font-semibold tracking-tight">
            Assessments
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Search, filter and inspect tomato disease assessments
            produced by the KILIMO computer-vision pipeline.
          </p>

        </section>


        {/* Summary */}

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <MetricCard
            label="Total assessments"
            value={
              String(
                data.assessments.length
              )
            }
            description="Loaded assessment records"
            icon={ClipboardCheck}
          />

          <MetricCard
            label="Average confidence"
            value={
              averageConfidence ===
              null
                ? "—"
                : percentage(
                    averageConfidence
                  )
            }
            description="Across loaded predictions"
            icon={Filter}
          />

          <MetricCard
            label="High / severe"
            value={
              String(
                severeCount
              )
            }
            description="Assessments requiring attention"
            icon={ShieldAlert}
          />

          <MetricCard
            label="From WhatsApp"
            value={
              String(
                whatsappCount
              )
            }
            description="Farmer image submissions"
            icon={Smartphone}
          />

        </section>


        {/* Filters */}

        <section className="mt-6 rounded-xl border bg-card">

          <form
            method="GET"
            className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-[1.4fr_1fr_1fr_1fr_auto]"
          >

            <div>

              <label
                htmlFor="assessment-search"
                className="mb-2 block text-xs font-medium text-muted-foreground"
              >
                Search
              </label>

              <div className="relative">

                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

                <input
                  id="assessment-search"
                  name="q"
                  defaultValue={
                    filters.q ?? ""
                  }
                  placeholder="ID, farmer or disease..."
                  className="h-10 w-full rounded-lg border bg-background pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/20"
                />

              </div>

            </div>


            <FilterSelect
              label="Disease"
              name="disease"
              defaultValue={
                filters.disease ?? ""
              }
              options={
                diseases
              }
              placeholder="All diseases"
            />


            <FilterSelect
              label="Severity"
              name="severity"
              defaultValue={
                filters.severity ?? ""
              }
              options={
                severities
              }
              placeholder="All severities"
            />


            <FilterSelect
              label="Source"
              name="source"
              defaultValue={
                filters.source ?? ""
              }
              options={
                sources
              }
              placeholder="All sources"
            />


            <div className="flex items-end gap-2">

              <button
                type="submit"
                className="h-10 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Apply
              </button>

              <Link
                href="/assessments"
                className="inline-flex h-10 items-center rounded-lg border bg-background px-4 text-sm font-medium transition-colors hover:bg-accent"
              >
                Clear
              </Link>

            </div>

          </form>

        </section>


        {/* Table */}

        <section className="mt-6 overflow-hidden rounded-xl border bg-card">

          <div className="flex items-center justify-between border-b px-5 py-4">

            <div>

              <h2 className="text-sm font-semibold">
                Assessment history
              </h2>

              <p className="mt-1 text-xs text-muted-foreground">
                Showing{" "}
                <span className="font-mono tabular-nums">
                  {filteredAssessments.length}
                </span>{" "}
                of{" "}
                <span className="font-mono tabular-nums">
                  {data.assessments.length}
                </span>{" "}
                loaded assessments
              </p>

            </div>

          </div>


          <div className="overflow-x-auto">

            <Table>

              <TableHeader>

                <TableRow className="hover:bg-transparent">

                  <TableHead>
                    ID
                  </TableHead>

                  <TableHead>
                    Farmer
                  </TableHead>

                  <TableHead>
                    Prediction
                  </TableHead>

                  <TableHead>
                    Confidence
                  </TableHead>

                  <TableHead>
                    Severity
                  </TableHead>

                  <TableHead>
                    Affected area
                  </TableHead>

                  <TableHead>
                    Source
                  </TableHead>

                  <TableHead>
                    Created
                  </TableHead>

                  <TableHead className="w-16" />

                </TableRow>

              </TableHeader>


              <TableBody>

                {filteredAssessments.map(
                  (assessment) => (

                    <TableRow
                      key={
                        assessment.id
                      }
                      className="group transition-colors"
                    >

                      <TableCell className="font-mono text-xs font-medium">
                        A-
                        {assessment.id}
                      </TableCell>


                      <TableCell className="font-mono text-xs text-muted-foreground">

                        {maskPhoneNumber(
                          assessment.phone_number
                        )}

                      </TableCell>


                      <TableCell>

                        <p className="text-sm font-medium">
                          {assessment.disease}
                        </p>

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


                      <TableCell className="font-mono text-xs tabular-nums">

                        {affectedArea(
                          assessment
                            .affected_area_percentage
                        )}

                      </TableCell>


                      <TableCell>

                        <Badge
                          variant="secondary"
                          className="capitalize"
                        >
                          {assessment.source}
                        </Badge>

                      </TableCell>


                      <TableCell className="font-mono text-xs text-muted-foreground">

                        {formatDate(
                          assessment.created_at
                        )}

                      </TableCell>


                      <TableCell className="text-right">

                        <Link
                          href={
                            `/assessments/${assessment.id}`
                          }
                          aria-label={
                            `View assessment ${assessment.id}`
                          }
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


            {filteredAssessments.length === 0 && (

              <div className="px-6 py-16 text-center">

                <ClipboardCheck className="mx-auto size-6 text-muted-foreground" />

                <p className="mt-4 text-sm font-medium">
                  No assessments found
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Try adjusting the current search or filter settings.
                </p>

              </div>

            )}

          </div>

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
}: {
  label: string
  value: string
  description: string
  icon: React.ComponentType<{
    className?: string
  }>
}) {
  return (
    <Card className="shadow-none">

      <CardContent className="p-5">

        <div className="flex items-start justify-between">

          <div>

            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {label}
            </p>

            <p className="mt-3 font-mono text-2xl font-semibold tracking-tight tabular-nums">
              {value}
            </p>

          </div>

          <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">
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


function FilterSelect({
  label,
  name,
  defaultValue,
  options,
  placeholder,
}: {
  label: string
  name: string
  defaultValue: string
  options: string[]
  placeholder: string
}) {
  return (
    <div>

      <label className="mb-2 block text-xs font-medium text-muted-foreground">
        {label}
      </label>

      <select
        name={name}
        defaultValue={defaultValue}
        className="h-10 w-full rounded-lg border bg-background px-3 text-sm outline-none transition-colors focus:border-ring focus:ring-2 focus:ring-ring/20"
      >

        <option value="">
          {placeholder}
        </option>

        {options.map(
          (option) => (
            <option
              key={option}
              value={option}
            >
              {option}
            </option>
          )
        )}

      </select>

    </div>
  )
}