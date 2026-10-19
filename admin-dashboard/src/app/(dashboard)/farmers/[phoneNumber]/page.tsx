import Link from "next/link"

import {
  ArrowLeft,
  Bot,
  ImageIcon,
  Leaf,
  MessageCircle,
  ShieldCheck,
  UserRound,
} from "lucide-react"

import {
  getFarmerHistory,
  getFarmerSessions,
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
  ).format(new Date(value))
}


function maskPhoneNumber(
  phoneNumber: string
) {
  if (phoneNumber.length < 8) {
    return phoneNumber
  }

  return (
    `${phoneNumber.slice(0, 6)}••••${phoneNumber.slice(-3)}`
  )
}


function severityClass(
  severity: string | null
) {
  const value =
    severity?.toLowerCase() ?? ""

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


interface FarmerPageProps {
  params: Promise<{
    phoneNumber: string
  }>
}


export default async function FarmerPage({
  params,
}: FarmerPageProps) {
  const {
    phoneNumber:
      encodedPhoneNumber,
  } =
    await params

  const phoneNumber =
    decodeURIComponent(
      encodedPhoneNumber
    )

  const [
    historyData,
    sessionData,
  ] =
    await Promise.all([
      getFarmerHistory(
        phoneNumber,
        200
      ),

      getFarmerSessions(
        100,
        0
      ),
    ])


  const session =
    sessionData.sessions.find(
      (item) =>
        item.phone_number ===
        phoneNumber
    )


  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1500px] px-6 py-8 lg:px-8 xl:px-10">

        {/* Back */}

        <Link
          href="/farmers"
          className="mb-6 inline-flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          Farmers
        </Link>


        {/* Hero */}

        <section className="flex flex-col gap-5 border-b pb-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Farmer session
            </p>

            <h1 className="font-mono text-2xl font-semibold tracking-tight lg:text-3xl">
              {maskPhoneNumber(
                phoneNumber
              )}
            </h1>

            <p className="mt-2 text-sm text-muted-foreground">
              WhatsApp conversation activity and current assessment context.
            </p>

          </div>


          <div className="flex flex-wrap items-center gap-2">

            <Badge
              variant="outline"
              className="gap-1.5"
            >
              <ShieldCheck className="size-3" />
              WhatsApp session
            </Badge>

            {session?.last_severity && (
              <Badge
                variant="outline"
                className={
                  severityClass(
                    session.last_severity
                  )
                }
              >
                {session.last_severity}
              </Badge>
            )}

          </div>

        </section>


        {/* Context metrics */}

        <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <ContextCard
            label="Latest prediction"
            value={
              session?.last_disease ??
              "No assessment"
            }
            icon={Leaf}
          />

          <ContextCard
            label="Severity"
            value={
              session?.last_severity ??
              "—"
            }
            icon={ShieldCheck}
          />

          <ContextCard
            label="Confidence"
            value={
              percentage(
                session?.last_confidence ??
                null
              )
            }
            icon={Leaf}
            mono
          />

          <ContextCard
            label="Messages"
            value={
              String(
                historyData.count
              )
            }
            icon={MessageCircle}
            mono
          />

        </section>


        <section className="mt-6 grid gap-6 xl:grid-cols-[0.7fr_1.3fr]">

          {/* Session summary */}

          <div className="space-y-6">

            <Card className="shadow-none">

              <CardContent className="p-5">

                <h2 className="text-sm font-semibold">
                  Session details
                </h2>

                <div className="mt-5 space-y-4">

                  <MetadataRow
                    label="Phone"
                    value={
                      maskPhoneNumber(
                        phoneNumber
                      )
                    }
                    mono
                  />

                  <MetadataRow
                    label="Language"
                    value={
                      session?.language?.toUpperCase() ??
                      "—"
                    }
                  />

                  <MetadataRow
                    label="Last active"
                    value={
                      session
                        ? formatDate(
                            session.last_active_at
                          )
                        : "—"
                    }
                    mono
                  />

                  <MetadataRow
                    label="Conversation records"
                    value={
                      String(
                        historyData.count
                      )
                    }
                    mono
                  />

                </div>

              </CardContent>

            </Card>


            <Card className="shadow-none">

              <CardContent className="p-5">

                <h2 className="text-sm font-semibold">
                  Current assessment context
                </h2>

                <div className="mt-5">

                  {session?.last_disease ? (

                    <>
                      <p className="text-lg font-semibold tracking-tight">
                        {session.last_disease}
                      </p>

                      <div className="mt-4 flex flex-wrap gap-2">

                        {session.last_severity && (
                          <Badge
                            variant="outline"
                            className={
                              severityClass(
                                session.last_severity
                              )
                            }
                          >
                            {session.last_severity}
                          </Badge>
                        )}

                        <Badge variant="secondary">
                          {percentage(
                            session.last_confidence
                          )}{" "}
                          confidence
                        </Badge>

                      </div>

                    </>

                  ) : (

                    <div className="py-6 text-center">

                      <Leaf className="mx-auto size-5 text-muted-foreground" />

                      <p className="mt-3 text-sm font-medium">
                        No assessment context
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        This farmer has not completed an image assessment.
                      </p>

                    </div>

                  )}

                </div>

              </CardContent>

            </Card>

          </div>


          {/* Timeline */}

          <section className="overflow-hidden rounded-xl border bg-card">

            <div className="flex items-center justify-between border-b px-5 py-4">

              <div>

                <h2 className="text-sm font-semibold">
                  Conversation timeline
                </h2>

                <p className="mt-1 text-xs text-muted-foreground">
                  Farmer and KILIMO interaction history
                </p>

              </div>

              <Badge
                variant="secondary"
                className="font-mono tabular-nums"
              >
                {historyData.count}
              </Badge>

            </div>


            {historyData.history.length === 0 ? (

              <div className="px-6 py-16 text-center">

                <MessageCircle className="mx-auto size-6 text-muted-foreground" />

                <p className="mt-4 text-sm font-medium">
                  No conversation history
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Farmer interactions will appear here.
                </p>

              </div>

            ) : (

              <div className="divide-y">

                {historyData.history.map(
                  (message) => {

                    const isFarmer =
                      message.role ===
                      "farmer"

                    const isImage =
                      message.message_type ===
                      "image"

                    return (
                      <article
                        key={message.id}
                        className="grid gap-4 px-5 py-5 transition-colors hover:bg-muted/20 md:grid-cols-[92px_1fr]"
                      >

                        <time className="font-mono text-[11px] leading-5 text-muted-foreground">
                          {formatDate(
                            message.created_at
                          )}
                        </time>


                        <div className="min-w-0">

                          <div className="mb-2 flex flex-wrap items-center gap-2">

                            <div
                              className={
                                `flex size-7 items-center justify-center rounded-md border ${
                                  isFarmer
                                    ? "bg-background"
                                    : "bg-muted"
                                }`
                              }
                            >
                              {isFarmer ? (
                                <UserRound className="size-3.5" />
                              ) : (
                                <Bot className="size-3.5" />
                              )}
                            </div>


                            <span className="text-xs font-semibold">
                              {isFarmer
                                ? "Farmer"
                                : "KILIMO"}
                            </span>


                            <Badge
                              variant="outline"
                              className="text-[10px]"
                            >
                              {isImage
                                ? "Image"
                                : "Text"}
                            </Badge>

                          </div>


                          {isImage && (
                            <div className="mb-3 inline-flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                              <ImageIcon className="size-3.5" />
                              Tomato leaf image
                            </div>
                          )}


                          <p className="whitespace-pre-wrap text-sm leading-6 text-foreground/90">
                            {
                              message.content ||
                              (
                                isImage
                                  ? "Image submission recorded."
                                  : "No text content recorded."
                              )
                            }
                          </p>

                        </div>

                      </article>
                    )
                  }
                )}

              </div>

            )}

          </section>

        </section>

      </div>

    </main>
  )
}


function ContextCard({
  label,
  value,
  icon: Icon,
  mono = false,
}: {
  label: string
  value: string
  icon: React.ComponentType<{
    className?: string
  }>
  mono?: boolean
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
                `mt-3 truncate text-lg font-semibold ${
                  mono
                    ? "font-mono tabular-nums"
                    : ""
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

      </CardContent>

    </Card>
  )
}


function MetadataRow({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div className="flex items-start justify-between gap-6 border-b pb-4 last:border-0 last:pb-0">

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