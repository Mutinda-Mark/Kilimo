import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  Database,
  MessageSquare,
  Server,
  TriangleAlert,
} from "lucide-react"

import {
  getDatabaseStatistics,
  getModelInformation,
  getRecentWhatsAppMessages,
  getWhatsAppStatistics,
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


function formatDate(
  value: string | null
) {
  if (!value) {
    return "—"
  }

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
    return "—"
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


function statusVariant(
  status: string
):
  | "default"
  | "secondary"
  | "destructive"
  | "outline" {

  if (status === "completed") {
    return "default"
  }

  if (status === "failed") {
    return "destructive"
  }

  if (status === "processing") {
    return "secondary"
  }

  return "outline"
}


export default async function SystemPage() {

  const [
    database,
    whatsapp,
    recentMessages,
    model,
  ] = await Promise.all([
    getDatabaseStatistics(),
    getWhatsAppStatistics(),
    getRecentWhatsAppMessages(20),
    getModelInformation(),
  ])

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Header */}

      <div className="mb-8">

        <h1 className="text-3xl font-bold tracking-tight">
          System
        </h1>

        <p className="mt-2 text-muted-foreground">
          Monitor KILIMO backend services,
          WhatsApp processing and model configuration.
        </p>

      </div>


      {/* Main health cards */}

      <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Database
            </CardTitle>

            <Database className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="flex items-center gap-2">

              {database.connected ? (
                <CheckCircle2 className="size-5" />
              ) : (
                <TriangleAlert className="size-5" />
              )}

              <span className="text-2xl font-bold">
                {
                  database.connected
                    ? "Connected"
                    : "Unavailable"
                }
              </span>

            </div>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              WhatsApp Processed
            </CardTitle>

            <MessageSquare className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {whatsapp.completed}
            </div>

            <p className="text-xs text-muted-foreground">
              {whatsapp.total} total received
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Failed Messages
            </CardTitle>

            <TriangleAlert className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {whatsapp.failed}
            </div>

            <p className="text-xs text-muted-foreground">
              Processing failures
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">

            <CardTitle className="text-sm font-medium">
              Last 24 Hours
            </CardTitle>

            <Activity className="size-4 text-muted-foreground" />

          </CardHeader>

          <CardContent>

            <div className="text-3xl font-bold">
              {whatsapp.received_24h}
            </div>

            <p className="text-xs text-muted-foreground">
              WhatsApp messages received
            </p>

          </CardContent>

        </Card>

      </div>


      {/* Configuration */}

      <div className="mb-8 grid gap-6 lg:grid-cols-2">

        {/* Model */}

        <Card>

          <CardHeader>

            <CardTitle className="flex items-center gap-2">

              <BrainCircuit className="size-5" />

              CV Model

            </CardTitle>

            <CardDescription>
              Current tomato disease model configuration.
            </CardDescription>

          </CardHeader>

          <CardContent className="space-y-4">

            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Task
              </span>

              <span className="font-medium">
                {model.task}
              </span>

            </div>


            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Backbone
              </span>

              <span className="font-mono text-sm">
                {model.backbone}
              </span>

            </div>


            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Classes
              </span>

              <span className="font-medium">
                {model.num_classes}
              </span>

            </div>


            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Input Size
              </span>

              <span className="font-medium">
                {model.image_size} × {model.image_size}
              </span>

            </div>


            <div className="flex justify-between">

              <span className="text-muted-foreground">
                Status
              </span>

              <Badge>
                {model.status}
              </Badge>

            </div>

          </CardContent>

        </Card>


        {/* Database */}

        <Card>

          <CardHeader>

            <CardTitle className="flex items-center gap-2">

              <Server className="size-5" />

              Database Records

            </CardTitle>

            <CardDescription>
              Current PostgreSQL storage totals.
            </CardDescription>

          </CardHeader>

          <CardContent className="space-y-4">

            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Farmer Sessions
              </span>

              <span className="font-medium">
                {database.sessions}
              </span>

            </div>


            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Conversation Messages
              </span>

              <span className="font-medium">
                {database.conversation_messages}
              </span>

            </div>


            <div className="flex justify-between border-b pb-3">

              <span className="text-muted-foreground">
                Assessments
              </span>

              <span className="font-medium">
                {database.assessments}
              </span>

            </div>


            <div className="flex justify-between">

              <span className="text-muted-foreground">
                WhatsApp Events
              </span>

              <span className="font-medium">
                {database.whatsapp_messages}
              </span>

            </div>

          </CardContent>

        </Card>

      </div>


      {/* WhatsApp state */}

      <Card className="mb-8">

        <CardHeader>

          <CardTitle>
            WhatsApp Processing
          </CardTitle>

          <CardDescription>
            Current message-processing state.
          </CardDescription>

        </CardHeader>

        <CardContent>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            <div className="rounded-lg border p-4">

              <p className="text-sm text-muted-foreground">
                Total
              </p>

              <p className="mt-1 text-2xl font-bold">
                {whatsapp.total}
              </p>

            </div>


            <div className="rounded-lg border p-4">

              <p className="text-sm text-muted-foreground">
                Completed
              </p>

              <p className="mt-1 text-2xl font-bold">
                {whatsapp.completed}
              </p>

            </div>


            <div className="rounded-lg border p-4">

              <p className="text-sm text-muted-foreground">
                Processing
              </p>

              <p className="mt-1 text-2xl font-bold">
                {whatsapp.processing}
              </p>

            </div>


            <div className="rounded-lg border p-4">

              <p className="text-sm text-muted-foreground">
                Failed
              </p>

              <p className="mt-1 text-2xl font-bold">
                {whatsapp.failed}
              </p>

            </div>

          </div>

        </CardContent>

      </Card>


      {/* Recent processing */}

      <Card>

        <CardHeader>

          <CardTitle>
            Recent WhatsApp Processing
          </CardTitle>

          <CardDescription>
            Latest webhook messages handled by KILIMO.
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
                  Type
                </TableHead>

                <TableHead>
                  Status
                </TableHead>

                <TableHead>
                  Received
                </TableHead>

                <TableHead>
                  Completed
                </TableHead>

                <TableHead>
                  Error
                </TableHead>

              </TableRow>

            </TableHeader>


            <TableBody>

              {recentMessages.messages.map(
                (message) => (

                  <TableRow
                    key={message.message_id}
                  >

                    <TableCell className="font-mono text-xs">

                      {maskPhoneNumber(
                        message.phone_number
                      )}

                    </TableCell>


                    <TableCell className="capitalize">

                      {message.message_type ?? "—"}

                    </TableCell>


                    <TableCell>

                      <Badge
                        variant={
                          statusVariant(
                            message.status
                          )
                        }
                      >

                        {message.status}

                      </Badge>

                    </TableCell>


                    <TableCell className="text-sm text-muted-foreground">

                      {formatDate(
                        message.received_at
                      )}

                    </TableCell>


                    <TableCell className="text-sm text-muted-foreground">

                      {formatDate(
                        message.completed_at
                      )}

                    </TableCell>


                    <TableCell className="max-w-[250px] truncate text-sm text-muted-foreground">

                      {message.error_message ?? "—"}

                    </TableCell>

                  </TableRow>

                )
              )}

            </TableBody>

          </Table>


          {recentMessages.messages.length === 0 && (

            <div className="py-10 text-center text-sm text-muted-foreground">
              No WhatsApp processing records yet.
            </div>

          )}

        </CardContent>

      </Card>

    </main>
  )
}