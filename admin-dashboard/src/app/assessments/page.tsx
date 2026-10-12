import Link from "next/link"

import {
  ChevronRight,
  ClipboardList,
  Filter,
  ImageIcon,
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


interface AssessmentsPageProps {
  searchParams: Promise<{
    disease?: string
    severity?: string
    source?: string
  }>
}


export default async function AssessmentsPage({
  searchParams,
}: AssessmentsPageProps) {

  const filters = await searchParams

  const data = await getRecentAssessments(
    100,
    0
  )

  const diseases = Array.from(
    new Set(
      data.assessments.map(
        (item) => item.disease
      )
    )
  ).sort()

  const severities = Array.from(
    new Set(
      data.assessments.map(
        (item) => item.severity
      )
    )
  ).sort()

  const sources = Array.from(
    new Set(
      data.assessments.map(
        (item) => item.source
      )
    )
  ).sort()

  const filteredAssessments =
    data.assessments.filter(
      (assessment) => {

        if (
          filters.disease
          && assessment.disease
          !== filters.disease
        ) {
          return false
        }

        if (
          filters.severity
          && assessment.severity
          !== filters.severity
        ) {
          return false
        }

        if (
          filters.source
          && assessment.source
          !== filters.source
        ) {
          return false
        }

        return true
      }
    )

  const severeCount =
    data.assessments.filter(
      (item) =>
        item.severity === "Severe"
        || item.severity === "High"
    ).length

  const whatsappCount =
    data.assessments.filter(
      (item) =>
        item.source === "whatsapp"
    ).length

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Header */}

      <div className="mb-8">

        <h1 className="text-3xl font-bold tracking-tight">
          Assessments
        </h1>

        <p className="mt-2 text-muted-foreground">
          Review historical tomato image assessments
          produced by KILIMO.
        </p>

      </div>


      {/* Summary cards */}

      <div className="mb-8 grid gap-4 md:grid-cols-3">

        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Total Assessments
            </CardTitle>

            <ClipboardList className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {data.assessments.length}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              High / Severe
            </CardTitle>

            <Filter className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {severeCount}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              From WhatsApp
            </CardTitle>

            <ImageIcon className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {whatsappCount}
            </div>

          </CardContent>

        </Card>

      </div>


      {/* Filters */}

      <Card className="mb-6">

        <CardHeader>

          <CardTitle className="text-base">
            Filters
          </CardTitle>

          <CardDescription>
            Narrow the assessment list by prediction,
            severity or source.
          </CardDescription>

        </CardHeader>

        <CardContent>

          <form
            method="GET"
            className="grid gap-4 md:grid-cols-4"
          >

            {/* Disease */}

            <div>

              <label className="mb-2 block text-sm font-medium">
                Disease
              </label>

              <select
                name="disease"
                defaultValue={
                  filters.disease ?? ""
                }
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              >

                <option value="">
                  All diseases
                </option>

                {diseases.map(
                  (disease) => (

                    <option
                      key={disease}
                      value={disease}
                    >
                      {disease}
                    </option>

                  )
                )}

              </select>

            </div>


            {/* Severity */}

            <div>

              <label className="mb-2 block text-sm font-medium">
                Severity
              </label>

              <select
                name="severity"
                defaultValue={
                  filters.severity ?? ""
                }
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              >

                <option value="">
                  All severities
                </option>

                {severities.map(
                  (severity) => (

                    <option
                      key={severity}
                      value={severity}
                    >
                      {severity}
                    </option>

                  )
                )}

              </select>

            </div>


            {/* Source */}

            <div>

              <label className="mb-2 block text-sm font-medium">
                Source
              </label>

              <select
                name="source"
                defaultValue={
                  filters.source ?? ""
                }
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              >

                <option value="">
                  All sources
                </option>

                {sources.map(
                  (source) => (

                    <option
                      key={source}
                      value={source}
                    >
                      {source}
                    </option>

                  )
                )}

              </select>

            </div>


            {/* Actions */}

            <div className="flex items-end gap-2">

              <button
                type="submit"
                className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
              >
                Apply
              </button>

              <Link
                href="/assessments"
                className="flex h-10 items-center rounded-md border px-4 text-sm font-medium"
              >
                Clear
              </Link>

            </div>

          </form>

        </CardContent>

      </Card>


      {/* Assessment table */}

      <Card>

        <CardHeader>

          <CardTitle>
            Assessment History
          </CardTitle>

          <CardDescription>
            Showing {filteredAssessments.length} of{" "}
            {data.assessments.length} assessments.
          </CardDescription>

        </CardHeader>

        <CardContent>

          <Table>

            <TableHeader>

              <TableRow>

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
                  Severity
                </TableHead>

                <TableHead>
                  Confidence
                </TableHead>

                <TableHead>
                  Affected Area
                </TableHead>

                <TableHead>
                  Source
                </TableHead>

                <TableHead>
                  Time
                </TableHead>

                <TableHead />

              </TableRow>

            </TableHeader>


            <TableBody>

              {filteredAssessments.map(
                (assessment) => (

                  <TableRow
                    key={assessment.id}
                  >

                    <TableCell className="font-mono text-xs">
                      #{assessment.id}
                    </TableCell>


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


                    <TableCell>

                      {affectedArea(
                        assessment
                          .affected_area_percentage
                      )}

                    </TableCell>


                    <TableCell>

                      <Badge variant="secondary">
                        {assessment.source}
                      </Badge>

                    </TableCell>


                    <TableCell className="text-sm text-muted-foreground">

                      {formatDate(
                        assessment.created_at
                      )}

                    </TableCell>


                    <TableCell className="text-right">

                      <Link
                        href={
                          `/assessments/${assessment.id}`
                        }
                        className="inline-flex items-center gap-1 text-sm font-medium hover:underline"
                      >

                        View

                        <ChevronRight className="size-4" />

                      </Link>

                    </TableCell>

                  </TableRow>

                )
              )}

            </TableBody>

          </Table>


          {filteredAssessments.length === 0 && (

            <div className="py-12 text-center text-sm text-muted-foreground">
              No assessments match the selected filters.
            </div>

          )}

        </CardContent>

      </Card>

    </main>
  )
}