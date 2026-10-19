import {
  Activity,
  BrainCircuit,
  Database,
  MessageSquare,
  Server,
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
  ).format(new Date(value))
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
    `${phoneNumber.slice(0, 6)}••••${phoneNumber.slice(-3)}`
  )
}


function statusClass(
  status: string
) {
  switch (
    status.toLowerCase()
  ) {
    case "completed":
      return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"

    case "failed":
      return "border-red-200 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"

    case "processing":
      return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300"

    default:
      return ""
  }
}


export default async function SystemPage() {
  const [
    database,
    whatsapp,
    recentMessages,
    model,
  ] =
    await Promise.all([
      getDatabaseStatistics(),
      getWhatsAppStatistics(),
      getRecentWhatsAppMessages(
        20
      ),
      getModelInformation(),
    ])


  const whatsappHealthy =
    whatsapp.failed === 0

  const modelHealthy =
    ![
      "error",
      "failed",
      "unavailable",
    ].includes(
      model.status.toLowerCase()
    )


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1700px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Header */}

        <section className="flex flex-col gap-5 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Platform operations
            </p>

            <h1 className="text-3xl font-semibold tracking-tight">
              System
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Monitor backend connectivity, model configuration,
              WhatsApp processing and stored platform records.
            </p>

          </div>


          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2">

            <span
              className={
                `size-2 rounded-full ${
                  database.connected &&
                  modelHealthy
                    ? "bg-emerald-500"
                    : "bg-amber-500"
                }`
              }
            />

            <span className="text-xs font-medium">
              Platform monitoring active
            </span>

          </div>

        </section>


        {/* Operational health */}

        <section className="mt-6">

          <div className="mb-3">

            <h2 className="text-sm font-semibold">
              Service health
            </h2>

            <p className="mt-1 text-xs text-muted-foreground">
              Current status of core KILIMO components.
            </p>

          </div>


          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

            <ServiceCard
              title="PostgreSQL"
              status={
                database.connected
                  ? "Connected"
                  : "Unavailable"
              }
              healthy={
                database.connected
              }
              icon={Database}
              detail={
                `${database.assessments} assessments stored`
              }
            />

            <ServiceCard
              title="WhatsApp pipeline"
              status={
                whatsappHealthy
                  ? "Operational"
                  : "Attention"
              }
              healthy={
                whatsappHealthy
              }
              icon={MessageSquare}
              detail={
                `${whatsapp.completed} completed events`
              }
            />

            <ServiceCard
              title="Vision model"
              status={
                model.status
              }
              healthy={
                modelHealthy
              }
              icon={BrainCircuit}
              detail={
                `${model.backbone} · ${model.num_classes} classes`
              }
            />

            <ServiceCard
              title="Message intake"
              status="Active"
              healthy
              icon={Activity}
              detail={
                `${whatsapp.received_24h} events in 24 hours`
              }
            />

          </div>

        </section>


        {/* Main system info */}

        <section className="mt-6 grid gap-6 xl:grid-cols-2">

          {/* Model */}

          <Card className="shadow-none">

            <CardContent className="p-0">

              <div className="flex items-start gap-3 border-b px-5 py-4">

                <div className="flex size-8 items-center justify-center rounded-lg border bg-muted/40">

                  <BrainCircuit className="size-3.5" />

                </div>

                <div>

                  <h2 className="text-sm font-semibold">
                    Computer vision model
                  </h2>

                  <p className="mt-1 text-xs text-muted-foreground">
                    Current deployed image-assessment configuration.
                  </p>

                </div>

              </div>


              <div className="p-5">

                <InfoRow
                  label="Task"
                  value={
                    model.task
                  }
                />

                <InfoRow
                  label="Backbone"
                  value={
                    model.backbone
                  }
                  mono
                />

                <InfoRow
                  label="Classes"
                  value={
                    String(
                      model.num_classes
                    )
                  }
                  mono
                />

                <InfoRow
                  label="Input resolution"
                  value={
                    `${model.image_size} × ${model.image_size}`
                  }
                  mono
                />

                <InfoRow
                  label="Runtime status"
                  value={
                    model.status
                  }
                  last
                />

              </div>

            </CardContent>

          </Card>


          {/* DB */}

          <Card className="shadow-none">

            <CardContent className="p-0">

              <div className="flex items-start gap-3 border-b px-5 py-4">

                <div className="flex size-8 items-center justify-center rounded-lg border bg-muted/40">

                  <Server className="size-3.5" />

                </div>

                <div>

                  <h2 className="text-sm font-semibold">
                    Database inventory
                  </h2>

                  <p className="mt-1 text-xs text-muted-foreground">
                    Current PostgreSQL application record totals.
                  </p>

                </div>

              </div>


              <div className="grid grid-cols-2">

                <InventoryCell
                  label="Farmer sessions"
                  value={
                    database.sessions
                  }
                />

                <InventoryCell
                  label="Conversation messages"
                  value={
                    database.conversation_messages
                  }
                  right
                />

                <InventoryCell
                  label="Assessments"
                  value={
                    database.assessments
                  }
                  bottom
                />

                <InventoryCell
                  label="WhatsApp events"
                  value={
                    database.whatsapp_messages
                  }
                  right
                  bottom
                />

              </div>

            </CardContent>

          </Card>

        </section>


        {/* WhatsApp metrics */}

        <section className="mt-6 overflow-hidden rounded-xl border bg-card">

          <div className="flex items-start gap-3 border-b px-5 py-4">

            <div className="flex size-8 items-center justify-center rounded-lg border bg-muted/40">

              <MessageSquare className="size-3.5" />

            </div>

            <div>

              <h2 className="text-sm font-semibold">
                WhatsApp processing
              </h2>

              <p className="mt-1 text-xs text-muted-foreground">
                Message processing state recorded by the webhook pipeline.
              </p>

            </div>

          </div>


          <div className="grid sm:grid-cols-2 xl:grid-cols-4">

            <PipelineMetric
              label="Total"
              value={
                whatsapp.total
              }
            />

            <PipelineMetric
              label="Completed"
              value={
                whatsapp.completed
              }
            />

            <PipelineMetric
              label="Processing"
              value={
                whatsapp.processing
              }
            />

            <PipelineMetric
              label="Failed"
              value={
                whatsapp.failed
              }
              last
            />

          </div>

        </section>


        {/* Event log */}

        <section className="mt-6 overflow-hidden rounded-xl border bg-card">

          <div className="flex items-center justify-between border-b px-5 py-4">

            <div>

              <h2 className="text-sm font-semibold">
                Recent processing events
              </h2>

              <p className="mt-1 text-xs text-muted-foreground">
                Latest WhatsApp messages processed by the backend.
              </p>

            </div>


            <Badge
              variant="secondary"
              className="font-mono tabular-nums"
            >
              {recentMessages.messages.length}
            </Badge>

          </div>


          <div className="overflow-x-auto">

            <Table>

              <TableHeader>

                <TableRow className="hover:bg-transparent">

                  <TableHead>
                    Message
                  </TableHead>

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
                      key={
                        message.message_id
                      }
                      className="transition-colors"
                    >

                      <TableCell>

                        <span className="block max-w-44 truncate font-mono text-[11px] text-muted-foreground">
                          {message.message_id}
                        </span>

                      </TableCell>


                      <TableCell className="font-mono text-xs">

                        {maskPhoneNumber(
                          message.phone_number
                        )}

                      </TableCell>


                      <TableCell className="capitalize">

                        {message.message_type ??
                          "—"}

                      </TableCell>


                      <TableCell>

                        <Badge
                          variant="outline"
                          className={
                            statusClass(
                              message.status
                            )
                          }
                        >
                          {message.status}
                        </Badge>

                      </TableCell>


                      <TableCell className="font-mono text-xs text-muted-foreground">

                        {formatDate(
                          message.received_at
                        )}

                      </TableCell>


                      <TableCell className="font-mono text-xs text-muted-foreground">

                        {formatDate(
                          message.completed_at
                        )}

                      </TableCell>


                      <TableCell>

                        {message.error_message ? (

                          <span
                            title={
                              message.error_message
                            }
                            className="block max-w-64 truncate text-xs text-red-600 dark:text-red-400"
                          >
                            {message.error_message}
                          </span>

                        ) : (

                          <span className="text-xs text-muted-foreground">
                            —
                          </span>

                        )}

                      </TableCell>

                    </TableRow>

                  )
                )}

              </TableBody>

            </Table>


            {recentMessages.messages.length === 0 && (

              <div className="px-6 py-16 text-center">

                <MessageSquare className="mx-auto size-6 text-muted-foreground" />

                <p className="mt-4 text-sm font-medium">
                  No processing events
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  WhatsApp webhook activity will appear here.
                </p>

              </div>

            )}

          </div>

        </section>

      </div>

    </main>
  )
}


