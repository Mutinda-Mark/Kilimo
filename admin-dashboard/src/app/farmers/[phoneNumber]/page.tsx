import Link from "next/link"

import {
  ArrowLeft,
  Bot,
  ImageIcon,
  MessageCircle,
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
  CardHeader,
  CardTitle,
} from "@/components/ui/card"


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


interface FarmerPageProps {
  params: Promise<{
    phoneNumber: string
  }>
}


export default async function FarmerPage({
  params,
}: FarmerPageProps) {

  const {
    phoneNumber: encodedPhoneNumber,
  } = await params

  const phoneNumber =
    decodeURIComponent(
      encodedPhoneNumber
    )

  const [
    historyData,
    sessionData,
  ] = await Promise.all([
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
        item.phone_number
        === phoneNumber
    )

  return (
    <main className="flex-1 p-6 lg:p-10">

      {/* Back link */}

      <Link
        href="/farmers"
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >

        <ArrowLeft className="size-4" />

        Back to farmers

      </Link>


      {/* Farmer heading */}

      <div className="mb-8 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">

        <div>

          <p className="text-sm font-medium text-muted-foreground">
            Farmer Session
          </p>

          <h1 className="text-3xl font-bold tracking-tight">
            {maskPhoneNumber(
              phoneNumber
            )}
          </h1>

          <p className="mt-2 text-muted-foreground">
            WhatsApp conversation and latest
            assessment context.
          </p>

        </div>

        {session?.last_disease && (

          <Badge
            variant="secondary"
            className="w-fit"
          >
            {session.last_disease}
          </Badge>

        )}

      </div>


      {/* Session information */}

      <div className="mb-8 grid gap-4 md:grid-cols-4">

        <Card>

          <CardHeader className="pb-2">

            <CardTitle className="text-sm">
              Latest Prediction
            </CardTitle>

          </CardHeader>

          <CardContent>

            <p className="font-semibold">
              {
                session?.last_disease
                ?? "No assessment"
              }
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="pb-2">

            <CardTitle className="text-sm">
              Severity
            </CardTitle>

          </CardHeader>

          <CardContent>

            <p className="font-semibold">
              {
                session?.last_severity
                ?? "—"
              }
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="pb-2">

            <CardTitle className="text-sm">
              Confidence
            </CardTitle>

          </CardHeader>

          <CardContent>

            <p className="font-semibold">
              {percentage(
                session?.last_confidence
                ?? null
              )}
            </p>

          </CardContent>

        </Card>


        <Card>

          <CardHeader className="pb-2">

            <CardTitle className="text-sm">
              Messages
            </CardTitle>

          </CardHeader>

          <CardContent>

            <p className="font-semibold">
              {historyData.count}
            </p>

          </CardContent>

        </Card>

      </div>


      {/* Conversation */}

      <Card>

        <CardHeader>

          <CardTitle className="flex items-center gap-2">

            <MessageCircle className="size-5" />

            Conversation History

          </CardTitle>

        </CardHeader>


        <CardContent>

          {historyData.history.length === 0 ? (

            <div className="py-12 text-center text-sm text-muted-foreground">
              No conversation messages available.
            </div>

          ) : (

            <div className="space-y-6">

              {historyData.history.map(
                (message) => {

                  const isFarmer =
                    message.role === "farmer"

                  const isImage =
                    message.message_type
                    === "image"

                  return (
                    <div
                      key={message.id}
                      className={
                        `flex ${
                          isFarmer
                            ? "justify-start"
                            : "justify-end"
                        }`
                      }
                    >

                      <div
                        className={
                          `max-w-[85%] rounded-2xl px-4 py-3 md:max-w-[70%] ${
                            isFarmer
                              ? "bg-muted"
                              : "bg-primary text-primary-foreground"
                          }`
                        }
                      >

                        {/* Sender */}

                        <div className="mb-2 flex items-center gap-2">

                          {isFarmer ? (
                            <UserRound className="size-4" />
                          ) : (
                            <Bot className="size-4" />
                          )}

                          <span className="text-xs font-semibold">
                            {
                              isFarmer
                                ? "Farmer"
                                : "KILIMO"
                            }
                          </span>

                          {isImage && (

                            <Badge
                              variant="outline"
                              className={
                                !isFarmer
                                  ? "border-primary-foreground/30 text-primary-foreground"
                                  : ""
                              }
                            >

                              <ImageIcon className="mr-1 size-3" />

                              Image

                            </Badge>

                          )}

                        </div>


                        {/* Message */}

                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {
                            message.content
                            || (
                              isImage
                                ? "Tomato leaf image uploaded."
                                : "No message content."
                            )
                          }
                        </p>


                        {/* Timestamp */}

                        <p
                          className={
                            `mt-2 text-[11px] ${
                              isFarmer
                                ? "text-muted-foreground"
                                : "text-primary-foreground/70"
                            }`
                          }
                        >
                          {formatDate(
                            message.created_at
                          )}
                        </p>

                      </div>

                    </div>
                  )
                }
              )}

            </div>

          )}

        </CardContent>

      </Card>

    </main>
  )
}