import {
  NextResponse,
} from "next/server"

import {
  requireAdminUser,
} from "@/lib/auth"

import {
  getDatabaseStatistics,
  getWhatsAppStatistics,
} from "@/lib/kilimo-api"


export async function GET() {
  await requireAdminUser()

  const [
    database,
    whatsapp,
  ] =
    await Promise.all([
      getDatabaseStatistics(),
      getWhatsAppStatistics(),
    ])


  const notifications = []


  if (!database.connected) {
    notifications.push({
      id: "database",
      severity: "critical",
      title:
        "Database unavailable",
      description:
        "KILIMO cannot currently connect to PostgreSQL.",
      href: "/system",
    })
  }


  if (
    whatsapp.failed > 0
  ) {
    notifications.push({
      id: "whatsapp-failed",
      severity: "warning",
      title:
        `${whatsapp.failed} failed WhatsApp event${
          whatsapp.failed === 1
            ? ""
            : "s"
        }`,
      description:
        "Review recent processing failures.",
      href: "/system",
    })
  }


  if (
    whatsapp.processing > 0
  ) {
    notifications.push({
      id: "whatsapp-processing",
      severity: "info",
      title:
        `${whatsapp.processing} message${
          whatsapp.processing === 1
            ? ""
            : "s"
        } processing`,
      description:
        "WhatsApp work is currently in progress.",
      href: "/system",
    })
  }


  return NextResponse.json({
    count:
      notifications.length,
    notifications,
  })
}