function ServiceCard({
  title,
  status,
  healthy,
  icon: Icon,
  detail,
}: {
  title: string
  status: string
  healthy: boolean
  icon: React.ComponentType<{
    className?: string
  }>
  detail: string
}) {
  return (
    <Card className="shadow-none">

      <CardContent className="p-5">

        <div className="flex items-start justify-between gap-4">

          <div className="flex size-9 items-center justify-center rounded-lg border bg-muted/40">

            <Icon className="size-4" />

          </div>


          <span
            className={
              `size-2 rounded-full ${
                healthy
                  ? "bg-emerald-500"
                  : "bg-amber-500"
              }`
            }
          />

        </div>


        <p className="mt-4 text-sm font-semibold">
          {title}
        </p>

        <p className="mt-1 text-xs font-medium">
          {status}
        </p>

        <p className="mt-2 text-xs text-muted-foreground">
          {detail}
        </p>

      </CardContent>

    </Card>
  )
}


function InfoRow({
  label,
  value,
  mono = false,
  last = false,
}: {
  label: string
  value: string
  mono?: boolean
  last?: boolean
}) {
  return (
    <div
      className={
        `flex items-center justify-between gap-5 py-3 ${
          last
            ? ""
            : "border-b"
        }`
      }
    >

      <span className="text-xs text-muted-foreground">
        {label}
      </span>

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

    </div>
  )
}


function InventoryCell({
  label,
  value,
  right = false,
  bottom = false,
}: {
  label: string
  value: number
  right?: boolean
  bottom?: boolean
}) {
  return (
    <div
      className={
        `p-5 ${
          !right
            ? "border-r"
            : ""
        } ${
          !bottom
            ? "border-b"
            : ""
        }`
      }
    >

      <p className="text-xs text-muted-foreground">
        {label}
      </p>

      <p className="mt-2 font-mono text-xl font-semibold tabular-nums">
        {value}
      </p>

    </div>
  )
}


function PipelineMetric({
  label,
  value,
  last = false,
}: {
  label: string
  value: number
  last?: boolean
}) {
  return (
    <div
      className={
        `p-5 ${
          last
            ? ""
            : "border-b sm:border-r xl:border-b-0"
        }`
      }
    >

      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>

      <p className="mt-2 font-mono text-2xl font-semibold tabular-nums">
        {value}
      </p>

    </div>
  )
}