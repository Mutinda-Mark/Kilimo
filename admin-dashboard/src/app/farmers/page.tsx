import Link from "next/link"

import {
  ChevronRight,
  Leaf,
  MessageSquareText,
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
  ).format(
    new Date(value)
  )
}


function maskPhoneNumber(
  phoneNumber: string
) {
  if (phoneNumber.length < 8) {
    return phoneNumber
  }

  return (
    phoneNumber.slice(0, 6)
    + "****"
    + phoneNumber.slice(-3)
  )
}


export default async function FarmersPage() {

  const [
    data,
    summary,
  ] = await Promise.all([
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

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Header */}

      <div className="mb-8">

        <h1 className="text-3xl font-bold tracking-tight">
          Farmers
        </h1>

        <p className="mt-2 text-muted-foreground">
          View farmer sessions, previous assessments
          and conversation history.
        </p>

      </div>


      {/* Summary */}

      <div className="mb-8 grid gap-4 md:grid-cols-3">

        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Total Sessions
            </CardTitle>

            <Users className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {summary.total_sessions}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              With Assessments
            </CardTitle>

            <Leaf className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {assessedFarmers}
            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Active 24 Hours
            </CardTitle>

            <MessageSquareText className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {summary.active_sessions_24h}
            </div>

          </CardContent>

        </Card>

      </div>


      {/* Farmer table */}

      <Card>

        <CardHeader>

          <CardTitle>
            Farmer Sessions
          </CardTitle>

          <CardDescription>
            Select a farmer to inspect their
            conversation with KILIMO.
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
                  Language
                </TableHead>

                <TableHead>
                  Latest Assessment
                </TableHead>

                <TableHead>
                  Severity
                </TableHead>

                <TableHead>
                  Confidence
                </TableHead>

                <TableHead>
                  Last Active
                </TableHead>

                <TableHead />

              </TableRow>

            </TableHeader>


            <TableBody>

              {data.sessions.map(
                (session) => (

                  <TableRow
                    key={
                      session.phone_number
                    }
                  >

                    <TableCell>

                      <div>

                        <p className="font-medium">
                          {maskPhoneNumber(
                            session.phone_number
                          )}
                        </p>

                        <p className="text-xs text-muted-foreground">
                          WhatsApp farmer
                        </p>

                      </div>

                    </TableCell>


                    <TableCell className="uppercase">
                      {session.language}
                    </TableCell>


                    <TableCell>

                      {session.last_disease ? (

                        <Badge variant="secondary">
                          {session.last_disease}
                        </Badge>

                      ) : (

                        <span className="text-sm text-muted-foreground">
                          No assessment
                        </span>

                      )}

                    </TableCell>


                    <TableCell>
                      {session.last_severity ?? "—"}
                    </TableCell>


                    <TableCell>

                      {percentage(
                        session.last_confidence
                      )}

                    </TableCell>


                    <TableCell className="text-sm text-muted-foreground">

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


          {data.sessions.length === 0 && (

            <div className="py-10 text-center text-sm text-muted-foreground">
              No farmer sessions are available.
            </div>

          )}

        </CardContent>

      </Card>

    </main>
  )
}